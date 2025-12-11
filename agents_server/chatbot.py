# chatbot.py
import os
import sys
import datetime
from typing import Optional
from dotenv import load_dotenv
from llm_client import GrokClient

load_dotenv()

class ClinicalTrialChatbot:
    """
    Patient-friendly chatbot interface for clinical trial information
    Powered by ClinicalAgent 2.0 LangGraph workflow
    """
    
    def __init__(self):
        # Initialize LLM model
        self.llm = GrokClient()
        
        # Conversation history
        self.conversation_history = []

        
    def generate_patient_friendly_response(self, agent_results: dict, original_query: str) -> str:
        """
        Generate a patient-friendly response from agent results
        """
        if agent_results.get("status") == "error":
            return f"""
I'm sorry, I encountered an issue while processing your question: {agent_results.get('error')}

Please try rephrasing your question or ask something else about clinical trials.
"""
        
        # Get the synthesized summary
        full_analysis = agent_results.get("synthesized_summary", "")
        
        # Extract patient-friendly section if available
        if "**PATIENT-FRIENDLY SUMMARY**" in full_analysis:
            parts = full_analysis.split("**DETAILED TECHNICAL ANALYSIS**")
            patient_section = parts[0].replace("**PATIENT-FRIENDLY SUMMARY**", "").strip()
            
            # Format the response
            response = f"""
📋 **Here's what I found about your question:**

{patient_section}

---

💡 **Would you like to know more?** You can ask me to:
- Explain the technical details
- Look up a specific trial by its NCT number
- Search for trials related to other conditions
- Learn about safety or effectiveness data
"""
        else:
            # Fallback: Use LLM to simplify the response
            simplification_prompt = f"""
            You are a helpful healthcare assistant. A patient asked: "{original_query}"
            
            Here is the technical analysis:
            {full_analysis[:2000]}
            
            Please provide a simple, patient-friendly summary (3-4 paragraphs) that:
            1. Directly answers their question in plain language
            2. Highlights the most important points
            3. Mentions any key numbers or success rates
            4. Avoids medical jargon
            
            Do not include technical details or complex medical terminology.
            """
            
            patient_friendly = self.llm.generate(simplification_prompt, max_tokens=800, temperature=0.7)
            
            response = f"""
📋 **Here's what I found about your question:**

{patient_friendly}

---

💡 **Need more information?** I can also:
- Provide detailed technical analysis
- Search for specific trials by NCT number
- Answer questions about safety or effectiveness
"""
        
        return response
    
    def get_detailed_analysis(self, agent_results: dict) -> str:
        """
        Extract and format detailed technical analysis
        """
        full_analysis = agent_results.get("synthesized_summary", "")
        
        if "**DETAILED TECHNICAL ANALYSIS**" in full_analysis:
            parts = full_analysis.split("**DETAILED TECHNICAL ANALYSIS**")
            if len(parts) > 1:
                return f"""
📊 **DETAILED TECHNICAL ANALYSIS**

{parts[1].strip()}
"""
        
        return full_analysis
    
    def process_message(self, user_message: str, detailed: bool = False) -> dict:
        """
        Process a user message and return a response
        Uses ClinicalAgent 2.0 LangGraph workflow
        """
        # Store in conversation history
        self.conversation_history.append({
            "timestamp": datetime.datetime.now(),
            "user": user_message,
            "type": "detailed" if detailed else "simple"
        })
        
        # Check if this is a numbered format trial prediction
        is_trial_prediction = self._is_trial_prediction_format(user_message)
        
        if is_trial_prediction:
            # Use LangGraph v2 workflow for trial predictions
            result = self._process_with_langgraph(user_message)
        else:
            # For general questions, use simple LLM response
            response = self.llm.generate(
                f"You are a helpful clinical trial assistant. Answer this question concisely: {user_message}",
                max_tokens=500,
                temperature=0.7
            )
            
            result = {
                "response": response,
                "activated_agents": ["General LLM"],
                "status": "success",
                "raw_results": {"response": response}
            }
        
        # Store response in history
        self.conversation_history.append({
            "timestamp": datetime.datetime.now(),
            "bot": result["response"],
            "activated_agents": result.get("activated_agents", [])
        })
        
        return result
    
    def _is_trial_prediction_format(self, text: str) -> bool:
        """Check if input is in numbered trial prediction format"""
        import re
        # Look for pattern: (1) drug: ... (2) disease: ...
        pattern = r'\(1\)\s*drug:'
        return bool(re.search(pattern, text, re.IGNORECASE))
    
    def _process_with_langgraph(self, user_message: str) -> dict:
        """Process using ClinicalAgent 2.0 LangGraph workflow"""
        try:
            from langgraph_v2.workflow import ClinicalTrialWorkflow
            
            print("\n🔬 Using ClinicalAgent 2.0 LangGraph Workflow...")
            workflow = ClinicalTrialWorkflow(verbose=True)
            result = workflow.predict(user_message)
            
            # Format for chatbot display
            response_text = self._format_langgraph_response(result)
            
            return {
                "response": response_text,
                "activated_agents": ["ClinicalAgent 2.0", "Planning", "Enrollment", "Safety", "Efficacy", "Reasoning"],
                "status": "success" if not result['errors'] else "partial",
                "raw_results": result
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "response": f"❌ Error processing trial prediction: {str(e)}\n\nPlease check your input format.",
                "activated_agents": ["ClinicalAgent 2.0"],
                "status": "error",
                "raw_results": {"error": str(e)}
            }
    
    def _format_langgraph_response(self, result: dict) -> str:
        """Format LangGraph workflow result for chatbot display"""
        response = f"""
╔══════════════════════════════════════════════════════════════╗
║          🏥 Clinical Trial Prediction Results 🏥            ║
╚══════════════════════════════════════════════════════════════╝

🎯 **PREDICTION**: {result['prediction']}
📊 **CONFIDENCE**: {int(result['confidence'] * 100)}%

🧠 **REASONING**:
{result['reasoning']}

"""
        
        response += "\n" + "="*65 + "\n"
        response += "📑 **INDIVIDUAL AGENT REPORTS**\n"
        response += "="*65 + "\n"
        
        if result['reports']['enrollment']:
            response += f"\n👥 **ENROLLMENT ANALYSIS** (Historian):\n{result['reports']['enrollment']}\n"
        
        if result['reports']['safety']:
            response += f"\n💊 **SAFETY ANALYSIS** (Regulator):\n{result['reports']['safety']}\n"
        
        if result['reports']['efficacy']:
            response += f"\n🔬 **EFFICACY ANALYSIS** (Scientist):\n{result['reports']['efficacy']}\n"
        
        if result['warnings']:
            response += "\n⚠️  **WARNINGS**:\n"
            for warning in result['warnings']:
                response += f"  • {warning}\n"
        
        if result['errors']:
            response += "\n❌ **ERRORS**:\n"
            for error in result['errors']:
                response += f"  • {error}\n"
        
        response += "\n" + "="*65 + "\n"
        response += f"📝 **Parsed Input**:\n"
        response += f"  • Drug (original): {result['drug_parsed']['original']}\n"
        response += f"  • Drug (cleaned): {result['drug_parsed']['cleaned']}\n"
        response += f"  • Disease: {result['disease_parsed']}\n"
        
        return response
    
    def get_welcome_message(self) -> str:
        """
        Get welcome message for the chatbot
        """
        return """
╔══════════════════════════════════════════════════════════════╗
║    🏥 Clinical Trial Assistant - ClinicalAgent 2.0 🏥      ║
╚══════════════════════════════════════════════════════════════╝

Hello! I'm your Clinical Trial Assistant powered by ClinicalAgent 2.0.
I can help you predict trial outcomes and provide detailed analysis.

📋 **What I can help with:**
   • Predicting clinical trial success (PASS/FAIL)
   • Analyzing enrollment feasibility from historical data
   • Assessing drug safety risks via FDA databases
   • Evaluating efficacy through biological pathways
   • Answering general clinical trial questions

💬 **For Trial Predictions** (ClinicalAgent 2.0):
   Use this numbered format:
   (1) drug: <drug_name>; (2) disease: <disease_name>; 
   (3) inclusion criteria: <criteria>; (4) exclusion criteria: <criteria>;

   Example:
   "(1) drug: Metformin tablet; (2) disease: Type 2 Diabetes; 
    (3) inclusion criteria: Adults 18-65 with HbA1c > 7.0%; 
    (4) exclusion criteria: Severe kidney disease;"

🔍 **General Questions**:
   • "What trials are available for diabetes?"
   • "What are the safety concerns for aspirin?"
   • "Tell me about trial NCT01234567"

🔧 **Special commands:**
   • Type 'help' for more information
   • Type 'examples' for sample queries
   • Type 'history' to see our conversation
   • Type 'quit' or 'exit' to end our chat

Let's get started! What would you like to know?
"""

    
    def display_help(self) -> str:
        """
        Display detailed help information
        """
        return """
╔══════════════════════════════════════════════════════════════╗
║                         HELP GUIDE                           ║
╚══════════════════════════════════════════════════════════════╝

📖 **HOW TO USE THIS CHATBOT:**

1️⃣  **Simple Questions (Default Mode)**
   Just type your question naturally:
   • "Are there trials for diabetes?"
   • "What is the success rate for enrollment?"
   • "Tell me about cancer treatment studies"
   
   You'll get easy-to-understand answers in plain language.

2️⃣  **Detailed Analysis Mode**
   Start your question with 'detailed':
   • "detailed what trials are available for diabetes?"
   • "detailed analyze NCT01234567"
   
   You'll get comprehensive technical information.

3️⃣  **Specific Trial Lookup**
   Include an NCT number in your question:
   • "Tell me about trial NCT01234567"
   • "What is NCT98765432 about?"

📊 **TYPES OF INFORMATION:**

🎯 **Enrollment Information**
   • Patient eligibility criteria
   • Success rate predictions
   • Recruitment status and patterns
   • Demographic requirements

⚕️ **Safety Information**
   • Adverse events and side effects
   • Risk profiles
   • Safety concerns

✨ **Effectiveness Information**
   • Treatment outcomes
   • Clinical benefits
   • Success rates

🔧 **SPECIAL COMMANDS:**

• help       - Show this help message
• history    - View conversation history
• clear      - Clear conversation history
• examples   - Show example questions
• quit/exit  - End the conversation

💡 **TIPS:**
   ✓ Ask questions in your own words
   ✓ Be specific about conditions or trial numbers
   ✓ Request clarification if something is unclear
   ✓ Use 'detailed' mode for technical information
"""
    
    def show_examples(self) -> str:
        """
        Show example queries
        """
        return """
╔══════════════════════════════════════════════════════════════╗
║                    EXAMPLE QUESTIONS                         ║
╚══════════════════════════════════════════════════════════════╝

🔍 **GENERAL SEARCHES:**
   • "What clinical trials are available for Type 2 diabetes?"
   • "Show me recent cancer treatment studies"
   • "Are there any trials for Alzheimer's disease?"

📈 **ENROLLMENT & SUCCESS RATES:**
   • "What is the enrollment success rate for diabetes trials?"
   • "How many patients typically enroll in Phase 3 studies?"
   • "What are the eligibility requirements for heart disease trials?"
   • "What is the chance of success for this trial?"

🔬 **SPECIFIC TRIALS:**
   • "Tell me about trial NCT01234567"
   • "What is the status of NCT98765432?"
   • "Is NCT01234567 still recruiting?"

⚠️ **SAFETY INFORMATION:**
   • "What are the side effects of diabetes trial medications?"
   • "Are there safety concerns with NCT01234567?"
   • "What risks are associated with cancer immunotherapy trials?"

✅ **EFFECTIVENESS:**
   • "How effective are the treatments in diabetes trials?"
   • "What are the outcomes for patients in cancer trials?"
   • "Do diabetes medications in trials show good results?"

📊 **DETAILED ANALYSIS:**
   • "detailed analyze all diabetes trials"
   • "detailed what is the complete information on NCT01234567"
   • "detailed show me comprehensive safety data for cancer trials"

💡 **TIP:** You can combine multiple aspects in one question!
   "What is the success rate and safety profile of diabetes trials?"
"""
    
    def show_history(self) -> str:
        """
        Display conversation history
        """
        if not self.conversation_history:
            return "No conversation history yet. Start by asking a question!"
        
        history_text = """
╔══════════════════════════════════════════════════════════════╗
║                   CONVERSATION HISTORY                        ║
╚══════════════════════════════════════════════════════════════╝

"""
        for i, entry in enumerate(self.conversation_history, 1):
            timestamp = entry['timestamp'].strftime("%H:%M:%S")
            if 'user' in entry:
                history_text += f"\n[{timestamp}] 👤 You: {entry['user']}\n"
            elif 'bot' in entry:
                agents = ', '.join(entry.get('activated_agents', []))
                history_text += f"[{timestamp}] 🤖 Assistant (via {agents}):\n"
                # Show truncated response
                response = entry['bot'][:200] + "..." if len(entry['bot']) > 200 else entry['bot']
                history_text += f"{response}\n"
        
        return history_text
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        return "✓ Conversation history cleared."


def interactive_chatbot():
    """
    Interactive chatbot mode
    """
    chatbot = ClinicalTrialChatbot()
    
    # Display welcome message
    print(chatbot.get_welcome_message())
    
    last_results = None
    
    while True:
        try:
            # Get user input
            user_input = input("\n💬 You: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\n👋 Thank you for using the Clinical Trial Assistant!")
                print("Stay healthy and informed! Goodbye!\n")
                break
            
            if user_input.lower() == 'help':
                print(chatbot.display_help())
                continue
            
            if user_input.lower() == 'examples':
                print(chatbot.show_examples())
                continue
            
            if user_input.lower() == 'history':
                print(chatbot.show_history())
                continue
            
            if user_input.lower() == 'clear':
                print(chatbot.clear_history())
                continue
            
            # Check if user wants detailed analysis
            detailed = False
            if user_input.lower().startswith('detailed '):
                detailed = True
                user_input = user_input[9:].strip()  # Remove 'detailed ' prefix
            
            # Check if asking for details of last query
            if user_input.lower() in ['more details', 'detailed', 'technical details', 'full analysis'] and last_results:
                print("\n🤖 Assistant:\n")
                print(chatbot.get_detailed_analysis(last_results))
                continue
            
            # Process the message
            print("\n🔍 Analyzing your question...\n")
            result = chatbot.process_message(user_input, detailed=detailed)
            last_results = result['raw_results']
            
            # Display response
            print("🤖 Assistant:\n")
            print(result['response'])
            
            # Show which agents were used (for transparency)
            if result['activated_agents']:
                agents_str = ', '.join(result['activated_agents'])
                print(f"\n📊 (Analysis powered by: {agents_str})")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Take care!\n")
            break
        except Exception as e:
            print(f"\n❌ I encountered an error: {str(e)}")
            print("Please try asking your question in a different way.\n")


def main():
    """
    Main entry point
    """
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            chatbot = ClinicalTrialChatbot()
            print(chatbot.display_help())
            return
        elif sys.argv[1] == "--examples":
            chatbot = ClinicalTrialChatbot()
            print(chatbot.show_examples())
            return
        elif sys.argv[1] == "--query":
            if len(sys.argv) > 2:
                chatbot = ClinicalTrialChatbot()
                query = " ".join(sys.argv[2:])
                detailed = query.lower().startswith('detailed ')
                if detailed:
                    query = query[9:]
                
                print("\n🔍 Processing your question...\n")
                result = chatbot.process_message(query, detailed=detailed)
                print(result['response'])
                return
            else:
                print("Error: Please provide a query")
                print("Usage: python chatbot.py --query 'your question here'")
                return
    
    # Default to interactive mode
    interactive_chatbot()


if __name__ == "__main__":
    main()
