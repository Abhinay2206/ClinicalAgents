# agents/reasoning_agent.py
class ReasoningAgent:
    def __init__(self, llm):
        self.llm = llm

    def synthesize(self, reports):
        prompt = f"""
        Combine the following reports into a final reasoning summary:

        --- Enrollment ---
        {reports['enrollment']}

        --- Efficacy ---
        {reports['efficacy']}

        --- Safety ---
        {reports['safety']}

        Based on the above, create a concise and balanced conclusion about the clinical trial.
        Mention key strengths, weaknesses, and readiness for next phase trials.
        """
        return self.llm.generate(prompt)
