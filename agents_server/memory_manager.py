"""
Memory Manager for ClinicalAgents
Handles conversation memory, context tracking, and entity extraction
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from storage.mongo_async import AsyncMongoStore


class MemoryManager:
    """
    Manages conversation memory and context for the clinical agents system.
    Provides context-aware query processing and entity tracking.
    """
    
    def __init__(self, store: Optional[AsyncMongoStore] = None, llm=None):
        self.store = store or AsyncMongoStore()
        self.llm = llm
        self.context_window_size = 10  # Number of recent messages to keep in active context
        
    async def add_to_memory(
        self,
        session_id: str,
        user_id: str,
        user_message: str,
        agent_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a conversation turn to memory with entity extraction and context tracking
        """
        # Extract entities from both user message and agent response
        entities = self._extract_entities(user_message + " " + agent_response)
        
        # Create memory document
        memory_data = {
            "session_id": session_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow(),
            "user_message": user_message,
            "agent_response": agent_response,
            "entities": entities,
            "metadata": metadata or {}
        }
        
        # Save to database
        memory_id = await self.store.save_memory_state(session_id, memory_data)
        
        # Check if we need to summarize (every 10 turns)
        memory_count = await self.store.get_memory_count(session_id)
        if memory_count % 10 == 0 and memory_count > 0:
            await self._create_summary(session_id, user_id)
        
        return memory_id
    
    async def get_relevant_context(
        self,
        session_id: str,
        current_query: str,
        k: int = 5
    ) -> Dict[str, Any]:
        """
        Get relevant context for the current query from memory
        Returns recent context and extracted entities
        """
        # Get recent memory states
        recent_memory = await self.store.get_memory_state(session_id, limit=self.context_window_size)
        
        # Extract entities from current query
        current_entities = self._extract_entities(current_query)
        
        # Aggregate all entities from recent memory
        all_entities = {
            "diseases": set(),
            "drugs": set(),
            "trials": set()
        }
        
        for memory in recent_memory:
            if "entities" in memory:
                for key in all_entities.keys():
                    if key in memory["entities"]:
                        all_entities[key].update(memory["entities"][key])
        
        # Convert sets to lists for JSON serialization
        all_entities = {k: list(v) for k, v in all_entities.items()}
        
        # Get conversation summary if available
        summary = await self.store.get_conversation_summary(session_id)
        
        # Build context object
        context = {
            "recent_messages": recent_memory[:k],
            "entities": all_entities,
            "current_entities": current_entities,
            "summary": summary,
            "message_count": len(recent_memory)
        }
        
        return context
    
    async def _create_summary(self, session_id: str, user_id: str) -> str:
        """
        Create a summary of the conversation using LLM
        """
        if not self.llm:
            return ""
        
        # Get all memory for this session
        all_memory = await self.store.get_memory_state(session_id, limit=50)
        
        if not all_memory:
            return ""
        
        # Build conversation text
        conversation_text = ""
        for memory in all_memory:
            conversation_text += f"User: {memory.get('user_message', '')}\n"
            conversation_text += f"Assistant: {memory.get('agent_response', '')}\n\n"
        
        # Create summary prompt
        summary_prompt = f"""
        Summarize the following clinical trial conversation in 2-3 sentences.
        Focus on:
        - Main topics discussed (diseases, drugs, trials)
        - Key questions asked by the user
        - Important findings or recommendations
        
        Conversation:
        {conversation_text[:3000]}
        
        Summary:
        """
        
        try:
            summary = self.llm.generate(summary_prompt, max_tokens=200, temperature=0.3)
            
            # Save summary to database
            await self.store.save_conversation_summary(session_id, user_id, summary)
            
            return summary
        except Exception as e:
            print(f"Error creating summary: {e}")
            return ""
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract clinical entities (diseases, drugs, trials) from text
        """
        entities = {
            "diseases": [],
            "drugs": [],
            "trials": []
        }
        
        # Extract NCT trial IDs
        nct_pattern = r'NCT\d{8}'
        trials = re.findall(nct_pattern, text, re.IGNORECASE)
        entities["trials"] = [t.upper() for t in trials]
        
        # Common disease patterns
        disease_patterns = [
            r'\b(diabetes|diabetic)\b',
            r'\b(cancer|carcinoma|tumor|malignancy)\b',
            r'\b(alzheimer\'?s?|dementia)\b',
            r'\b(parkinson\'?s?)\b',
            r'\b(covid-?19|coronavirus)\b',
            r'\b(heart disease|cardiovascular|cardiac)\b',
            r'\b(stroke|cerebrovascular)\b',
            r'\b(asthma|copd|respiratory)\b',
            r'\b(depression|anxiety|mental health)\b',
            r'\b(hiv|aids)\b',
            r'\b(hepatitis)\b',
            r'\b(arthritis|rheumatoid)\b',
            r'\b(hypertension|high blood pressure)\b',
            r'\b(pneumonia|infection)\b'
        ]
        
        diseases = set()
        for pattern in disease_patterns:
            matches = re.findall(pattern, text.lower())
            diseases.update(matches)
        entities["diseases"] = list(diseases)
        
        # Common drug suffixes and patterns
        drug_patterns = [
            r'\b\w+mab\b',  # Monoclonal antibodies
            r'\b\w+nib\b',  # Kinase inhibitors
            r'\b\w+cin\b',  # Antibiotics
            r'\b\w+mycin\b',  # Antibiotics
            r'\b\w+cillin\b',  # Penicillins
            r'\b\w+pril\b',  # ACE inhibitors
            r'\b\w+sartan\b',  # ARBs
            r'\b\w+statin\b',  # Statins
            r'\b\w+olol\b',  # Beta blockers
        ]
        
        drugs = set()
        for pattern in drug_patterns:
            matches = re.findall(pattern, text.lower())
            drugs.update(matches)
        entities["drugs"] = list(drugs)
        
        return entities
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get user preferences for personalized responses
        """
        preferences = await self.store.get_user_preferences(user_id)
        
        if not preferences:
            # Return default preferences
            return {
                "response_style": "balanced",
                "preferred_agents": [],
                "excluded_topics": [],
                "language_level": "intermediate"
            }
        
        return preferences.get("preferences", {})
    
    async def update_user_preference(
        self,
        user_id: str,
        preference_key: str,
        preference_value: Any
    ) -> bool:
        """
        Update a specific user preference
        """
        return await self.store.save_user_preference(user_id, preference_key, preference_value)
    
    async def clear_session_memory(self, session_id: str) -> bool:
        """
        Clear memory for a specific session
        """
        return await self.store.clear_memory_state(session_id)
    
    async def get_entity_history(
        self,
        user_id: str,
        entity_type: str,
        limit: int = 20
    ) -> List[str]:
        """
        Get history of entities (diseases, drugs, trials) mentioned by user
        """
        memories = await self.store.get_user_memory_history(user_id, limit=limit)
        
        entities = set()
        for memory in memories:
            if "entities" in memory and entity_type in memory["entities"]:
                entities.update(memory["entities"][entity_type])
        
        return list(entities)
