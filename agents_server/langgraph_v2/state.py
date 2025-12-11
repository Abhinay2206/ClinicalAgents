"""
State management for ClinicalAgent 2.0 LangGraph workflow
Defines the state structure passed between nodes
"""

from typing import TypedDict, Optional, List, Annotated
from langgraph.graph import add_messages


class ClinicalTrialState(TypedDict):
    """
    State structure for the clinical trial prediction workflow
    
    This state is passed between all nodes in the LangGraph workflow.
    Each agent node updates relevant fields as it processes.
    """
    
    # Input data (parsed from numbered format)
    messages: Annotated[List[dict], add_messages]  # Chat messages
    raw_input: str  # Original user input
    drug_name: Optional[str]  # Extracted drug name
    drug_name_cleaned: Optional[str]  # Cleaned drug name (remove "capsule", "injection", etc.)
    disease_name: Optional[str]  # Extracted disease/condition
    inclusion_criteria: Optional[str]  # Inclusion criteria text
    exclusion_criteria: Optional[str]  # Exclusion criteria text
    
    # Agent execution results
    enrollment_report: Optional[str]  # From Enrollment Agent
    enrollment_data: Optional[dict]  # Raw enrollment data
    
    safety_report: Optional[str]  # From Safety Agent
    safety_data: Optional[dict]  # Raw FDA safety data
    safety_status: Optional[str]  # "SUCCESS" or "NOT_FOUND"
    
    efficacy_report: Optional[str]  # From Efficacy Agent
    efficacy_data: Optional[dict]  # Raw Neo4j pathway data
    
    # Human-in-the-loop state
    human_input_needed: bool  # Flag to trigger human node
    human_input_query: Optional[str]  # Question to ask the user
    human_input_response: Optional[str]  # User's response
    human_retry_count: int  # Number of human input attempts
    
    # Final output
    final_prediction: Optional[str]  # "PASS" or "FAIL"
    confidence_score: Optional[float]  # 0.0 to 1.0
    reasoning_trace: Optional[str]  # Chain-of-thought explanation
    
    # Workflow metadata
    current_step: Optional[str]  # Current node being executed
    errors: List[str]  # Accumulated errors
    warnings: List[str]  # Accumulated warnings


def create_initial_state(raw_input: str) -> ClinicalTrialState:
    """
    Create initial state from user input
    
    Args:
        raw_input: The raw user input string (numbered format)
        
    Returns:
        Initialized ClinicalTrialState
    """
    return ClinicalTrialState(
        messages=[],
        raw_input=raw_input,
        drug_name=None,
        drug_name_cleaned=None,
        disease_name=None,
        inclusion_criteria=None,
        exclusion_criteria=None,
        enrollment_report=None,
        enrollment_data=None,
        safety_report=None,
        safety_data=None,
        safety_status=None,
        efficacy_report=None,
        efficacy_data=None,
        human_input_needed=False,
        human_input_query=None,
        human_input_response=None,
        human_retry_count=0,
        final_prediction=None,
        confidence_score=None,
        reasoning_trace=None,
        current_step="parse_input",
        errors=[],
        warnings=[]
    )


def update_state(state: ClinicalTrialState, **updates) -> ClinicalTrialState:
    """
    Helper to update state with new values
    
    Args:
        state: Current state
        **updates: Fields to update
        
    Returns:
        Updated state
    """
    new_state = state.copy()
    new_state.update(updates)
    return new_state
