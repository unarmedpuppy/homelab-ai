"""
Tayne Mattermost Bot - Webhook Handler

Receives Mattermost outgoing webhook requests when @tayne is mentioned,
queries local-ai-router with Tayne persona, and responds.
"""

from __future__ import annotations

import logging
import random
import time
from collections import defaultdict
from typing import Any

import httpx
from fastapi import APIRouter, Form, HTTPException

from ..config import get_bot, get_settings
from ..mattermost import MattermostClient, MattermostClientError, get_client
from ..tayne_persona import (
    API_DOWN_MESSAGE,
    CHARACTER_BREAK_PHRASES,
    DEFAULT_COOLDOWN_SECONDS,
    DEFAULT_MAX_RESPONSE_LENGTH,
    DEFAULT_RAPID_FIRE_THRESHOLD,
    DEFAULT_RAPID_FIRE_WINDOW,
    DEFAULT_REQUEST_TIMEOUT,
    FALLBACK_QUOTES,
    RATE_LIMITED_RESPONSES,
    TAYNE_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["tayne"])

# Rate limiting state (in-memory, resets on restart)
user_cooldowns: dict[str, float] = defaultdict(float)
user_message_times: dict[str, list[float]] = defaultdict(list)


def is_rate_limited(user_id: str) -> tuple[bool, bool]:
    """
    Check if user is rate limited.
    
    Returns:
        (is_limited, is_rapid_fire): Tuple indicating if limited and if it's rapid fire spam
    """
    now = time.time()
    
    # Check basic cooldown
    if now - user_cooldowns[user_id] < DEFAULT_COOLDOWN_SECONDS:
        return True, False
    
    # Check rapid-fire spam (many messages in short window)
    user_message_times[user_id] = [
        t for t in user_message_times[user_id] 
        if now - t < DEFAULT_RAPID_FIRE_WINDOW
    ]
    user_message_times[user_id].append(now)
    
    if len(user_message_times[user_id]) > DEFAULT_RAPID_FIRE_THRESHOLD:
        return True, True
    
    # Update cooldown
    user_cooldowns[user_id] = now
    return False, False


def needs_fallback(response: str) -> bool:
    """
    Detect if the LLM response has gone off the rails or broken character.
    """
    if len(response) > DEFAULT_MAX_RESPONSE_LENGTH:
        return True
    
    response_lower = response.lower()
    for phrase in CHARACTER_BREAK_PHRASES:
        if phrase in response_lower:
            return True
    
    return False


def clean_message(text: str, trigger_word: str) -> str:
    """Remove trigger word from message."""
    # Remove the trigger word (case insensitive)
    import re
    cleaned = re.sub(re.escape(trigger_word), '', text, flags=re.IGNORECASE).strip()
    return cleaned if cleaned else "Hello Tayne!"


async def query_tayne(
    message: str,
    user_name: str,
    channel_id: str,
    user_id: str,
) -> str | None:
    """
    Query local-ai-router with Tayne's persona.
    
    Returns:
        Response text, or None if the API call failed
    """
    settings = get_settings()
    local_ai_url = settings.local_ai_url
    local_ai_api_key = settings.local_ai_api_key
    
    if not local_ai_url:
        logger.error("LOCAL_AI_URL not configured")
        return None
    
    api_messages = [
        {"role": "system", "content": TAYNE_SYSTEM_PROMPT},
        {"role": "user", "content": f"{user_name}: {message}"},
    ]
    
    payload = {
        "model": "auto",
        "messages": api_messages,
        "max_tokens": 200,
        "temperature": 0.9,
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Enable-Memory": "true",
        "X-Conversation-ID": f"mattermost-{channel_id}",
        "X-Project": "tayne-mattermost-bot",
        "X-User-ID": user_id,
    }
    
    if local_ai_api_key:
        headers["Authorization"] = f"Bearer {local_ai_api_key}"
    
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{local_ai_url}/v1/chat/completions",
                json=payload,
                headers=headers,
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data["choices"][0]["message"]["content"]
                
                # Check guardrails
                if needs_fallback(response_text):
                    logger.info(f"Guardrail triggered, using fallback. Original: {response_text[:100]}...")
                    return random.choice(FALLBACK_QUOTES)
                
                return response_text
            else:
                logger.error(f"API returned status {response.status_code}: {response.text}")
                return None
                
    except httpx.TimeoutException:
        logger.error("API request timed out")
        return None
    except httpx.RequestError as e:
        logger.error(f"API connection error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error querying API: {e}")
        return None


@router.post("/webhook/tayne/mention")
async def handle_tayne_mention(
    token: str = Form(default=""),
    team_id: str = Form(default=""),
    team_domain: str = Form(default=""),
    channel_id: str = Form(default=""),
    channel_name: str = Form(default=""),
    timestamp: str = Form(default=""),
    user_id: str = Form(default=""),
    user_name: str = Form(default=""),
    post_id: str = Form(default=""),
    text: str = Form(default=""),
    trigger_word: str = Form(default="@tayne"),
) -> dict[str, Any]:
    """
    Handle Mattermost outgoing webhook when @tayne is mentioned.
    
    Mattermost sends form-encoded data, we respond with JSON.
    The response is automatically posted back to the channel.
    """
    logger.info(f"Tayne mentioned by {user_name} in {channel_name}: {text[:50]}...")
    
    # Validate webhook token if configured
    settings = get_settings()
    if settings.tayne_webhook_token and token != settings.tayne_webhook_token:
        logger.warning(f"Invalid webhook token from {user_name}")
        raise HTTPException(status_code=401, detail="Invalid webhook token")
    
    # Check rate limiting
    is_limited, is_rapid_fire = is_rate_limited(user_id)
    
    if is_limited:
        response_text = random.choice(RATE_LIMITED_RESPONSES)
        if is_rapid_fire:
            response_text = random.choice(FALLBACK_QUOTES)
        
        return {
            "text": response_text,
            "response_type": "comment",
        }
    
    # Clean the message (remove trigger word)
    cleaned_message = clean_message(text, trigger_word)
    
    # Query Tayne
    response = await query_tayne(
        message=cleaned_message,
        user_name=user_name,
        channel_id=channel_id,
        user_id=user_id,
    )
    
    if response:
        return {
            "text": response,
            "response_type": "comment",
        }
    else:
        # API is down
        return {
            "text": API_DOWN_MESSAGE,
            "response_type": "comment",
        }


@router.get("/webhook/tayne/health")
async def tayne_health() -> dict[str, Any]:
    """Health check for Tayne webhook."""
    settings = get_settings()
    
    # Check if local-ai-router is reachable
    local_ai_healthy = False
    if settings.local_ai_url:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{settings.local_ai_url}/health")
                local_ai_healthy = response.status_code == 200
        except Exception:
            pass
    
    # Check if Tayne bot is configured in Mattermost
    tayne_bot = get_bot("tayne")
    tayne_configured = tayne_bot is not None and tayne_bot.is_configured()
    
    return {
        "status": "healthy" if (local_ai_healthy and tayne_configured) else "degraded",
        "local_ai_router": "connected" if local_ai_healthy else "disconnected",
        "tayne_bot_configured": tayne_configured,
        "local_ai_url": settings.local_ai_url or "not configured",
    }
