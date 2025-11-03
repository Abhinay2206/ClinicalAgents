# chatbot.py
import os
import sys
import datetime
from typing import Optional
from dotenv import load_dotenv
from gemini_client import GeminiClient
from simple_dynamic_orchestrator import SimpleDynamicOrchestrator
from agents.human_proxy_agent import HumanProxyAgent

load_dotenv()

class ClinicalTrialChatbot:
    """
    Patient-friendly chatbot interface for clinical trial information
    """
    
    def __init__(self):
        # Initialize Gemini 2.5 Flash model
        self.llm = GeminiClient(model_name="gemini-2.5-flash")
        
        # Initialize dynamic orchestrator
        self.orchestrator = SimpleDynamicOrchestrator(self.llm)

        # HumanProxyAgent for session management, review gate, and Mongo logging
        use_proxy = (os.getenv("USE_PROXY", "1") != "0")
        self.proxy: Optional[HumanProxyAgent] = HumanProxyAgent(self.llm) if use_proxy else None
        self.session_id = self.proxy.session_id if self.proxy else None
        
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
        """
        # Store in conversation history
        self.conversation_history.append({
            "timestamp": datetime.datetime.now(),
            "user": user_message,
            "type": "detailed" if detailed else "simple"
        })
        
        if self.proxy:
            # Use proxy for full pipeline (reasoner + reviewer + Mongo logging)
            result = self.proxy.handle_user_prompt(user_message)
            agent_results = result.get("agent_results", {})
            response_text = result.get("final_output", "")
            self.session_id = result.get("session_id", self.session_id)
        else:
            # Fallback to direct orchestrator path
            agent_results = self.orchestrator.process_query(user_message)
            if detailed:
                response_text = self.get_detailed_analysis(agent_results)
            else:
                response_text = self.generate_patient_friendly_response(agent_results, user_message)
        
        # Store response in history
        self.conversation_history.append({
            "timestamp": datetime.datetime.now(),
            "bot": response_text,
            "activated_agents": agent_results.get("activated_agents", [])
        })
        
        return {
            "response": response_text,
            "activated_agents": agent_results.get("activated_agents", []),
            "status": agent_results.get("status", "success"),
            "raw_results": agent_results
        }
    
    def get_welcome_message(self) -> str:
        """
        Get welcome message for the chatbot
        """
        return """
╔══════════════════════════════════════════════════════════════╗
║         🏥 Clinical Trial Information Assistant 🏥          ║
╚══════════════════════════════════════════════════════════════╝

Hello! I'm your Clinical Trial Assistant. I can help you understand
clinical trials in simple terms and provide detailed information when needed.

📋 **What I can help with:**
   • Finding clinical trials for specific conditions
   • Explaining enrollment criteria and success rates
   • Providing safety and effectiveness information
   • Answering questions about specific trials (NCT numbers)
   • Translating complex medical information into plain language

💬 **Example questions you can ask:**
   • "What trials are available for diabetes?"
   • "What are the chances of success for cancer trials?"
   • "Is trial NCT01234567 safe?"
   • "What are the enrollment requirements for heart disease studies?"

🔍 **Special commands:**
   • Type 'detailed' before your question for technical analysis
   • Type 'help' for more information
   • Type 'history' to see our conversation
   • Type 'quit' or 'exit' to end our chat

Let's get started! What would you like to know about clinical trials?
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
    # Show active session id if proxy enabled
    if chatbot.proxy and chatbot.session_id:
        print(f"[session: {chatbot.session_id}] (Mongo logging {'ON' if os.getenv('MONGODB_URI') else 'OFF'})")
    
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
            if user_input.lower().startswith('session'):
                # session -> show current, session new -> new id
                parts = user_input.split()
                if len(parts) == 1:
                    print(f"Current session: {chatbot.session_id or 'N/A'}")
                elif len(parts) == 2 and parts[1].lower() == 'new':
                    if chatbot.proxy:
                        # create a new proxy with new session id
                        chatbot.proxy = HumanProxyAgent(chatbot.llm)
                        chatbot.session_id = chatbot.proxy.session_id
                        print(f"✓ Started new session: {chatbot.session_id}")
                    else:
                        print("Proxy disabled. Enable USE_PROXY to manage sessions.")
                else:
                    print("Usage: 'session' | 'session new'")
                continue
            if user_input.lower().startswith('replay'):
                if chatbot.proxy:
                    parts = user_input.split()
                    sid = parts[1] if len(parts) > 1 else chatbot.session_id
                    if not sid:
                        print("No session id specified or active.")
                        continue
                    # fetch and print a simple replay summary
                    try:
                        import asyncio
                        replay = asyncio.run(chatbot.proxy.replay_session(sid))
                        events = replay.get('events', [])
                        print(f"\nReplay for session {sid} - {len(events)} events:")
                        for e in events:
                            ts = str(e.get('timestamp',''))
                            print(f"- [{ts}] {e.get('event')} via {e.get('agent_name')}")
                    except Exception as e:
                        print(f"Failed to replay: {e}")
                else:
                    print("Proxy disabled. Enable USE_PROXY to use replay.")
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
