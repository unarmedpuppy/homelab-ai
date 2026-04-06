from __future__ import annotations

import httpx

from llm_tui.config import Config
from llm_tui.models import ManagerStatus, ModelInfo, ModelCard, RequestMetric


class ManagerClient:
    def __init__(self, config: Config):
        self.config = config
        self._client = httpx.AsyncClient(timeout=5)

    async def get_status(self) -> ManagerStatus | None:
        try:
            r = await self._client.get(f"{self.config.manager_url}/status")
            r.raise_for_status()
            d = r.json()
            return ManagerStatus(
                mode=d.get("mode", "on-demand"),
                gaming_mode_active=d.get("gaming_mode_active", False),
                gaming_mode_enabled=d.get("gaming_mode_enabled", False),
                gpu_vram_gb=d.get("gpu_vram_gb", 0),
                default_model=d.get("default_model", ""),
                idle_timeout=d.get("idle_timeout", 0),
                active_requests=d.get("active_requests", 0),
                running=[ModelInfo(**m) for m in d.get("running", [])],
                stopped=[ModelInfo(**m) for m in d.get("stopped", [])],
                total=d.get("summary", {}).get("total", 0),
                available=d.get("summary", {}).get("available", 0),
                running_count=d.get("summary", {}).get("running", 0),
            )
        except (httpx.HTTPError, Exception):
            return None

    async def get_model_cards(self) -> list[ModelCard]:
        try:
            r = await self._client.get(f"{self.config.manager_url}/v1/models/cards")
            r.raise_for_status()
            d = r.json()
            return [ModelCard(**m) for m in d.get("models", [])]
        except (httpx.HTTPError, Exception):
            return []

    async def swap_model(self, model_id: str) -> dict | None:
        try:
            r = await self._client.post(
                f"{self.config.manager_url}/swap/{model_id}",
                timeout=600,
            )
            r.raise_for_status()
            return r.json()
        except (httpx.HTTPError, Exception):
            return None

    async def stop_all(self) -> dict | None:
        try:
            r = await self._client.post(f"{self.config.manager_url}/stop-all")
            r.raise_for_status()
            return r.json()
        except (httpx.HTTPError, Exception):
            return None

    async def toggle_gaming_mode(self, enable: bool) -> dict | None:
        try:
            r = await self._client.post(
                f"{self.config.manager_url}/gaming-mode",
                json={"enable": enable},
            )
            r.raise_for_status()
            return r.json()
        except (httpx.HTTPError, Exception):
            return None

    async def get_recent_metrics(self, limit: int = 50) -> list[RequestMetric]:
        try:
            r = await self._client.get(
                f"{self.config.router_url}/metrics/recent",
                params={"limit": limit},
            )
            r.raise_for_status()
            data = r.json()
            rows = data if isinstance(data, list) else data.get("metrics", [])
            return [RequestMetric(**m) for m in rows]
        except (httpx.HTTPError, Exception):
            return []

    async def close(self):
        await self._client.aclose()
