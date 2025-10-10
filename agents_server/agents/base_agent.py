# agents/base_agent.py
class LLMAgent:
    def __init__(self, name, role, llm):
        self.name = name
        self.role = role
        self.llm = llm

    def run(self, prompt):
        response = self.llm.generate(prompt)
        return response
