"""
HumanProxyAgent
 - Main interface between user and AI agents
 - Maintains session context, routes to orchestrator, reasoner, reviewer
 - Logs chat memory and audit events to MongoDB (async)
 - Provides history fetch and replay helpers
 - Integrates memory state and feedback learning
"""
from __future__ import annotations

import asyncio
import uuid
import os
from typing import Any, Dict, Optional

from agents.reasoner_agent import ReasonerAgent
from agents.reviewer_agent import ReviewerAgent
from simple_dynamic_orchestrator import SimpleDynamicOrchestrator
from storage.mongo_async import AsyncMongoStore
from memory_manager import MemoryManager
from feedback_manager import FeedbackManager


class HumanProxyAgent:
    def __init__(
        self,
        llm,
        store: Optional[AsyncMongoStore] = None,
        orchestrator: Optional[SimpleDynamicOrchestrator] = None,
        session_id: Optional[str] = None,
    ):
        self.llm = llm
        self.session_id = session_id or str(uuid.uuid4())
        self.store = store or AsyncMongoStore()
        self.orchestrator = orchestrator or SimpleDynamicOrchestrator(llm)
        self.reasoner = ReasonerAgent(llm)
        self.reviewer = ReviewerAgent(llm)
        
        # Initialize memory and feedback managers
        self.memory_manager = MemoryManager(store=self.store, llm=llm)
        self.feedback_manager = FeedbackManager(store=self.store, llm=llm)
        
        # Snapshot cadence (every N turns). 1 = every turn
        try:
            self.snapshot_every = max(1, int(os.getenv("SNAPSHOT_EVERY", "1")))
        except Exception:
            self.snapshot_every = 1
        self._turn_counts: dict[str, int] = {}

    # -------- async core --------
    async def handle_user_prompt_async(self, prompt: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        sid = self.session_id
        
        # 1) Get relevant context from memory
        try:
            context = await self.memory_manager.get_relevant_context(sid, prompt)
        except Exception as e:
            print(f"Error getting context: {e}")
            context = {}
        
        # 2) log user prompt
        try:
            await self.store.log_event(sid, event="user_prompt", agent_name="user", content={"prompt": prompt}, status="received")
            await self.store.save_chat_message(sid, role="user", content=prompt)
        except Exception:
            # Storage failures should not block the conversation
            pass

        # 3) orchestrate with planning-first workflow
        print("\n" + "="*60)
        print("🤖 HUMAN PROXY AGENT - Starting Clinical Trial Analysis")
        print("="*60)
        
        # Use planning-enabled workflow
        agent_results = self.orchestrator.process_query_with_planning(prompt)
        
        try:
            await self.store.log_event(sid, event="orchestrator_results", agent_name="orchestrator", content=agent_results, status=agent_results.get("status", "ok"))
        except Exception:
            pass

        # 4) build context for reasoner and fetch prior history
        try:
            history = await self.store.get_session_history(sid)
        except Exception:
            history = []
        reasoner_out = self.reasoner.reason(prompt, agent_results, history)
        try:
            await self.store.log_event(sid, event="reasoner_output", agent_name="ReasonerAgent", content=reasoner_out, status="ok")
        except Exception:
            pass

        # 5) review before finalizing
        review = self.reviewer.review(prompt, reasoner_out)
        try:
            await self.store.log_event(sid, event="review", agent_name="ReviewerAgent", content=review, status=review.get("status", "ok"))
        except Exception:
            pass

        final_answer = reasoner_out.get("answer", "")
        if review.get("status") == "needs_revision":
            suggestions = review.get("suggestions", [])
            revised = self.reasoner.revise(final_answer, suggestions)
            final_answer = revised or final_answer
            try:
                await self.store.log_event(sid, event="revision_applied", agent_name="ReasonerAgent", content={"suggestions": suggestions, "revised": final_answer}, status="ok")
            except Exception:
                pass
        
        # 6) Apply learned corrections from feedback
        try:
            activated_agent = agent_results.get("activated_agents", ["general"])[0]
            correction_result = await self.feedback_manager.apply_learned_corrections(
                response=final_answer,
                query=prompt,
                agent_name=activated_agent
            )
            
            if correction_result.get("modified"):
                final_answer = correction_result["response"]
                print(f"Applied learned correction from pattern: {correction_result.get('applied_patterns')}")
        except Exception as e:
            print(f"Error applying learned corrections: {e}")
        
        # 7) Calculate confidence score
        try:
            confidence = self.feedback_manager.calculate_confidence(agent_results, context)
            needs_review = self.feedback_manager.should_request_human_review(confidence)
        except Exception as e:
            print(f"Error calculating confidence: {e}")
            confidence = 0.8
            needs_review = False

        # 8) save assistant message & snapshot
        try:
            await self.store.save_chat_message(sid, role="assistant", content=final_answer, agent_outputs={
                "activated_agents": agent_results.get("activated_agents", []),
                "reasoner": reasoner_out,
                "review": review,
                "confidence": confidence,
                "needs_review": needs_review,
                "context_used": context
            })
            # Increment turn count and snapshot conditionally
            self._turn_counts[sid] = self._turn_counts.get(sid, 0) + 1
            if self._turn_counts[sid] % self.snapshot_every == 0:
                await self.store.snapshot_session(sid)
        except Exception:
            pass
        
        # 9) Save to memory
        try:
            if user_id:
                await self.memory_manager.add_to_memory(
                    session_id=sid,
                    user_id=user_id,
                    user_message=prompt,
                    agent_response=final_answer,
                    metadata={
                        "activated_agents": agent_results.get("activated_agents", []),
                        "confidence": confidence
                    }
                )
        except Exception as e:
            print(f"Error saving to memory: {e}")

        return {
            "session_id": sid,
            "final_output": final_answer,
            "review": review,
            "reasoner": reasoner_out,
            "agent_results": agent_results,
            "confidence": confidence,
            "needs_review": needs_review,
            "context": context
        }

    # -------- sync wrapper for ease-of-use in existing code --------
    def handle_user_prompt(self, prompt: str) -> Dict[str, Any]:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Running inside an event loop (e.g., notebook) – create a new task
                return asyncio.run(self.handle_user_prompt_async(prompt))  # type: ignore
            else:
                return loop.run_until_complete(self.handle_user_prompt_async(prompt))
        except RuntimeError:
            # No running loop
            return asyncio.run(self.handle_user_prompt_async(prompt))

    # -------- utilities --------
    async def fetch_session_history(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        sid = session_id or self.session_id
        history = await self.store.get_session_history(sid)
        audits = await self.store.get_audit_logs(sid)
        return {"session_id": sid, "history": history, "audit_logs": audits}

    async def replay_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        sid = session_id or self.session_id
        audits = await self.store.get_audit_logs(sid)
        # A simple replay returns ordered events; a full re-execution could be implemented if needed
        return {"session_id": sid, "events": audits}
