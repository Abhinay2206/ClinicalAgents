"""
Configuration management for ClinicalAgent 2.0
Loads and validates API credentials and service endpoints
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Centralized configuration for ClinicalAgent 2.0"""
    
    # LLM Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # Neo4j Configuration (for Efficacy Agent)
    NEO4J_URI: str = os.getenv("NEO4J_URI", "")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "")
    
    # ChromaDB Configuration (for Enrollment Agent)
    CHROMA_API_KEY: str = os.getenv("CHROMA_API_KEY", "")
    CHROMA_TENANT: str = os.getenv("CHROMA_TENANT", "")
    CHROMA_DATABASE: str = os.getenv("CHROMA_DATABASE", "ClinicalAgents")
    CHROMA_COLLECTION: str = os.getenv("CHROMA_COLLECTION", "clinical_trials")
    
    # OpenFDA API (no key required for public API)
    OPENFDA_BASE_URL: str = "https://api.fda.gov/drug/label.json"
    
    # Human-in-the-Loop Configuration
    HUMAN_INPUT_TIMEOUT: int = int(os.getenv("HUMAN_INPUT_TIMEOUT", "300"))  # 5 minutes
    MAX_HUMAN_RETRIES: int = int(os.getenv("MAX_HUMAN_RETRIES", "3"))
    
    # Workflow Configuration
    WORKFLOW_TIMEOUT: int = int(os.getenv("WORKFLOW_TIMEOUT", "600"))  # 10 minutes
    ENABLE_PARALLEL_EXECUTION: bool = os.getenv("ENABLE_PARALLEL_EXECUTION", "true").lower() == "true"
    
    @classmethod
    def validate(cls) -> dict[str, bool]:
        """
        Validate that all required credentials are present
        
        Returns:
            Dictionary with validation results for each service
        """
        validation = {
            "groq": bool(cls.GROQ_API_KEY),
            "neo4j": bool(cls.NEO4J_URI and cls.NEO4J_PASSWORD),
            "chromadb": bool(cls.CHROMA_API_KEY and cls.CHROMA_TENANT),
            "openfda": True,  # Public API, no key required
        }
        return validation
    
    @classmethod
    def is_fully_configured(cls) -> bool:
        """Check if all services are configured"""
        validation = cls.validate()
        return all(validation.values())
    
    @classmethod
    def get_missing_config(cls) -> list[str]:
        """Get list of missing configuration items"""
        validation = cls.validate()
        missing = [service for service, valid in validation.items() if not valid]
        return missing
    
    @classmethod
    def print_status(cls) -> None:
        """Print configuration status"""
        print("\n" + "="*60)
        print("ClinicalAgent 2.0 Configuration Status")
        print("="*60)
        
        validation = cls.validate()
        for service, valid in validation.items():
            status = "✅ OK" if valid else "❌ MISSING"
            print(f"{service.upper():12s}: {status}")
        
        if not cls.is_fully_configured():
            print("\n⚠️  Missing configuration:")
            for service in cls.get_missing_config():
                print(f"   - {service.upper()}")
            print("\nPlease check your .env file and ensure all credentials are set.")
        else:
            print("\n✅ All services configured successfully!")
        
        print("="*60 + "\n")


if __name__ == "__main__":
    # Test configuration
    Config.print_status()
