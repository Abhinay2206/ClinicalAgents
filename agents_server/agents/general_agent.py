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
        """Provide helpful guidance and clarifying questions"""
        print(f"\n💬 General Agent received query: '{user_query}'")
        
        # Enhanced heuristic to detect medical/clinical context
        q = (user_query or "").lower()
        clinical_keywords = [
            "clinical", "trial", "nct", "study", "cancer", "diabetes", "disease", 
            "therapy", "treatment", "drug", "medicine", "medication", "patient",
            "enrollment", "safety", "efficacy", "side effect", "symptom", 
            "diagnosis", "condition", "health", "medical"
        ]
        
        clinical = any(k in q for k in clinical_keywords)

        if clinical:
            prompt = f"""
            You are a patient-friendly clinical trial assistant. A user asked:
            "{user_query}"

            Provide a helpful, well-formatted response that uses markdown formatting for clarity.
            
            Structure your response using this format:
            
            # Clinical Trial Assistant - Here to Help
            
            ## 👋 Understanding Your Question
            
            [1-2 sentences acknowledging their question empathetically and showing you understand what they're looking for]
            
            ## 🔍 What I Can Help You With
            
            I specialize in providing research-based information on:
            
            - **Clinical Trial Search**: Find trials for specific conditions, by NCT ID, or by location
            - **Drug Safety Profiles**: Side effects, contraindications, and safety warnings
            - **Treatment Effectiveness**: Clinical trial results and efficacy data  
            - **Enrollment Information**: Trial eligibility, enrollment success predictions, and study details
            - **Medical Research**: Evidence-based information from clinical studies
            
            ## 🎯 How to Get Better Answers
            
            To provide you with the most accurate and helpful information, try asking in one of these ways:
            
            1. **For Safety Information**: 
               - "What are the safety details about aspirin?"
               - "Side effects of metformin for diabetes"
               - "Is ibuprofen safe during pregnancy?"
            
            2. **For Effectiveness Data**:
               - "How effective is chemotherapy for lung cancer?"
               - "Treatment outcomes for statins in heart disease"
               - "Does insulin work for type 2 diabetes?"
            
            3. **For Clinical Trials**:
               - "Find clinical trials for Alzheimer's disease"
               - "Show me details for NCT01234567"
               - "What trials are recruiting for breast cancer?"
            
            ## 💡 Next Steps
            
            Please provide:
            - Specific drug name (e.g., "aspirin", "metformin", "lisinopril")
            - Disease or condition (e.g., "Type 2 diabetes", "hypertension", "breast cancer")
            - Trial ID if you have one (e.g., "NCT01234567")
            - What you want to know (safety, effectiveness, or enrollment info)
            
            ---
            ⚕️ *Disclaimer: I provide research information for educational purposes. Always consult your healthcare provider for personalized medical advice and treatment decisions.*
            
            How can I assist you with clinical trial or medical research information today?
            """
            return self.run(prompt)
        else:
            prompt = f"""
            You are a helpful assistant specialized in clinical trial and medical research information. A user asked:
            "{user_query}"

            Provide a short, friendly, well-formatted message using markdown.
            
            Structure your response as:
            
            # Clinical Trial Research Assistant
            
            ## 🏥 My Specialization
            
            I'm designed specifically to help with clinical trial information, treatment safety profiles, effectiveness data, and enrollment details for medical research studies.
            
            ## 🔄 Let's Refocus
            
            The question you asked doesn't seem to be related to clinical trials or medical research. However, I'd be happy to help if you have questions about:
            
            ### Example Questions I Can Answer:
            
            1. **Drug Safety**: "What are the safety details about **[drug name]**?"
               - Examples: aspirin, metformin, atorvastatin
            
            2. **Clinical Trials**: "Find clinical trials for **[condition]**"
               - Examples: diabetes, lung cancer, Alzheimer's disease
            
            3. **Treatment Effectiveness**: "How effective is **[treatment]** for **[condition]**?"
               - Examples: chemotherapy for breast cancer, insulin for diabetes
            
            ## 💬 How Can I Help You Today?
            
            Please feel free to ask me anything related to clinical trials, drug safety, or treatment effectiveness, and I'll provide you with evidence-based information!
            
            ---
            ⚕️ *Note: I specialize in clinical and medical research information for educational purposes.*
            """
            return self.run(prompt)
