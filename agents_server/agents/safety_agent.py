# agents/safety_agent.py
import requests
from .base_agent import LLMAgent

class SafetyAgent(LLMAgent):
    def __init__(self, llm, fda_api_key=None):
        super().__init__("Safety", "Analyze drug safety data", llm)
        self.api_key = fda_api_key
        self.base_url = "https://api.fda.gov/drug/label.json"

    def fetch_safety_data(self, drug_name, limit=1):
        """Fetch safety data for a specific drug"""
        # Clean the drug name for better API search
        clean_drug_name = drug_name.strip().lower()
        
        params = {
            'search': f'openfda.generic_name:"{clean_drug_name}" OR openfda.brand_name:"{clean_drug_name}"',
            'limit': limit
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            print(f"FDA API Request URL: {response.url}")
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                print(f"FDA API returned {len(results)} results for '{drug_name}'")
                return results
            elif response.status_code == 404:
                print(f"FDA API: No data found for drug '{drug_name}'")
                return []
            else:
                print(f"FDA API request failed with status code: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                return []
        except Exception as e:
            print(f"Error fetching FDA data: {e}")
            return []

    def fetch_drugs_by_disease(self, disease, limit=10):
        """Fetch drugs approved for a specific disease/condition"""
        params = {
            'search': f'indications_and_usage:"{disease}" OR purpose:"{disease}"',
            'limit': limit
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get("results", [])
            else:
                print(f"FDA API request failed with status code: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error fetching drugs by disease: {e}")
            return []

    def analyze_drug_safety(self, drug_name):
        """Analyze safety data for a specific drug"""
        data = self.fetch_safety_data(drug_name)
        
        if not data:
            # Provide general safety analysis when FDA data is not available
            prompt = f"""
            You are a clinical safety expert providing information to patients and healthcare professionals.
            Provide a general safety assessment for {drug_name} based on established medical knowledge.
            
            Structure your response in TWO sections:
            
            **PATIENT-FRIENDLY SUMMARY** (Write in simple, clear language):
            - Explain the main safety concerns in plain terms
            - List the most common side effects patients should know about
            - Mention who should NOT take this medication (contraindications)
            - Note any serious warnings (if applicable)
            - Provide simple safety tips
            - Keep it brief (3-4 paragraphs)
            
            **DETAILED TECHNICAL ANALYSIS**:
            1. **Common Safety Profile**: General safety considerations and contraindications
            2. **Typical Side Effects**: Most commonly reported adverse reactions with frequencies
            3. **Special Populations**: Safety considerations for elderly, pregnant women, children
            4. **Drug Interactions**: Major classes of medications that may interact
            5. **Monitoring Requirements**: What parameters should be monitored during treatment
            6. **Risk Factors**: Patient conditions that may increase risk
            7. **Risk Mitigation Strategies**: How to minimize adverse events
            
            Note: This analysis is based on general medical knowledge. For specific safety information, consult FDA-approved labeling and clinical guidelines.
            
            Always start with the PATIENT-FRIENDLY SUMMARY first.
            """
            return self.run(prompt)
        
        # Extract relevant safety information from FDA labels
        safety_info = []
        for label in data:
            info = {
                'drug': label.get('openfda', {}).get('generic_name', [drug_name]),
                'brand_names': label.get('openfda', {}).get('brand_name', []),
                'warnings': label.get('warnings', []),
                'boxed_warning': label.get('boxed_warning', []),
                'contraindications': label.get('contraindications', []),
                'adverse_reactions': label.get('adverse_reactions', []),
                'precautions': label.get('precautions', []),
                'drug_interactions': label.get('drug_interactions', [])
            }
            safety_info.append(info)
        
        prompt = f"""
        You are a clinical safety expert providing information to patients and healthcare professionals.
        Analyze the following FDA drug label safety information for {drug_name}:
        
        {safety_info}
        
        Structure your response in TWO sections:
        
        **PATIENT-FRIENDLY SUMMARY** (Write in simple, clear language):
        - Start with the most critical safety information (black box warnings if present)
        - List common side effects in order of importance
        - Explain who should avoid this medication
        - Mention important drug interactions in plain language
        - Provide practical safety advice
        - Keep it concise (3-4 paragraphs)
        
        **DETAILED TECHNICAL ANALYSIS**:
        1. Black box warnings (if any) - most serious warnings
        2. Major contraindications - when NOT to use
        3. Common adverse reactions and their frequencies
        4. Significant drug interactions with mechanisms
        5. Special precautions and populations at risk
        6. Monitoring requirements and parameters
        7. Overall risk assessment and recommendations
        8. Risk mitigation strategies
        
        Focus on clinically relevant safety concerns and actionable guidance.
        Always start with the PATIENT-FRIENDLY SUMMARY first.
        """
        
        return self.run(prompt)

    def analyze_drugs_for_disease(self, disease):
        """Analyze drugs available for a specific disease/condition"""
        data = self.fetch_drugs_by_disease(disease)
        
        if not data:
            return f"No FDA approved drugs found for {disease}. Unable to perform drug analysis."
        
        # Extract drug information and safety profiles
        drug_profiles = []
        for label in data:
            openfda_info = label.get('openfda', {})
            
            # Extract drug names
            generic_names = openfda_info.get('generic_name', [])
            brand_names = openfda_info.get('brand_name', [])
            
            # Get primary drug name
            primary_name = generic_names[0] if generic_names else (brand_names[0] if brand_names else "Unknown")
            
            drug_info = {
                'primary_name': primary_name,
                'generic_names': generic_names,
                'brand_names': brand_names,
                'manufacturer': openfda_info.get('manufacturer_name', []),
                'indications': label.get('indications_and_usage', []),
                'dosage_forms': openfda_info.get('dosage_form', []),
                'routes': openfda_info.get('route', []),
                'warnings': label.get('warnings', []),
                'boxed_warning': label.get('boxed_warning', []),
                'contraindications': label.get('contraindications', []),
                'adverse_reactions': label.get('adverse_reactions', []),
                'drug_interactions': label.get('drug_interactions', []),
                'pregnancy_category': openfda_info.get('pregnancy_category', [])
            }
            drug_profiles.append(drug_info)
        
        prompt = f"""
        Analyze the following FDA-approved drugs for treating {disease}:
        
        {drug_profiles}
        
        Please provide a comprehensive analysis covering:
        
        1. **Available Treatment Options:**
           - List of approved drugs with generic and brand names
           - Different dosage forms and routes of administration
           - Key manufacturers
        
        2. **Safety Profile Comparison:**
           - Drugs with black box warnings
           - Common contraindications across treatments
           - Most frequent adverse reactions
           - Drug interaction considerations
        
        3. **Special Populations:**
           - Pregnancy safety categories
           - Pediatric and geriatric considerations
           - Renal/hepatic impairment considerations
        
        4. **Clinical Recommendations:**
           - First-line vs. second-line treatment options
           - Safety considerations for drug selection
           - Monitoring recommendations
           - Risk-benefit analysis
        
        5. **Comparative Safety Assessment:**
           - Safest options for different patient populations
           - Drugs requiring special monitoring
           - Alternatives for patients with contraindications
        
        Focus on practical clinical decision-making and patient safety considerations.
        """
        
        return self.run(prompt)

    def analyze(self, query, analysis_type="auto"):
        
        
        # Auto-detect analysis type if not specified
        if analysis_type == "auto":
            # Common disease keywords that suggest disease-based search
            disease_keywords = [
                'cancer', 'diabetes', 'hypertension', 'depression', 'anxiety', 'asthma', 
                'copd', 'heart failure', 'stroke', 'epilepsy', 'migraine', 'arthritis',
                'infection', 'pneumonia', 'influenza', 'covid', 'hiv', 'hepatitis',
                'alzheimer', 'parkinson', 'schizophrenia', 'bipolar', 'pain', 'fever'
            ]
            
            query_lower = query.lower()
            if any(keyword in query_lower for keyword in disease_keywords):
                analysis_type = "disease"
            else:
                analysis_type = "drug"
        
        if analysis_type == "drug":
            return self.analyze_drug_safety(query)
        elif analysis_type == "disease":
            return self.analyze_drugs_for_disease(query)
        else:
            return f"Unknown analysis type: {analysis_type}. Use 'drug' or 'disease'."

    def get_drug_list_for_disease(self, disease, limit=20):
        """Get a simple list of drugs for a disease without full analysis"""
        data = self.fetch_drugs_by_disease(disease, limit)
        
        if not data:
            return f"No drugs found for {disease}"
        
        drug_list = []
        for label in data:
            openfda_info = label.get('openfda', {})
            generic_names = openfda_info.get('generic_name', [])
            brand_names = openfda_info.get('brand_name', [])
            
            if generic_names:
                drug_list.extend(generic_names)
            elif brand_names:
                drug_list.extend(brand_names)
        
        # Remove duplicates and return unique list
        unique_drugs = list(set(drug_list))
        return unique_drugs[:limit]
