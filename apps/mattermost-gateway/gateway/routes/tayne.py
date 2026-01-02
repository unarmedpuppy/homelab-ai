"""
Tayne Mattermost Bot - Webhook Handler

Receives Mattermost outgoing webhook requests when @tayne is mentioned,
routes to agent-core (with fallback to direct local-ai-router), and responds.
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

user_cooldowns: dict[str, float] = defaultdict(float)
user_message_times: dict[str, list[float]] = defaultdict(list)


def is_rate_limited(user_id: str) -> tuple[bool, bool]:
    """Returns (is_limited, is_rapid_fire)."""
    now = time.time()
    
    if now - user_cooldowns[user_id] < DEFAULT_COOLDOWN_SECONDS:
        return True, False
    
    user_message_times[user_id] = [
        t for t in user_message_times[user_id] 
        if now - t < DEFAULT_RAPID_FIRE_WINDOW
    ]
    user_message_times[user_id].append(now)
    
    if len(user_message_times[user_id]) > DEFAULT_RAPID_FIRE_THRESHOLD:
        return True, True
    
    user_cooldowns[user_id] = now
    return False, False


def needs_fallback(response: str) -> bool:
    if len(response) > DEFAULT_MAX_RESPONSE_LENGTH:
        return True
    
    response_lower = response.lower()
    for phrase in CHARACTER_BREAK_PHRASES:
        if phrase in response_lower:
            return True
    
    return False


def clean_message(text: str, trigger_word: str) -> str:
    import re
    cleaned = re.sub(re.escape(trigger_word), '', text, flags=re.IGNORECASE).strip()
    return cleaned if cleaned else "Hello Tayne!"


async def query_agent_core(
    message: str,
    user_name: str,
    channel_id: str,
    user_id: str,
) -> str | None:
    """Query agent-core for Tayne response. Returns None if unavailable."""
    settings = get_settings()
    agent_core_url = settings.agent_core_url
    
    if not agent_core_url:
        logger.warning("AGENT_CORE_URL not configured")
        return None
    
    payload = {
        "message": message,
        "user": {
            "platform": "mattermost",
            "platform_user_id": user_id,
            "display_name": user_name,
        },
        "conversation_id": f"mattermost-{channel_id}",
        "context": {
            "channel_id": channel_id,
        },
    }
    
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{agent_core_url}/v1/agent/tayne/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response")
            else:
                logger.warning(f"Agent-core returned status {response.status_code}")
                return None
                
    except httpx.TimeoutException:
        logger.warning("Agent-core request timed out")
        return None
    except httpx.RequestError as e:
        logger.warning(f"Agent-core connection error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error querying agent-core: {e}")
        return None


async def query_local_ai_direct(
    message: str,
    user_name: str,
    channel_id: str,
    user_id: str,
) -> str | None:
    """Fallback: Query local-ai-router directly with Tayne persona."""
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
                
                if needs_fallback(response_text):
                    logger.info(f"Guardrail triggered, using fallback. Original: {response_text[:100]}...")
                    return random.choice(FALLBACK_QUOTES)
                
                return response_text
            else:
                logger.error(f"Local AI returned status {response.status_code}: {response.text}")
                return None
                
    except httpx.TimeoutException:
        logger.error("Local AI request timed out")
        return None
    except httpx.RequestError as e:
        logger.error(f"Local AI connection error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error querying Local AI: {e}")
        return None


async def query_tayne(
    message: str,
    user_name: str,
    channel_id: str,
    user_id: str,
) -> str | None:
    """Query Tayne via agent-core, with fallback to direct local-ai-router."""
    response = await query_agent_core(message, user_name, channel_id, user_id)
    if response:
        logger.info("Response from agent-core")
        return response
    
    logger.info("Agent-core unavailable, falling back to direct local-ai-router")
    return await query_local_ai_direct(message, user_name, channel_id, user_id)


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
    """Handle Mattermost outgoing webhook when @tayne is mentioned."""
    logger.info(f"Tayne mentioned by {user_name} in {channel_name}: {text[:50]}...")
    
    settings = get_settings()
    if settings.tayne_webhook_token and token != settings.tayne_webhook_token:
        logger.warning(f"Invalid webhook token from {user_name}")
        raise HTTPException(status_code=401, detail="Invalid webhook token")
    
    is_limited, is_rapid_fire = is_rate_limited(user_id)
    
    if is_limited:
        response_text = random.choice(RATE_LIMITED_RESPONSES)
        if is_rapid_fire:
            response_text = random.choice(FALLBACK_QUOTES)
        
        return {
            "text": response_text,
            "response_type": "comment",
        }
    
    cleaned_message = clean_message(text, trigger_word)
    
    response = await query_tayne(
        message=cleaned_message,
        user_name=user_name,
        channel_id=channel_id,
        user_id=user_id,
    )
    
    tayne_bot = get_bot("tayne")
    if tayne_bot and tayne_bot.is_configured():
        try:
            client = get_client(tayne_bot)
            response_text = response if response else API_DOWN_MESSAGE
            client.post_message(
                channel=channel_id,
                message=response_text,
                thread_id=post_id,
            )
            return {}
        except MattermostClientError as e:
            logger.error(f"Failed to post as Tayne: {e}")
            return {
                "text": response if response else API_DOWN_MESSAGE,
                "response_type": "comment",
            }
    else:
        logger.warning("Tayne bot not configured, using webhook response")
        return {
            "text": response if response else API_DOWN_MESSAGE,
            "response_type": "comment",
        }


@router.get("/webhook/tayne/health")
async def tayne_health() -> dict[str, Any]:
    """Health check for Tayne webhook including agent-core status."""
    settings = get_settings()
    
    agent_core_healthy = False
    if settings.agent_core_url:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{settings.agent_core_url}/v1/health")
                agent_core_healthy = response.status_code == 200
        except Exception:
            pass
    
    local_ai_healthy = False
    if settings.local_ai_url:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{settings.local_ai_url}/health")
                local_ai_healthy = response.status_code == 200
        except Exception:
            pass
    
    tayne_bot = get_bot("tayne")
    tayne_configured = tayne_bot is not None and tayne_bot.is_configured()
    
    all_healthy = agent_core_healthy and tayne_configured
    degraded = (not agent_core_healthy and local_ai_healthy) and tayne_configured
    
    if all_healthy:
        status = "healthy"
    elif degraded:
        status = "degraded"
    else:
        status = "unhealthy"
    
    return {
        "status": status,
        "agent_core": "connected" if agent_core_healthy else "disconnected",
        "local_ai_router": "connected" if local_ai_healthy else "disconnected",
        "tayne_bot_configured": tayne_configured,
        "agent_core_url": settings.agent_core_url or "not configured",
        "local_ai_url": settings.local_ai_url or "not configured",
    }
