"""
Feedback Manager for ClinicalAgents
Handles human feedback collection, pattern learning, and response improvement
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from storage.mongo_async import AsyncMongoStore


class FeedbackManager:
    """
    Manages human feedback collection and learning from feedback.
    Enables the system to improve based on user corrections and preferences.
    """
    
    def __init__(self, store: Optional[AsyncMongoStore] = None, llm=None):
        self.store = store or AsyncMongoStore()
        self.llm = llm
        self.confidence_threshold = 0.7  # Threshold for requesting human review
        
    async def collect_feedback(
        self,
        session_id: str,
        user_id: str,
        message_id: str,
        feedback_type: str,
        feedback_data: Dict[str, Any]
    ) -> str:
        """
        Collect feedback from user on an agent response
        
        Args:
            session_id: Session ID
            user_id: User ID
            message_id: ID of the message being reviewed
            feedback_type: Type of feedback (thumbs_up, thumbs_down, correction, rating)
            feedback_data: Additional feedback data (rating, correction_text, etc.)
        """
        # Get the original message
        original_message = await self._get_message(message_id)
        
        if not original_message:
            raise ValueError(f"Message {message_id} not found")
        
        # Create feedback document
        feedback_doc = {
            "session_id": session_id,
            "user_id": user_id,
            "message_id": message_id,
            "timestamp": datetime.utcnow(),
            "feedback_type": feedback_type,
            "original_response": original_message.get("content", ""),
            "agent_name": original_message.get("agent_outputs", {}).get("activated_agents", ["unknown"])[0] if original_message.get("agent_outputs") else "unknown",
            "query": await self._get_user_query(session_id, message_id),
            **feedback_data
        }
        
        # Save feedback
        feedback_id = await self.store.save_feedback(feedback_doc)
        
        # If this is a correction, learn from it
        if feedback_type == "correction" and "correction_text" in feedback_data:
            await self._learn_from_correction(
                agent_name=feedback_doc["agent_name"],
                query=feedback_doc["query"],
                original_response=feedback_doc["original_response"],
                corrected_response=feedback_data["correction_text"]
            )
        
        return feedback_id
    
    async def _get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get a message by ID from chat memory"""
        return await self.store.get_message_by_id(message_id)
    
    async def _get_user_query(self, session_id: str, message_id: str) -> str:
        """Get the user query that preceded this message"""
        history = await self.store.get_session_history(session_id)
        
        # Find the message and get the previous user message
        for i, msg in enumerate(history):
            if str(msg.get("_id")) == message_id:
                # Look backwards for user message
                for j in range(i-1, -1, -1):
                    if history[j].get("role") == "user":
                        return history[j].get("content", "")
        
        return ""
    
    async def _learn_from_correction(
        self,
        agent_name: str,
        query: str,
        original_response: str,
        corrected_response: str
    ):
        """
        Learn from a user correction and store as a pattern
        """
        # Extract the pattern from the correction
        pattern = await self._extract_pattern(query, original_response, corrected_response)
        
        if pattern:
            # Check if similar pattern exists
            existing_pattern = await self.store.get_learned_pattern(
                agent_name=agent_name,
                query_pattern=pattern["query_pattern"]
            )
            
            if existing_pattern:
                # Update existing pattern
                await self.store.update_learned_pattern(
                    pattern_id=existing_pattern["_id"],
                    learned_response=corrected_response,
                    feedback_count=existing_pattern.get("feedback_count", 0) + 1
                )
            else:
                # Create new pattern
                await self.store.save_learned_pattern(pattern)
    
    async def _extract_pattern(
        self,
        query: str,
        original_response: str,
        corrected_response: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract a learnable pattern from a correction using LLM
        """
        if not self.llm:
            # Fallback: simple pattern extraction
            return {
                "query_pattern": query.lower()[:100],
                "learned_response": corrected_response,
                "confidence": 0.5,
                "pattern_type": "correction",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "feedback_count": 1,
                "examples": [{
                    "query": query,
                    "original": original_response,
                    "corrected": corrected_response
                }]
            }
        
        # Use LLM to extract generalizable pattern
        pattern_prompt = f"""
        Analyze this user correction and extract a generalizable pattern.
        
        User Query: {query}
        Original Response: {original_response[:500]}
        Corrected Response: {corrected_response[:500]}
        
        Extract:
        1. What type of query is this? (general pattern, not specific details)
        2. What was wrong with the original response?
        3. What principle should be applied in similar cases?
        
        Format your response as:
        PATTERN: <general query pattern>
        ISSUE: <what was wrong>
        PRINCIPLE: <what to do instead>
        """
        
        try:
            llm_response = self.llm.generate(pattern_prompt, max_tokens=300, temperature=0.3)
            
            # Parse LLM response
            pattern_match = re.search(r'PATTERN:\s*(.+)', llm_response)
            issue_match = re.search(r'ISSUE:\s*(.+)', llm_response)
            principle_match = re.search(r'PRINCIPLE:\s*(.+)', llm_response)
            
            if pattern_match:
                return {
                    "query_pattern": pattern_match.group(1).strip(),
                    "learned_response": corrected_response,
                    "confidence": 0.7,
                    "pattern_type": "correction",
                    "issue": issue_match.group(1).strip() if issue_match else "",
                    "principle": principle_match.group(1).strip() if principle_match else "",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "feedback_count": 1,
                    "examples": [{
                        "query": query,
                        "original": original_response,
                        "corrected": corrected_response
                    }]
                }
        except Exception as e:
            print(f"Error extracting pattern with LLM: {e}")
        
        return None
    
    async def get_similar_feedback(
        self,
        query: str,
        agent_name: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get similar feedback for a query to apply learned corrections
        """
        # Get learned patterns for this agent
        patterns = await self.store.get_learned_patterns(agent_name=agent_name, limit=limit)
        
        # Simple similarity matching (can be enhanced with embeddings)
        query_lower = query.lower()
        similar_patterns = []
        
        for pattern in patterns:
            pattern_text = pattern.get("query_pattern", "").lower()
            
            # Check for keyword overlap
            query_words = set(query_lower.split())
            pattern_words = set(pattern_text.split())
            overlap = len(query_words & pattern_words)
            
            if overlap > 0:
                pattern["similarity_score"] = overlap / max(len(query_words), len(pattern_words))
                similar_patterns.append(pattern)
        
        # Sort by similarity and confidence
        similar_patterns.sort(
            key=lambda x: (x.get("similarity_score", 0) * x.get("confidence", 0)),
            reverse=True
        )
        
        return similar_patterns[:limit]
    
    async def apply_learned_corrections(
        self,
        response: str,
        query: str,
        agent_name: str
    ) -> Dict[str, Any]:
        """
        Apply learned corrections to a response if applicable
        """
        # Get similar feedback
        similar_feedback = await self.get_similar_feedback(query, agent_name, limit=3)
        
        if not similar_feedback:
            return {
                "modified": False,
                "response": response,
                "applied_patterns": []
            }
        
        # Check if any high-confidence patterns apply
        applicable_patterns = [
            p for p in similar_feedback
            if p.get("confidence", 0) >= 0.7 and p.get("similarity_score", 0) >= 0.5
        ]
        
        if not applicable_patterns:
            return {
                "modified": False,
                "response": response,
                "applied_patterns": []
            }
        
        # Apply the highest-confidence pattern
        best_pattern = applicable_patterns[0]
        
        # Use LLM to apply the pattern principle if available
        if self.llm and "principle" in best_pattern:
            improvement_prompt = f"""
            Improve this response based on learned feedback.
            
            Original Response: {response}
            
            Learned Principle: {best_pattern.get('principle', '')}
            
            Example Correction: {best_pattern.get('learned_response', '')[:300]}
            
            Provide an improved response that applies the learned principle while maintaining accuracy.
            """
            
            try:
                improved_response = self.llm.generate(improvement_prompt, max_tokens=500, temperature=0.5)
                
                return {
                    "modified": True,
                    "response": improved_response,
                    "applied_patterns": [best_pattern.get("query_pattern", "")],
                    "original_response": response
                }
            except Exception as e:
                print(f"Error applying learned correction: {e}")
        
        return {
            "modified": False,
            "response": response,
            "applied_patterns": []
        }
    
    def calculate_confidence(
        self,
        agent_results: Dict[str, Any],
        context: Dict[str, Any]
    ) -> float:
        """
        Calculate confidence score for agent results
        
        Factors:
        - Number of agents activated
        - Consistency between agents
        - Availability of relevant context
        - Quality of agent responses
        """
        confidence = 0.5  # Base confidence
        
        # Factor 1: Multiple agents agreeing increases confidence
        activated_agents = agent_results.get("activated_agents", [])
        if len(activated_agents) > 1:
            confidence += 0.15
        
        # Factor 2: Successful agent execution
        if agent_results.get("status") == "success":
            confidence += 0.2
        
        # Factor 3: Relevant context available
        if context.get("message_count", 0) > 0:
            confidence += 0.1
        
        # Factor 4: Entities extracted
        if context.get("entities"):
            entity_count = sum(len(v) for v in context.get("entities", {}).values())
            if entity_count > 0:
                confidence += 0.05
        
        # Cap at 1.0
        return min(confidence, 1.0)
    
    def should_request_human_review(self, confidence: float) -> bool:
        """
        Determine if human review should be requested based on confidence
        """
        return confidence < self.confidence_threshold
    
    async def analyze_feedback_patterns(self, agent_name: str) -> Dict[str, Any]:
        """
        Analyze feedback patterns for an agent to identify improvement areas
        """
        # Get all feedback for this agent
        feedback = await self.store.get_feedback_for_agent(agent_name, limit=100)
        
        if not feedback:
            return {
                "total_feedback": 0,
                "positive_ratio": 0,
                "common_issues": [],
                "improvement_areas": []
            }
        
        # Analyze feedback
        total = len(feedback)
        positive = sum(1 for f in feedback if f.get("feedback_type") in ["thumbs_up", "rating"] and f.get("rating", 0) >= 4)
        corrections = [f for f in feedback if f.get("feedback_type") == "correction"]
        
        # Extract common issues from corrections
        common_issues = []
        if corrections and self.llm:
            issues_text = "\n".join([
                f"- {f.get('correction_text', '')[:100]}"
                for f in corrections[:10]
            ])
            
            analysis_prompt = f"""
            Analyze these user corrections and identify common issues:
            
            {issues_text}
            
            List the top 3 common issues or improvement areas.
            """
            
            try:
                issues_response = self.llm.generate(analysis_prompt, max_tokens=200, temperature=0.3)
                common_issues = [line.strip() for line in issues_response.split("\n") if line.strip()]
            except Exception as e:
                print(f"Error analyzing feedback patterns: {e}")
        
        return {
            "total_feedback": total,
            "positive_ratio": positive / total if total > 0 else 0,
            "correction_count": len(corrections),
            "common_issues": common_issues[:3],
            "improvement_areas": common_issues[:3]
        }
