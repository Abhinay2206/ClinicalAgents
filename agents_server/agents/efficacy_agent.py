# agents/efficacy_agent.py
import os
from neo4j import GraphDatabase
from .base_agent import LLMAgent

class EfficacyAgent(LLMAgent):
    def __init__(self, llm, neo4j_uri=None, user=None, password=None):
        super().__init__("Efficacy", "Analyze treatment outcomes", llm)
        
        # Use environment variables if not provided
        neo4j_uri = neo4j_uri or os.getenv('NEO4J_URI')
        user = user or os.getenv('NEO4J_USER') or os.getenv('NEO4J_USERNAME')  # Support both variants
        password = password or os.getenv('NEO4J_PASSWORD')
        
        self.driver = None
        if not all([neo4j_uri, user, password]):
            print("ℹ️ Neo4j credentials not found. EfficacyAgent will use general LLM-based analysis when database data is unavailable.")
        else:
            try:
                self.driver = GraphDatabase.driver(neo4j_uri, auth=(user, password))
                # Test the connection
                with self.driver.session() as session:
                    session.run("RETURN 1")
                print(f"✅ Successfully connected to Neo4j at {neo4j_uri}")
            except Exception as e:
                print(f"❌ Failed to connect to Neo4j: {e}")
                self.driver = None

    def fetch_efficacy_data(self, drug_name):
        if not self.driver:
            return []

        # Heuristic: only query DB for plausible single drug names, avoid generic phrases
        dn = (drug_name or "").strip()
        if len(dn.split()) > 3 or " for " in dn.lower():
            return []

        # Basic sanitization to avoid breaking the query
        dn_safe = dn.replace("'", "\\'")

        try:
            query = (
                "MATCH (d:Drug {name: $name})-[:HAS_OUTCOME]->(o:Outcome) "
                "RETURN d.name AS drug, o.result AS result, o.metric AS metric, o.value AS value"
            )
            with self.driver.session() as session:
                results = session.run(query, name=dn_safe)
                return [r.data() for r in results]
        except Exception as e:
            print(f"Error querying Neo4j: {e}")
            return []

    def extract_entity_with_llm(self, query):
        """Use LLM to extract the drug or treatment name from the query"""
        prompt = f"""
        You are a medical entity extraction assistant. Extract the drug name OR treatment name from this query.
        
        Instructions:
        - Return ONLY the drug/treatment name itself (e.g., "aspirin", "chemotherapy", "metformin")
        - Do NOT include any explanations, prefixes, or punctuation
        - If multiple entities exist, return the PRIMARY one being asked about
        - If no clear entity exists, return: UNKNOWN
        
        Examples:
        Query: "How effective is aspirin for heart disease?" → aspirin
        Query: "Treatment outcomes for metformin in diabetes" → metformin
        Query: "Does chemotherapy work for lung cancer?" → chemotherapy
        
        Query: "{query}"
        
        Entity:
        """
        
        try:
            entity = self.llm.generate(prompt, max_tokens=50, temperature=0.1).strip()
            # Clean up the response
            entity = entity.replace('"', '').replace("'", '').replace('Entity:', '').strip()
            if entity.endswith('.'):
                entity = entity[:-1]
            # Remove common prefixes
            for prefix in ['The entity is', 'Entity:', 'Answer:']:
                if entity.startswith(prefix):
                    entity = entity[len(prefix):].strip()
            
            if entity and entity.upper() != 'UNKNOWN' and len(entity) > 1:
                print(f"✓ Efficacy Agent - LLM extracted entity: '{entity}'")
                return entity
            else:
                print(f"⚠ Efficacy Agent - LLM could not extract entity")
                return "UNKNOWN"
        except Exception as e:
            print(f"❌ Efficacy Agent - Error extracting entity: {e}")
            return "UNKNOWN"

    def analyze(self, drug_name):
        """Analyze efficacy data for a treatment"""
        original_query = drug_name.strip()
        print(f"\n🔬 Efficacy Agent received query: '{original_query}'")
        
        # Try LLM extraction first for better accuracy
        extracted_entity = self.extract_entity_with_llm(original_query)
        
        if extracted_entity and extracted_entity != "UNKNOWN":
            drug_name = extracted_entity
            print(f"✓ Using LLM-extracted entity: '{drug_name}'")
        else:
            # Fallback: use original query with simple cleaning
            import re
            drug_name = re.sub(r'^(how effective is|effectiveness of|efficacy of|treatment outcomes for)\s+', '', 
                             original_query, flags=re.IGNORECASE).strip()
            drug_name = drug_name.rstrip('?').strip()
            print(f"⚠ Using cleaned query: '{drug_name}'")
        
        print(f"🎯 Efficacy agent analyzing: '{drug_name}'")
        
        data = []
        if self.driver:
            data = self.fetch_efficacy_data(drug_name)
        
        if not data:
            # Provide analysis based on LLM's medical knowledge when DB is unavailable
            prompt = f"""
            You are a clinical pharmacology expert. Provide a concise efficacy analysis for {drug_name}.
            
            IMPORTANT: Use your medical knowledge to provide REAL, ACCURATE clinical data. For well-established medications (like metformin, aspirin, etc.), you MUST provide the actual known efficacy data.
            
            **Structure your response as follows:**
            
            ## Efficacy Analysis: {drug_name}
            
            ### Clinical Efficacy Summary
            [Provide 2-3 sentences about the primary indication(s) and overall efficacy. Be specific with percentages and clinical outcomes.]
            
            ### Key Efficacy Data
            Present the most important clinical efficacy metrics in a table:
            
            | Metric | Value/Outcome | Evidence Level |
            |--------|---------------|----------------|
            | Primary Indication | [Disease/condition] | [FDA approved/Phase X] |
            | Response Rate | [X% of patients] | [RCT/Meta-analysis] |
            | Effect Size | [Specific measurement, e.g., HbA1c reduction of 1.5%] | [Study type] |
            | NNT (if known) | [Number] | [Source if available] |
            
            ### Mechanisms of Action
            [1-2 sentences explaining HOW the drug works to achieve its therapeutic effect]
            
            ### Clinical Evidence Highlights
            • [Key finding 1 with specific data]
            • [Key finding 2 with specific data]
            • [Key finding 3 with specific data]
            
            ### Practical Considerations
            - **Best suited for**: [Patient population]
            - **Time to effect**: [Duration]
            - **Comparative effectiveness**: [How it compares to alternatives]
            
            **CRITICAL**: If this is a well-known, established medication (e.g., metformin for diabetes, aspirin for cardiovascular disease), you MUST provide the actual known efficacy data. Do NOT say "no evidence" for established treatments.
            
            If you genuinely don't have specific data for an obscure or experimental treatment, state: "Limited published efficacy data available for {drug_name}. Further clinical studies needed."
            """
        else:
            prompt = f"""
            As a clinical pharmacology specialist providing educational content for healthcare professionals 
            and medical researchers, analyze treatment efficacy data for {drug_name}.
            
            This is an evidence-based medical education analysis for clinical decision support.
            
            Database records available:
            {data}
            
            CRITICAL REQUIREMENTS:
            - Extract and present ALL specific numbers from the data
            - Calculate and present percentages and rates
            - Provide statistical interpretation where possible
            - Use markdown tables and structured formatting
            - Be concrete and data-driven throughout
            - Reference specific data points in every section
            
            Structure your response using this EXACT format:
            
            # Efficacy Analysis: {drug_name}
            
            ## 🎯 Clinical Efficacy Summary (From Database)
            - **Data Records Found**: {len(data)}
            - **Key Metrics Identified**: [List main outcomes from data]
            - **Overall Assessment**: [Based on available data]
            - **Data Quality**: [Complete/Partial/Limited]
            
            ## 📋 Patient-Friendly Overview
            
            [2-3 clear paragraphs in simple language explaining:
            - What the treatment results mean for a patient
            - Describe success rates in plain terms (e.g., "7 out of 10 patients improved")
            - Highlight the most important findings from the data
            - Put numbers in context that patients understand]
            
            ## 📊 Efficacy Data from Database
            
            ### Summary of All Metrics
            | Metric/Outcome | Value/Result | Details |
            |----------------|--------------|---------|
            [Extract and list EVERY data point from the database records]
            
            ### Response Rates (If Available)
            - **Overall Response**: [Extract from data]
            - **Complete Response**: [Extract from data]
            - **Partial Response**: [Extract from data]
            - **Effect Size**: [Calculate or report from data]
            
            ## 📈 Statistical Analysis
            
            ### Primary Outcomes
            | Outcome Measure | Result | Interpretation |
            |-----------------|--------|----------------|
            [List each outcome with its value and what it means clinically]
            
            ### Statistical Significance (If Available in Data)
            - **p-values**: [Report any significance testing]
            - **Confidence Intervals**: [If present in data]
            - **Number Needed to Treat (NNT)**: [Calculate if possible: NNT = 1 / (response rate - baseline rate)]
            
            ## 🔬 Clinical Interpretation
            
            ### What These Results Mean
            - **Clinical Significance**: [Is the effect size clinically meaningful?]
            - **Patient Impact**: [How does this translate to patient benefit?]
            - **Magnitude of Effect**: [Small/Moderate/Large based on data]
            
            ### Comparison Context
            - **Typical Response Rates**: [How do these results compare to expected outcomes?]
            - **Clinical Benchmarks**: [Are these results better/similar/worse than standard?]
            
            ## 🎯 Subgroup Analyses (If Data Available)
            
            | Patient Subgroup | Response Rate | Notes |
            |------------------|---------------|-------|
            [Extract any subgroup data from database]
            
            ## ⚖️ Strengths and Limitations of Data
            
            ### Data Strengths
            - **[Strength 1]**: [What the data shows well]
            - **[Strength 2]**: [Reliability factors]
            
            ### Data Limitations
            - **[Limitation 1]**: [What's missing or incomplete]
            - **[Limitation 2]**: [Cautions in interpretation]
            
            ## 💡 Clinical Practice Implications
            
            Based on the database evidence:
            
            ### When to Consider {drug_name}
            - **Recommended for**: [Based on efficacy data]
            - **Expected outcomes**: [What data suggests patients can expect]
            
            ### Optimizing Treatment Success
            1. **[Recommendation 1]**: [Based on data patterns]
            2. **[Recommendation 2]**: [Evidence-based guidance]
            
            ## 📋 Bottom Line: Key Efficacy Points
            
            Based on database analysis:
            
            1. **[Most important efficacy finding with specific number]**
            2. **[Second key finding with quantitative data]**
            3. **[Clinical significance summary]**
            4. **[Patient selection insight from data]**
            5. **[Important caveat or consideration]**
            
            ---
            
            ## 📊 Data Summary
            - **Database Records Analyzed**: {len(data)}
            - **Metrics Extracted**: [Count of different outcomes]
            - **Data Completeness**: [Assessment of how comprehensive the data is]
            
            ---
            *Note: This analysis is based on database records for educational purposes. Always consult healthcare professionals for treatment decisions.*
            
            REMEMBER: Focus on QUANTITATIVE data and SPECIFIC METRICS from the database. Always include exact numbers and calculations.
            """
        
        return self.run(prompt)
