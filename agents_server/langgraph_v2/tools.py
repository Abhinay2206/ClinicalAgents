"""
Tool wrappers for existing ClinicalAgent agents
Provides interfaces to ChromaDB, OpenFDA, and Neo4j through existing agent implementations
"""

import sys
import os
import asyncio
import functools
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

# Add parent directory to path to import existing agents
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.enrollment_agent import EnrollmentAgent
from agents.safety_agent import SafetyAgent
from agents.efficacy_agent import EfficacyAgent
from llm_client import GrokClient


class ClinicalAgentTools:
    """
    Wrapper class for interfacing with existing clinical agents
    Provides the three required tool functions: search_chroma, check_fda, query_graph
    """
    
    def __init__(self, llm=None, verbose: bool = False):
        """
        Initialize tool wrappers with shared LLM client
        
        Args:
            llm: LLM client instance (defaults to GrokClient)
            verbose: Enable verbose logging
        """
        self.llm = llm or GrokClient()
        self.verbose = verbose
        self.executor = ThreadPoolExecutor(max_workers=4)  # For timeout operations
        
        # Initialize agents (with error handling)
        try:
            self.enrollment_agent = EnrollmentAgent(self.llm, verbose=verbose)
            if verbose:
                print("✅ Enrollment Agent initialized")
        except Exception as e:
            print(f"⚠️  Enrollment Agent initialization failed: {e}")
            self.enrollment_agent = None
        
        try:
            self.safety_agent = SafetyAgent(self.llm)
            if verbose:
                print("✅ Safety Agent initialized")
        except Exception as e:
            print(f"⚠️  Safety Agent initialization failed: {e}")
            self.safety_agent = None
        
        try:
            self.efficacy_agent = EfficacyAgent(self.llm)
            if verbose:
                print("✅ Efficacy Agent initialized")
        except Exception as e:
            print(f"⚠️  Efficacy Agent initialization failed: {e}")
            self.efficacy_agent = None
    
    def _run_with_timeout(self, func, timeout_seconds, *args, **kwargs):
        """Run a function with timeout protection"""
        future = self.executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout_seconds)
        except FuturesTimeoutError:
            future.cancel()
            raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds")
    
    def search_chroma(self, criteria_text: str, top_k: int = 5) -> Dict:
        """
        Search ChromaDB for similar clinical trials based on eligibility criteria
        
        Args:
            criteria_text: Combined inclusion + exclusion criteria
            top_k: Number of similar trials to retrieve
            
        Returns:
            {
                "status": "SUCCESS" or "ERROR",
                "trials": [...],  # List of similar trials
                "summary": str,    # Human-readable summary
                "error": str or None
            }
        """
        if not self.enrollment_agent:
            return {
                "status": "ERROR",
                "trials": [],
                "summary": "Enrollment Agent not available",
                "error": "Agent initialization failed"
            }
        
        try:
            if self.verbose:
                print(f"\n🔍 Searching ChromaDB for similar trials (10s timeout)...")
                print(f"   Criteria: {criteria_text[:100]}...")
            
            # Use semantic search from enrollment agent with 10-second timeout
            results = self._run_with_timeout(
                self.enrollment_agent.semantic_search, 
                10, 
                criteria_text, 
                top_k=top_k
            )
            
            if not results:
                return {
                    "status": "SUCCESS",
                    "trials": [],
                    "summary": "No similar trials found in database",
                    "error": None
                }
            
            # Format results
            trials = []
            for result in results:
                metadata = result.get('metadata', {})
                trials.append({
                    'nct_id': metadata.get('nct_id', 'N/A'),
                    'disease': metadata.get('disease', 'N/A'),
                    'status': metadata.get('status', 'N/A'),
                    'phase': metadata.get('phase', 'N/A'),
                    'similarity_score': result.get('similarity_score', 0),
                    'eligibility_criteria': metadata.get('eligibility_criteria', 'N/A'),
                    'why_stopped': metadata.get('why_stopped', 'N/A')
                })
            
            # Generate summary
            completed_count = sum(1 for t in trials if 'completed' in t['status'].lower())
            terminated_count = sum(1 for t in trials if any(kw in t['status'].lower() for kw in ['terminated', 'withdrawn', 'suspended']))
            
            summary = f"Found {len(trials)} similar trials. {completed_count} completed successfully, {terminated_count} terminated/failed."
            
            if self.verbose:
                print(f"✅ Found {len(trials)} similar trials")
            
            return {
                "status": "SUCCESS",
                "trials": trials,
                "summary": summary,
                "error": None
            }
            
        except TimeoutError as e:
            error_msg = f"ChromaDB search timeout: {str(e)}"
            if self.verbose:
                print(f"⏱️ {error_msg}")
            return {
                "status": "ERROR",
                "trials": [],
                "summary": "ChromaDB search timed out after 10 seconds",
                "error": str(e)
            }
        except Exception as e:
            error_msg = f"ChromaDB search error: {str(e)}"
            if self.verbose:
                print(f"❌ {error_msg}")
            
            return {
                "status": "ERROR",
                "trials": [],
                "summary": error_msg,
                "error": str(e)
            }
    
    def check_fda(self, drug_name: str) -> Dict:
        """
        Query OpenFDA API for drug safety information
        
        Args:
            drug_name: Name of the drug to search
            
        Returns:
            {
                "status": "SUCCESS" or "NOT_FOUND" or "ERROR",
                "drug_name": str,
                "data": {...},  # FDA label data if found
                "error": str or None
            }
        """
        if not self.safety_agent:
            return {
                "status": "ERROR",
                "drug_name": drug_name,
                "data": None,
                "error": "Safety Agent not available"
            }
        
        try:
            if self.verbose:
                print(f"\n💊 Querying OpenFDA for drug: {drug_name} (10s timeout)...")
            
            # Use safety agent's FDA fetcher with 10-second timeout
            fda_data = self._run_with_timeout(
                self.safety_agent.fetch_safety_data,
                10,
                drug_name,
                limit=1
            )
            
            if not fda_data or len(fda_data) == 0:
                if self.verbose:
                    print(f"⚠️  Drug '{drug_name}' NOT FOUND in OpenFDA")
                
                return {
                    "status": "NOT_FOUND",
                    "drug_name": drug_name,
                    "data": None,
                    "error": None
                }
            
            # Extract key safety information
            label = fda_data[0]
            safety_info = {
                'generic_name': label.get('openfda', {}).get('generic_name', []),
                'brand_name': label.get('openfda', {}).get('brand_name', []),
                'warnings': label.get('warnings', []),
                'boxed_warning': label.get('boxed_warning', []),
                'contraindications': label.get('contraindications', []),
                'adverse_reactions': label.get('adverse_reactions', []),
                'drug_interactions': label.get('drug_interactions', [])
            }
            
            if self.verbose:
                print(f"✅ Found FDA data for {drug_name}")
                if safety_info['boxed_warning']:
                    print(f"   ⚠️  Has BLACK BOX WARNING")
            
            return {
                "status": "SUCCESS",
                "drug_name": drug_name,
                "data": safety_info,
                "error": None
            }
            
        except TimeoutError as e:
            error_msg = f"OpenFDA query timeout: {str(e)}"
            if self.verbose:
                print(f"⏱️ {error_msg}")
            return {
                "status": "ERROR",
                "drug_name": drug_name,
                "data": None,
                "error": "OpenFDA query timed out after 10 seconds"
            }
        except Exception as e:
            error_msg = f"OpenFDA query error: {str(e)}"
            if self.verbose:
                print(f"❌ {error_msg}")
            
            return {
                "status": "ERROR",
                "drug_name": drug_name,
                "data": None,
                "error": str(e)
            }
    
    def query_graph(self, drug_name: str, disease_name: str) -> Dict:
        """
        Query Neo4j HetioNet for drug-disease pathway evidence
        
        Args:
            drug_name: Name of the drug/compound
            disease_name: Name of the disease
            
        Returns:
            {
                "status": "SUCCESS" or "NOT_FOUND" or "ERROR",
                "drug_name": str,
                "disease_name": str,
                "pathways": [...],  # List of biological pathways
                "summary": str,
                "error": str or None
            }
        """
        if not self.efficacy_agent:
            return {
                "status": "ERROR",
                "drug_name": drug_name,
                "disease_name": disease_name,
                "pathways": [],
                "summary": "Efficacy Agent not available",
                "error": "Agent initialization failed"
            }
        
        try:
            if self.verbose:
                print(f"\n🔬 Querying Neo4j HetioNet (3s timeout)...")
                print(f"   Drug: {drug_name}, Disease: {disease_name}")
            
            # Use efficacy agent's Neo4j fetcher with short timeout (DB likely empty)
            pathway_data = self._run_with_timeout(
                self.efficacy_agent.fetch_efficacy_data,
                3,  # Reduced from 5s - fail fast if DB empty
                drug_name
            )
            
            if not pathway_data or len(pathway_data) == 0:
                if self.verbose:
                    print(f"⚠️  No pathway evidence in Neo4j - using medical knowledge (8s timeout)")
                
                # Use LLM medical knowledge for drug-disease efficacy when Neo4j has no data
                # Add timeout to prevent very long LLM generations
                try:
                    llm_analysis = self._run_with_timeout(
                        self.efficacy_agent.analyze,
                        8,  # Reduced from 10s for faster response
                        f"{drug_name} for {disease_name}"
                    )
                    return {
                        "status": "SUCCESS",
                        "drug_name": drug_name,
                        "disease_name": disease_name,
                        "pathways": [],
                        "summary": f"Analysis based on medical knowledge (Neo4j data unavailable)",
                        "llm_analysis": llm_analysis,
                        "error": None
                    }
                except Exception as e:
                    return {
                        "status": "NOT_FOUND",
                        "drug_name": drug_name,
                        "disease_name": disease_name,
                        "pathways": [],
                        "summary": f"No biological pathway evidence found connecting {drug_name} to {disease_name}",
                        "error": None
                    }
            
            # Format pathway results
            pathways = []
            for pathway in pathway_data:
                pathways.append({
                    'drug': pathway.get('drug', drug_name),
                    'metric': pathway.get('metric', 'N/A'),
                    'result': pathway.get('result', 'N/A'),
                    'value': pathway.get('value', 'N/A')
                })
            
            summary = f"Found {len(pathways)} biological pathway(s) connecting {drug_name} to disease treatment"
            
            if self.verbose:
                print(f"✅ Found {len(pathways)} pathway(s)")
            
            return {
                "status": "SUCCESS",
                "drug_name": drug_name,
                "disease_name": disease_name,
                "pathways": pathways,
                "summary": summary,
                "error": None
            }
            
        except TimeoutError as e:
            error_msg = f"Neo4j/Efficacy analysis timeout: {str(e)}"
            if self.verbose:
                print(f"⏱️ {error_msg}")
            return {
                "status": "ERROR",
                "drug_name": drug_name,
                "disease_name": disease_name,
                "pathways": [],
                "summary": "Efficacy analysis timed out - query too complex",
                "error": str(e)
            }
        except Exception as e:
            error_msg = f"Neo4j query error: {str(e)}"
            if self.verbose:
                print(f"❌ {error_msg}")
            
            return {
                "status": "ERROR",
                "drug_name": drug_name,
                "disease_name": disease_name,
                "pathways": [],
                "summary": error_msg,
                "error": str(e)
            }


# Singleton instance for efficiency
_tools_instance: Optional[ClinicalAgentTools] = None


def get_tools(verbose: bool = False) -> ClinicalAgentTools:
    """Get or create singleton tools instance"""
    global _tools_instance
    if _tools_instance is None:
        _tools_instance = ClinicalAgentTools(verbose=verbose)
    return _tools_instance


# Individual tool functions for LangGraph node usage
def search_chroma(criteria_text: str, top_k: int = 5) -> Dict:
    """Wrapper for ChromaDB search"""
    tools = get_tools()
    return tools.search_chroma(criteria_text, top_k)


def check_fda(drug_name: str) -> Dict:
    """Wrapper for OpenFDA query"""
    tools = get_tools()
    return tools.check_fda(drug_name)


def query_graph(drug_name: str, disease_name: str) -> Dict:
    """Wrapper for Neo4j HetioNet query"""
    tools = get_tools()
    return tools.query_graph(drug_name, disease_name)
