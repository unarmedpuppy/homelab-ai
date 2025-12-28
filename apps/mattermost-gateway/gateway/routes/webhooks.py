from __future__ import annotations

import logging

from fastapi import APIRouter, Header, HTTPException, Request

from ..config import get_bot, get_settings
from ..mattermost import MattermostClientError, get_client
from ..models import WebhookResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/webhook/{bot_name}", response_model=WebhookResponse)
async def webhook_post(
    bot_name: str,
    request: Request,
    x_channel: str | None = Header(default=None, alias="X-Channel"),
) -> WebhookResponse:
    bot = get_bot(bot_name)
    if not bot:
        raise HTTPException(status_code=400, detail=f"Unknown bot: {bot_name}")

    if not bot.is_configured():
        raise HTTPException(
            status_code=503, detail=f"Bot '{bot_name}' is not configured"
        )

    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        try:
            body = await request.json()
            message = body.get("message") or body.get("text") or str(body)
            channel = body.get("channel") or x_channel or bot.default_channel
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")
    else:
        body = await request.body()
        message = body.decode("utf-8")
        channel = x_channel or bot.default_channel

    if not message or not message.strip():
        raise HTTPException(status_code=400, detail="Empty message")

    settings = get_settings()
    channel = channel or settings.default_channel

    try:
        client = get_client(bot)
        result = client.post_message(channel=channel, message=message)
        logger.info(f"Webhook posted to {channel} as {bot_name}: {message[:50]}...")
        return WebhookResponse(success=True, post_id=result.get("id"))
    except MattermostClientError as e:
        logger.error(f"Mattermost error: {e}")
        return WebhookResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error in webhook: {e}")
        return WebhookResponse(success=False, error="Internal error")
