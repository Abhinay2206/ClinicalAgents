"""
ReasonerAgent
 - Performs reasoning, retrieval (from orchestrator outputs), and generation
 - Returns a structured output including a concise reasoning trace
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

def _extract_json(text: str) -> str:
    """Extract a JSON object from raw LLM output.
    - Strips Markdown code fences if present
    - Finds the first {...} JSON object span
    """
    t = text.strip()
    # Remove markdown code fences
    if t.startswith("```"):
        # ```json\n{...}\n```
        t = t.strip('`')
        # After stripping backticks, try to locate the first '{' to the last '}'
    # Find JSON object boundaries
    start = t.find('{')
    end = t.rfind('}')
    if start != -1 and end != -1 and end > start:
        return t[start:end+1]
    return text


class ReasonerAgent:
    def __init__(self, llm):
        self.llm = llm

    def _build_prompt(self, user_prompt: str, context: Dict[str, Any], history: Optional[List[Dict[str, Any]]] = None) -> str:
        activated = ", ".join(context.get("activated_agents", []))
        individual = context.get("individual_results", [])
        synthesized = context.get("synthesized_summary", "")

        history_snippets = []
        if history:
            for msg in history[-5:]:  # include last 5 turns for brevity
                role = msg.get("role") or ("assistant" if "bot" in msg else "user")
                text = msg.get("content") or msg.get("user") or msg.get("bot") or ""
                if text:
                    history_snippets.append(f"{role}: {text[:500]}")

        indiv_compiled = []
        for r in individual:
            if r.get("status") == "success":
                indiv_compiled.append({
                    "agent": r.get("agent"),
                    "query_used": r.get("query_used"),
                    "excerpt": (r.get("result", "")[:1200] if isinstance(r.get("result"), str) else str(r.get("result"))[:1200])
                })

        prompt = f"""
You are a clinical reasoning assistant. Analyze the user's prompt using the provided multi-agent context and produce a structured JSON response.

USER_PROMPT:\n{user_prompt}

RECENT_HISTORY (last few turns, may be empty):
{json.dumps(history_snippets, ensure_ascii=False)}

AGENTS_ACTIVATED: {activated}

INDIVIDUAL_AGENT_RESULTS (truncated excerpts):
{json.dumps(indiv_compiled, ensure_ascii=False)}

SYNTHESIZED_SUMMARY (free-form text, may be absent):
{synthesized[:2000]}

Return a JSON object with this exact schema:
{{
  "answer": string,            // final answer to show the user (clear and helpful)
  "steps": [string, ...],      // 3-8 concise bullets describing the reasoning steps taken (no sensitive chain-of-thought; keep it brief)
  "citations": [string, ...],  // list of NCT IDs, study names, or references if present; else []
  "used_agents": [string, ...],// agents used in reasoning
  "confidence": string,        // one of: "low" | "medium" | "high"
  "notes": string              // short notes to help a reviewer (constraints, assumptions)
}}

Important:
- The value MUST be valid JSON, with double quotes, and no extra commentary.
- Keep "steps" concise; do not reveal hidden chain-of-thought.
- If no citations exist, return an empty array for "citations".
"""
        return prompt

    def reason(self, user_prompt: str, context: Dict[str, Any], history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        prompt = self._build_prompt(user_prompt, context, history)
        raw = self.llm.generate(prompt, max_tokens=1200, temperature=0.4)
        try:
            data = json.loads(_extract_json(raw))
        except Exception:
            # Fallback: wrap as JSON
            data = {
                "answer": raw,
                "steps": ["Summarized multi-agent context", "Formulated a patient-friendly answer"],
                "citations": [],
                "used_agents": context.get("activated_agents", []),
                "confidence": "medium",
                "notes": "Model returned non-JSON; wrapped into structured schema."
            }
        return data

    def revise(self, current_answer: str, suggestions: List[str]) -> str:
        prompt = f"""
Revise the following answer to improve accuracy, clarity, and consistency based on reviewer suggestions.

CURRENT_ANSWER:\n{current_answer}

REVIEWER_SUGGESTIONS:\n{json.dumps(suggestions, ensure_ascii=False)}

Return only the revised answer text.
"""
        return self.llm.generate(prompt, max_tokens=800, temperature=0.3)
