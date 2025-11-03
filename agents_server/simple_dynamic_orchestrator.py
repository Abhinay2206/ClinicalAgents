# simple_dynamic_orchestrator.py
import os
import re
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

from agents.enrollment_agent import EnrollmentAgent
from agents.efficacy_agent import EfficacyAgent
from agents.safety_agent import SafetyAgent
from agents.resoning_agent import ReasoningAgent
from agents.general_agent import GeneralAgent
from gemini_client import GeminiClient

load_dotenv()

class SimpleDynamicOrchestrator:
    """
    Simple dynamic agent orchestrator that determines which agents to activate
    based on user prompts using keyword analysis and intent detection.
    """
    
    def __init__(self, llm=None):
        self.llm = llm or GeminiClient(model_name="gemini-2.5-flash")
        
        # Track available agents regardless of individual init failures
        self.agents_available: List[str] = []
        
        # Initialize all available agents
        try:
            self.enrollment_agent = EnrollmentAgent(self.llm)
            self.agents_available.append("enrollment")
            print("✓ Enrollment agent initialized")
        except Exception as e:
            print(f"⚠ Enrollment agent failed to initialize: {e}")
            self.enrollment_agent = None
        
        try:
            self.efficacy_agent = EfficacyAgent(self.llm)
            self.agents_available.append("efficacy")
            print("✓ Efficacy agent initialized")
        except Exception as e:
            print(f"⚠ Efficacy agent failed to initialize: {e}")
            self.efficacy_agent = None
        
        try:
            self.safety_agent = SafetyAgent(self.llm)
            self.agents_available.append("safety")
            print("✓ Safety agent initialized")
        except Exception as e:
            print(f"⚠ Safety agent failed to initialize: {e}")
            self.safety_agent = None
        
        try:
            self.reasoning_agent = ReasoningAgent(self.llm)
            print("✓ Reasoning agent initialized")
        except Exception as e:
            print(f"⚠ Reasoning agent failed to initialize: {e}")
            self.reasoning_agent = None
        
        # General fallback agent (always available)
        try:
            self.general_agent = GeneralAgent(self.llm)
            self.agents_available.append("general")
            print("✓ General agent initialized")
        except Exception as e:
            print(f"⚠ General agent failed to initialize: {e}")
            self.general_agent = None
        
        # Agent capabilities mapping
        self.agent_capabilities = {
            "enrollment": {
                "keywords": ["enroll", "recruitment", "recruit", "participant", "patient", "eligibility", "criteria", 
                           "demographic", "population", "how many", "number of", "ratio", "percentage", "enrolled",
                           "success rate", "enrollment success", "recruitment success", "trial success rate",
                           "chances of enrollment", "probability of enrollment", "joining trial", "participate in trial",
                           "nct", "specific trial", "lookup", "look up", "find trial", "trial details", "study id"],
                "description": "Analyzes patient enrollment, recruitment patterns, eligibility criteria, demographic data, and enrollment success rates",
                "priority_keywords": ["enroll", "recruit", "success rate", "enrollment success", "how many", "ratio", "percentage", "nct", "specific trial", "lookup", "look up"]
            },
            "efficacy": {
                "keywords": ["efficacy", "effectiveness", "effective", "outcome", "result", "response", "treatment outcome", 
                           "benefit", "improvement", "cure", "therapeutic", "clinical outcome", "treatment success",
                           "drug effectiveness", "therapy effectiveness", "clinical response"],
                "description": "Evaluates treatment effectiveness, clinical outcomes, therapeutic benefits, and treatment success rates",
                "priority_keywords": ["efficacy", "effectiveness", "treatment outcome", "clinical outcome"]
            },
            "safety": {
                "keywords": ["safety", "adverse", "side effect", "risk", "toxicity", "harm", "contraindication", 
                           "warning", "dangerous", "safe", "hazard", "reaction", "complication"],
                "description": "Assesses safety profiles, adverse events, risks, and contraindications",
                "priority_keywords": ["safety", "adverse", "side effect", "risk"]
            },
            "general": {
                "keywords": [],
                "description": "Provides helpful guidance, clarifying questions, and safe fallback responses for any prompt",
                "priority_keywords": []
            }
        }
    
    def analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """
        Analyze user query to determine which agents should be activated
        using keyword matching and context analysis
        """
        query_lower = query.lower()
        
        # Score each agent based on keyword matches
        agent_scores = {}
        priority_matches = {}
        
        for agent_name, config in self.agent_capabilities.items():
            if agent_name not in self.agents_available:
                continue
                
            # Regular keyword scoring
            score = sum(1 for keyword in config["keywords"] if keyword in query_lower)
            
            # Priority keyword scoring (weighted more heavily)
            priority_score = sum(2 for keyword in config["priority_keywords"] if keyword in query_lower)
            
            total_score = score + priority_score
            
            if total_score > 0:
                agent_scores[agent_name] = total_score
                priority_matches[agent_name] = priority_score > 0
        
        # Special cases and context analysis
        
        # 1. Detect disease mentions and severity indicators
        disease_keywords = [
            'cancer', 'diabetes', 'alzheimer', 'parkinson', 'covid', 'heart disease',
            'stroke', 'asthma', 'depression', 'hiv', 'hepatitis', 'arthritis',
            'hypertension', 'copd', 'pneumonia', 'infection', 'tumor', 'disease'
        ]
        severity_indicators = ['stage', 'grade', 'severe', 'acute', 'chronic', 'advanced', 'metastatic']
        
        has_disease_mention = any(disease in query_lower for disease in disease_keywords)
        has_severity_mention = any(severity in query_lower for severity in severity_indicators)
        
        if has_disease_mention or has_severity_mention:
            print(f"Detected disease/severity context - ensuring efficacy and safety agents are activated")
            # Ensure efficacy and safety agents are included for disease-related queries
            if "efficacy" in self.agents_available:
                agent_scores["efficacy"] = agent_scores.get("efficacy", 0) + 5
            if "safety" in self.agents_available:
                agent_scores["safety"] = agent_scores.get("safety", 0) + 5
            # Also include enrollment for comprehensive analysis
            if "enrollment" in self.agents_available:
                # Boost enrollment equally so it isn't filtered out later
                agent_scores["enrollment"] = agent_scores.get("enrollment", 0) + 5
        
        # 2. Prioritize efficacy for treatment/therapy success queries
        treatment_success_indicators = [
            "treatment success", "therapy success", "response rate", "treatment response",
            "therapy response", "clinical response rate", "treatment effectiveness"
        ]
        if any(indicator in query_lower for indicator in treatment_success_indicators):
            print("Detected treatment/therapy success query - prioritizing efficacy agent")
            if "efficacy" in self.agents_available:
                agent_scores["efficacy"] = agent_scores.get("efficacy", 0) + 10
        
        # Context-aware disambiguation for "success" queries
        # If query mentions "success rate" with trial/enrollment context, it's about enrollment
        enrollment_success_indicators = [
            "success rate of trial", "trial success rate", "success rate for trial",
            "enrollment success", "recruitment success", "chances of enrollment",
            "probability of enrollment", "success rate of enrollment"
        ]
        if any(indicator in query_lower for indicator in enrollment_success_indicators):
            print("Detected enrollment success rate query - prioritizing enrollment agent")
            # Boost enrollment score significantly
            if "enrollment" in agent_scores:
                agent_scores["enrollment"] += 10
            else:
                agent_scores["enrollment"] = 10
            # Reduce efficacy score if it was triggered by generic "success"
            if "efficacy" in agent_scores and "treatment" not in query_lower and "drug" not in query_lower:
                agent_scores["efficacy"] = max(0, agent_scores["efficacy"] - 5)
        
        # If asking about a specific NCT trial without specific focus, activate all agents
        if re.search(r'NCT\d{8}', query, re.IGNORECASE) and len(agent_scores) <= 1:
            print("Detected NCT ID - activating comprehensive analysis")
            agent_scores = {agent: 1 for agent in self.agents_available}

        # If query suggests looking up a specific trial, strongly prioritize enrollment
        lookup_indicators = ["nct", "specific trial", "lookup", "look up", "find trial", "trial details", "study id"]
        if any(ind in query_lower for ind in lookup_indicators):
            if "enrollment" in self.agents_available:
                agent_scores["enrollment"] = agent_scores.get("enrollment", 0) + 10
        
        # 3. If there's general clinical context and only one or zero agents, activate all
        clinical_keywords = ["clinical trial", "study", "trial", "drug", "treatment", "therapy", "medicine", "medication"]
        has_clinical_context = any(keyword in query_lower for keyword in clinical_keywords)
        
        if has_clinical_context and len(agent_scores) <= 1:
            print("Detected general clinical context with few agents - activating all available agents")
            agent_scores = {agent: max(agent_scores.get(agent, 0), 3) for agent in self.agents_available}
        
        # If multiple agents have similar scores, include all high-scoring ones
        if len(agent_scores) > 1:
            max_score = max(agent_scores.values())
            high_scoring_agents = [agent for agent, score in agent_scores.items() if score >= max_score * 0.7]
            agent_scores = {agent: agent_scores[agent] for agent in high_scoring_agents}
            # Ensure enrollment is kept for disease/clinical contexts
            if (has_disease_mention or has_clinical_context) and "enrollment" in self.agents_available:
                agent_scores.setdefault("enrollment", 3)
        
        # 4. If disease condition exists but few agents activated, ensure comprehensive coverage
        if has_disease_mention and len(agent_scores) <= 1:
            print("Disease detected with minimal agents - activating comprehensive analysis")
            # Activate all available agents for disease-related queries
            for agent in self.agents_available:
                if agent not in agent_scores:
                    agent_scores[agent] = 2
        
        # Default to all agents if no clear intent but has medical context
        if not agent_scores:
            if has_disease_mention or has_clinical_context:
                print("Medical context detected - activating all available agents")
                agent_scores = {agent: 1 for agent in self.agents_available}
            elif self.general_agent:
                print("No clear intent detected - defaulting to general agent")
                agent_scores = {"general": 1}
        
        # Determine coordination strategy
        coordination_strategy = "parallel" if len(agent_scores) > 1 else "single"
        
        return {
            "agents_to_activate": list(agent_scores.keys()),
            "agent_scores": agent_scores,
            "priority_matches": priority_matches,
            "coordination_strategy": coordination_strategy,
            "query": query
        }
    
    def create_agent_specific_query(self, original_query: str, agent_name: str) -> str:
        """
        Create agent-specific queries based on the original query and agent capabilities
        """
        # Make queries more clinical and educational in nature
        if agent_name == "enrollment":
            return f"Provide clinical trial enrollment analysis for: {original_query}"
        elif agent_name == "efficacy":
            return f"Analyze therapeutic efficacy data for: {original_query}"
        elif agent_name == "safety":
            return f"Review clinical safety profile for: {original_query}"
        else:
            return original_query
    
    def extract_clinical_trial_info(self, query: str) -> Dict[str, str]:
        """
        Extract specific clinical trial information from the query
        """
        info = {}
        
        # Extract NCT ID
        nct_match = re.search(r'NCT\d{8}', query, re.IGNORECASE)
        if nct_match:
            info['nct_id'] = nct_match.group().upper()
            print(f"Extracted NCT ID: {info['nct_id']}")
        
        # Extract disease/condition
        disease_patterns = [
            (r'diabetes\w*', 'diabetes'),
            (r'cancer\w*', 'cancer'), 
            (r'alzheimer\w*', 'alzheimer'),
            (r'parkinson\w*', 'parkinson'),
            (r'covid\w*', 'covid'),
            (r'heart\s+disease', 'heart disease'),
            (r'stroke\w*', 'stroke'),
            (r'asthma\w*', 'asthma'),
            (r'depression\w*', 'depression'),
            (r'hiv\w*', 'hiv')
        ]
        
        for pattern, condition in disease_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                info['condition'] = condition
                print(f"Extracted condition: {condition}")
                break
        
        # Extract drug/treatment name
        drug_patterns = [
            r'(?:drug|medication|treatment|therapy)[\s:]+([\w\s-]+?)(?:\s+(?:for|in|against|trial)|$)',
            r'(?:^|\s)([\w-]+(?:mab|nib|cin|mycin|cillin))(?:\s|$)',  # Common drug suffixes
        ]
        
        for pattern in drug_patterns:
            drug_match = re.search(pattern, query, re.IGNORECASE)
            if drug_match:
                drug_name = drug_match.group(1).strip()
                if len(drug_name) > 2:  # Avoid very short matches
                    info['drug'] = drug_name
                    print(f"Extracted drug: {drug_name}")
                    break
        
        return info
    
    def execute_agent_analysis(self, agent_name: str, query: str, clinical_info: Dict[str, str]) -> Dict[str, Any]:
        """
        Execute analysis for a specific agent
        """
        # Get the agent
        agent = getattr(self, f"{agent_name}_agent", None)
        if not agent:
            return {
                "agent": agent_name,
                "status": "error",
                "error": f"{agent_name} agent not available",
                "query_used": query
            }
        
        agent_query = self.create_agent_specific_query(query, agent_name)
        
        try:
            # Handle different agent signature requirements
            if agent_name == "enrollment":
                # Enrollment agent supports search_type and context
                analysis_kwargs = {}
                
                if 'nct_id' in clinical_info:
                    analysis_kwargs['search_type'] = 'nct_id'
                    agent_query = clinical_info['nct_id']
                    print(f"Using NCT ID search for {agent_name}: {clinical_info['nct_id']}")
                elif 'condition' in clinical_info:
                    analysis_kwargs['search_type'] = 'disease'
                    analysis_kwargs['context'] = clinical_info['condition']
                    agent_query = clinical_info['condition']
                    print(f"Using disease search for {agent_name}: {clinical_info['condition']}")
                elif 'drug' in clinical_info:
                    analysis_kwargs['context'] = clinical_info['drug']
                    agent_query = clinical_info['drug']
                    print(f"Using drug context for {agent_name}: {clinical_info['drug']}")
                
                result = agent.analyze(agent_query, **analysis_kwargs)
                
            elif agent_name == "efficacy":
                # Efficacy agent only takes drug_name parameter
                if 'drug' in clinical_info:
                    agent_query = clinical_info['drug']
                    print(f"Using drug name for {agent_name}: {clinical_info['drug']}")
                elif 'condition' in clinical_info:
                    # For condition-based queries, create a general drug query
                    agent_query = f"treatments for {clinical_info['condition']}"
                    print(f"Using condition-based query for {agent_name}: {agent_query}")
                else:
                    # Use the original query
                    print(f"Using original query for {agent_name}: {agent_query}")
                
                result = agent.analyze(agent_query)
                
            elif agent_name == "safety":
                # Safety agent takes query and analysis_type
                analysis_kwargs = {}
                
                if 'drug' in clinical_info:
                    agent_query = clinical_info['drug']
                    analysis_kwargs['analysis_type'] = 'drug'
                    print(f"Using drug analysis for {agent_name}: {clinical_info['drug']}")
                elif 'condition' in clinical_info:
                    agent_query = clinical_info['condition']
                    analysis_kwargs['analysis_type'] = 'disease'
                    print(f"Using disease analysis for {agent_name}: {clinical_info['condition']}")
                else:
                    # Let the agent auto-detect
                    print(f"Using auto-detection for {agent_name}: {agent_query}")
                
                result = agent.analyze(agent_query, **analysis_kwargs)
            
            elif agent_name == "general":
                # General agent handles any prompt safely
                result = agent.analyze(query)
            else:
                # Fallback for other agents
                result = agent.analyze(agent_query)
            
            return {
                "agent": agent_name,
                "status": "success",
                "result": result,
                "query_used": agent_query
            }
        except Exception as e:
            print(f"Error in {agent_name} agent: {e}")
            return {
                "agent": agent_name,
                "status": "error",
                "error": str(e),
                "query_used": agent_query
            }
    
    def synthesize_results(self, agent_results: List[Dict[str, Any]], original_query: str) -> Dict[str, Any]:
        """
        Synthesize results from multiple agents using the reasoning agent
        """
        if not agent_results:
            return {"error": "No agent results to synthesize"}
        
        successful_results = [r for r in agent_results if r["status"] == "success"]
        
        if not successful_results:
            error_summary = []
            for result in agent_results:
                if result["status"] == "error":
                    error_summary.append(f"{result['agent']}: {result['error']}")
            
            return {
                "status": "error",
                "error": "All agent analyses failed",
                "error_details": error_summary,
                "individual_results": agent_results,
                "original_query": original_query
            }
        
        # If only one agent succeeded, return its result directly with minimal synthesis
        if len(successful_results) == 1:
            result = successful_results[0]
            return {
                "status": "success",
                "original_query": original_query,
                "activated_agents": [result["agent"]],
                "individual_results": agent_results,
                "synthesized_summary": f"Analysis from {result['agent']} agent:\n\n{result['result']}"
            }
        
        # Prepare synthesis input for multiple agents
        synthesis_input = {}
        for result in successful_results:
            synthesis_input[result["agent"]] = result["result"]
        
        # Use reasoning agent for synthesis if available
        try:
            if self.reasoning_agent:
                final_summary = self.reasoning_agent.synthesize(synthesis_input)
            else:
                # Fallback synthesis
                final_summary = "Multiple agent analysis:\n\n"
                for agent_name, result in synthesis_input.items():
                    final_summary += f"=== {agent_name.upper()} ANALYSIS ===\n"
                    final_summary += result + "\n\n"
            
            return {
                "status": "success",
                "original_query": original_query,
                "activated_agents": list(synthesis_input.keys()),
                "individual_results": agent_results,
                "synthesized_summary": final_summary
            }
        except Exception as e:
            print(f"Synthesis error: {e}")
            # Return individual results if synthesis fails
            return {
                "status": "partial_success",
                "error": f"Synthesis failed: {str(e)}",
                "original_query": original_query,
                "activated_agents": list(synthesis_input.keys()),
                "individual_results": agent_results
            }
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Main method to process user queries dynamically
        """
        print(f"\n📝 Processing query: {query}")
        
        # Analyze query intent
        intent_analysis = self.analyze_query_intent(query)
        print(f"🎯 Intent analysis - Agents to activate: {intent_analysis['agents_to_activate']}")
        
        # Extract clinical trial information
        clinical_info = self.extract_clinical_trial_info(query)
        
        # Execute agent analyses
        agent_results = []
        activated_agents = intent_analysis["agents_to_activate"]
        
        if not activated_agents:
            return {
                "status": "error",
                "error": "No suitable agents available for this query",
                "original_query": query
            }
        
        print(f"🚀 Activating {len(activated_agents)} agent(s): {', '.join(activated_agents)}")
        
        for agent_name in activated_agents:
            print(f"  ⚡ Executing {agent_name} agent...")
            result = self.execute_agent_analysis(agent_name, query, clinical_info)
            agent_results.append(result)
            
            status_emoji = "✅" if result['status'] == 'success' else "❌"
            print(f"  {status_emoji} {agent_name} agent completed - Status: {result['status']}")
        
        # Synthesize results
        print("🔄 Synthesizing results...")
        final_result = self.synthesize_results(agent_results, query)
        
        success_count = sum(1 for r in agent_results if r['status'] == 'success')
        print(f"✨ Analysis complete - {success_count}/{len(agent_results)} agents successful")
        
        return final_result

    def get_agent_capabilities(self) -> Dict[str, str]:
        """
        Return information about available agents and their capabilities
        """
        capabilities = {}
        for agent_name, config in self.agent_capabilities.items():
            if agent_name in self.agents_available:
                capabilities[agent_name] = config["description"]
        return capabilities
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of all agents
        """
        return {
            "available_agents": self.agents_available,
            "total_agents": len(self.agent_capabilities),
            "llm_model": getattr(self.llm, 'model_name', 'Unknown'),
            "capabilities": self.get_agent_capabilities()
        }