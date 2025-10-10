# agents/safety_agent.py
import requests
from .base_agent import LLMAgent

class SafetyAgent(LLMAgent):
    def __init__(self, llm, fda_api_key=None):
        super().__init__("Safety", "Analyze drug safety data", llm)
        self.api_key = fda_api_key
        self.base_url = "https://api.fda.gov/drug/label.json"

    def fetch_safety_data(self, drug_name, limit=1):
        
        params = {
            'search': f'openfda.generic_name:"{drug_name}"',
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
            print(f"Error fetching FDA data: {e}")
            return []

    def analyze(self, drug_name):
        
        data = self.fetch_safety_data(drug_name)
        
        if not data:
            return f"No FDA label data found for {drug_name}. Unable to perform safety analysis."
        
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
        Analyze the following FDA drug label safety information for {drug_name}:
        
        {safety_info}
        
        Please provide a comprehensive safety analysis covering:
        1. Black box warnings (if any)
        2. Major contraindications
        3. Common adverse reactions and their frequencies
        4. Significant drug interactions
        5. Special precautions and populations at risk
        6. Overall risk assessment and recommendations
        
        Focus on clinically relevant safety concerns and risk mitigation strategies.
        """
        
        return self.run(prompt)
