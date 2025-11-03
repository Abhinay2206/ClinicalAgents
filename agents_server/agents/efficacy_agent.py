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

    def analyze(self, drug_name):
        
        data = []
        if self.driver:
            data = self.fetch_efficacy_data(drug_name)
        
        if not data:
            # Provide a general analysis when DB is unavailable or has no records
            prompt = f"""
            As a clinical pharmacology specialist providing educational content for healthcare professionals 
            and medical researchers, analyze treatment efficacy data for {drug_name}.
            
            This is an evidence-based medical education analysis for clinical decision support.
            
            Structure your response in TWO sections:
            
            **PATIENT-FRIENDLY SUMMARY** (Write in simple, clear language):
            - Explain what {drug_name} is used for in everyday terms
            - Describe how well it works (effectiveness) in plain language
            - Mention typical results patients can expect
            - Note any important factors that affect how well it works
            - Keep it brief (2-3 paragraphs)
            
            **DETAILED TECHNICAL ANALYSIS**:
            1. Common therapeutic uses and indications
            2. Typical efficacy rates and clinical outcomes with specific percentages/numbers
            3. Key clinical trial findings (if known) with study references
            4. Factors that may influence efficacy (patient characteristics, dosing, etc.)
            5. Comparison with alternative treatments
            6. Quality of evidence and limitations
            7. Clinical recommendations
            
            Focus on evidence-based medicine and clinical pharmacology.
            Always start with the PATIENT-FRIENDLY SUMMARY first.
            """
        else:
            prompt = f"""
            As a clinical pharmacology specialist providing educational content for healthcare professionals 
            and medical researchers, analyze treatment efficacy data for {drug_name}.
            
            This is an evidence-based medical education analysis for clinical decision support.
            
            Database records available:
            {data}
            
            Structure your response in TWO sections:
            
            **PATIENT-FRIENDLY SUMMARY** (Write in simple, clear language):
            - Explain what the treatment results mean for a patient
            - Describe success rates in plain terms (e.g., "7 out of 10 patients improved")
            - Highlight the most important findings
            - Keep it brief (2-3 paragraphs)
            
            **DETAILED TECHNICAL ANALYSIS**:
            1. Summary of key efficacy metrics and results with specific numbers
            2. Statistical significance and confidence intervals (if available)
            3. Clinical interpretation of the outcomes
            4. Comparison with standard treatments
            5. Subgroup analyses (if available)
            6. Quality of evidence assessment
            7. Recommendations for clinical practice
            
            Focus on evidence-based medicine and clinical pharmacology.
            Always start with the PATIENT-FRIENDLY SUMMARY first.
            """
        
        return self.run(prompt)
