"""
AgentCard Support for A2A Protocol

AgentCard enables agent discovery and capability advertisement.
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class AgentCard:
    """AgentCard for A2A protocol agent discovery."""
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None,
        transports: Optional[List[Dict[str, Any]]] = None,
        authentication: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.agent_id = agent_id
        self.name = name
        self.version = version
        self.capabilities = capabilities or []
        self.transports = transports or []
        self.authentication = authentication or {"type": "none", "required": False}
        self.metadata = metadata or {}
        self.created_at = datetime.now().isoformat() + "Z"
        self.updated_at = datetime.now().isoformat() + "Z"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "capabilities": self.capabilities,
            "transports": self.transports,
            "authentication": self.authentication,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentCard":
        """Create from dictionary."""
        card = cls(
            agent_id=data["agent_id"],
            name=data["name"],
            version=data.get("version", "1.0.0"),
            capabilities=data.get("capabilities", []),
            transports=data.get("transports", []),
            authentication=data.get("authentication", {"type": "none", "required": False}),
            metadata=data.get("metadata", {})
        )
        card.created_at = data.get("created_at", card.created_at)
        card.updated_at = data.get("updated_at", card.updated_at)
        return card
    
    @classmethod
    def from_json(cls, json_str: str) -> "AgentCard":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def save(self, directory: Path) -> Path:
        """Save AgentCard to file."""
        directory.mkdir(parents=True, exist_ok=True)
        file_path = directory / f"{self.agent_id}.json"
        file_path.write_text(self.to_json())
        return file_path
    
    @classmethod
    def load(cls, file_path: Path) -> "AgentCard":
        """Load AgentCard from file."""
        return cls.from_json(file_path.read_text())


# AgentCard directory
AGENTCARDS_DIR = Path(__file__).parent.parent.parent / "communication" / "agentcards"


def ensure_agentcards_dir():
    """Ensure agentcards directory exists."""
    AGENTCARDS_DIR.mkdir(parents=True, exist_ok=True)


def create_agentcard(
    agent_id: str,
    name: str,
    capabilities: List[str],
    transports: Optional[List[Dict[str, Any]]] = None,
    **kwargs
) -> AgentCard:
    """
    Create and save an AgentCard.
    
    Args:
        agent_id: Unique agent identifier
        name: Agent name
        capabilities: List of agent capabilities
        transports: List of transport configurations
        **kwargs: Additional metadata
    
    Returns:
        Created AgentCard
    """
    ensure_agentcards_dir()
    
    # Default transports if not provided
    if transports is None:
        transports = [
            {
                "type": "http",
                "endpoint": "http://localhost:3001/a2a",
                "methods": ["POST"]
            },
            {
                "type": "sse",
                "endpoint": "http://localhost:3001/a2a/stream",
                "events": ["message", "status"]
            }
        ]
    
    card = AgentCard(
        agent_id=agent_id,
        name=name,
        capabilities=capabilities,
        transports=transports,
        metadata=kwargs
    )
    
    card.save(AGENTCARDS_DIR)
    return card


def get_agentcard(agent_id: str) -> Optional[AgentCard]:
    """
    Get AgentCard by agent ID.
    
    Args:
        agent_id: Agent identifier
    
    Returns:
        AgentCard if found, None otherwise
    """
    ensure_agentcards_dir()
    file_path = AGENTCARDS_DIR / f"{agent_id}.json"
    
    if file_path.exists():
        return AgentCard.load(file_path)
    return None


def list_agentcards() -> List[AgentCard]:
    """
    List all AgentCards.
    
    Returns:
        List of AgentCards
    """
    ensure_agentcards_dir()
    
    cards = []
    for file_path in AGENTCARDS_DIR.glob("*.json"):
        try:
            cards.append(AgentCard.load(file_path))
        except Exception:
            continue
    
    return cards


def update_agentcard(agent_id: str, updates: Dict[str, Any]) -> Optional[AgentCard]:
    """
    Update an existing AgentCard.
    
    Args:
        agent_id: Agent identifier
        updates: Dictionary of updates
    
    Returns:
        Updated AgentCard if found, None otherwise
    """
    card = get_agentcard(agent_id)
    if not card:
        return None
    
    # Update fields
    if "name" in updates:
        card.name = updates["name"]
    if "version" in updates:
        card.version = updates["version"]
    if "capabilities" in updates:
        card.capabilities = updates["capabilities"]
    if "transports" in updates:
        card.transports = updates["transports"]
    if "authentication" in updates:
        card.authentication = updates["authentication"]
    if "metadata" in updates:
        card.metadata.update(updates["metadata"])
    
    card.updated_at = datetime.now().isoformat() + "Z"
    card.save(AGENTCARDS_DIR)
    
    return card

