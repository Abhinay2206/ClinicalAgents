# agents/enrollment_agent.py
import os
import chromadb
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from .base_agent import LLMAgent

class EnrollmentAgent(LLMAgent):
    def __init__(self, llm, collection_name=None, api_key=None, tenant=None, database=None):
        super().__init__("Enrollment", "Analyze patient enrollment data and search clinical trials", llm)
        
        # ChromaDB connection parameters from environment variables
        self.collection_name = collection_name or os.getenv('CHROMA_COLLECTION', 'clinical_trials')
        self.api_key = api_key or os.getenv('CHROMA_API_KEY')
        self.tenant = tenant or os.getenv('CHROMA_TENANT')
        self.database = database or os.getenv('CHROMA_DATABASE', 'ClinicalAgents')
        
        # Validate required credentials
        if not self.api_key:
            raise ValueError("ChromaDB API key not found. Set CHROMA_API_KEY environment variable or pass api_key parameter.")
        if not self.tenant:
            raise ValueError("ChromaDB tenant not found. Set CHROMA_TENANT environment variable or pass tenant parameter.")
        
        # Initialize sentence transformer for encoding queries
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Initialize ChromaDB client and collection
        self.init_chromadb()
    
    def init_chromadb(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Initialize ChromaDB cloud client
            self.client = chromadb.CloudClient(
                api_key=self.api_key,
                tenant=self.tenant,
                database=self.database
            )
            
            # Get the collection
            self.collection = self.client.get_collection(self.collection_name)
            
            # Get collection stats
            count = self.collection.count()
            print(f"Connected to ChromaDB collection '{self.collection_name}' with {count} documents")
            
        except Exception as e:
            print(f"Error connecting to ChromaDB: {e}")
            self.client = None
            self.collection = None
    
    def search_by_nct_id(self, nct_id):
        """Search for a specific clinical trial by NCT ID"""
        if not self.collection:
            return None
        
        try:
            # Search ChromaDB for exact NCT ID match
            results = self.collection.get(
                where={"nct_id": nct_id}
            )
            
            if results['documents'] and len(results['documents']) > 0:
                # Return the first match with metadata
                return {
                    'document': results['documents'][0],
                    'metadata': results['metadatas'][0],
                    'id': results['ids'][0]
                }
            return None
            
        except Exception as e:
            print(f"Error searching by NCT ID: {e}")
            return None
    
    def search_by_disease(self, disease, top_k=10):
        """Search for clinical trials by disease name"""
        if not self.collection:
            return []
        
        try:
            # Search ChromaDB using semantic search since metadata filtering is complex
            # ChromaDB's where clause has limited string matching capabilities
            return self.semantic_search(f"{disease} disease condition clinical trial", top_k)
            
        except Exception as e:
            print(f"Error searching by disease: {e}")
            # Fallback to semantic search if metadata filtering fails
            return self.semantic_search(disease, top_k)
    
    def semantic_search(self, query, top_k=5):
        """Perform semantic search using ChromaDB"""
        if not self.collection:
            return []
        
        try:
            # Encode the query using the same model as used for indexing
            query_embedding = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
            
            # Search ChromaDB collection
            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=top_k
            )
            
            # Format results with similarity scores (distances)
            formatted_results = []
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'id': results['ids'][0][i],
                    'similarity_score': 1 - results['distances'][0][i],  # Convert distance to similarity
                    'rank': i + 1
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"Error in semantic search: {e}")
            return []
    
    def search_clinical_trials(self, search_term, search_type="auto", top_k=5):
        # Convert search_term to string if it's not already
        if isinstance(search_term, (np.ndarray, list)):
            search_term = str(search_term[0]) if len(search_term) > 0 else ""
        elif not isinstance(search_term, str):
            search_term = str(search_term)
        
        # Auto-detect search type if not specified
        if search_type == "auto":
            if search_term.upper().startswith("NCT"):
                search_type = "nct_id"
            elif any(disease in search_term.lower() for disease in ['cancer', 'diabetes', 'alzheimer', 'asthma', 'hiv', 'heart', 'stroke', 'parkinson', 'covid', 'depression']):
                search_type = "disease"
            else:
                search_type = "semantic"
        
        if search_type == "nct_id":
            result = self.search_by_nct_id(search_term)
            return [result] if result else []
        
        elif search_type == "disease":
            return self.search_by_disease(search_term, top_k)
        
        elif search_type == "semantic":
            return self.semantic_search(search_term, top_k)
        
        else:
            print(f"Unknown search type: {search_type}")
            return []
    
    def analyze_enrollment(self, search_term, search_type="auto", context=None):
        """
        Analyze enrollment patterns for clinical trials based on search results
        """
        trials = self.search_clinical_trials(search_term, search_type, top_k=5)
        
        if not trials:
            return f"No clinical trials found for search term: '{search_term}'"
        
        # Prepare trial summaries for analysis
        trial_summaries = []
        for i, trial in enumerate(trials, 1):
            metadata = trial.get('metadata', {})
            summary = f"""
            Trial {i} (NCT ID: {metadata.get('nct_id', 'N/A')}):
            - Disease: {metadata.get('disease', 'N/A')}
            - Status: {metadata.get('status', 'N/A')}
            - Phase: {metadata.get('phase', 'N/A')}
            - Study Type: {metadata.get('study_type', 'N/A')}
            - Conditions: {metadata.get('conditions', 'N/A')}
            - Why Stopped: {metadata.get('why_stopped', 'N/A')}
            - Eligibility Criteria: {metadata.get('eligibility_criteria', 'N/A')[:500]}...
            """
            if 'similarity_score' in trial:
                summary += f"\n            - Similarity Score: {trial.get('similarity_score', 0):.3f}"
            
            trial_summaries.append(summary)
        
        analysis_context = context or search_term
        prompt = f"""
        Analyze the following clinical trials for enrollment insights related to '{analysis_context}':
        
        {chr(10).join(trial_summaries)}
        
        Please provide a comprehensive enrollment analysis covering:
        
        1. **Enrollment Patterns & Status Analysis:**
           - Current status distribution of found trials
           - Common reasons for termination or suspension
           - Success factors for completed/active trials
        
        2. **Eligibility Criteria Analysis:**
           - Common inclusion criteria patterns
           - Frequent exclusion criteria
           - Age, gender, and condition-specific requirements
        
        3. **Study Design Insights:**
           - Most common phases and study types
           - Typical conditions and target populations
        
        4. **Recruitment Challenges & Recommendations:**
           - Identified barriers to enrollment
           - Suggestions for improving patient recruitment
           - Timeline and feasibility considerations
        
        5. **Strategic Recommendations:**
           - Best practices for similar future trials
           - Risk factors to avoid
           - Optimal patient population targeting
        
        Focus on actionable insights that can guide clinical trial planning and patient recruitment strategies.
        """
        
        return self.run(prompt)
    
    def get_trial_details(self, nct_id):
        """Get detailed information about a specific trial by NCT ID"""
        trial = self.search_by_nct_id(nct_id)
        if not trial:
            return f"Trial with NCT ID '{nct_id}' not found in the database."
        
        metadata = trial.get('metadata', {})
        details = f"""
        **Clinical Trial Details - {metadata.get('nct_id', 'N/A')}**
        
        - **Disease/Condition:** {metadata.get('disease', 'N/A')}
        - **Overall Status:** {metadata.get('status', 'N/A')}
        - **Phase:** {metadata.get('phase', 'N/A')}
        - **Study Type:** {metadata.get('study_type', 'N/A')}
        - **Conditions:** {metadata.get('conditions', 'N/A')}
        - **Why Stopped:** {metadata.get('why_stopped', 'N/A')}
        
        **Eligibility Criteria:**
        {metadata.get('eligibility_criteria', 'N/A')}
        
        **Document Text:**
        {trial.get('document', 'N/A')}
        """
        
        return details
    
    def analyze(self, query, **kwargs):
       
        search_type = kwargs.get('search_type', 'auto')
        context = kwargs.get('context', None)
        
        # Convert query to string if it's not already
        if isinstance(query, (np.ndarray, list)):
            query = str(query[0]) if len(query) > 0 else ""
        elif not isinstance(query, str):
            query = str(query)
        
        # Use the enrollment analysis method
        return self.analyze_enrollment(query, search_type, context)