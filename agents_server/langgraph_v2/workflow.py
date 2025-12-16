"""
LangGraph Workflow for ClinicalAgent 2.0
Orchestrates 5 agents to predict clinical trial outcomes with human-in-the-loop
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

from .state import ClinicalTrialState, create_initial_state
from .numbered_input_parser import NumberedInputParser
from .tools import get_tools
from .config import Config
from llm_client import GrokClient


class ClinicalTrialWorkflow:
    """
    LangGraph workflow for predicting clinical trial outcomes
    
    Workflow structure:
        parse_input → enrollment → safety → [human if NOT_FOUND] → efficacy → reasoning → END
    """
    
    def __init__(self, llm=None, verbose: bool = True, checkpointer=None):
        """
        Initialize the workflow
        
        Args:
            llm: LLM client (defaults to GrokClient)
            verbose: Enable verbose logging
            checkpointer: LangGraph checkpointer for state persistence (enables HITL)
        """
        self.llm = llm or GrokClient()
        self.verbose = verbose
        self.checkpointer = checkpointer
        self.tools = get_tools(verbose=verbose)
        self.graph = self._build_graph()
        
        if verbose:
            print("\n" + "="*60)
            print("🤖 ClinicalAgent 2.0 - LangGraph Workflow Initialized")
            if checkpointer:
                print("   ✓ Checkpointer enabled (HITL supported)")
            print("="*60)
            Config.print_status()
    
    def _build_graph(self) -> StateGraph:
        """Construct the LangGraph workflow"""
        
        # Create graph with our state structure
        workflow = StateGraph(ClinicalTrialState)
        
        # Add nodes
        workflow.add_node("parse_input", self.parse_input_node)
        workflow.add_node("enrollment", self.enrollment_node)
        workflow.add_node("safety", self.safety_node)
        workflow.add_node("efficacy", self.efficacy_node)
        workflow.add_node("human", self.human_node)
        workflow.add_node("reasoning", self.reasoning_node)
        
        # Set entry point
        workflow.set_entry_point("parse_input")
        
        # Add edges
        workflow.add_edge("parse_input", "enrollment")
        workflow.add_edge("enrollment", "safety")
        
        # Conditional edge: safety → human if NOT_FOUND, else → efficacy
        workflow.add_conditional_edges(
            "safety",
            self.should_request_human_input,
            {
                "human": "human",
                "efficacy": "efficacy"
            }
        )
        
        # Human node loops back to safety
        workflow.add_edge("human", "safety")
        
        # Efficacy → reasoning → END
        workflow.add_edge("efficacy", "reasoning")
        workflow.add_edge("reasoning", END)
        
        # Compile with checkpointer if provided
        if self.checkpointer:
            return workflow.compile(checkpointer=self.checkpointer)
        else:
            return workflow.compile()
    
    # ======================== NODE IMPLEMENTATIONS ========================
    
    def parse_input_node(self, state: ClinicalTrialState) -> ClinicalTrialState:
        """
        Node 1: Parse numbered input format
        Extracts: drug, disease, inclusion_criteria, exclusion_criteria
        """
        if self.verbose:
            print("\n" + "="*60)
            print("📝 STEP 1: Parsing Input")
            print("="*60)
        
        raw_input = state["raw_input"]
        parsed = NumberedInputParser.parse(raw_input)
        
        # Validate parsing
        is_valid, issues = NumberedInputParser.validate_parse(parsed)
        
        if not is_valid:
            state["errors"].append(f"Parsing validation failed: {', '.join(issues)}")
            if self.verbose:
                print(f"❌ Parsing errors: {', '.join(issues)}")
        
        if parsed["parsing_errors"]:
            state["warnings"].extend(parsed["parsing_errors"])
            if self.verbose:
                print(f"⚠️  Parsing warnings: {', '.join(parsed['parsing_errors'])}")
        
        # Update state
        state["drug_name"] = parsed["drug"]
        state["drug_name_cleaned"] = parsed["drug_cleaned"]
        state["disease_name"] = parsed["disease"]
        state["inclusion_criteria"] = parsed["inclusion_criteria"]
        state["exclusion_criteria"] = parsed["exclusion_criteria"]
        state["current_step"] = "parse_input"
        
        if self.verbose:
            print(f"\n✅ Parsing Complete:")
            print(f"   Drug (raw): {parsed['drug']}")
            print(f"   Drug (cleaned): {parsed['drug_cleaned']}")
            print(f"   Disease: {parsed['disease']}")
            print(f"   Inclusion criteria: {parsed['inclusion_criteria'][:50] if parsed['inclusion_criteria'] else None}...")
            print(f"   Exclusion criteria: {parsed['exclusion_criteria'][:50] if parsed['exclusion_criteria'] else None}...")
        
        return state
    
    def enrollment_node(self, state: ClinicalTrialState) -> ClinicalTrialState:
        """
        Node 2: Enrollment Agent
        Query ChromaDB for similar trials based on eligibility criteria
        """
        if self.verbose:
            print("\n" + "="*60)
            print("👥 STEP 2: Enrollment Analysis (Historian)")
            print("="*60)
        
        # Combine criteria for search
        criteria_parts = []
        if state.get("disease_name"):
            criteria_parts.append(f"Disease: {state['disease_name']}")
        if state.get("inclusion_criteria"):
            criteria_parts.append(f"Inclusion: {state['inclusion_criteria']}")
        if state.get("exclusion_criteria"):
            criteria_parts.append(f"Exclusion: {state['exclusion_criteria']}")
        
        criteria_text = ". ".join(criteria_parts)
        
        # Call ChromaDB search tool
        result = self.tools.search_chroma(criteria_text, top_k=5)
        
        # Update state
        state["enrollment_data"] = result
        state["current_step"] = "enrollment"
        
        if result["status"] == "SUCCESS":
            # Generate report using LLM
            prompt = f"""Based on the following similar clinical trials from our database, provide an enrollment feasibility analysis:

{result['summary']}

Similar Trials:
{self._format_trials_for_llm(result['trials'])}

Provide a brief analysis (3-4 sentences) about enrollment feasibility for a trial on {state.get('disease_name', 'this condition')} with similar eligibility criteria.
Focus on historical success/failure patterns."""

            try:
                report = self.llm.generate(prompt, max_tokens=300, temperature=0.3)
                state["enrollment_report"] = report
                
                if self.verbose:
                    print(f"\n✅ Enrollment Analysis: {result['summary']}")
                    print(f"\n{report}")
            except Exception as e:
                error_msg = f"Failed to generate enrollment report: {str(e)}"
                state["errors"].append(error_msg)
                state["enrollment_report"] = result["summary"]
                if self.verbose:
                    print(f"⚠️  {error_msg}")
        else:
            state["errors"].append(f"Enrollment search failed: {result.get('error', 'Unknown error')}")
            state["enrollment_report"] = result["summary"]
            
            if self.verbose:
                print(f"⚠️  Enrollment search failed: {result.get('error')}")
        
        return state
    
    def safety_node(self, state: ClinicalTrialState) -> ClinicalTrialState:
        """
        Node 3: Safety Agent
        Query OpenFDA for drug safety data
        """
        if self.verbose:
            print("\n" + "="*60)
            print("🔬 STEP 3: Safety Analysis (Regulator)")
            print("="*60)
        
        # Use cleaned drug name, or fall back to human input if retrying
        drug_to_query = state.get("human_input_response") or state.get("drug_name_cleaned") or state.get("drug_name")
        
        if not drug_to_query:
            state["errors"].append("No drug name provided")
            state["safety_status"] = "ERROR"
            return state
        
        # Call OpenFDA tool
        result = self.tools.check_fda(drug_to_query)
        
        # Update state
        state["safety_data"] = result
        state["safety_status"] = result["status"]
        state["current_step"] = "safety"
        
        if result["status"] == "SUCCESS":
            # Generate safety report using LLM
            prompt = f"""Based on the following FDA safety data for {drug_to_query}, provide a brief safety risk assessment:

FDA Data Summary:
- Generic Names: {result['data'].get('generic_name', [])}
- Brand Names: {result['data'].get('brand_name', [])}
- Has Boxed Warning: {bool(result['data'].get('boxed_warning'))}
- Has Contraindications: {bool(result['data'].get('contraindications'))}
- Has Drug Interactions: {bool(result['data'].get('drug_interactions'))}

Provide a brief safety risk assessment (3-4 sentences). Focus on critical safety concerns that might affect trial approval."""

            try:
                report = self.llm.generate(prompt, max_tokens=300, temperature=0.3)
                state["safety_report"] = report
                
                if self.verbose:
                    print(f"\n✅ Safety Data Found for: {drug_to_query}")
                    if result['data'].get('boxed_warning'):
                        print("   ⚠️  BLACK BOX WARNING present")
                    print(f"\n{report}")
            except Exception as e:
                error_msg = f"Failed to generate safety report: {str(e)}"
                state["errors"].append(error_msg)
                state["safety_report"] = f"FDA data found for {drug_to_query} but report generation failed"
                
                if self.verbose:
                    print(f"⚠️  {error_msg}")
            
            # Reset human input flag if it was previously set
            state["human_input_needed"] = False
            
        elif result["status"] == "NOT_FOUND":
            # Trigger human-in-the-loop if we haven't exceeded retry limit
            if state["human_retry_count"] < Config.MAX_HUMAN_RETRIES:
                state["human_input_needed"] = True
                state["human_input_query"] = f"Drug '{drug_to_query}' not found in OpenFDA database. Please provide a synonym or generic name:"
                state["safety_report"] = None
                
                if self.verbose:
                    print(f"\n⚠️  Drug NOT FOUND: {drug_to_query}")
                    print(f"   Triggering human-in-the-loop (attempt {state['human_retry_count'] + 1}/{Config.MAX_HUMAN_RETRIES})")
            else:
                # Max retries exceeded
                state["human_input_needed"] = False
                state["safety_report"] = f"Drug '{drug_to_query}' not found in FDA database after {Config.MAX_HUMAN_RETRIES} attempts. Proceeding with limited safety analysis."
                state["warnings"].append(f"Could not find FDA data for {drug_to_query}")
                
                if self.verbose:
                    print(f"\n⚠️  Max retries exceeded for drug: {drug_to_query}")
                    print("   Proceeding without FDA safety data")
        else:
            # ERROR status
            state["errors"].append(f"Safety check failed: {result.get('error')}")
            state["safety_report"] = f"Safety check error: {result.get('error', 'Unknown error')}"
            state["human_input_needed"] = False
            
            if self.verbose:
                print(f"❌ Safety check error: {result.get('error')}")
        
        return state
    
    def efficacy_node(self, state: ClinicalTrialState) -> ClinicalTrialState:
        """
        Node 4: Efficacy Agent
        Query Neo4j HetioNet for drug-disease pathways
        """
        if self.verbose:
            print("\n" + "="*60)
            print("🧬 STEP 4: Efficacy Analysis (Scientist)")
            print("="*60)
        
        drug_name = state.get("drug_name_cleaned") or state.get("drug_name")
        disease_name = state.get("disease_name")
        
        if not drug_name or not disease_name:
            state["errors"].append("Missing drug or disease name for efficacy analysis")
            state["efficacy_report"] = "Cannot perform efficacy analysis: missing drug or disease name"
            return state
        
        # Call Neo4j HetioNet tool
        result = self.tools.query_graph(drug_name, disease_name)
        
        # Update state
        state["efficacy_data"] = result
        state["current_step"] = "efficacy"
        
        if result["status"] == "SUCCESS":
            # Check if we have LLM analysis (when Neo4j had no data)
            if result.get("llm_analysis"):
                state["efficacy_report"] = result["llm_analysis"]
                
                if self.verbose:
                    print(f"\n✅ Efficacy Analysis from Medical Knowledge")
                    print(f"\n{result['llm_analysis'][:500]}...")
            else:
                # Generate efficacy report from pathway data using LLM
                prompt = f"""Based on the following biological pathway evidence from HetioNet, provide an efficacy assessment:

{result['summary']}

Pathways Found: {len(result['pathways'])}
{self._format_pathways_for_llm(result['pathways'])}

Provide a brief efficacy assessment (3-4 sentences) for {drug_name} in treating {disease_name}. Focus on biological plausibility based on pathway evidence."""

                try:
                    report = self.llm.generate(prompt, max_tokens=300, temperature=0.3)
                    state["efficacy_report"] = report
                    
                    if self.verbose:
                        print(f"\n✅ Efficacy Evidence: {result['summary']}")
                        print(f"\n{report}")
                except Exception as e:
                    error_msg = f"Failed to generate efficacy report: {str(e)}"
                    state["errors"].append(error_msg)
                    state["efficacy_report"] = result["summary"]
                    
                    if self.verbose:
                        print(f"⚠️  {error_msg}")
        
        elif result["status"] == "NOT_FOUND":
            state["efficacy_report"] = result["summary"]
            state["warnings"].append(f"No pathway evidence found for {drug_name} - {disease_name}")
            
            if self.verbose:
                print(f"\n⚠️  No pathway evidence found")
        else:
            # ERROR
            state["errors"].append(f"Efficacy query failed: {result.get('error')}")
            state["efficacy_report"] = f"Efficacy query error: {result.get('error', 'Unknown error')}"
            
            if self.verbose:
                print(f"❌ Efficacy query error: {result.get('error')}")
        
        return state
    
    def human_node(self, state: ClinicalTrialState) -> ClinicalTrialState:
        """
        Node 5: Human-in-the-Loop
        
        This node pauses the workflow and waits for user input via the API.
        The workflow will interrupt here, and the API will return the query to the frontend.
        When the user provides input via /chat/resume, the workflow continues from here.
        """
        if self.verbose:
            print("\n" + "="*60)
            print("👤 HUMAN-IN-THE-LOOP - Waiting for User Input")
            print("="*60)
        
        query = state.get("human_input_query", "")
        
        # Check if we already have user input (from resume)
        if state.get("human_input_response"):
            if self.verbose:
                print(f"\n✅ Received user input: {state['human_input_response']}")
            
            # Clear the input flag so we proceed to safety check with new drug name
            state["human_input_needed"] = False
            state["current_step"] = "human_input_received"
            return state
        
        # No user input yet - this is the first time hitting this node
        # Use LangGraph's interrupt to pause execution
        from langgraph.errors import NodeInterrupt
        
        if self.verbose:
            print(f"\n⏸️  PAUSING workflow - waiting for user input")
            print(f"   Question: {query}")
        
        state["current_step"] = "waiting_for_human_input"
        state["human_retry_count"] += 1
        
        # Raise interrupt - this will pause the workflow and return control to the API
        # The state will be checkpointed at this point
        raise NodeInterrupt(
            f"Human input requested: {query}"
        )
    
    def reasoning_node(self, state: ClinicalTrialState) -> ClinicalTrialState:
        """
        Node 6: Reasoning Agent (The Judge)
        Synthesize all reports into final Pass/Fail prediction with Chain-of-Thought
        """
        if self.verbose:
            print("\n" + "="*60)
            print("⚖️  STEP 5: Final Reasoning & Prediction (Judge)")
            print("="*60)
        
        # Gather all reports
        enrollment_report = state.get("enrollment_report", "No enrollment data")
        safety_report = state.get("safety_report", "No safety data")
        efficacy_report = state.get("efficacy_report", "No efficacy data")
        
        # Chain-of-Thought prompt with better output formatting
        cot_prompt = f"""You are a clinical trial expert providing a final **PASS or FAIL** prediction for a clinical trial.

**TRIAL DETAILS:**
- **Drug**: {state.get('drug_name')}
- **Disease**: {state.get('disease_name')}
- **Inclusion Criteria**: {state.get('inclusion_criteria', 'Not specified')}
- **Exclusion Criteria**: {state.get('exclusion_criteria', 'Not specified')}

---

## AGENT REPORTS SUMMARY

### 1️⃣ Enrollment Feasibility Review
{enrollment_report}

### 2️⃣ Safety Risk Assessment  
{safety_report}

### 3️⃣ Efficacy Plausibility
{efficacy_report}

---

## YOUR TASK

Synthesize the three agent reports above using Chain-of-Thought reasoning to decide if this trial should **PASS** or **FAIL**.

**PASS** = Trial has good prospects (reasonable enrollment feasibility, manageable safety risks, biological/clinical evidence of efficacy)
**FAIL** = Critical issues exist (severe safety concerns, poor historical enrollment, no plausible mechanism/efficacy evidence)

Provide your analysis in this **EXACT** structure:

---

## 🎯 Clinical Trial Prediction

**Prediction**: [PASS or FAIL]  
**Confidence**: [0-100]%

---

## 📊 Step-by-Step Analysis

### Step 1: Enrollment Feasibility Review
[Analyze the enrollment report. Is there historical precedent for successful enrollment with similar criteria? Any red flags in similar trials?]

### Step 2: Safety Risk Assessment
[Analyze safety data. Are there critical safety concerns (boxed warnings, severe contraindications)? Will these impact trial approval or participant safety?]

### Step 3: Efficacy Plausibility
[Analyze efficacy evidence. Is there a biological mechanism or clinical evidence supporting this treatment for this disease? For well-known drugs, is this an established indication?]

### Step 4: Final Decision
[Synthesize all three analyses. Weigh the evidence. Explain your final verdict.]

---

## 💭 Reasoning

[Provide 2-3 clear sentences explaining why you chose PASS or FAIL, highlighting the most critical factors that influenced your decision.]

---

**IMPORTANT**: 
- Be data-driven and evidence-based in your reasoning
- For well-established drug-disease combinations (e.g., metformin for Type 2 Diabetes), recognize the strong clinical evidence
- Consider the totality of evidence, not just individual agent reports
- A trial can PASS even with some safety risks if they are known, manageable, and outweighed by efficacy
"""

        try:
            # Generate final prediction
            reasoning_output = self.llm.generate(cot_prompt, max_tokens=800, temperature=0.4)
            
            # Extract prediction and confidence from reformatted output
            prediction = "UNKNOWN"
            confidence = 0.5
            
            # Look for prediction in new format
            if "**Prediction**: PASS" in reasoning_output or "**Prediction**: [PASS]" in reasoning_output or "Prediction: PASS" in reasoning_output:
                prediction = "PASS"
            elif "**Prediction**: FAIL" in reasoning_output or "**Prediction**: [FAIL]" in reasoning_output or "Prediction: FAIL" in reasoning_output:
                prediction = "FAIL"
            # Fallback to old format
            elif "**PREDICTION: PASS**" in reasoning_output or "PREDICTION: PASS" in reasoning_output:
                prediction = "PASS"
            elif "**PREDICTION: FAIL**" in reasoning_output or "PREDICTION: FAIL" in reasoning_output:
                prediction = "FAIL"
            
            # Try to extract confidence score (support both formats)
            import re
            conf_match = re.search(r'\*\*Confidence\*\*:\s*(\d+)%?', reasoning_output)
            if not conf_match:
                conf_match = re.search(r'\*\*CONFIDENCE:\s*(\d+)%?\*\*', reasoning_output)
            if conf_match:
                confidence = float(conf_match.group(1)) / 100.0
            
            # Update state
            state["reasoning_trace"] = reasoning_output
            state["final_prediction"] = prediction
            state["confidence_score"] = confidence
            state["current_step"] = "complete"
            
            if self.verbose:
                print(f"\n{reasoning_output}")
                print("\n" + "="*60)
                print(f"🎯 FINAL PREDICTION: {prediction}")
                print(f"📊 CONFIDENCE SCORE: {int(confidence * 100)}%")
                print("="*60)
            
        except Exception as e:
            error_msg = f"Reasoning failed: {str(e)}"
            state["errors"].append(error_msg)
            state["reasoning_trace"] = error_msg
            state["final_prediction"] = "ERROR"
            state["confidence_score"] = 0.0
            
            if self.verbose:
                print(f"❌ {error_msg}")
        
        return state
    
    # ======================== CONDITIONAL EDGE LOGIC ========================
    
    def should_request_human_input(self, state: ClinicalTrialState) -> Literal["human", "efficacy"]:
        """
        Conditional edge: Route to human node if input is needed
        
        Checks if the safety check failed due to drug not found and HITL is needed.
        The workflow will pause (interrupt) at the human node, waiting for user input.
        """
        # Check if human input is needed (drug not found, retry count not exceeded)
        if state.get("human_input_needed", False):
            if self.verbose:
                print(f"\n🔀 Routing to HUMAN node (retry {state.get('human_retry_count', 0) + 1})")
            return "human"
        else:
            if self.verbose:
                print(f"\n🔀 Routing to EFFICACY node")
            return "efficacy"
    
    # ======================== HELPER METHODS ========================
    
    def _format_trials_for_llm(self, trials: list) -> str:
        """Format trial list for LLM prompt"""
        if not trials:
            return "No trials found"
        
        formatted = []
        for i, trial in enumerate(trials[:5], 1):
            formatted.append(
                f"{i}. NCT{trial.get('nct_id', 'N/A')} - {trial.get('disease', 'N/A')} "
                f"(Status: {trial.get('status', 'N/A')}, Phase: {trial.get('phase', 'N/A')})"
            )
        return "\n".join(formatted)
    
    def _format_pathways_for_llm(self, pathways: list) -> str:
        """Format pathway list for LLM prompt"""
        if not pathways:
            return "No pathways found"
        
        formatted = []
        for i, pathway in enumerate(pathways[:5], 1):
            formatted.append(
                f"{i}. {pathway.get('metric', 'N/A')}: {pathway.get('result', 'N/A')} "
                f"(Value: {pathway.get('value', 'N/A')})"
            )
        return "\n".join(formatted)
    
    # ======================== PUBLIC API ========================
    
    def predict(self, raw_input: str, config: dict = None) -> dict:
        """
        Main entry point: predict clinical trial outcome
        
        Args:
            raw_input: Numbered format input string
            config: Optional config dict with thread_id for resuming interrupted workflows
            
        Returns:
            {
                "prediction": "PASS" or "FAIL" or "ERROR",
                "confidence": float (0.0 to 1.0),
                "reasoning": str,
                "reports": {
                    "enrollment": str,
                    "safety": str,
                    "efficacy": str
                },
                "warnings": list,
                "errors": list,
                "interrupted": bool (True if HITL needed),
                "thread_id": str (for resuming)
            }
        """
        # Create initial state
        initial_state = create_initial_state(raw_input)
        
        # Run the workflow with config (for thread_id support)
        try:
            if config:
                final_state = self.graph.invoke(initial_state, config)
            else:
                final_state = self.graph.invoke(initial_state)
            
            # Format output
            return {
                "prediction": final_state.get("final_prediction", "ERROR"),
                "confidence": final_state.get("confidence_score", 0.0),
                "reasoning": final_state.get("reasoning_trace", "No reasoning available"),
                "reports": {
                    "enrollment": final_state.get("enrollment_report"),
                    "safety": final_state.get("safety_report"),
                    "efficacy": final_state.get("efficacy_report")
                },
                "drug_parsed": {
                    "original": final_state.get("drug_name"),
                    "cleaned": final_state.get("drug_name_cleaned")
                },
                "disease_parsed": final_state.get("disease_name"),
                "warnings": final_state.get("warnings", []),
                "errors": final_state.get("errors", []),
                "interrupted": False
            }
        except Exception as e:
            # Check if this is a NodeInterrupt (HITL triggered)
            from langgraph.errors import NodeInterrupt
            if isinstance(e, NodeInterrupt):
                # Workflow is paused, waiting for human input
                return {
                    "interrupted": True,
                    "interrupt_message": str(e),
                    "status": "waiting_for_input"
                }
            else:
                # Actual error
                raise


# Convenience function
def predict_trial_outcome(raw_input: str, verbose: bool = True) -> dict:
    """
    Convenience function to run a trial prediction
    
    Args:
        raw_input: Numbered format input
        verbose: Enable logging
        
    Returns:
        Prediction results dictionary
    """
    workflow = ClinicalTrialWorkflow(verbose=verbose)
    return workflow.predict(raw_input)
