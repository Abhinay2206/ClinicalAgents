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
            # Provide analysis based on established knowledge when FDA data is not available
            prompt = f"""
            You are a clinical safety expert providing comprehensive information to patients and healthcare professionals.
            Analyze the safety profile for the specific drug: {drug_name}
            
            CRITICAL REQUIREMENTS - YOU MUST:
            1. Reference "{drug_name}" specifically throughout your entire response
            2. Provide AT LEAST 8-10 specific data points with frequencies, percentages, or concrete metrics
            3. Use markdown formatting with headers, tables, and bullet points
            4. Include severity classifications for all adverse events
            5. If you genuinely lack ANY specific data about {drug_name}, respond ONLY with:
               "I don't have sufficient specific safety data for {drug_name}. Please consult FDA labeling or a healthcare professional."
            6. DO NOT provide generic safety information - every statement must be specific to {drug_name}
            7. Include statistical data, clinical trial results, and real-world evidence where available
            8. Use structured tables for side effect profiles and drug interactions
            
            Structure your response using this EXACT format:
            
            # Safety Profile: {drug_name}
            
            ## 🎯 Executive Summary
            - **Risk Level**: [Low/Moderate/High] - with justification
            - **Most Common Side Effects**: [Top 3-5 with specific percentages]
            - **Serious Risks**: [Critical warnings with incidence rates]
            - **Contraindications**: [Who should absolutely NOT use this]
            - **Patient Exposure Data**: [Number of patients studied, if known]
            
            ## 📋 Patient-Friendly Overview
            
            [3-4 clear paragraphs explaining in simple terms:
            - What {drug_name} is and what it treats
            - Main safety concerns patients should know
            - Common side effects they might experience with frequencies
            - Important warnings and who should avoid it
            - When to seek medical attention]
            
            ## 📊 Adverse Event Profile
            
            ### Very Common (≥10% incidence)
            | Side Effect | Frequency | Severity | Typical Onset | Management |
            |-------------|-----------|----------|---------------|------------|
            | [List each] | [%] | [Mild/Mod/Severe] | [Timeframe] | [Brief guidance] |
            
            ### Common (1-10% incidence)
            | Side Effect | Frequency | Severity | Typical Onset | Management |
            |-------------|-----------|----------|---------------|------------|
            | [List each] | [%] | [Mild/Mod/Severe] | [Timeframe] | [Brief guidance] |
            
            ### Serious Adverse Events (Any frequency)
            | Event | Frequency | Risk Factors | Warning Signs | Action Required |
            |-------|-----------|--------------|---------------|-----------------|
            | [List each serious risk] | [%] | [Who is at higher risk] | [What to watch for] | [What to do] |
            
            ## 🔬 Clinical Safety Data
            - **Patient Exposure**: [N patients in clinical trials, post-marketing surveillance data]
            - **Study Duration**: [How long patients were followed]
            - **Key Clinical Trials**: [Reference major safety studies if known]
            - **Long-term Safety**: [Available data on extended use]
            
            ## ⚠️ Black Box Warnings & Contraindications
            
            ### Absolute Contraindications
            - **[Condition/Situation 1]**: [Detailed explanation]
            - **[Condition/Situation 2]**: [Detailed explanation]
            
            ### Warnings & Precautions
            - **[Warning 1]**: [Detailed explanation with risk data]
            - **[Warning 2]**: [Detailed explanation with risk data]
            
            ## 👥 Special Populations
            
            ### Pregnancy & Lactation
            - **Pregnancy Category**: [Category if applicable]
            - **Risk Assessment**: [Specific data for {drug_name}]
            - **Breastfeeding**: [Safety information]
            
            ### Pediatric Use
            - **Safety Data**: [Age-specific information]
            - **Dosing Considerations**: [If relevant]
            
            ### Geriatric Use
            - **Special Risks**: [Age-related concerns]
            - **Dose Adjustments**: [If needed]
            
            ### Renal/Hepatic Impairment
            - **Renal**: [Dose adjustments, monitoring]
            - **Hepatic**: [Dose adjustments, monitoring]
            
            ## 💊 Drug Interactions
            
            | Interacting Drug/Class | Interaction Type | Severity | Clinical Effect | Management |
            |------------------------|------------------|----------|-----------------|------------|
            | [Drug 1] | [Mechanism] | [Major/Moderate/Minor] | [What happens] | [How to handle] |
            | [Drug 2] | [Mechanism] | [Major/Moderate/Minor] | [What happens] | [How to handle] |
            
            ## 🔍 Monitoring Requirements
            - **Baseline**: [What to check before starting]
            - **Ongoing**: [Regular monitoring needed]
            - **Frequency**: [How often]
            - **Parameters to Watch**: [Specific values/signs]
            
            ## 💡 Risk Mitigation Strategies
            1. **[Strategy 1]**: [Detailed guidance]
            2. **[Strategy 2]**: [Detailed guidance]
            3. **[Strategy 3]**: [Detailed guidance]
            
            ## 📋 Bottom Line: Key Takeaways
            1. **[Most critical safety point]**
            2. **[Second most important point]**
            3. **[Third key point]**
            4. **[When to seek immediate medical attention]**
            5. **[Important reminder about monitoring/compliance]**
            
            ---
            *Note: This analysis is for educational purposes. Always consult healthcare professionals for medical advice.*
            
            REMEMBER: Every data point must be specific to {drug_name}. Use tables and structured formatting throughout.
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
        You are a clinical safety expert providing comprehensive information to patients and healthcare professionals.
        Analyze the following FDA drug label safety information for the specific drug: {drug_name}
        
        FDA DATA:
        {safety_info}
        
        CRITICAL REQUIREMENTS - YOU MUST:
        1. Reference "{drug_name}" specifically throughout your response
        2. Extract and present ALL specific data from the FDA label (exact frequencies, percentages, numbers)
        3. Use markdown formatting with headers, tables, and structured lists
        4. DO NOT add generic safety information beyond what's in the FDA data
        5. Focus exclusively on {drug_name} - extract every specific data point available
        6. Include ALL adverse event rates, drug interactions, and warnings from the data
        7. Present data in structured tables for easy scanning
        8. Preserve exact FDA language for black box warnings
        
        Structure your response using this EXACT format:
        
        # Safety Profile: {drug_name}
        
        ## 🎯 Executive Summary (From FDA Data)
        - **Risk Level**: [Based on black box warnings and serious adverse events]
        - **Most Common Side Effects**: [Extract top 5 with exact percentages from FDA data]
        - **Serious Risks**: [List all serious adverse events with rates]
        - **Contraindications**: [List all from FDA data]
        - **Brand Names**: {safety_info[0].get('brand_names', []) if safety_info else 'N/A'}
        
        ## 📋 Patient-Friendly Overview
        
        [3-4 clear paragraphs in simple language explaining:
        - What {drug_name} is used for (from FDA indications)
        - The most important safety information from the FDA label
        - Common side effects patients should expect (with frequencies from data)
        - Serious warnings and when to seek immediate medical help
        - Who should not take this medication (contraindications from FDA)]
        
        ## ⚠️ FDA Black Box Warnings
        
        {f"### CRITICAL WARNING" if safety_info and any(label.get('boxed_warning') for label in safety_info) else ""}
        
        [Extract and present VERBATIM all black box warnings from the FDA data. If none exist, state "No black box warnings in FDA data."]
        
        ## 📊 Adverse Event Profile (From FDA Clinical Trials)
        
        ### Very Common Side Effects (≥10% incidence)
        | Side Effect | Frequency | Details from FDA Label |
        |-------------|-----------|------------------------|
        | [Extract each] | [Exact %] | [Any additional context from FDA data] |
        
        ### Common Side Effects (1-10% incidence)
        | Side Effect | Frequency | Details from FDA Label |
        |-------------|-----------|------------------------|
        | [Extract each] | [Exact %] | [Any additional context from FDA data] |
        
        ### Serious Adverse Events
        | Event | Frequency | Risk Factors | FDA Guidance |
        |-------|-----------|--------------|--------------|
        | [List all serious events from FDA data] | [Rate] | [If specified] | [Management guidance] |
        
        ## 🚫 Contraindications (From FDA Label)
        
        ### Absolute Contraindications
        [Extract and list ALL contraindications from FDA data with full explanations]
        
        1. **[Contraindication 1]**: [Full FDA explanation]
        2. **[Contraindication 2]**: [Full FDA explanation]
        
        ## ⚡ Warnings & Precautions (From FDA Label)
        
        [Extract ALL warnings and precautions with complete explanations]
        
        - **[Warning 1]**: [Detailed FDA guidance with any statistical data]
        - **[Warning 2]**: [Detailed FDA guidance with any statistical data]
        
        ## 💊 Drug Interactions (From FDA Label)
        
        | Interacting Drug/Class | Interaction Mechanism | Clinical Effect | FDA Management Guidance |
        |------------------------|----------------------|-----------------|-------------------------|
        | [Extract each interaction] | [Mechanism if specified] | [Effect from FDA data] | [FDA recommendations] |
        
        ## 👥 Special Populations (FDA Guidance)
        
        ### Pregnancy & Lactation
        - **Pregnancy**: [Extract exact FDA pregnancy guidance]
        - **Lactation**: [Extract exact FDA breastfeeding guidance]
        - **Contraception**: [If FDA specifies contraception requirements]
        
        ### Pediatric Use
        [Extract complete FDA pediatric safety information]
        
        ### Geriatric Use
        [Extract complete FDA geriatric safety information]
        
        ### Renal Impairment
        [Extract FDA guidance on renal impairment]
        
        ### Hepatic Impairment
        [Extract FDA guidance on hepatic impairment]
        
        ## 🔍 FDA-Recommended Monitoring
        
        [Extract all monitoring requirements from FDA label]
        
        - **Before Starting**: [Baseline requirements]
        - **During Treatment**: [Ongoing monitoring]
        - **Parameters to Monitor**: [Specific tests/values]
        - **Frequency**: [How often per FDA guidance]
        
        ## 📋 Bottom Line: Critical Safety Points
        
        Based on the FDA label analysis:
        
        1. **[Most critical safety issue from black box/warnings]**
        2. **[Most common adverse event with frequency]**
        3. **[Key contraindication]**
        4. **[Important drug interaction]**
        5. **[Critical monitoring requirement]**
        
        ---
        
        ## 📄 Data Source Summary
        - **Generic Name(s)**: {safety_info[0].get('drug', 'N/A') if safety_info else 'N/A'}
        - **Brand Name(s)**: {', '.join(safety_info[0].get('brand_names', [])) if safety_info and safety_info[0].get('brand_names') else 'N/A'}
        - **FDA Labels Analyzed**: {len(safety_info)}
        
        ---
        *Note: This analysis is based on FDA-approved labeling. Always consult healthcare professionals for medical advice.*
        
        REMEMBER: Extract EVERY specific data point from the FDA data. Use exact frequencies and preserve FDA language for warnings.
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

    def extract_entity_with_llm(self, query):
        """Use LLM to extract the drug or disease name from the query"""
        prompt = f"""
        You are a medical entity extraction assistant. Extract the drug name OR disease name from this query.
        
        Instructions:
        - Return ONLY the drug/disease name itself (e.g., "aspirin", "diabetes", "metformin")
        - Do NOT include any explanations, prefixes, or punctuation
        - If multiple entities exist, return the PRIMARY one being asked about
        - For drug safety questions, prioritize the drug name
        - If no clear entity exists, return: UNKNOWN
        
        Examples:
        Query: "What are the safety details about aspirin?" → aspirin
        Query: "Side effects of metformin for diabetes" → metformin
        Query: "Is ibuprofen safe?" → ibuprofen
        Query: "Tell me about cancer trials" → cancer
        
        Query: "{query}"
        
        Entity:
        """
        
        try:
            entity = self.llm.generate(prompt, max_tokens=50, temperature=0.1).strip()
            # Clean up the response
            entity = entity.replace('"', '').replace("'", '').replace('Entity:', '').strip()
            # Remove trailing period if present
            if entity.endswith('.'):
                entity = entity[:-1]
            # Remove common prefixes that LLM might add
            for prefix in ['The entity is', 'Entity:', 'Answer:']:
                if entity.startswith(prefix):
                    entity = entity[len(prefix):].strip()
            
            if entity and entity.upper() != 'UNKNOWN' and len(entity) > 1:
                print(f"✓ LLM extracted entity: '{entity}' from '{query}'")
                return entity
            else:
                print(f"⚠ LLM could not extract entity from: '{query}'")
                return "UNKNOWN"
        except Exception as e:
            print(f"❌ Error extracting entity with LLM: {e}")
            return "UNKNOWN"

    def analyze(self, query, analysis_type="auto"):
        """
        Main analysis method that routes to drug or disease analysis
        Extracts clean entity names from queries before processing
        """
        original_query = query.strip()
        print(f"\n🔍 Safety Agent received query: '{original_query}'")
        
        # Always try LLM extraction first for best accuracy
        extracted_entity = self.extract_entity_with_llm(original_query)
        
        # Use extracted entity if valid, otherwise try simple regex cleanup
        if extracted_entity and extracted_entity != "UNKNOWN":
            clean_query = extracted_entity
            print(f"✓ Using LLM-extracted entity: '{clean_query}'")
        else:
            # Fallback: simple regex-based cleaning
            import re
            clean_query = original_query
            
            # Remove common question patterns to get just the entity name
            patterns_to_remove = [
                r'^review clinical safety profile for:\s*',
                r'^analyze safety (of|for)\s*',
                r'^what (are|is) the (side effects?|safety|risks?) (of|for)\s*',
                r'^is\s+.*?\s+safe(\s+for)?',
                r'^safety (of|for)\s*',
                r'^\s*provide.*?for:\s*',
                r'^safety details about\s*',
                r'^tell me about\s*',
                r'^i want to know about\s*',
            ]
            
            for pattern in patterns_to_remove:
                clean_query = re.sub(pattern, '', clean_query, flags=re.IGNORECASE).strip()
            
            # Remove trailing question marks and extra whitespace
            clean_query = clean_query.rstrip('?').strip()
            print(f"⚠ Using regex-cleaned query: '{clean_query}'")
        
        # Auto-detect analysis type if not specified
        if analysis_type == "auto":
            # Common disease keywords that suggest disease-based search
            disease_keywords = [
                'cancer', 'diabetes', 'hypertension', 'depression', 'anxiety', 'asthma', 
                'copd', 'heart failure', 'stroke', 'epilepsy', 'migraine', 'arthritis',
                'infection', 'pneumonia', 'influenza', 'covid', 'hiv', 'hepatitis',
                'alzheimer', 'parkinson', 'schizophrenia', 'bipolar', 'pain', 'fever'
            ]
            
            query_lower = clean_query.lower()
            if any(keyword in query_lower for keyword in disease_keywords):
                analysis_type = "disease"
                print(f"📋 Detected disease query, type: {analysis_type}")
            else:
                analysis_type = "drug"
                print(f"💊 Detected drug query, type: {analysis_type}")
        
        print(f"🎯 Safety agent analyzing: '{clean_query}' (type: {analysis_type})")
        
        if analysis_type == "drug":
            return self.analyze_drug_safety(clean_query)
        elif analysis_type == "disease":
            return self.analyze_drugs_for_disease(clean_query)
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
