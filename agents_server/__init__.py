"""ClinicalAgents package.

Provides:
- SimpleDynamicOrchestrator
- HumanProxyAgent (session, logging, review)
- AsyncMongoStore (chat memory, audit logs, backups)

This package can be run as a module for the API server:
  python -m agents_server.api
"""

__all__ = [
    "__version__",
]

__version__ = "0.1.0"
