from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from ..config import get_bot
from ..mattermost import MattermostClientError, get_client
from ..models import (
    PostMessageRequest,
    PostMessageResponse,
    ReactRequest,
    ReactResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/post", response_model=PostMessageResponse)
async def post_message(request: PostMessageRequest) -> PostMessageResponse:
    bot = get_bot(request.bot)
    if not bot:
        raise HTTPException(status_code=400, detail=f"Unknown bot: {request.bot}")

    if not bot.is_configured():
        raise HTTPException(
            status_code=503, detail=f"Bot '{request.bot}' is not configured"
        )

    try:
        client = get_client(bot)
        result = client.post_message(
            channel=request.channel,
            message=request.message,
            props=request.props,
            thread_id=request.thread_id,
        )
        return PostMessageResponse(success=True, post_id=result.get("id"))
    except MattermostClientError as e:
        logger.error(f"Mattermost error: {e}")
        return PostMessageResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error posting message: {e}")
        return PostMessageResponse(success=False, error="Internal error")


@router.post("/react", response_model=ReactResponse)
async def add_reaction(request: ReactRequest) -> ReactResponse:
    bot = get_bot(request.bot)
    if not bot:
        raise HTTPException(status_code=400, detail=f"Unknown bot: {request.bot}")

    if not bot.is_configured():
        raise HTTPException(
            status_code=503, detail=f"Bot '{request.bot}' is not configured"
        )

    try:
        client = get_client(bot)
        client.add_reaction(post_id=request.post_id, emoji=request.emoji)
        return ReactResponse(success=True)
    except MattermostClientError as e:
        logger.error(f"Mattermost error: {e}")
        return ReactResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error adding reaction: {e}")
        return ReactResponse(success=False, error="Internal error")
