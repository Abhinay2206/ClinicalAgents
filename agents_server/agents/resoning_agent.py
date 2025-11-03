# agents/reasoning_agent.py
class ReasoningAgent:
    def __init__(self, llm):
        self.llm = llm

    def synthesize(self, reports):
        """
        Synthesize multiple agent reports into a comprehensive patient-friendly summary
        """
        # Build the reports section dynamically based on available reports
        report_sections = []
        
        if 'enrollment' in reports:
            report_sections.append(f"""--- Enrollment Analysis ---
{reports['enrollment']}""")
        
        if 'efficacy' in reports:
            report_sections.append(f"""--- Efficacy Analysis ---
{reports['efficacy']}""")
        
        if 'safety' in reports:
            report_sections.append(f"""--- Safety Analysis ---
{reports['safety']}""")
        
        combined_reports = "\n\n".join(report_sections)
        
        prompt = f"""
        You are a clinical trial expert who helps patients understand complex medical information.
        
        You have received the following specialized analyses:
        
        {combined_reports}
        
        Your task is to synthesize this information into a comprehensive response with TWO sections:
        
        **PATIENT-FRIENDLY SUMMARY** (3-4 paragraphs in simple, clear language):
        - Start with the most important findings that a patient would care about
        - Explain enrollment success rates and what they mean for a patient
        - Highlight safety considerations in plain terms (avoid medical jargon)
        - Mention effectiveness/outcomes in easy-to-understand language
        - Point out any red flags or particularly positive signs
        - Use analogies or comparisons to make complex concepts clear
        
        **DETAILED TECHNICAL ANALYSIS** (Comprehensive professional summary):
        - Synthesize the key findings from all analyses
        - Provide enrollment insights with success predictions and factors
        - Detail efficacy/effectiveness data with clinical significance
        - Summarize safety profile with risk stratification
        - Discuss strengths, weaknesses, and overall assessment
        - Include recommendations for patients considering enrollment
        - Mention readiness for next phase or market approval if applicable
        
        IMPORTANT GUIDELINES:
        - Always start with the PATIENT-FRIENDLY SUMMARY first
        - Use clear section headers
        - Include specific numbers and percentages when available
        - Maintain a balanced, objective tone
        - Highlight both benefits and risks
        - Make actionable recommendations when possible
        """
        
        return self.llm.generate(prompt, max_tokens=3000, temperature=0.7)
