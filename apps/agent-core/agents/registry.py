"""
Agent Registry

Discovers and manages agent instances. Each agent has a unique ID,
persona configuration, and default settings.
"""

from abc import ABC, abstractmethod
from typing import Optional

# Import agents
from .tayne import TayneAgent


class AgentBase(ABC):
    """Base class for all agents."""
    
    @property
    @abstractmethod
    def agent_id(self) -> str:
        """Unique identifier for this agent."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Short description of this agent."""
        pass
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt defining agent personality."""
        pass
    
    @property
    def model(self) -> str:
        """Default model to use. 'auto' lets router choose."""
        return "auto"
    
    @property
    def max_tokens(self) -> int:
        """Default max tokens for responses."""
        return 200
    
    @property
    def temperature(self) -> float:
        """Default temperature for responses."""
        return 0.9


# Registry of available agents
_AGENTS: dict[str, AgentBase] = {}


def _register_agents():
    """Register all available agents."""
    global _AGENTS
    
    agents = [
        TayneAgent(),
    ]
    
    for agent in agents:
        _AGENTS[agent.agent_id] = agent


def get_agent(agent_id: str) -> Optional[AgentBase]:
    """Get an agent by ID."""
    if not _AGENTS:
        _register_agents()
    return _AGENTS.get(agent_id)


def list_agents() -> list[dict]:
    """List all available agents."""
    if not _AGENTS:
        _register_agents()
    
    return [
        {
            "id": agent.agent_id,
            "name": agent.name,
            "description": agent.description,
        }
        for agent in _AGENTS.values()
    ]
