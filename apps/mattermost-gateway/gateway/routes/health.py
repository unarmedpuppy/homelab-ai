from __future__ import annotations

import logging

from fastapi import APIRouter

from ..config import BOT_REGISTRY, get_configured_bots
from ..mattermost import get_client
from ..models import HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    configured_bots = get_configured_bots()

    mattermost_status = "disconnected"
    if configured_bots:
        first_bot = BOT_REGISTRY.get(configured_bots[0])
        if first_bot:
            try:
                client = get_client(first_bot)
                if client.check_connection():
                    mattermost_status = "connected"
            except Exception as e:
                logger.warning(f"Health check failed: {e}")
                mattermost_status = f"error: {e}"

    return HealthResponse(
        status="healthy" if mattermost_status == "connected" else "degraded",
        bots=configured_bots,
        mattermost=mattermost_status,
    )
