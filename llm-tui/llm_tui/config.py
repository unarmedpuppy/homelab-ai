import os
from dataclasses import dataclass


@dataclass
class Config:
    manager_url: str = os.getenv("LLM_MANAGER_URL", "http://localhost:8000")
    router_url: str = os.getenv("LLM_ROUTER_URL", "http://localhost:8000")  # defaults to manager
    gpu_poll_interval: float = float(os.getenv("GPU_POLL_SEC", "2"))
    api_poll_interval: float = float(os.getenv("API_POLL_SEC", "5"))
    metrics_poll_interval: float = float(os.getenv("METRICS_POLL_SEC", "3"))
