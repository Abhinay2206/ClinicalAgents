"""
Reference Resolver for ClinicalAgents
Handles pronoun and reference resolution in conversational context
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Any


class ReferenceResolver:
    """
    Resolves pronouns and references in queries using conversation context.
    Enables natural follow-up queries like "What about its efficacy?" 
    """
    
    def __init__(self, llm=None):
        self.llm = llm
        
        # Common pronouns that need resolution
        self.pronouns = ['it', 'its', 'that', 'this', 'these', 'those', 'them', 'they']
        
        # Expansion triggers
        self.expansion_triggers = [
            'more', 'expand', 'elaborate', 'details', 'explain', 'clarify',
            'tell me more', 'can you', 'what about', 'how about'
        ]
    
    def needs_resolution(self, query: str) -> bool:
        """
        Check if query contains references that need resolution
        """
        query_lower = query.lower()
        
        # Check for pronouns
        has_pronouns = any(
            re.search(r'\b' + pronoun + r'\b', query_lower)
            for pronoun in self.pronouns
        )
        
        # Check for expansion triggers
        has_expansion = any(
            trigger in query_lower 
            for trigger in self.expansion_triggers
        )
        
        # Check for relative references without explicit subject
        has_relative = bool(re.search(r'\b(more|additional|further)\s+(info|information|details|data)\b', query_lower))
        
        return has_pronouns or has_expansion or has_relative
    
    def resolve_references(
        self, 
        query: str, 
        context: Dict[str, Any]
    ) -> str:
        """
        Resolve references in query using conversation context
        
        Args:
            query: Current user query
            context: Conversation context with entities, last messages, etc.
            
        Returns:
            Query with references resolved
        """
        if not self.needs_resolution(query):
            return query
        
        # Extract context entities
        last_entities = self._extract_last_entities(context)
        last_topic = self._extract_last_topic(context)
        
        # Try simple pattern-based resolution first
        resolved = self._resolve_with_patterns(query, last_entities, last_topic)
        
        # If LLM available and resolution seems incomplete, use LLM
        if self.llm and self._needs_llm_resolution(resolved, query):
            resolved = self._resolve_with_llm(query, context)
        
        return resolved
    
    def _extract_last_entities(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Extract the most recently mentioned entities from context"""
        entities = {}
        
        # Get entities from context
        if 'entities' in context:
            ctx_entities = context['entities']
            
            # Get most recent drug
            if 'drugs' in ctx_entities and ctx_entities['drugs']:
                entities['drug'] = ctx_entities['drugs'][-1]
            
            # Get most recent disease
            if 'diseases' in ctx_entities and ctx_entities['diseases']:
                entities['disease'] = ctx_entities['diseases'][-1]
            
            # Get most recent trial
            if 'trials' in ctx_entities and ctx_entities['trials']:
                entities['trial'] = ctx_entities['trials'][-1]
        
        # Also check current_entities for the last user message
        if 'current_entities' in context:
            curr = context['current_entities']
            if 'drugs' in curr and curr['drugs']:
                entities['drug'] = curr['drugs'][0]
            if 'diseases' in curr and curr['diseases']:
                entities['disease'] = curr['diseases'][0]
            if 'trials' in curr and curr['trials']:
                entities['trial'] = curr['trials'][0]
        
        return entities
    
    def _extract_last_topic(self, context: Dict[str, Any]) -> str:
        """Extract the main topic from the last conversation turn"""
        if 'recent_messages' in context and context['recent_messages']:
            last_msg = context['recent_messages'][0]
            
            # Try to get the user message
            if 'user_message' in last_msg:
                return last_msg['user_message']
            
            # Or extract from agent response
            if 'agent_response' in last_msg:
                response = last_msg['agent_response']
                # Get first sentence as topic
                sentences = response.split('.')
                if sentences:
                    return sentences[0].strip()
        
        return ""
    
    def _resolve_with_patterns(
        self, 
        query: str, 
        entities: Dict[str, str],
        last_topic: str
    ) -> str:
        """
        Resolve references using pattern matching
        """
        resolved = query
        
        # Pattern 1: "it" or "its" -> most recent drug or disease
        if re.search(r'\b(it|its)\b', resolved, re.IGNORECASE):
            # Prefer drug, then disease
            subject = entities.get('drug') or entities.get('disease') or entities.get('trial')
            
            if subject:
                # Replace "it" with subject (preserve case)
                resolved = re.sub(
                    r'\bit\b', 
                    subject, 
                    resolved, 
                    flags=re.IGNORECASE
                )
                # Replace "its" with "subject's"
                resolved = re.sub(
                    r'\bits\b', 
                    f"{subject}'s", 
                    resolved, 
                    flags=re.IGNORECASE
                )
        
        # Pattern 2: "that" or "this" -> reference to last topic
        if re.search(r'\b(that|this)\b', resolved, re.IGNORECASE):
            subject = entities.get('drug') or entities.get('disease')
            if subject:
                resolved = re.sub(
                    r'\b(that|this)\b',
                    subject,
                    resolved,
                    count=1,
                    flags=re.IGNORECASE
                )
        
        # Pattern 3: "What about X?" where X is vague -> "What about [entity]'s X?"
        match = re.search(r'what about (the |its )?(\w+)', resolved, re.IGNORECASE)
        if match and entities.get('drug'):
            aspect = match.group(2)
            # If aspect is generic (efficacy, safety, etc.), add entity
            if aspect.lower() in ['efficacy', 'safety', 'effectiveness', 'side effects', 'risks', 'benefits']:
                drug = entities['drug']
                resolved = re.sub(
                    r'what about',
                    f'What about {drug}\'s',
                    resolved,
                    count=1,
                    flags=re.IGNORECASE
                )
        
        return resolved
    
    def _needs_llm_resolution(self, resolved: str, original: str) -> bool:
        """
        Check if the query still needs LLM-based resolution
        """
        # If query didn't change much, might need LLM
        if resolved.lower() == original.lower():
            return True
        
        # If still has pronouns, need more resolution
        if any(re.search(r'\b' + p + r'\b', resolved, re.IGNORECASE) for p in self.pronouns):
            return True
        
        return False
    
    def _resolve_with_llm(
        self, 
        query: str, 
        context: Dict[str, Any]
    ) -> str:
        """
        Use LLM to resolve complex references
        """
        if not self.llm:
            return query
        
        # Build context summary
        context_summary = self._build_context_summary(context)
        
        prompt = f"""Given this conversation context, rewrite the user's query to be self-contained by resolving any pronouns or references.

Previous conversation context:
{context_summary}

User's current query: "{query}"

Rewrite the query to be clear and self-contained, replacing pronouns like "it", "that", "this" with specific entities from the context.
Provide ONLY the rewritten query, nothing else.

Rewritten query:"""
        
        try:
            resolved = self.llm.generate(prompt, max_tokens=150, temperature=0.3)
            # Clean up the response
            resolved = resolved.strip().strip('"').strip("'")
            return resolved if resolved else query
        except Exception as e:
            print(f"Error in LLM resolution: {e}")
            return query
    
    def _build_context_summary(self, context: Dict[str, Any]) -> str:
        """Build a concise summary of conversation context for LLM"""
        summary_parts = []
        
        # Add entities
        if 'entities' in context:
            entities = context['entities']
            if entities.get('drugs'):
                summary_parts.append(f"Drug mentioned: {', '.join(entities['drugs'][-3:])}")
            if entities.get('diseases'):
                summary_parts.append(f"Disease mentioned: {', '.join(entities['diseases'][-3:])}")
            if entities.get('trials'):
                summary_parts.append(f"Trial mentioned: {', '.join(entities['trials'][-3:])}")
        
        # Add last message
        if 'recent_messages' in context and context['recent_messages']:
            last = context['recent_messages'][0]
            if 'user_message' in last:
                summary_parts.append(f"Last user query: {last['user_message'][:200]}")
            if 'agent_response' in last:
                summary_parts.append(f"Last response: {last['agent_response'][:200]}")
        
        return "\n".join(summary_parts) if summary_parts else "No previous context"
    
    def expand_query(
        self, 
        query: str, 
        previous_response: str,
        aspect: Optional[str] = None
    ) -> str:
        """
        Expand a query that requests more details
        
        Args:
            query: Original query (e.g., "tell me more")
            previous_response: The response to expand on
            aspect: Specific aspect to expand (optional)
        """
        if not self.llm:
            return query
        
        prompt = f"""The user asked for more details about a previous response.

Previous response (summarized):
{previous_response[:500]}

User's request: "{query}"

Create a specific query that asks for more details about the most relevant aspect of the previous response.
Provide ONLY the expanded query, nothing else.

Expanded query:"""
        
        try:
            expanded = self.llm.generate(prompt, max_tokens=100, temperature=0.3)
            return expanded.strip().strip('"').strip("'")
        except Exception as e:
            print(f"Error expanding query: {e}")
            return query
