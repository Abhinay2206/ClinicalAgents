"""
ClinicalAgent 2.0 - LangGraph-based Multi-Agent System
for Clinical Trial Outcome Prediction

This module provides a LangGraph workflow orchestrator that coordinates
5 specialized agents to predict clinical trial success.
"""

__version__ = "2.0.0"

from .workflow import ClinicalTrialWorkflow
from .state import ClinicalTrialState
from .config import Config

__all__ = ["ClinicalTrialWorkflow", "ClinicalTrialState", "Config"]
