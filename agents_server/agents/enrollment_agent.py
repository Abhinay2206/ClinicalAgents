# agents/enrollment_agent.py
import os
import pickle
import faiss
import numpy as np
from .base_agent import LLMAgent

class EnrollmentAgent(LLMAgent):
    def __init__(self, llm, faiss_index_path=None, metadata_pkl_path=None):
        super().__init__("Enrollment", "Analyze patient enrollment data", llm)
        
        # Use datasets folder paths if not provided
        base_path = os.path.join(os.path.dirname(__file__), '..', 'datasets')
        self.faiss_index_path = faiss_index_path or os.path.join(base_path, 'clinical_trials.faiss')
        self.metadata_pkl_path = metadata_pkl_path or os.path.join(base_path, 'clinical_trials_metadata.pkl')
        
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
                self.metadata = pickle.load(f)
            print(f"Loaded metadata for {len(self.metadata)} clinical trials")
            
        except Exception as e:
            print(f"Error loading data: {e}")
            self.index = None
            self.metadata = None
    
    def search_similar_trials(self, query_embedding, top_k=5):
       
        if self.index is None or self.metadata is None:
            return []
        
        try:
            # Ensure query_embedding is the right format
            if isinstance(query_embedding, list):
                query_embedding = np.array(query_embedding, dtype=np.float32)
            
            if len(query_embedding.shape) == 1:
                query_embedding = query_embedding.reshape(1, -1)
            
            # Search similar vectors
            distances, indices = self.index.search(query_embedding, top_k)
            
            # Get metadata for similar trials
            similar_trials = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < len(self.metadata):
                    trial_data = self.metadata[idx].copy()
                    trial_data['similarity_score'] = float(1 / (1 + distance))  # Convert distance to similarity
                    trial_data['rank'] = i + 1
                    similar_trials.append(trial_data)
            
            return similar_trials
            
        except Exception as e:
            print(f"Error searching similar trials: {e}")
            return []
    
    def analyze(self, query_embedding, drug_name=None):
    
        similar_trials = self.search_similar_trials(query_embedding)
        
        if not similar_trials:
            return "No similar clinical trials found for enrollment analysis."
        
        # Prepare data for LLM analysis
        trial_summaries = []
        for trial in similar_trials:
            summary = f"""
            Trial {trial.get('rank', 'N/A')} (Similarity: {trial.get('similarity_score', 0):.3f}):
            - Title: {trial.get('title', 'N/A')}
            - Phase: {trial.get('phase', 'N/A')}
            - Status: {trial.get('status', 'N/A')}
            - Enrollment: {trial.get('enrollment', 'N/A')} participants
            - Duration: {trial.get('duration', 'N/A')}
            - Conditions: {trial.get('conditions', 'N/A')}
            - Interventions: {trial.get('interventions', 'N/A')}
            """
            trial_summaries.append(summary)
        
        context = drug_name if drug_name else "the target treatment"
        prompt = f"""
        Analyze the following similar clinical trials for enrollment patterns related to {context}:
        
        {chr(10).join(trial_summaries)}
        
        Please provide an analysis covering:
        1. Typical enrollment numbers and timelines
        2. Common inclusion/exclusion criteria patterns
        3. Enrollment challenges and success factors
        4. Recommendations for optimizing patient recruitment
        5. Feasibility assessment based on historical data
        
        Focus on actionable insights for planning a new clinical trial.
        """
        
        return self.run(prompt)