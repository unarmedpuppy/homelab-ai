"""
A2A (Agent-to-Agent) Protocol Support

Provides A2A-compliant message format, AgentCard support, and protocol adapters.
"""

from .message import A2AMessage, A2ARequest, A2AResponse, A2AError
from .agentcard import AgentCard, create_agentcard, get_agentcard, list_agentcards
from .adapter import to_a2a_format, from_a2a_format, validate_a2a_message

__all__ = [
    "A2AMessage",
    "A2ARequest",
    "A2AResponse",
    "A2AError",
    "AgentCard",
    "create_agentcard",
    "get_agentcard",
    "list_agentcards",
    "to_a2a_format",
    "from_a2a_format",
    "validate_a2a_message",
]

