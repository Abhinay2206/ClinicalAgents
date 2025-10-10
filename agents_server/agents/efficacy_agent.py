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
        
        if not all([neo4j_uri, user, password]):
            raise ValueError("Neo4j credentials not found. Set NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD environment variables.")
        
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
        
        try:
            query = f"""
            MATCH (d:Drug {{name: '{drug_name}'}})-[:HAS_OUTCOME]->(o:Outcome)
            RETURN d.name AS drug, o.result AS result, o.metric AS metric, o.value AS value
            """
            with self.driver.session() as session:
                results = session.run(query)
                return [r.data() for r in results]
        except Exception as e:
            print(f"Error querying Neo4j: {e}")
            return []

    def analyze(self, drug_name):
        
        if not self.driver:
            return f"Cannot analyze efficacy for {drug_name}: Neo4j connection not available. Please check your database credentials and connection."
        
        data = self.fetch_efficacy_data(drug_name)
        
        if not data:
            # Provide a mock analysis when no data is available
            prompt = f"""
            No specific efficacy data found in the database for {drug_name}. 
            Please provide a general efficacy analysis for {drug_name} based on your knowledge, including:
            1. Common therapeutic uses and indications
            2. Typical efficacy rates and clinical outcomes
            3. Key clinical trial findings (if known)
            4. Factors that may influence efficacy
            5. Comparison with alternative treatments
            
            Note: This analysis is based on general medical knowledge as no specific database records were found.
            """
        else:
            prompt = f"""
            Analyze efficacy outcomes for {drug_name} based on the following database records:
            {data}
            
            Please provide a comprehensive analysis including:
            1. Summary of key efficacy metrics and results
            2. Statistical significance and confidence intervals (if available)
            3. Clinical interpretation of the outcomes
            4. Comparison with standard treatments
            5. Recommendations for clinical practice
            """
        
        return self.run(prompt)
