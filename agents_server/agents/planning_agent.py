# agents/planning_agent.py
from .enrollment_agent import EnrollmentAgent
from .efficacy_agent import EfficacyAgent
from .safety_agent import SafetyAgent

class PlanningAgent:
    def __init__(self, llm, config=None):
        # Initialize agents with default paths from datasets folder
        self.enrollment_agent = EnrollmentAgent(llm)
        self.efficacy_agent = EfficacyAgent(llm)  # Uses environment variables
        self.safety_agent = SafetyAgent(llm)

    def execute_plan(self, query_embedding, drug_name):
        # Convert drug_name to a search query for enrollment analysis
        # Since we're dealing with clinical trials, use the drug_name as the search term
        enrollment_query = drug_name if drug_name else "cancer clinical trials"
        
        enrollment_report = self.enrollment_agent.analyze(enrollment_query)
        efficacy_report = self.efficacy_agent.analyze(drug_name)
        safety_report = self.safety_agent.analyze(drug_name)

        return {
            "enrollment": enrollment_report,
            "efficacy": efficacy_report,
            "safety": safety_report
        }
