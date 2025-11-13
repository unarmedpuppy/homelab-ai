"""
Agent Memory Integration using Memori

Memori provides transparent memory management for AI agents:
- Automatic context injection before LLM calls
- Automatic conversation recording
- Background pattern learning (Conscious Agent)
- Multi-agent support
"""

from .memori_helper import get_memori_instance, setup_memori

__all__ = ["get_memori_instance", "setup_memori"]

