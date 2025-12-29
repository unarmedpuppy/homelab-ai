"""
Provider and Model data models for the routing system.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum


class ProviderType(str, Enum):
    """Provider type enum."""
    LOCAL = "local"
    CLOUD = "cloud"


class AuthType(str, Enum):
    """Authentication type enum."""
    NONE = "none"
    API_KEY = "api_key"
    BEARER = "bearer"


class ModelCapabilities(BaseModel):
    """Model capability flags."""
    streaming: bool = True
    function_calling: bool = False
    vision: bool = False
    json_mode: bool = False


class Model(BaseModel):
    """Model configuration."""
    id: str
    name: str
    provider_id: str
    description: Optional[str] = None
    context_window: int = 4096
    max_tokens: int = 2048
    is_default: bool = False
    cost_per_1k_tokens: float = 0.0
    capabilities: ModelCapabilities = Field(default_factory=ModelCapabilities)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Provider(BaseModel):
    """Provider configuration."""
    id: str
    name: str
    type: ProviderType
    description: Optional[str] = None
    endpoint: str
    priority: int = 10
    enabled: bool = True
    max_concurrent: int = 1
    health_check_interval: int = 30
    health_check_timeout: int = 5
    health_check_path: str = "/health"
    auth_type: Optional[AuthType] = None
    auth_secret: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Runtime state (not from config)
    current_requests: int = 0
    is_healthy: bool = True
    last_health_check: Optional[float] = None
    consecutive_failures: int = 0


class ProviderConfig(BaseModel):
    """Full provider configuration from YAML."""
    providers: List[Provider]
    models: List[Model]
    settings: Dict[str, Any] = Field(default_factory=dict)


class ProviderSelection(BaseModel):
    """Result of provider/model selection."""
    provider: Provider
    model: Model
    reason: str  # Why this provider/model was selected
