# agents/general_agent.py
from .base_agent import LLMAgent

class GeneralAgent(LLMAgent):
    """
    Safe fallback agent to handle any prompt gracefully.
    - If the prompt is clinical/medical, provide helpful guidance and next steps.
    - If the prompt is unrelated, gently reorient toward clinical trial topics and ask clarifying questions.
    """
    def __init__(self, llm):
        super().__init__("General", "Provide safe fallback and clarifying guidance", llm)

    def analyze(self, user_query: str) -> str:
        # Minimal heuristic to detect medical/clinical context
        q = (user_query or "").lower()
        clinical = any(k in q for k in [
            "clinical", "trial", "nct", "study", "cancer", "diabetes", "disease", "therapy", "treatment", "drug", "medicine"
        ])

        if clinical:
            prompt = f"""
            You are a patient-friendly clinical trial assistant. A user asked:
            "{user_query}"

            Provide a helpful response that:
            - Acknowledges their question empathetically
            - Explains what kinds of information you can provide (trials, enrollment, safety, effectiveness)
            - Offers 2-3 actionable next steps (e.g., share condition, location, NCT ID, treatment name)
            - Includes a short safety disclaimer (not medical advice; talk to their clinician)
            - Keeps language clear and supportive (2-3 short paragraphs + a short bullet list)
            """
            return self.run(prompt)
        else:
            prompt = f"""
            You are a helpful assistant specialized in clinical trial information. A user asked:
            "{user_query}"

            Provide a short, friendly message that:
            - States your specialization (clinical trials, safety, effectiveness, enrollment)
            - Offers to help reframe their question for this domain
            - Suggests a couple of example prompts they can try
            Keep it concise (1 short paragraph + 3 bullet examples).
            """
            return self.run(prompt)
