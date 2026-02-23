"""Pydantic models for Agent Gateway."""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """Agent deployment type."""
    SERVER = "server"  # Always-on, health-checked (runs on server)
    CLI = "cli"        # Interactive, no health checks (runs locally via Claude Code)


class AgentStatus(str, Enum):
    """Agent health status."""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class HealthCheckConfig(BaseModel):
    """Health check configuration."""
    interval_seconds: int = 30
    timeout_seconds: int = 10
    failure_threshold: int = 3


class AgentConfig(BaseModel):
    """Agent configuration from config.yaml."""
    name: str
    description: str = ""
    endpoint: str = ""
    agent_type: AgentType = AgentType.CLI
    expected_online: bool = False
    tags: list[str] = Field(default_factory=list)


class AgentHealth(BaseModel):
    """Health check result for an agent."""
    status: AgentStatus = AgentStatus.UNKNOWN
    last_check: Optional[datetime] = None
    last_success: Optional[datetime] = None
    response_time_ms: Optional[float] = None
    consecutive_failures: int = 0
    error: Optional[str] = None
    version: Optional[str] = None


class Agent(BaseModel):
    """Agent with current status."""
    id: str
    name: str
    description: str = ""
    endpoint: str = ""
    agent_type: AgentType = AgentType.CLI
    expected_online: bool = False
    tags: list[str] = Field(default_factory=list)
    health: AgentHealth = Field(default_factory=AgentHealth)

    @property
    def status(self) -> AgentStatus:
        return self.health.status


class AgentDetails(Agent):
    """Extended agent details for single-agent endpoint."""
    # Additional fields can be added here
    pass


class FleetStats(BaseModel):
    """Fleet-wide statistics."""
    total_agents: int = 0
    online_count: int = 0
    offline_count: int = 0
    degraded_count: int = 0
    unknown_count: int = 0
    expected_online_count: int = 0
    unexpected_offline_count: int = 0
    avg_response_time_ms: Optional[float] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class GatewayConfig(BaseModel):
    """Full gateway configuration."""
    health_check: HealthCheckConfig = Field(default_factory=HealthCheckConfig)
    agents: dict[str, AgentConfig] = Field(default_factory=dict)


class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobCreateRequest(BaseModel):
    """Request to create a new job."""
    agent_id: str
    prompt: str
    model: str = "sonnet"
    working_directory: Optional[str] = None
    allowed_tools: Optional[list[str]] = None
    max_turns: Optional[int] = None


class Job(BaseModel):
    """Job with current status."""
    job_id: str
    agent_id: str
    prompt: str
    model: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None
    turns: int = 0
    tokens_used: Optional[int] = None


class JobListResponse(BaseModel):
    """Response for job listing."""
    jobs: list[Job]
    total: int = 0
