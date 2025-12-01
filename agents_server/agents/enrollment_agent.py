# agents/enrollment_agent.py
import os
import chromadb
import numpy as np
import pandas as pd
import faiss
import pickle
import requests
import json
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from .base_agent import LLMAgent

class EnrollmentAgent(LLMAgent):
    # Class-level cache for shared resources
    _model_cache = None
    _faiss_cache = {}
    
    def __init__(self, llm, collection_name=None, api_key=None, tenant=None, database=None, verbose: bool = False):
        super().__init__("Enrollment", "Analyze patient enrollment data and search clinical trials", llm)
        
        self.verbose = verbose
        
        # ChromaDB connection parameters from environment variables
        self.collection_name = collection_name or os.getenv('CHROMA_COLLECTION', 'clinical_trials')
        self.api_key = api_key or os.getenv('CHROMA_API_KEY')
        self.tenant = tenant or os.getenv('CHROMA_TENANT')
        self.database = database or os.getenv('CHROMA_DATABASE', 'ClinicalAgents')
        
        # Use cached sentence transformer (expensive to load)
        if EnrollmentAgent._model_cache is None:
            EnrollmentAgent._model_cache = SentenceTransformer("all-MiniLM-L6-v2")
        self.model = EnrollmentAgent._model_cache
        
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
            if self.verbose:
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
            if self.verbose:
                count = self.collection.count()
                print(f"Connected to ChromaDB collection '{self.collection_name}' with {count} documents")
            
        except Exception as e:
            if self.verbose:
                print(f"Error connecting to ChromaDB: {e}")
            self.client = None
            self.collection = None

    def init_faiss(self):
        """Initialize FAISS index and load trial metadata from local datasets with caching"""
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Check if we have cached FAISS data
            cache_key = f"{base_dir}_faiss"
            if cache_key in EnrollmentAgent._faiss_cache:
                cached = EnrollmentAgent._faiss_cache[cache_key]
                self.faiss_index = cached.get('index')
                self.faiss_documents = cached.get('documents', [])
                self.faiss_df = cached.get('df')
                if self.verbose:
                    print(f"Using cached FAISS data ({len(self.faiss_documents)} documents)")
                return
            
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
                if self.verbose:
                    print(f"Loaded FAISS index from {faiss_path} with {self.faiss_index.ntotal} vectors")

            # Load metadata (prefer pkl if available, else CSV and synthesize text)
            pkl_path = next((p for p in metadata_pkl_candidates if os.path.exists(p)), None)
            if pkl_path:
                try:
                    with open(pkl_path, 'rb') as f:
                        meta = pickle.load(f)
                    self.faiss_documents = meta.get('documents', [])
                    self.faiss_df = meta.get('df')
                    if self.verbose:
                        print(f"Loaded metadata from {pkl_path} with {len(self.faiss_documents)} documents")
                except Exception as e:
                    if self.verbose:
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
                    if self.verbose:
                        print(f"Loaded CSV from {csv_path} with {len(self.faiss_documents)} documents")

            if self.faiss_index is None and self.faiss_df is not None:
                # As a last resort, build an in-memory FAISS index from CSV (slower but functional)
                try:
                    if self.verbose:
                        print("FAISS index not found. Building transient index from CSV (first run may be slow)...")
                    embeddings = self.model.encode(self.faiss_documents, convert_to_numpy=True, normalize_embeddings=True)
                    d = embeddings.shape[1]
                    self.faiss_index = faiss.IndexFlatIP(d)
                    self.faiss_index.add(embeddings)
                    if self.verbose:
                        print(f"Built transient FAISS index with {self.faiss_index.ntotal} vectors")
                except Exception as e:
                    if self.verbose:
                        print(f"Error building transient FAISS index: {e}")
            
            # Cache for future instances
            EnrollmentAgent._faiss_cache[cache_key] = {
                'index': self.faiss_index,
                'documents': self.faiss_documents,
                'df': self.faiss_df
            }
        except Exception as e:
            if self.verbose:
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
    
    def fetch_from_clinicaltrials_api(self, search_term, page_size=100):
        """
        Fetch clinical trials from ClinicalTrials.gov API
        Returns list of trials in a format compatible with local search results
        """
        try:
            url = "https://clinicaltrials.gov/api/v2/studies"
            params = {
                "query.term": search_term,
                "pageSize": page_size
            }
            
            if self.verbose:
                print(f"Fetching trials from ClinicalTrials.gov API for: {search_term}")
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            studies = data.get('studies', [])
            
            if self.verbose:
                print(f"Retrieved {len(studies)} trials from API")
            
            # Convert API format to our standard format
            formatted_results = []
            for i, study in enumerate(studies):
                protocol = study.get('protocolSection', {})
                identification = protocol.get('identificationModule', {})
                status_module = protocol.get('statusModule', {})
                eligibility = protocol.get('eligibilityModule', {})
                conditions_module = protocol.get('conditionsModule', {})
                design_module = protocol.get('designModule', {})
                
                nct_id = identification.get('nctId', 'N/A')
                title = identification.get('briefTitle', 'N/A')
                overall_status = status_module.get('overallStatus', 'N/A')
                why_stopped = status_module.get('whyStopped', 'N/A')
                phase = design_module.get('phases', ['N/A'])[0] if design_module.get('phases') else 'N/A'
                study_type = design_module.get('studyType', 'N/A')
                conditions = ', '.join(conditions_module.get('conditions', ['N/A']))
                eligibility_criteria = eligibility.get('eligibilityCriteria', 'N/A')
                
                metadata = {
                    'nct_id': nct_id,
                    'disease': conditions,
                    'status': overall_status,
                    'phase': phase,
                    'study_type': study_type,
                    'conditions': conditions,
                    'why_stopped': why_stopped,
                    'eligibility_criteria': eligibility_criteria,
                    'title': title
                }
                
                document = f"Disease: {conditions}. NCT ID: {nct_id}. Status: {overall_status}. " \
                          f"Why Stopped: {why_stopped}. Eligibility: {eligibility_criteria[:200]}... " \
                          f"Phase: {phase}. Conditions: {conditions}. Study Type: {study_type}."
                
                formatted_results.append({
                    'document': document,
                    'metadata': metadata,
                    'id': nct_id,
                    'rank': i + 1,
                    'source': 'api'
                })
            
            return formatted_results
            
        except requests.exceptions.RequestException as e:
            if self.verbose:
                print(f"Error fetching from ClinicalTrials.gov API: {e}")
            return []
        except Exception as e:
            if self.verbose:
                print(f"Unexpected error in API fetch: {e}")
            return []
    
    def assess_search_results(self, results, min_similarity=0.3, min_results=3):
        """
        Assess if search results are sufficient or if API fallback is needed
        Returns True if results are sufficient, False if API fallback needed
        """
        if not results:
            return False
        
        if len(results) < min_results:
            return False
        
        # Check similarity scores if available
        has_good_matches = False
        for result in results:
            similarity = result.get('similarity_score', 0)
            if similarity >= min_similarity:
                has_good_matches = True
                break
        
        return has_good_matches or len(results) >= 5
    
    def decide_response_strategy(self, query, api_results):
        """
        Use LLM to decide whether to use API results or provide a generalized answer
        Returns decision dict with 'use_api_data' boolean and 'reasoning' string
        """
        if not api_results:
            return {
                'use_api_data': False,
                'reasoning': 'No API results available'
            }
        
        # Prepare summary of API results
        result_summary = f"Found {len(api_results)} trials from ClinicalTrials.gov API:\n"
        for i, trial in enumerate(api_results[:5], 1):
            meta = trial.get('metadata', {})
            result_summary += f"{i}. {meta.get('nct_id', 'N/A')} - {meta.get('title', 'N/A')[:80]}... " \
                            f"Status: {meta.get('status', 'N/A')}\n"
        
        prompt = f"""
        Analyze the following query and API search results to decide the best response strategy.
        
        USER QUERY: {query}
        
        API RESULTS SUMMARY:
        {result_summary}
        
        Decide whether to:
        A) Use the API trial data to provide specific trial information
        B) Provide a generalized answer about clinical trials
        
        Choose A if:
        - The API results are relevant to the query
        - The trials found match what the user is asking about
        - Specific trial information would be helpful
        
        Choose B if:
        - The API results are not very relevant
        - The query is too general or vague
        - A general educational answer would be more appropriate
        
        Respond in JSON format:
        {{
            "decision": "A" or "B",
            "reasoning": "brief explanation"
        }}
        """
        
        try:
            response = self.run(prompt)
            # Try to extract JSON from response
            if '{' in response and '}' in response:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                json_str = response[json_start:json_end]
                decision_data = json.loads(json_str)
                
                return {
                    'use_api_data': decision_data.get('decision') == 'A',
                    'reasoning': decision_data.get('reasoning', 'LLM decision')
                }
        except Exception as e:
            if self.verbose:
                print(f"Error in LLM decision: {e}")
        
        # Default: use API data if we have results
        return {
            'use_api_data': len(api_results) > 0,
            'reasoning': 'Default decision based on result availability'
        }
    
    def filter_running_trials(self, trials):
        """
        Filter and return currently recruiting/active trials
        """
        running_statuses = ['recruiting', 'active', 'enrolling by invitation', 'not yet recruiting']
        running_trials = []
        
        for trial in trials:
            metadata = trial.get('metadata', {})
            status = metadata.get('status', '').lower()
            
            if any(running_status in status for running_status in running_statuses):
                running_trials.append(trial)
        
        return running_trials
    
    def generate_trial_suggestions(self, query, running_trials):
        """
        Generate suggestions for running trials using LLM
        Returns formatted suggestions with trial suitability analysis
        """
        if not running_trials:
            return "No currently recruiting trials found."
        
        # Prepare trial information
        trial_info = ""
        for i, trial in enumerate(running_trials[:10], 1):  # Limit to top 10
            metadata = trial.get('metadata', {})
            prediction = self.predict_enrollment_success(metadata)
            
            trial_info += f"""
Trial {i}: {metadata.get('nct_id', 'N/A')}
- Title: {metadata.get('title', 'N/A')}
- Status: {metadata.get('status', 'N/A')}
- Phase: {metadata.get('phase', 'N/A')}
- Conditions: {metadata.get('conditions', 'N/A')}
- Enrollment Success Prediction: {prediction['emoji']} {prediction['score']}% - {prediction['category']}
- Eligibility (brief): {metadata.get('eligibility_criteria', 'N/A')[:200]}...
"""
        
        prompt = f"""
        Based on the user's query and the following currently recruiting clinical trials, 
        provide suggestions about which trials might be most suitable.
        
        USER QUERY: {query}
        
        CURRENTLY RECRUITING TRIALS:
        {trial_info}
        
        Provide:
        1. A brief overview of the recruiting trials found
        2. For each trial, a suggestion about its suitability (consider enrollment success prediction, phase, conditions)
        3. Key factors patients should consider when choosing a trial
        
        Format your response in a clear, patient-friendly manner with bullet points.
        """
        
        try:
            suggestions = self.run(prompt)
            return suggestions
        except Exception as e:
            if self.verbose:
                print(f"Error generating suggestions: {e}")
            
            # Fallback: simple list
            fallback = f"**Currently Recruiting Trials ({len(running_trials)} found):**\n\n"
            for i, trial in enumerate(running_trials[:10], 1):
                meta = trial.get('metadata', {})
                pred = self.predict_enrollment_success(meta)
                fallback += f"{i}. **{meta.get('nct_id', 'N/A')}** - {meta.get('title', 'N/A')}\n"
                fallback += f"   - Status: {meta.get('status', 'N/A')}\n"
                fallback += f"   - Success Prediction: {pred['emoji']} {pred['score']}%\n\n"
            
            return fallback

    
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
        Enhanced with API fallback and running trial suggestions
        """
        # First try local search
        trials = self.search_clinical_trials(search_term, search_type, top_k=5)
        
        # Assess if local results are sufficient
        results_sufficient = self.assess_search_results(trials)
        
        # If local results are insufficient, try API
        if not results_sufficient:
            if self.verbose:
                print(f"Local results insufficient, fetching from ClinicalTrials.gov API...")
            
            api_trials = self.fetch_from_clinicaltrials_api(search_term, page_size=100)
            
            if api_trials:
                # Use LLM to decide response strategy
                decision = self.decide_response_strategy(search_term, api_trials)
                
                if decision['use_api_data']:
                    # Use API results
                    trials = api_trials[:10]  # Limit to top 10 for analysis
                    if self.verbose:
                        print(f"Using API data: {decision['reasoning']}")
                else:
                    # Provide generalized answer
                    if self.verbose:
                        print(f"Providing generalized answer: {decision['reasoning']}")
                    
                    return f"""
**Clinical Trial Enrollment Information**

Based on your query about "{search_term}", here's general information about clinical trial enrollment:

Clinical trials are research studies that test new medical approaches in people. To participate in a clinical trial, you must meet specific eligibility criteria which typically include:

- **Medical Condition**: Having the specific disease or condition being studied
- **Age Requirements**: Being within a certain age range
- **Health Status**: Meeting certain health criteria (e.g., organ function, previous treatments)
- **Geographic Location**: Being able to travel to the study site

**Finding Relevant Trials:**

While we found {len(api_trials)} trials in the ClinicalTrials.gov database related to your search, they may have varying levels of relevance. We recommend:

1. Visit ClinicalTrials.gov directly and search for "{search_term}"
2. Consult with your healthcare provider about trial participation
3. Contact trial coordinators to discuss eligibility in detail

**Currently Recruiting Trials:**

{self._format_running_trials_summary(api_trials)}

For more specific information, please refine your search or consult with a healthcare professional.
"""
        
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
            - Title: {metadata.get('title', metadata.get('disease', 'N/A'))}
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
        
        # Filter running trials
        running_trials = self.filter_running_trials(trials)
        
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
            
            response = f"""
**PATIENT-FRIENDLY SUMMARY**

I found {len(trials)} clinical research studies related to {analysis_context}. Here's what the enrollment data shows:

The average enrollment success prediction across these studies is {avg_score:.0f}%, which indicates {'strong' if avg_score >= 70 else 'moderate' if avg_score >= 50 else 'variable'} recruitment potential. {len([p for p in success_predictions if p['score'] >= 75])} studies show high success probability (75%+), while {len([p for p in success_predictions if p['score'] < 50])} show lower success rates.

Key findings from the enrollment analysis:
"""
            
            # Add trial-by-trial summary
            for i, (trial, pred) in enumerate(zip(trials, success_predictions), 1):
                meta = trial.get('metadata', {})
                response += f"\n- Study {i} ({meta.get('nct_id', 'N/A')}): {pred['emoji']} {pred['score']}% success rate - Status: {meta.get('status', 'N/A')}, Phase: {meta.get('phase', 'N/A')}"
            
            response += f"""

Most studies are looking for participants who meet specific medical criteria related to {analysis_context}. The studies with higher success rates tend to be in later phases (Phase 3/4) and are currently active in recruitment.

**DETAILED TECHNICAL ANALYSIS**

1. **Enrollment Success Predictions**

Success Rate Distribution:
"""
            for i, pred in enumerate(success_predictions, 1):
                response += f"\n   Study {i}: {pred['score']}% - {pred['category']}"
                for factor in pred['factors']:
                    response += f"\n      {factor}"
            
            response += "\n\n2. **Study Status Overview**\n"
            statuses = {}
            for trial in trials:
                status = trial.get('metadata', {}).get('status', 'Unknown')
                statuses[status] = statuses.get(status, 0) + 1
            
            for status, count in statuses.items():
                response += f"   - {status}: {count} studies\n"
        
        # Add running trials section
        if running_trials:
            response += f"\n\n---\n\n## 🟢 CURRENTLY RECRUITING TRIALS ({len(running_trials)} Active)\n\n"
            
            # Generate suggestions for running trials
            suggestions = self.generate_trial_suggestions(search_term, running_trials)
            response += suggestions
            
            # Add detailed list of running trials
            response += f"\n\n**Detailed Information on Active Trials:**\n\n"
            for i, trial in enumerate(running_trials[:10], 1):
                meta = trial.get('metadata', {})
                pred = self.predict_enrollment_success(meta)
                response += f"""
**{i}. {meta.get('nct_id', 'N/A')}** - {meta.get('title', meta.get('disease', 'N/A'))}
- **Status:** {meta.get('status', 'N/A')}
- **Phase:** {meta.get('phase', 'N/A')}
- **Conditions:** {meta.get('conditions', 'N/A')}
- **Enrollment Success:** {pred['emoji']} {pred['score']}% ({pred['category']})
- **Study Type:** {meta.get('study_type', 'N/A')}

"""
        else:
            response += "\n\n---\n\n**Note:** No currently recruiting trials found in this dataset. Trials may be completed, terminated, or not yet recruiting.\n"
        
        return response
    
    def _format_running_trials_summary(self, trials):
        """Helper method to format running trials summary"""
        running = self.filter_running_trials(trials)
        if not running:
            return "No currently recruiting trials found in the results."
        
        summary = f"Found {len(running)} currently recruiting trials:\n\n"
        for i, trial in enumerate(running[:5], 1):
            meta = trial.get('metadata', {})
            summary += f"{i}. **{meta.get('nct_id', 'N/A')}** - {meta.get('title', meta.get('disease', 'N/A')[:60])}...\n"
            summary += f"   Status: {meta.get('status', 'N/A')}\n\n"
        
        if len(running) > 5:
            summary += f"...and {len(running) - 5} more recruiting trials.\n"
        
        return summary

    
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