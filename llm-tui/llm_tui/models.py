from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class GPUStats:
    index: int
    name: str
    temp_c: int
    power_draw_w: float
    power_limit_w: float
    vram_total_mb: int
    vram_used_mb: int
    vram_free_mb: int
    utilization_pct: int

    @property
    def vram_pct(self) -> float:
        if self.vram_total_mb == 0:
            return 0
        return (self.vram_used_mb / self.vram_total_mb) * 100


@dataclass
class ModelInfo:
    id: str
    name: str
    type: str = "text"
    vram_gb: float = 0
    runtime: str = "vllm"
    status: str = "stopped"
    last_used: float = 0
    idle_seconds: int | None = None
    container: str = ""


@dataclass
class ModelCard:
    id: str
    name: str
    hf_model: str = ""
    type: str = "text"
    quantization: str | None = None
    vram_gb: float = 0
    max_context: int | None = None
    default_context: int | None = None
    gpu_count: int = 1
    runtime: str = "vllm"
    description: str = ""
    tags: list[str] = field(default_factory=list)
    status: str = "stopped"
    cached: bool = False
    cache_size_gb: float | None = None
    idle_seconds: int | None = None


@dataclass
class ManagerStatus:
    mode: str = "on-demand"
    gaming_mode_active: bool = False
    gaming_mode_enabled: bool = False
    gpu_vram_gb: int = 0
    default_model: str = ""
    idle_timeout: int = 0
    running: list[ModelInfo] = field(default_factory=list)
    stopped: list[ModelInfo] = field(default_factory=list)
    active_requests: int = 0
    total: int = 0
    available: int = 0
    running_count: int = 0


@dataclass
class RequestMetric:
    id: int = 0
    timestamp: str = ""
    model_requested: str = ""
    model_used: str = ""
    backend: str = ""
    endpoint: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    duration_ms: int = 0
    success: bool = True
    streaming: bool = False
    user_id: str = ""
    username: str = ""
    display_name: str = ""
    source: str = ""
    project: str = ""

    @property
    def display_user(self) -> str:
        return self.display_name or self.username or self.user_id or self.project or "unknown"

    @property
    def tokens_per_sec(self) -> float:
        if self.duration_ms <= 0 or self.completion_tokens <= 0:
            return 0
        return self.completion_tokens / (self.duration_ms / 1000)

    @classmethod
    def from_api(cls, data: dict) -> RequestMetric:
        """Build from router or manager API response, ignoring unknown fields."""
        return cls(
            id=data.get("id", 0),
            timestamp=data.get("timestamp", ""),
            model_requested=data.get("model_requested", ""),
            model_used=data.get("model_used", ""),
            backend=data.get("backend", ""),
            endpoint=data.get("endpoint", ""),
            prompt_tokens=data.get("prompt_tokens") or 0,
            completion_tokens=data.get("completion_tokens") or 0,
            total_tokens=data.get("total_tokens") or 0,
            duration_ms=data.get("duration_ms") or 0,
            success=data.get("success", True),
            streaming=data.get("streaming", False),
            user_id=data.get("user_id", ""),
            username=data.get("username", ""),
            display_name=data.get("display_name", ""),
            source=data.get("source", ""),
            project=data.get("project", ""),
        )
