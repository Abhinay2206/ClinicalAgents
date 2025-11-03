# agents/enrollment_agent.py
import os
import chromadb
import numpy as np
import pandas as pd
import faiss
import pickle
from typing import List, Dict, Any, Optional
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
        
        # Initialize sentence transformer for encoding queries
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Backends
        self.client = None
        self.collection = None
        self.faiss_index = None
        self.faiss_documents: List[str] = []
        self.faiss_df: Optional[pd.DataFrame] = None
        
        # Prefer Chroma if credentials exist, else fallback to local FAISS/CSV
        if self.api_key and self.tenant:
            self.init_chromadb()
            # If Chroma init fails, fall back to FAISS
            if not self.collection:
                self.init_faiss()
        else:
            print("ChromaDB credentials not found. Falling back to local FAISS/CSV search.")
            self.init_faiss()
    
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

    def init_faiss(self):
        """Initialize FAISS index and load trial metadata from local datasets"""
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            datasets_dir = os.path.join(base_dir, 'datasets')
            faiss_path_candidates = [
                os.path.join(datasets_dir, 'clinical_trials.faiss'),
                os.path.join(base_dir, 'scripts', 'clinical_trials.faiss'),
            ]
            csv_candidates = [
                os.path.join(datasets_dir, 'clinical_trials.csv'),
                os.path.join(base_dir, 'scripts', '..', 'datasets', 'clinical_trials.csv'),
            ]
            metadata_pkl_candidates = [
                os.path.join(base_dir, 'scripts', 'clinical_trials_metadata.pkl')
            ]

            # Load FAISS index
            faiss_path = next((p for p in faiss_path_candidates if os.path.exists(p)), None)
            if faiss_path and os.path.exists(faiss_path):
                self.faiss_index = faiss.read_index(faiss_path)
                print(f"Loaded FAISS index from {faiss_path} with {self.faiss_index.ntotal} vectors")

            # Load metadata (prefer pkl if available, else CSV and synthesize text)
            pkl_path = next((p for p in metadata_pkl_candidates if os.path.exists(p)), None)
            if pkl_path:
                try:
                    with open(pkl_path, 'rb') as f:
                        meta = pickle.load(f)
                    self.faiss_documents = meta.get('documents', [])
                    self.faiss_df = meta.get('df')
                    print(f"Loaded metadata from {pkl_path} with {len(self.faiss_documents)} documents")
                except Exception as e:
                    print(f"Warning: Failed to load metadata pkl: {e}")

            if self.faiss_df is None:
                csv_path = next((p for p in csv_candidates if os.path.exists(p)), None)
                if csv_path and os.path.exists(csv_path):
                    self.faiss_df = pd.read_csv(csv_path)
                    # Build documents similar to indexing pipeline
                    def row_to_text(row):
                        def safe_get(field, default="N/A"):
                            value = row.get(field, default)
                            return str(value) if pd.notna(value) else default
                        return (
                            f"Disease: {safe_get('Disease')}. "
                            f"NCT ID: {safe_get('NCT ID')}. "
                            f"Status: {safe_get('Overall Status')}. "
                            f"Why Stopped: {safe_get('Why Stopped')}. "
                            f"Eligibility: {safe_get('Eligibility Criteria')}. "
                            f"Phase: {safe_get('Phase')}. "
                            f"Conditions: {safe_get('Conditions')}. "
                            f"Study Type: {safe_get('Study type')}."
                        )
                    self.faiss_documents = self.faiss_df.apply(row_to_text, axis=1).tolist()
                    print(f"Loaded CSV from {csv_path} with {len(self.faiss_documents)} documents")

            if self.faiss_index is None and self.faiss_df is not None:
                # As a last resort, build an in-memory FAISS index from CSV (slower but functional)
                try:
                    print("FAISS index not found. Building transient index from CSV (first run may be slow)...")
                    embeddings = self.model.encode(self.faiss_documents, convert_to_numpy=True, normalize_embeddings=True)
                    d = embeddings.shape[1]
                    self.faiss_index = faiss.IndexFlatIP(d)
                    self.faiss_index.add(embeddings)
                    print(f"Built transient FAISS index with {self.faiss_index.ntotal} vectors")
                except Exception as e:
                    print(f"Error building transient FAISS index: {e}")
        except Exception as e:
            print(f"Error initializing local FAISS/CSV backend: {e}")
    
    def search_by_nct_id(self, nct_id):
        """Search for a specific clinical trial by NCT ID"""
        # Prefer Chroma, else local DataFrame filter
        if self.collection:
            try:
                results = self.collection.get(where={"nct_id": nct_id})
                if results['documents'] and len(results['documents']) > 0:
                    return {
                        'document': results['documents'][0],
                        'metadata': results['metadatas'][0],
                        'id': results['ids'][0]
                    }
                return None
            except Exception as e:
                print(f"Error searching by NCT ID (Chroma): {e}")
                return None
        
        if self.faiss_df is not None:
            try:
                matches = self.faiss_df[self.faiss_df.get('NCT ID') == nct_id]
                if not matches.empty:
                    row = matches.iloc[0]
                    idx = int(matches.index[0])
                    doc = self.faiss_documents[idx] if 0 <= idx < len(self.faiss_documents) else ''
                    meta = {
                        'nct_id': row.get('NCT ID', 'N/A'),
                        'disease': row.get('Disease', 'N/A'),
                        'status': row.get('Overall Status', 'N/A'),
                        'phase': row.get('Phase', 'N/A'),
                        'study_type': row.get('Study type', 'N/A'),
                        'conditions': row.get('Conditions', 'N/A'),
                        'why_stopped': row.get('Why Stopped', 'N/A'),
                        'eligibility_criteria': row.get('Eligibility Criteria', 'N/A'),
                    }
                    return {'document': doc, 'metadata': meta, 'id': str(idx)}
            except Exception as e:
                print(f"Error searching by NCT ID (local): {e}")
        return None
    
    def search_by_disease(self, disease, top_k=10):
        """Search for clinical trials by disease name"""
        if self.collection:
            try:
                return self.semantic_search(f"{disease} disease condition clinical trial", top_k)
            except Exception as e:
                print(f"Error searching by disease (Chroma): {e}")
                return self.semantic_search(disease, top_k)
        # Local FAISS
        return self.semantic_search(disease, top_k)
    
    def semantic_search(self, query, top_k=5):
        """Perform semantic search using ChromaDB or local FAISS"""
        # ChromaDB path
        if self.collection:
            try:
                query_embedding = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
                results = self.collection.query(
                    query_embeddings=query_embedding.tolist(),
                    n_results=top_k
                )
                formatted_results = []
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'id': results['ids'][0][i],
                        'similarity_score': 1 - results['distances'][0][i],
                        'rank': i + 1
                    })
                return formatted_results
            except Exception as e:
                print(f"Error in semantic search (Chroma): {e}. Falling back to local search if available...")
                # fall through to local
        
        # Local FAISS path
        if self.faiss_index is None or self.faiss_df is None or not self.faiss_documents:
            return []
        try:
            q_emb = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
            D, I = self.faiss_index.search(q_emb.astype(np.float32), k=min(top_k, self.faiss_index.ntotal))
            results: List[Dict[str, Any]] = []
            for rank, idx in enumerate(I[0]):
                row = self.faiss_df.iloc[int(idx)]
                meta = {
                    'nct_id': row.get('NCT ID', 'N/A'),
                    'disease': row.get('Disease', 'N/A'),
                    'status': row.get('Overall Status', 'N/A'),
                    'phase': row.get('Phase', 'N/A'),
                    'study_type': row.get('Study type', 'N/A'),
                    'conditions': row.get('Conditions', 'N/A'),
                    'why_stopped': row.get('Why Stopped', 'N/A'),
                    'eligibility_criteria': row.get('Eligibility Criteria', 'N/A'),
                }
                results.append({
                    'document': self.faiss_documents[int(idx)],
                    'metadata': meta,
                    'id': str(int(idx)),
                    'similarity_score': float(D[0][rank]),
                    'rank': rank + 1,
                })
            return results
        except Exception as e:
            print(f"Error in semantic search (local FAISS): {e}")
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
    
    def predict_enrollment_success(self, trial_metadata):
        """
        Predict enrollment success rate based on trial metadata
        Returns a success score (0-100) with reasoning
        """
        status = trial_metadata.get('status', '').lower()
        phase = trial_metadata.get('phase', '').lower()
        why_stopped = trial_metadata.get('why_stopped', '').lower()
        study_type = trial_metadata.get('study_type', '').lower()
        
        # Base score
        score = 50
        factors = []
        
        # Status-based scoring
        if 'completed' in status:
            score += 30
            factors.append("✓ Trial successfully completed (+30)")
        elif 'recruiting' in status or 'active' in status:
            score += 20
            factors.append("✓ Currently recruiting or active (+20)")
        elif 'terminated' in status or 'suspended' in status or 'withdrawn' in status:
            score -= 40
            factors.append("✗ Trial was terminated/suspended (-40)")
        
        # Phase-based scoring
        if 'phase 3' in phase or 'phase iii' in phase:
            score += 15
            factors.append("✓ Phase 3 trial - higher success rate (+15)")
        elif 'phase 4' in phase or 'phase iv' in phase:
            score += 20
            factors.append("✓ Phase 4 trial - post-market study (+20)")
        elif 'phase 1' in phase or 'phase i' in phase:
            score -= 10
            factors.append("⚠ Early phase trial - higher risk (-10)")
        
        # Stop reason analysis
        if why_stopped and why_stopped != 'n/a' and 'not' not in why_stopped.lower():
            if 'lack of funding' in why_stopped or 'business' in why_stopped:
                score -= 15
                factors.append("⚠ Stopped due to funding/business (-15)")
            elif 'enrollment' in why_stopped or 'accrual' in why_stopped:
                score -= 25
                factors.append("✗ Poor enrollment history (-25)")
            elif 'safety' in why_stopped or 'adverse' in why_stopped:
                score -= 35
                factors.append("✗ Safety concerns led to stop (-35)")
        
        # Study type consideration
        if 'interventional' in study_type:
            score += 10
            factors.append("✓ Interventional study (+10)")
        elif 'observational' in study_type:
            score += 5
            factors.append("✓ Observational study (+5)")
        
        # Ensure score is within 0-100
        score = max(0, min(100, score))
        
        # Determine success category
        if score >= 75:
            category = "High Success Probability"
            emoji = "🟢"
        elif score >= 50:
            category = "Moderate Success Probability"
            emoji = "🟡"
        else:
            category = "Lower Success Probability"
            emoji = "🔴"
        
        return {
            'score': score,
            'category': category,
            'emoji': emoji,
            'factors': factors
        }
    
    def analyze_enrollment(self, search_term, search_type="auto", context=None):
        """
        Analyze enrollment patterns for clinical trials based on search results
        """
        trials = self.search_clinical_trials(search_term, search_type, top_k=5)
        
        if not trials:
            return f"No clinical trials found for search term: '{search_term}'"
        
        # Prepare trial summaries for analysis with success predictions
        trial_summaries = []
        success_predictions = []
        
        for i, trial in enumerate(trials, 1):
            metadata = trial.get('metadata', {})
            
            # Predict success rate
            prediction = self.predict_enrollment_success(metadata)
            success_predictions.append(prediction)
            
            summary = f"""
            Trial {i} (NCT ID: {metadata.get('nct_id', 'N/A')}):
            - Disease: {metadata.get('disease', 'N/A')}
            - Status: {metadata.get('status', 'N/A')}
            - Phase: {metadata.get('phase', 'N/A')}
            - Study Type: {metadata.get('study_type', 'N/A')}
            - Conditions: {metadata.get('conditions', 'N/A')}
            - Why Stopped: {metadata.get('why_stopped', 'N/A')}
            - Eligibility Criteria: {metadata.get('eligibility_criteria', 'N/A')[:500]}...
            - **ENROLLMENT SUCCESS PREDICTION: {prediction['emoji']} {prediction['score']}% - {prediction['category']}**
            - Success Factors: {'; '.join(prediction['factors'])}
            """
            if 'similarity_score' in trial:
                summary += f"\n            - Similarity Score: {trial.get('similarity_score', 0):.3f}"
            
            trial_summaries.append(summary)
        
        analysis_context = context or search_term
        
        # Frame as educational/clinical research context to avoid content policy issues
        prompt = f"""
        As a clinical research analyst providing educational information for healthcare professionals and researchers,
        analyze the following clinical trial enrollment data for {analysis_context} research studies.
        
        This is a scholarly analysis of anonymized clinical trial registry data for medical education purposes.
        
        CLINICAL TRIAL DATA:
        {chr(10).join(trial_summaries)}
        
        REQUIRED OUTPUT FORMAT - Provide TWO sections:
        
        **PATIENT-FRIENDLY SUMMARY**
        Write 3-4 paragraphs in clear, accessible language explaining:
        - Overview of the clinical research studies found
        - Enrollment success predictions and what they indicate
        - Key eligibility patterns and requirements
        - Important insights for potential study participants
        
        **DETAILED TECHNICAL ANALYSIS**
        
        1. **Enrollment Success Predictions**
           - Success rate distribution across studies
           - Predictive factors and their impact
           - Comparative analysis of success probabilities
        
        2. **Enrollment Patterns & Status**
           - Current study status distribution
           - Historical completion/termination patterns
           - Success factors in completed studies
        
        3. **Eligibility Criteria**
           - Common inclusion/exclusion criteria
           - Demographic requirements
           - Medical history considerations
        
        4. **Recruitment Analysis**
           - Identified enrollment barriers
           - Recruitment optimization strategies
           - Timeline and feasibility factors
        
        5. **Clinical Recommendations**
           - Best practices for study participation
           - Risk assessment considerations
           - Patient population suitability
        
        Focus on evidence-based analysis suitable for medical education and informed decision-making.
        Begin with the PATIENT-FRIENDLY SUMMARY.
        """
        
        # Use run method with retry logic
        response = self.run(prompt)
        
        # If response indicates content policy issue, try with more clinical framing
        if "content policy" in response.lower() or "unable to generate" in response.lower():
            # Fallback: Generate response from data directly
            avg_score = sum(p['score'] for p in success_predictions) / len(success_predictions)
            
            fallback_response = f"""
**PATIENT-FRIENDLY SUMMARY**

I found {len(trials)} clinical research studies related to {analysis_context}. Here's what the enrollment data shows:

The average enrollment success prediction across these studies is {avg_score:.0f}%, which indicates {'strong' if avg_score >= 70 else 'moderate' if avg_score >= 50 else 'variable'} recruitment potential. {len([p for p in success_predictions if p['score'] >= 75])} studies show high success probability (75%+), while {len([p for p in success_predictions if p['score'] < 50])} show lower success rates.

Key findings from the enrollment analysis:
"""
            
            # Add trial-by-trial summary
            for i, (trial, pred) in enumerate(zip(trials, success_predictions), 1):
                meta = trial.get('metadata', {})
                fallback_response += f"\n- Study {i} ({meta.get('nct_id', 'N/A')}): {pred['emoji']} {pred['score']}% success rate - Status: {meta.get('status', 'N/A')}, Phase: {meta.get('phase', 'N/A')}"
            
            fallback_response += f"""

Most studies are looking for participants who meet specific medical criteria related to {analysis_context}. The studies with higher success rates tend to be in later phases (Phase 3/4) and are currently active in recruitment.

**DETAILED TECHNICAL ANALYSIS**

1. **Enrollment Success Predictions**

Success Rate Distribution:
"""
            for i, pred in enumerate(success_predictions, 1):
                fallback_response += f"\n   Study {i}: {pred['score']}% - {pred['category']}"
                for factor in pred['factors']:
                    fallback_response += f"\n      {factor}"
            
            fallback_response += "\n\n2. **Study Status Overview**\n"
            statuses = {}
            for trial in trials:
                status = trial.get('metadata', {}).get('status', 'Unknown')
                statuses[status] = statuses.get(status, 0) + 1
            
            for status, count in statuses.items():
                fallback_response += f"   - {status}: {count} studies\n"
            
            return fallback_response
        
        return response
    
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