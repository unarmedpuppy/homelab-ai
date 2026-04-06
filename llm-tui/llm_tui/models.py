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

    @property
    def display_user(self) -> str:
        return self.display_name or self.username or self.user_id or "unknown"

    @property
    def tokens_per_sec(self) -> float:
        if self.duration_ms <= 0 or self.completion_tokens <= 0:
            return 0
        return self.completion_tokens / (self.duration_ms / 1000)
