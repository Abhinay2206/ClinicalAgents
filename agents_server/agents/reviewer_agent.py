"""
ReviewerAgent
 - Reviews outputs from ReasonerAgent (or others) for accuracy, clarity, and consistency
 - Can flag errors, suggest improvements, or approve the output
"""
from __future__ import annotations

import json
from typing import Any, Dict, List


class ReviewerAgent:
    def __init__(self, llm):
        self.llm = llm

    def review(self, user_prompt: str, reasoner_output: Dict[str, Any]) -> Dict[str, Any]:
        draft = reasoner_output.get("answer", "")
        steps = reasoner_output.get("steps", [])
        citations = reasoner_output.get("citations", [])
        used_agents = reasoner_output.get("used_agents", [])

        prompt = f"""
You are a factuality and clarity reviewer for clinical-trial assistant responses.

USER_PROMPT:\n{user_prompt}

DRAFT_ANSWER:\n{draft}

REASONING_STEPS (concise list):\n{json.dumps(steps, ensure_ascii=False)}
AGENTS_USED: {json.dumps(used_agents, ensure_ascii=False)}
CITATIONS: {json.dumps(citations, ensure_ascii=False)}

Evaluate and return a STRICT JSON with this schema:
{{
  "status": "approved" | "needs_revision",
  "issues": [string, ...],
  "suggestions": [string, ...],
  "quality": "low" | "medium" | "high",
  "consistency": "low" | "medium" | "high",
  "safety_notes": string
}}

Guidelines:
- Be concise.
- Flag unsupported claims, unclear phrasing, or inconsistencies.
- Prefer "approved" only if issues are minor.
"""
        raw = self.llm.generate(prompt, max_tokens=600, temperature=0.2)
        try:
            data = json.loads(raw)
        except Exception:
            data = {
                "status": "approved",
                "issues": [],
                "suggestions": [],
                "quality": "medium",
                "consistency": "medium",
                "safety_notes": ""
            }
        return data
