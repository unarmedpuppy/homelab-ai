from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from ..config import BOT_REGISTRY, get_bot, get_configured_bots
from ..mattermost import MattermostClientError, get_client
from ..models import Message, MessagesResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/messages", response_model=MessagesResponse)
async def get_messages(
    channel: str = Query(..., description="Channel name or ID"),
    limit: int = Query(default=50, ge=1, le=200, description="Number of messages"),
    since: int | None = Query(default=None, description="Timestamp to fetch after"),
    bot: str | None = Query(default=None, description="Bot to use for fetching"),
) -> MessagesResponse:
    configured_bots = get_configured_bots()
    if not configured_bots:
        raise HTTPException(status_code=503, detail="No bots configured")

    bot_name = bot or configured_bots[0]
    bot_config = get_bot(bot_name)
    if not bot_config:
        raise HTTPException(status_code=400, detail=f"Unknown bot: {bot_name}")

    if not bot_config.is_configured():
        raise HTTPException(
            status_code=503, detail=f"Bot '{bot_name}' is not configured"
        )

    try:
        client = get_client(bot_config)
        raw_messages = client.get_messages(channel=channel, limit=limit, since=since)

        messages = [
            Message(
                id=m["id"],
                user_id=m["user_id"],
                message=m["message"],
                create_at=m["create_at"],
                type=m.get("type"),
            )
            for m in raw_messages
        ]

        return MessagesResponse(success=True, messages=messages)
    except MattermostClientError as e:
        logger.error(f"Mattermost error: {e}")
        return MessagesResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error fetching messages: {e}")
        return MessagesResponse(success=False, error="Internal error")
