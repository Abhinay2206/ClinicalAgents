from __future__ import annotations

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class QueryContext:
    """Represents the context of a query"""
    is_followup: bool
    is_refinement: bool
    is_expansion: bool
    referenced_entities: Dict[str, List[str]]
    topic_continuation: bool
    needs_context_enrichment: bool
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB serialization"""
        return {
            'is_followup': self.is_followup,
            'is_refinement': self.is_refinement,
            'is_expansion': self.is_expansion,
            'referenced_entities': self.referenced_entities,
            'topic_continuation': self.topic_continuation,
            'needs_context_enrichment': self.needs_context_enrichment,
            'confidence': self.confidence
        }


class ContextProcessor:
    
    def __init__(self, llm=None):
        self.llm = llm
        
        # Follow-up indicators
        self.followup_patterns = [
            r'\b(what about|how about)\b',
            r'\b(also|additionally|furthermore)\b',
            r'\b(and|but) (what|how|can|does)\b',
            r'^\s*(it|its|that|this|these)',  # Starting with pronouns
        ]
        
        # Refinement indicators (user wants to modify/improve previous response)
        self.refinement_patterns = [
            r'\b(too|very|more|less) (general|specific|detailed|simple|technical)\b',
            r'\b(make it|can you make)\b',
            r'\b(focus on|concentrate on|emphasize)\b',
            r'\b(instead|rather|prefer)\b',
            r'\b(not |don\'t |doesn\'t )(want|need|like)\b',
        ]
        
        # Expansion indicators (user wants more details)
        self.expansion_patterns = [
            r'\b(tell me more|more (info|information|details|data))\b',
            r'\b(expand|elaborate|explain (more|further))\b',
            r'\b(can you (give|provide) more)\b',
            r'\b(what else|anything else)\b',
            r'\b(go (deeper|further)|dive deeper)\b',
        ]
    
    def analyze_query(
        self, 
        query: str, 
        conversation_history: List[Dict[str, Any]],
        memory_state: Dict[str, Any]
    ) -> QueryContext:
        query_lower = query.lower().strip()
        
        # Check if this is a follow-up
        is_followup = self._is_followup(query_lower, conversation_history)
        
        # Check if this is a refinement request
        is_refinement = self._is_refinement(query_lower)
        
        # Check if this is an expansion request
        is_expansion = self._is_expansion(query_lower)
        
        # Extract referenced entities
        referenced_entities = self._extract_referenced_entities(
            query, 
            memory_state
        )
        
        # Check if topic continues from previous
        topic_continuation = self._has_topic_continuation(
            query_lower, 
            conversation_history
        )
        
        # Determine if context enrichment is needed
        needs_enrichment = (
            is_followup or 
            is_refinement or 
            is_expansion or 
            topic_continuation or
            len(referenced_entities) > 0
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            is_followup, is_refinement, is_expansion, 
            referenced_entities, topic_continuation
        )
        
        return QueryContext(
            is_followup=is_followup,
            is_refinement=is_refinement,
            is_expansion=is_expansion,
            referenced_entities=referenced_entities,
            topic_continuation=topic_continuation,
            needs_context_enrichment=needs_enrichment,
            confidence=confidence
        )
    
    def _is_followup(
        self, 
        query: str, 
        conversation_history: List[Dict[str, Any]]
    ) -> bool:
        """Check if query is a follow-up to previous conversation"""
        # Must have previous conversation
        if not conversation_history:
            return False
        
        # Check for follow-up patterns
        for pattern in self.followup_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        
        # Check if query is very short (likely a follow-up)
        if len(query.split()) <= 5:
            # And contains question words or pronouns
            if any(word in query for word in ['it', 'that', 'this', 'what', 'how', 'why']):
                return True
        
        return False
    
    def _is_refinement(self, query: str) -> bool:
        """Check if query is asking to refine/modify previous response"""
        for pattern in self.refinement_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False
    
    def _is_expansion(self, query: str) -> bool:
        """Check if query is asking for more details/expansion"""
        for pattern in self.expansion_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        
        # Single word expansions
        if query.strip() in ['more', 'continue', 'elaborate', 'expand', 'details']:
            return True
        
        return False
    
    def _extract_referenced_entities(
        self, 
        query: str, 
        memory_state: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Extract entities that are referenced in the query"""
        referenced = {}
        
        # If memory state has entities
        if 'entities' in memory_state:
            entities = memory_state['entities']
            
            # Check if any known entities are mentioned in query
            for entity_type in ['drugs', 'diseases', 'trials']:
                if entity_type in entities:
                    mentioned = [
                        entity for entity in entities[entity_type]
                        if entity.lower() in query.lower()
                    ]
                    if mentioned:
                        referenced[entity_type] = mentioned
        
        return referenced
    
    def _has_topic_continuation(
        self, 
        query: str, 
        conversation_history: List[Dict[str, Any]]
    ) -> bool:
        if not conversation_history:
            return False
        
        # Get last user message
        last_user_msg = None
        for msg in reversed(conversation_history):
            if msg.get('role') == 'user':
                last_user_msg = msg.get('content', '')
                break
        
        if not last_user_msg:
            return False
        
        # Extract keywords (simple word overlap check)
        current_words = set(re.findall(r'\b\w{4,}\b', query.lower()))
        last_words = set(re.findall(r'\b\w{4,}\b', last_user_msg.lower()))
        
        # Remove common stop words
        stop_words = {'what', 'where', 'when', 'which', 'about', 'from', 'with', 'this', 'that', 'have', 'does'}
        current_words -= stop_words
        last_words -= stop_words
        
        # Check overlap
        overlap = current_words & last_words
        
        # If significant overlap (>30%), likely same topic
        if current_words and len(overlap) / len(current_words) > 0.3:
            return True
        
        return False
    
    def _calculate_confidence(
        self,
        is_followup: bool,
        is_refinement: bool,
        is_expansion: bool,
        referenced_entities: Dict[str, List[str]],
        topic_continuation: bool
    ) -> float:
        """Calculate confidence that this query needs context"""
        confidence = 0.0
        
        if is_followup:
            confidence += 0.3
        if is_refinement:
            confidence += 0.25
        if is_expansion:
            confidence += 0.25
        if referenced_entities:
            confidence += 0.1
        if topic_continuation:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def enrich_with_context(
        self,
        query: str,
        query_context: QueryContext,
        memory_state: Dict[str, Any],
        last_response: Optional[str] = None
    ) -> str:
        """
        Enrich query with conversational context
        
        Args:
            query: Original user query
            query_context: Analyzed query context
            memory_state: Memory state with history
            last_response: Previous agent response (if any)
            
        Returns:
            Enriched query with context
        """
        if not query_context.needs_context_enrichment:
            return query
        
        enriched = query
        
        # If it's a refinement, add context about what to refine
        if query_context.is_refinement and last_response:
            enriched = self._enrich_refinement(query, last_response)
        
        # If it's an expansion, add context about what to expand
        elif query_context.is_expansion and last_response:
            enriched = self._enrich_expansion(query, last_response, memory_state)
        
        # If it's a follow-up with entities, ensure entities are explicit
        elif query_context.is_followup and query_context.referenced_entities:
            enriched = self._enrich_followup(query, query_context.referenced_entities)
        
        return enriched
    
    def _enrich_refinement(self, query: str, last_response: str) -> str:
        """Enrich a refinement query with context"""
        # Extract what needs refinement
        context_snippet = last_response[:300]
        
        return f"{query}\n\nContext (previous response): {context_snippet}"
    
    def _enrich_expansion(
        self, 
        query: str, 
        last_response: str,
        memory_state: Dict[str, Any]
    ) -> str:
        """Enrich an expansion query with context"""
        # Identify what to expand
        context_snippet = last_response[:300]
        
        # Add entity context if available
        entities_context = ""
        if 'entities' in memory_state and memory_state['entities']:
            recent_entities = []
            for etype, elist in memory_state['entities'].items():
                if elist:
                    recent_entities.append(f"{etype}: {', '.join(elist[-2:])}")
            if recent_entities:
                entities_context = f"\nEntities discussed: {'; '.join(recent_entities)}"
        
        return f"{query}\n\nPrevious response: {context_snippet}{entities_context}"
    
    def _enrich_followup(
        self, 
        query: str, 
        referenced_entities: Dict[str, List[str]]
    ) -> str:
        """Enrich a follow-up query by making entities explicit"""
        # Build entity context
        entity_parts = []
        for etype, entities in referenced_entities.items():
            if entities:
                entity_parts.append(f"{etype}: {', '.join(entities)}")
        
        if entity_parts:
            entity_context = " | ".join(entity_parts)
            return f"{query}\n\nContext: {entity_context}"
        
        return query
    
    def get_conversation_summary(
        self, 
        conversation_history: List[Dict[str, Any]],
        max_turns: int = 5
    ) -> str:
        """
        Generate a brief summary of recent conversation for context
        """
        if not conversation_history:
            return "No previous conversation"
        
        # Get last N turns
        recent = conversation_history[-max_turns * 2:]  # *2 for user + assistant pairs
        
        summary_lines = []
        for msg in recent:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:150]  # Truncate
            summary_lines.append(f"{role.capitalize()}: {content}")
        
        return "\n".join(summary_lines)
