"""
Pydantic models for memory and metrics data structures.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Message role types."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class Backend(str, Enum):
    """Backend types."""
    GPU_3070 = "3070"
    GPU_3090 = "3090"
    OPENCODE_GLM = "opencode-glm"
    OPENCODE_CLAUDE = "opencode-claude"


# ============================================================================
# Conversation Models
# ============================================================================

class ConversationCreate(BaseModel):
    """Model for creating a new conversation."""
    id: str = Field(..., description="Unique conversation ID (UUID)")
    session_id: Optional[str] = Field(None, description="Optional session grouping")
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    project: Optional[str] = Field(None, description="Optional project tag")
    title: Optional[str] = Field(None, description="Optional conversation title")
    username: Optional[str] = Field(None, description="Username from request header")
    source: Optional[str] = Field(None, description="Source/origin of request (e.g., 'claude-code', 'cursor')")
    display_name: Optional[str] = Field(None, description="Human-readable display name")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ConversationUpdate(BaseModel):
    """Model for updating a conversation."""
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class Conversation(BaseModel):
    """Full conversation model."""
    id: str
    created_at: datetime
    updated_at: datetime
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    project: Optional[str] = None
    title: Optional[str] = None
    username: Optional[str] = None
    source: Optional[str] = None
    display_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    message_count: int = 0
    total_tokens: int = 0

    class Config:
        from_attributes = True


# ============================================================================
# Message Models
# ============================================================================

class ImageRef(BaseModel):
    """Image reference stored with a message."""
    filename: str
    path: str
    size: int
    mimeType: str
    width: int
    height: int


class MessageCreate(BaseModel):
    """Model for creating a new message."""
    conversation_id: str
    role: MessageRole
    content: Optional[str] = None
    model_used: Optional[str] = None
    backend: Optional[str] = None
    tokens_prompt: Optional[int] = None
    tokens_completion: Optional[int] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_results: Optional[List[Dict[str, Any]]] = None
    image_refs: Optional[List[ImageRef]] = None
    metadata: Optional[Dict[str, Any]] = None


class Message(BaseModel):
    """Full message model."""
    id: int
    conversation_id: str
    timestamp: datetime
    role: MessageRole
    content: Optional[str] = None
    model_used: Optional[str] = None
    backend: Optional[str] = None
    tokens_prompt: Optional[int] = None
    tokens_completion: Optional[int] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_results: Optional[List[Dict[str, Any]]] = None
    image_refs: Optional[List[ImageRef]] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# ============================================================================
# Metrics Models
# ============================================================================

class MetricCreate(BaseModel):
    """Model for creating a metrics record."""
    conversation_id: Optional[str] = None
    session_id: Optional[str] = None
    endpoint: str
    model_requested: str
    model_used: Optional[str] = None
    backend: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    duration_ms: Optional[int] = None
    success: bool = True
    error: Optional[str] = None
    streaming: bool = False
    tool_calls_count: Optional[int] = 0
    user_id: Optional[str] = None
    project: Optional[str] = None
    cost_usd: Optional[float] = None


class Metric(BaseModel):
    """Full metrics model."""
    id: int
    timestamp: datetime
    date: str
    conversation_id: Optional[str] = None
    session_id: Optional[str] = None
    endpoint: str
    model_requested: str
    model_used: Optional[str] = None
    backend: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    duration_ms: Optional[int] = None
    success: bool
    error: Optional[str] = None
    streaming: bool
    tool_calls_count: Optional[int] = None
    user_id: Optional[str] = None
    project: Optional[str] = None
    cost_usd: Optional[float] = None

    class Config:
        from_attributes = True


# ============================================================================
# Daily Stats Models
# ============================================================================

class DailyStats(BaseModel):
    """Daily aggregated statistics."""
    date: str
    total_requests: int
    total_messages: int
    total_tokens: int
    unique_conversations: int
    unique_sessions: int
    models_used: Dict[str, int]
    backends_used: Dict[str, int]
    avg_duration_ms: float
    success_rate: float
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Dashboard Models
# ============================================================================

class ActivityDay(BaseModel):
    """Single day activity for GitHub-style chart."""
    date: str
    count: int
    level: int = Field(..., ge=0, le=4, description="Activity level 0-4")


class ModelUsage(BaseModel):
    """Model usage statistics."""
    model: str
    count: int
    percentage: float
    total_tokens: int


class DashboardStats(BaseModel):
    """Complete dashboard statistics (OpenCode Wrapped style)."""
    started_date: str
    days_active: int
    most_active_day: str
    most_active_day_count: int
    activity_chart: List[ActivityDay]
    top_models: List[ModelUsage]
    providers_used: Dict[str, float]
    total_sessions: int
    total_messages: int
    total_tokens: int
    unique_projects: int
    longest_streak: int
    cost_savings: Optional[float] = None


# ============================================================================
# Search Models
# ============================================================================

class ConversationSearchResult(BaseModel):
    """Search result for conversation search."""
    conversation: Conversation
    messages: List[Message]
    relevance_score: Optional[float] = None


class SearchQuery(BaseModel):
    """Search query parameters."""
    q: str = Field(..., min_length=1, description="Search query")
    user_id: Optional[str] = None
    project: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(10, ge=1, le=100)
    offset: int = Field(0, ge=0)


class AgentRunStatus(str, Enum):
    """Agent run status types."""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    MAX_STEPS = "max_steps"
    CANCELLED = "cancelled"


class AgentStepRecord(BaseModel):
    id: int
    agent_run_id: str
    step_number: int
    action_type: str
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    tool_result: Optional[str] = None
    thinking: Optional[str] = None
    error: Optional[str] = None
    started_at: datetime
    duration_ms: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None

    class Config:
        from_attributes = True


class AgentRunRecord(BaseModel):
    """Database record for an agent run."""
    id: str
    task: str
    working_directory: Optional[str] = None
    model_requested: Optional[str] = None
    model_used: Optional[str] = None
    backend: Optional[str] = None
    status: AgentRunStatus
    final_answer: Optional[str] = None
    total_steps: int = 0
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    source: Optional[str] = None
    triggered_by: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class AgentRunWithSteps(AgentRunRecord):
    """Agent run with all its steps."""
    steps: List[AgentStepRecord] = []


class AgentRunsStats(BaseModel):
    """Aggregated statistics for agent runs."""
    total_runs: int
    completed: int
    failed: int
    running: int
    avg_steps: float
    avg_duration_ms: float
    by_source: Dict[str, int]
    by_status: Dict[str, int]


# ============================================================================
# Streaming Models
# ============================================================================

class StreamStatus(str, Enum):
    """Stream event status types."""
    ROUTING = "routing"
    LOADING = "loading"
    GENERATING = "generating"
    STREAMING = "streaming"
    DONE = "done"
    ERROR = "error"


class StreamEvent(BaseModel):
    """
    SSE stream event for real-time status updates.

    Emitted during chat completion requests to provide feedback on:
    - Backend selection (routing)
    - Model warmup (loading)
    - Response generation progress (generating)
    - Final completion (done)
    """
    status: StreamStatus
    message: Optional[str] = Field(None, description="Human-readable status message")
    content: Optional[str] = Field(None, description="Response content (for done status)")
    model: Optional[str] = Field(None, description="Model used for generation")
    backend: Optional[str] = Field(None, description="Backend/provider ID")
    provider_name: Optional[str] = Field(None, description="Human-readable provider name")
    timestamp: float = Field(..., description="Unix timestamp of event")
    estimated_time: Optional[int] = Field(None, description="Estimated wait time in seconds")
    delta: Optional[str] = Field(None, description="Incremental content chunk (for streaming status)")
    finish_reason: Optional[str] = Field(None, description="Finish reason (stop, length, etc.)")
    usage: Optional[Dict[str, int]] = Field(None, description="Token usage stats (for done status)")
    error_detail: Optional[str] = Field(None, description="Error details (for error status)")
    conversation_id: Optional[str] = Field(None, description="Conversation ID (for done status when memory is enabled)")
