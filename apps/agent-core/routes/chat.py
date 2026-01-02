"""
Chat endpoints for agent interactions.

POST /v1/agent/{agent_id}/chat - Chat with a specific agent
GET /v1/agents - List available agents
"""

import logging
from typing import Any, Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..agents import get_agent, list_agents
from ..config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


class UserInfo(BaseModel):
    """User information from the calling platform."""
    platform: str  # discord, mattermost, telegram, etc.
    platform_user_id: str
    display_name: Optional[str] = None


class ChatContext(BaseModel):
    """Optional context for the conversation."""
    channel_name: Optional[str] = None
    history: Optional[list[dict]] = None


class ChatRequest(BaseModel):
    """Chat request payload."""
    message: str
    user: UserInfo
    conversation_id: Optional[str] = None
    context: Optional[ChatContext] = None


class ChatResponse(BaseModel):
    """Chat response payload."""
    response: str
    agent: str
    conversation_id: Optional[str] = None
    tools_used: list[str] = []


@router.get("/v1/agents")
async def get_agents() -> dict[str, Any]:
    """List all available agents."""
    return {"agents": list_agents()}


@router.post("/v1/agent/{agent_id}/chat")
async def chat_with_agent(
    agent_id: str,
    request: ChatRequest,
) -> ChatResponse:
    """
    Chat with a specific agent.
    
    The agent processes the message using its persona and returns
    a response. Routes to local-ai-router for LLM inference.
    """
    # Get agent
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_id}' not found. Available: {[a['id'] for a in list_agents()]}"
        )
    
    settings = get_settings()
    
    if not settings.local_ai_url:
        logger.error("LOCAL_AI_URL not configured")
        # Return fallback for Tayne, generic error for others
        if hasattr(agent, 'get_api_down_message'):
            return ChatResponse(
                response=agent.get_api_down_message(),
                agent=agent_id,
                conversation_id=request.conversation_id,
            )
        raise HTTPException(status_code=503, detail="LLM backend not configured")
    
    # Build conversation ID
    conversation_id = request.conversation_id
    if not conversation_id:
        conversation_id = f"{request.user.platform}-{agent_id}-default"
    
    # Build messages array
    messages = [{"role": "system", "content": agent.system_prompt}]
    
    # Add history if provided
    if request.context and request.context.history:
        messages.extend(request.context.history)
    
    # Add user message with display name for context
    user_prefix = request.user.display_name or request.user.platform_user_id
    messages.append({"role": "user", "content": f"{user_prefix}: {request.message}"})
    
    # Build LLM request
    payload = {
        "model": agent.model,
        "messages": messages,
        "max_tokens": agent.max_tokens,
        "temperature": agent.temperature,
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Enable-Memory": "true",
        "X-Conversation-ID": conversation_id,
        "X-Project": f"agent-core-{agent_id}",
        "X-User-ID": f"{request.user.platform}:{request.user.platform_user_id}",
    }
    
    if settings.local_ai_api_key:
        headers["Authorization"] = f"Bearer {settings.local_ai_api_key}"
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{settings.local_ai_url}/v1/chat/completions",
                json=payload,
                headers=headers,
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data["choices"][0]["message"]["content"]
                
                # Check guardrails (if agent supports it)
                if hasattr(agent, 'needs_fallback') and agent.needs_fallback(response_text):
                    logger.info(f"Guardrail triggered for {agent_id}, using fallback")
                    response_text = agent.get_fallback_response()
                
                return ChatResponse(
                    response=response_text,
                    agent=agent_id,
                    conversation_id=conversation_id,
                )
            else:
                logger.error(f"LLM API returned {response.status_code}: {response.text}")
                if hasattr(agent, 'get_api_down_message'):
                    return ChatResponse(
                        response=agent.get_api_down_message(),
                        agent=agent_id,
                        conversation_id=conversation_id,
                    )
                raise HTTPException(status_code=502, detail="LLM backend error")
                
    except httpx.TimeoutException:
        logger.error("LLM API request timed out")
        if hasattr(agent, 'get_api_down_message'):
            return ChatResponse(
                response=agent.get_api_down_message(),
                agent=agent_id,
                conversation_id=conversation_id,
            )
        raise HTTPException(status_code=504, detail="LLM backend timeout")
        
    except httpx.RequestError as e:
        logger.error(f"LLM API connection error: {e}")
        if hasattr(agent, 'get_api_down_message'):
            return ChatResponse(
                response=agent.get_api_down_message(),
                agent=agent_id,
                conversation_id=conversation_id,
            )
        raise HTTPException(status_code=503, detail="LLM backend unavailable")
