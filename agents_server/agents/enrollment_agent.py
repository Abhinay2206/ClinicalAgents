# agents/enrollment_agent.py
import os
import pickle
import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from .base_agent import LLMAgent

class EnrollmentAgent(LLMAgent):
    def __init__(self, llm, faiss_index_path=None, metadata_pkl_path=None):
        super().__init__("Enrollment", "Analyze patient enrollment data and search clinical trials", llm)
        
        # Use datasets folder paths if not provided
        base_path = os.path.join(os.path.dirname(__file__), '..', 'datasets')
        self.faiss_index_path = faiss_index_path or os.path.join(base_path, 'clinical_trials.faiss')
        self.metadata_pkl_path = metadata_pkl_path or os.path.join(base_path, 'clinical_trials_metadata.pkl')
        
        # Initialize sentence transformer for encoding queries
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Load FAISS index and metadata
        self.load_data()
    
    def load_data(self):
        """Load FAISS index and metadata pickle file"""
        try:
            # Load FAISS index
            self.index = faiss.read_index(self.faiss_index_path)
            print(f"Loaded FAISS index with {self.index.ntotal} vectors")
            
            # Load metadata
            with open(self.metadata_pkl_path, 'rb') as f:
                metadata = pickle.load(f)
                self.documents = metadata.get('documents', [])
                self.df = metadata.get('df', pd.DataFrame())
            
            print(f"Loaded metadata for {len(self.documents)} clinical trials")
            
        except Exception as e:
            print(f"Error loading data: {e}")
            self.index = None
            self.documents = []
            self.df = pd.DataFrame()
    
    def search_by_nct_id(self, nct_id):
        """Search for a specific clinical trial by NCT ID"""
        if self.df.empty:
            return None
        
        # Search for exact NCT ID match
        matches = self.df[self.df['NCT ID'] == nct_id]
        if not matches.empty:
            return matches.iloc[0].to_dict()
        return None
    
    def search_by_disease(self, disease, top_k=10):
        """Search for clinical trials by disease name"""
        if self.df.empty:
            return []
        
        # Filter by disease (case-insensitive partial match)
        disease_matches = self.df[self.df['Disease'].str.contains(disease, case=False, na=False)]
        
        # Also check conditions column for broader matching
        condition_matches = self.df[self.df['Conditions'].str.contains(disease, case=False, na=False)]
        
        # Combine and remove duplicates
        all_matches = pd.concat([disease_matches, condition_matches]).drop_duplicates()
        
        return all_matches.head(top_k).to_dict('records')
    
    def semantic_search(self, query, top_k=5):
        """Perform semantic search using FAISS index"""
        if self.index is None or len(self.documents) == 0:
            return []
        
        try:
            # Encode the query
            query_embedding = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
            
            # Search FAISS index
            scores, indices = self.index.search(query_embedding, top_k)
            
            # Get results with similarity scores
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < len(self.df):
                    trial_data = self.df.iloc[idx].to_dict()
                    trial_data['similarity_score'] = float(score)
                    trial_data['rank'] = i + 1
                    trial_data['document_text'] = self.documents[idx]
                    results.append(trial_data)
            
            return results
            
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
            summary = f"""
            Trial {i} (NCT ID: {trial.get('NCT ID', 'N/A')}):
            - Disease: {trial.get('Disease', 'N/A')}
            - Status: {trial.get('Overall Status', 'N/A')}
            - Phase: {trial.get('Phase', 'N/A')}
            - Study Type: {trial.get('Study Type', 'N/A')}
            - Conditions: {trial.get('Conditions', 'N/A')}
            - Why Stopped: {trial.get('Why Stopped', 'N/A')}
            - Eligibility Criteria: {trial.get('Eligibility Criteria', 'N/A')[:500]}...
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
        
        details = f"""
        **Clinical Trial Details - {trial.get('NCT ID', 'N/A')}**
        
        - **Disease/Condition:** {trial.get('Disease', 'N/A')}
        - **Overall Status:** {trial.get('Overall Status', 'N/A')}
        - **Phase:** {trial.get('Phase', 'N/A')}
        - **Study Type:** {trial.get('Study Type', 'N/A')}
        - **Conditions:** {trial.get('Conditions', 'N/A')}
        - **Why Stopped:** {trial.get('Why Stopped', 'N/A')}
        
        **Eligibility Criteria:**
        {trial.get('Eligibility Criteria', 'N/A')}
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