"""Local AI Router - Intelligent routing to multiple LLM backends."""
import os
import json
import logging
import httpx
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse, Response
from pydantic import BaseModel
from typing import Optional
import asyncio

from agent import AgentRequest, AgentResponse, run_agent_loop, AGENT_TOOLS
from auth import ApiKey, validate_api_key_header, get_request_priority
from dependencies import get_request_tracker, log_chat_completion, RequestTracker
from memory import generate_conversation_id
from providers import ProviderManager, HealthChecker, ProviderSelection, build_chat_completions_url, build_request_headers
from stream import stream_chat_completion, stream_chat_completion_passthrough, StreamAccumulator
import prometheus_metrics as prom
# from middleware import MemoryMetricsMiddleware  # Replaced with dependency injection

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Global provider manager and health checker
provider_manager: Optional[ProviderManager] = None
health_checker: Optional[HealthChecker] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources on app startup/shutdown."""
    global provider_manager, health_checker

    # Startup: Initialize ProviderManager and HealthChecker
    config_path = Path(__file__).parent / "config" / "providers.yaml"
    logger.info(f"Loading provider configuration from: {config_path}")

    try:
        provider_manager = ProviderManager(config_path=str(config_path))
        logger.info(f"Loaded {len(provider_manager.providers)} providers, "
                   f"{len(provider_manager.get_all_models())} models")

        # Start health checker
        health_checker = HealthChecker(provider_manager, check_interval=30)
        await health_checker.start()
        logger.info("Health checker started")

        # Initialize Prometheus router info
        prom.init_router_info(version="1.0.0")
        logger.info("Prometheus metrics initialized")

    except Exception as e:
        logger.error(f"Failed to initialize providers: {e}")
        raise

    yield

    # Shutdown: Stop health checker
    if health_checker:
        await health_checker.stop()
        logger.info("Health checker stopped")


app = FastAPI(
    title="Local AI Router",
    description="OpenAI-compatible API router for multi-backend LLM inference",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://homelab-ai.server.unarmedpuppy.com",
        "https://local-ai-dashboard.server.unarmedpuppy.com",  # Legacy alias
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",   # Common dev port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration from environment
GAMING_PC_URL = os.getenv("GAMING_PC_URL", "http://gaming-pc.local:8000")
LOCAL_3070_URL = os.getenv("LOCAL_3070_URL", "http://llm-manager:8000")
OPENCODE_URL = os.getenv("OPENCODE_URL", "http://opencode-service:8002")
TTS_ENDPOINT = os.getenv("TTS_ENDPOINT", GAMING_PC_URL)  # TTS runs on Gaming PC

SMALL_TOKEN_THRESHOLD = int(os.getenv("SMALL_TOKEN_THRESHOLD", "2000"))
MEDIUM_TOKEN_THRESHOLD = int(os.getenv("MEDIUM_TOKEN_THRESHOLD", "16000"))

# Model aliases for routing
MODEL_ALIASES = {
    "small": "3070",
    "fast": "3070",
    "medium": "3090",
    "big": "3090",
    "gaming-pc": "3090",
    "glm": "opencode-glm",
    "claude": "opencode-claude",
}

# Backend configurations
BACKENDS = {
    "3070": {
        "url": LOCAL_3070_URL,
        "name": "Home Server (3070)",
        "available": True,
    },
    "3090": {
        "url": GAMING_PC_URL,
        "name": "Gaming PC (3090)",
        "available": True,
    },
    "opencode-glm": {
        "url": OPENCODE_URL,
        "name": "OpenCode (GLM-4.7)",
        "available": False,
    },
    "opencode-claude": {
        "url": OPENCODE_URL,
        "name": "OpenCode (Claude)",
        "available": False,
    },
}


class GamingModeStatus(BaseModel):
    """Gaming mode status from Windows PC."""
    gaming_mode: bool
    safe_to_game: bool
    running_models: list
    stopped_models: list


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    backends: dict
    gaming_mode: Optional[bool] = None


class ClaudeAgentRequest(BaseModel):
    """Request for Claude agent - simple passthrough to Claude Harness."""
    task: str
    working_directory: str = "/tmp"
    timeout: float = 300.0  # 5 minutes default


class ClaudeAgentResponse(BaseModel):
    """Response from Claude agent."""
    success: bool
    response: str
    error: Optional[str] = None


async def get_gaming_pc_status() -> Optional[GamingModeStatus]:
    """Check gaming PC status and gaming mode."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{GAMING_PC_URL}/status")
            if response.status_code == 200:
                data = response.json()
                return GamingModeStatus(**data)
    except Exception as e:
        logger.warning(f"Failed to get gaming PC status: {e}")
    return None


async def check_backend_health(backend_id: str) -> bool:
    """Check if a backend is healthy."""
    backend = BACKENDS.get(backend_id)
    if not backend or not backend["available"]:
        return False

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Try OpenAI-compatible health endpoint
            response = await client.get(f"{backend['url']}/health")
            if response.status_code == 200:
                return True
            # Try status endpoint (gaming PC uses this)
            response = await client.get(f"{backend['url']}/status")
            return response.status_code == 200
    except Exception:
        return False


def estimate_tokens(messages: list) -> int:
    """Rough token estimation (4 chars per token)."""
    total_chars = sum(
        len(m.get("content", "") or "")
        for m in messages
        if isinstance(m, dict)
    )
    return total_chars // 4


def has_force_big_signal(request: Request, body: dict) -> bool:
    """Check if request has force-big override."""
    # Header check
    if request.headers.get("X-Force-Big", "").lower() == "true":
        return True

    # Model name check
    model = body.get("model", "")
    if model in ["big", "3090", "gaming-pc"]:
        return True

    # Prompt tag check
    messages = body.get("messages", [])
    for msg in messages:
        if isinstance(msg, dict):
            content = msg.get("content", "") or ""
            if "#force_big" in content:
                return True

    return False


async def route_request(request: Request, body: dict, priority: int = 1) -> ProviderSelection:
    """
    Determine which provider and model to route to using ProviderManager.

    Routing priority:
    1. Explicit model/provider requests are honored directly
    2. Force-big signals escalate to 3090
    3. Token count > 2000 escalates to 3090 (3070 has 2K context limit)
    4. Default: route to 3070 (always-on, lower power)
    """
    if not provider_manager:
        raise HTTPException(status_code=503, detail="Provider manager not initialized")

    requested_model = body.get("model", "auto")
    requested_provider = body.get("provider")
    requested_model_id = body.get("modelId")

    if "/" in requested_model:
        parts = requested_model.split("/", 1)
        requested_provider = parts[0]
        requested_model_id = parts[1]
        requested_model = "auto"

    if requested_model in MODEL_ALIASES:
        alias_target = MODEL_ALIASES[requested_model]
        if alias_target == "3090":
            requested_model = "qwen2.5-14b-awq"
        elif alias_target == "3070":
            requested_model = "qwen2.5-7b-awq"
        elif alias_target == "opencode-glm":
            requested_model = "glm-4-flash"
        elif alias_target == "opencode-claude":
            requested_model = "claude-3-5-haiku"

    # Token-based escalation for "auto" requests
    if requested_model == "auto" and not requested_provider:
        token_estimate = estimate_tokens(body.get("messages", []))
        force_big = has_force_big_signal(request, body)
        
        if force_big or token_estimate > SMALL_TOKEN_THRESHOLD:
            requested_model = "qwen2.5-14b-awq"
            logger.info(f"Escalating to 3090: force_big={force_big}, tokens={token_estimate}")
        else:
            requested_model = "qwen2.5-7b-awq"
            logger.info(f"Using 3070 (default): tokens={token_estimate}")

    try:
        # Select provider using ProviderManager (it's async)
        selection = await provider_manager.select_provider_and_model(
            requested_model,
            provider_id=requested_provider,
            model_id=requested_model_id
        )

        if not selection:
            raise HTTPException(
                status_code=503,
                detail=f"No healthy provider available for model '{requested_model}'"
            )

        logger.info(
            f"Routed to provider '{selection.provider.name}' "
            f"with model '{selection.model.name}' "
            f"(requested: model='{requested_model}', provider='{requested_provider}', modelId='{requested_model_id}')"
        )

        return selection

    except Exception as e:
        logger.error(f"Routing error: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to route request: {str(e)}"
        )


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "Local AI Router",
        "version": "1.0.0",
        "description": "OpenAI-compatible API router for multi-backend LLM inference",
        "endpoints": {
            "health": "/health",
            "chat": "/v1/chat/completions",
            "tts": "/v1/audio/speech",
            "agent_local": "/agent/run",
            "agent_claude": "/agent/run/claude",
            "agent_tools": "/agent/tools",
            "providers": "/providers",
            "models": "/v1/models",
            "admin": "/admin/providers",
            "memory": "/memory/*",
            "metrics": "/metrics/*",
            "rag": "/rag/*",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check() -> HealthResponse:
    """Health check with provider status."""
    if not provider_manager:
        return HealthResponse(
            status="unhealthy",
            backends={"error": {"healthy": False, "reason": "Provider manager not initialized"}},
        )

    backend_status = {}

    # Get status from all providers
    provider_statuses = provider_manager.get_provider_status()
    for provider_id, status in provider_statuses.items():
        backend_status[provider_id] = {
            "name": status["name"],
            "healthy": status["healthy"],
            "enabled": status["enabled"],
            "current_requests": status["current_requests"],
            "max_concurrent": status["max_concurrent"],
        }

    # Check gaming mode (legacy compatibility)
    gaming_status = await get_gaming_pc_status()

    # Update Prometheus metrics for providers
    for provider_id, status in provider_statuses.items():
        prom.update_provider_metrics(
            provider_id=provider_id,
            is_healthy=status["healthy"],
            active_requests=status["current_requests"],
            max_concurrent=status["max_concurrent"],
            consecutive_failures=status.get("consecutive_failures", 0),
        )

    return HealthResponse(
        status="healthy" if any(s["healthy"] for s in backend_status.values()) else "degraded",
        backends=backend_status,
        gaming_mode=gaming_status.gaming_mode if gaming_status else None,
    )


@app.get("/metrics")
async def prometheus_metrics():
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus text format for scraping.
    """
    from fastapi.responses import Response
    
    # Update memory metrics
    try:
        from memory import get_conversation_stats
        stats = get_conversation_stats()
        prom.update_memory_metrics(
            conversations=stats.get("total_conversations", 0),
            messages=stats.get("total_messages", 0)
        )
    except Exception as e:
        logger.warning(f"Failed to update memory metrics: {e}")
    
    return Response(
        content=prom.get_metrics(),
        media_type=prom.get_content_type()
    )


@app.get("/providers")
async def get_providers():
    """
    List all configured providers with current health status.

    Returns basic provider information for API consumers.
    """
    from datetime import datetime

    if not provider_manager:
        raise HTTPException(status_code=503, detail="Provider manager not initialized")

    providers_list = []

    for provider in provider_manager.get_all_providers():
        providers_list.append({
            "id": provider.id,
            "name": provider.name,
            "type": provider.type.value,
            "status": "online" if provider.is_healthy else "offline",
            "priority": provider.priority,
            "gpu": provider.metadata.get("gpu") if provider.metadata else None,
            "location": provider.metadata.get("location") if provider.metadata else None,
            "lastHealthCheck": datetime.fromtimestamp(provider.last_health_check).isoformat() if provider.last_health_check else None,
        })

    return {"providers": providers_list}


@app.get("/admin/providers")
async def list_providers():
    """
    Admin endpoint: List all providers with detailed status and configuration.

    Returns comprehensive provider information including:
    - Provider metadata (name, type, endpoint, priority)
    - Current health status and consecutive failures
    - Load information (current requests vs max concurrent)
    - Available models for each provider
    - Health check history (if available)
    """
    if not provider_manager:
        raise HTTPException(status_code=503, detail="Provider manager not initialized")

    providers_info = []

    for provider in provider_manager.get_all_providers():
        # Get models for this provider
        provider_models = [
            {
                "id": model.id,
                "name": model.name,
                "context_window": model.context_window,
                "max_tokens": model.max_tokens,
                "is_default": model.is_default,
                "capabilities": {
                    "streaming": model.capabilities.streaming,
                    "function_calling": model.capabilities.function_calling,
                    "vision": model.capabilities.vision,
                    "json_mode": model.capabilities.json_mode,
                },
                "tags": model.tags,
            }
            for model in provider_manager.get_all_models()
            if model.provider_id == provider.id
        ]

        # Get health check result if available
        health_info = None
        if health_checker:
            health_status = health_checker.get_all_health_status()
            if provider.id in health_status:
                health_result = health_status[provider.id]
                from datetime import datetime
                health_info = {
                    "is_healthy": health_result.is_healthy,
                    "response_time_ms": health_result.response_time_ms,
                    "checked_at": datetime.fromtimestamp(health_result.timestamp).isoformat() if health_result.timestamp else None,
                    "error": health_result.error,
                }

        # Flatten health info to match dashboard's expected structure
        health_data = {
            "is_healthy": provider.is_healthy,
            "consecutive_failures": provider.consecutive_failures,
            "response_time_ms": health_info.get("response_time_ms") if health_info else None,
            "checked_at": health_info.get("checked_at") if health_info else None,
            "error": health_info.get("error") if health_info else None,
        }

        providers_info.append({
            "id": provider.id,
            "name": provider.name,
            "type": provider.type.value,
            "description": provider.description,
            "endpoint": provider.endpoint,
            "priority": provider.priority,
            "enabled": provider.enabled,
            "health": health_data,
            "load": {
                "current_requests": provider.current_requests,
                "max_concurrent": provider.max_concurrent,
                "utilization": round((provider.current_requests / provider.max_concurrent) * 100, 1) if provider.max_concurrent > 0 else 0,
            },
            "models": provider_models,
            "config": {
                "health_check_interval": provider.health_check_interval,
                "health_check_timeout": provider.health_check_timeout,
                "health_check_path": provider.health_check_path,
                "auth_type": provider.auth_type.value if provider.auth_type else None,
            },
            "metadata": provider.metadata,
        })

    return {
        "providers": providers_info,
        "total_providers": len(providers_info),
        "healthy_providers": sum(1 for p in providers_info if p["health"]["is_healthy"]),
    }


@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI-compatible)."""
    if not provider_manager:
        raise HTTPException(status_code=503, detail="Provider manager not initialized")

    models = []

    # Add all configured models
    for model in provider_manager.get_all_models():
        provider = provider_manager.get_provider(model.provider_id)
        models.append({
            "id": model.id,
            "object": "model",
            "owned_by": provider.type.value if provider else "unknown",
            "created": 0,  # Not tracked
            "provider": provider.name if provider else "unknown",
        })

    # Add routing aliases for backward compatibility
    models.extend([
        {"id": "auto", "object": "model", "owned_by": "router"},
        {"id": "small", "object": "model", "owned_by": "router"},
        {"id": "fast", "object": "model", "owned_by": "router"},
        {"id": "medium", "object": "model", "owned_by": "router"},
        {"id": "big", "object": "model", "owned_by": "router"},
    ])

    return {"object": "list", "data": models}


@app.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    background_tasks: BackgroundTasks,
    tracker: RequestTracker = Depends(get_request_tracker),
    api_key: ApiKey = Depends(validate_api_key_header)
):
    """OpenAI-compatible chat completions with intelligent routing."""
    body = await request.json()

    # Generate conversation ID early if memory is enabled but no ID provided
    # This ensures the streaming response includes the conversation_id in the 'done' event
    if tracker.enable_memory and not tracker.conversation_id:
        tracker.conversation_id = generate_conversation_id()
        logger.info(f"Generated conversation ID early for streaming: {tracker.conversation_id}")

    # Calculate request priority based on API key
    priority = get_request_priority(api_key)
    logger.info(f"Request from '{api_key.name}' (priority={priority})")

    # Route using ProviderManager
    selection = await route_request(request, body, priority=priority)

    # Update body with selected model ID
    body["model"] = selection.model.id

    # Convert image_refs to base64 vision format if present
    messages = body.get("messages", [])
    if messages_have_images(messages):
        if selection.model.capabilities.vision:
            body["messages"] = format_messages_for_vision(messages, IMAGE_DATA_DIR)
            logger.info(f"Formatted {len(messages)} messages for vision model")
        else:
            logger.warning(f"Model {selection.model.id} doesn't support vision, images will be ignored")

    # Build endpoint URL and request headers (handles cloud provider auth)
    endpoint_url = build_chat_completions_url(selection.provider)
    request_headers = build_request_headers(selection.provider)

    logger.info(
        f"Routing to {selection.provider.name} ({selection.provider.endpoint}) "
        f"with model {selection.model.id}"
    )

    async with provider_manager.track_request(selection.provider.id):
        stream = body.get("stream", False)

        if stream:
            enhanced_streaming = request.headers.get("X-Enhanced-Streaming", "").lower() == "true"
            accumulator = StreamAccumulator()
            passthrough_content = []

            if enhanced_streaming:
                async def stream_generator():
                    async for event_str in stream_chat_completion(selection, body, conversation_id=tracker.conversation_id):
                        yield event_str
                        if event_str.startswith('data: ') and event_str[6:].strip() != '[DONE]':
                            try:
                                event_data = json.loads(event_str[6:])
                                accumulator.add_chunk(event_data)
                            except json.JSONDecodeError:
                                pass
            else:
                async def stream_generator():
                    async for event_str in stream_chat_completion_passthrough(selection, body):
                        yield event_str
                        for line in event_str.split('\n'):
                            line = line.strip()
                            if line.startswith('data: ') and line[6:].strip() not in ('[DONE]', ''):
                                try:
                                    chunk = json.loads(line[6:])
                                    choices = chunk.get('choices', [])
                                    if choices and 'delta' in choices[0]:
                                        content = choices[0]['delta'].get('content', '')
                                        if content:
                                            passthrough_content.append(content)
                                except json.JSONDecodeError:
                                    pass

            async def log_stream_completion():
                try:
                    if enhanced_streaming:
                        response_data = accumulator.to_response_data(body)
                    else:
                        response_data = {
                            'id': 'stream-passthrough',
                            'object': 'chat.completion',
                            'model': selection.model.id,
                            'choices': [{
                                'index': 0,
                                'message': {'role': 'assistant', 'content': ''.join(passthrough_content)},
                                'finish_reason': 'stop',
                            }],
                            'provider': selection.provider.id,
                            'provider_name': selection.provider.name,
                        }
                    
                    if provider_manager:
                        usage = response_data.get("usage", {})
                        response_data["cost_usd"] = provider_manager.calculate_cost(
                            provider_id=selection.provider.id,
                            model_id=selection.model.id,
                            duration_ms=tracker.get_duration_ms(),
                            total_tokens=usage.get("total_tokens"),
                        )
                    
                    log_chat_completion(tracker, body, response_data, error=None)
                    logger.info(f"Logged streaming response (conversation: {tracker.conversation_id})")
                except Exception as e:
                    logger.error(f"Failed to log streaming completion: {e}")

            background_tasks.add_task(log_stream_completion)

            # Build response headers
            response_headers = {}
            if tracker.conversation_id:
                response_headers["X-Conversation-ID"] = tracker.conversation_id

            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream",
                headers=response_headers,
            )
        else:
            async with httpx.AsyncClient(timeout=300.0) as client:
                # Non-streaming response
                error = None
                response_data = None

                try:
                    response = await client.post(
                        endpoint_url,
                        json=body,
                        headers=request_headers,
                    )
                    response_data = response.json()

                    response_data["provider"] = selection.provider.id
                    response_data["provider_name"] = selection.provider.name
                    
                    if provider_manager:
                        usage = response_data.get("usage", {})
                        response_data["cost_usd"] = provider_manager.calculate_cost(
                            provider_id=selection.provider.id,
                            model_id=selection.model.id,
                            duration_ms=tracker.get_duration_ms(),
                            total_tokens=usage.get("total_tokens"),
                        )

                    background_tasks.add_task(
                        log_chat_completion,
                        tracker,
                        body,
                        response_data,
                        error=None
                    )

                    # Return with conversation ID header for client tracking
                    response_headers = {}
                    if tracker.conversation_id:
                        response_headers["X-Conversation-ID"] = tracker.conversation_id

                    return JSONResponse(content=response_data, headers=response_headers)

                except Exception as e:
                    error = str(e)
                    logger.error(f"Chat completion error: {error}")

                    # Log error metric in background
                    background_tasks.add_task(
                        log_chat_completion,
                        tracker,
                        body,
                        response_data=None,
                        error=error
                    )

                    raise


@app.post("/gaming-mode")
async def toggle_gaming_mode(enable: bool = True):
    """Proxy gaming mode toggle to Windows PC."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{GAMING_PC_URL}/gaming-mode",
                json={"enable": enable},
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to toggle gaming mode: {e}")


@app.post("/stop-all")
async def stop_all_models():
    """Proxy stop-all to Windows PC."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{GAMING_PC_URL}/stop-all")
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to stop models: {e}")

# ============================================================================
# TTS (Text-to-Speech) Endpoint
# ============================================================================

class TTSSpeechRequest(BaseModel):
    """OpenAI-compatible TTS speech request."""
    model: str = "tts-1"
    input: str  # The text to synthesize
    voice: str = "alloy"  # Voice to use (alloy, echo, fable, onyx, nova, shimmer)
    response_format: str = "mp3"  # Format: mp3, opus, aac, flac, wav, pcm
    speed: float = 1.0  # Speed: 0.25 to 4.0

@app.post("/v1/audio/speech")
async def text_to_speech(
    request: Request,
    api_key: ApiKey = Depends(validate_api_key_header)
):
    """
    OpenAI-compatible text-to-speech endpoint.
    
    Proxies requests to Gaming PC manager which hosts Chatterbox TTS.
    Returns audio data with appropriate headers.
    
    Example:
        curl -X POST http://localhost:8012/v1/audio/speech \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer lai_xxx" \
            -d '{
                "model": "tts-1",
                "input": "Hello, this is a test.",
                "voice": "alloy",
                "response_format": "mp3"
            }' \
            --output speech.mp3
    """
    try:
        body = await request.json()
        
        # Validate required field
        if "input" not in body:
            raise HTTPException(status_code=400, detail="Missing required field: input")
        
        # Ensure model is set to our TTS model
        body["model"] = "chatterbox-turbo"
        
        logger.info(f"TTS request: input='{body['input'][:50]}...', voice={body.get('voice', 'alloy')}")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{TTS_ENDPOINT}/v1/audio/speech",
                json=body,
            )
            
            if response.status_code != 200:
                error_msg = f"TTS generation failed: {response.text}"
                logger.error(error_msg)
                raise HTTPException(status_code=response.status_code, detail=error_msg)
            
            # Return audio data with headers from upstream
            response_headers = {}
            
            # Copy relevant headers from TTS service
            for header in ["content-type", "content-length", "x-audio-duration", "x-generation-time"]:
                if header in response.headers:
                    response_headers[header] = response.headers[header]
            
            return Response(
                content=response.content,
                headers=response_headers,
                media_type=response.headers.get("content-type", "audio/mpeg")
            )
            
    except httpx.TimeoutException:
        error_msg = "TTS generation timed out"
        logger.error(error_msg)
        raise HTTPException(status_code=504, detail=error_msg)
    except httpx.ConnectError as e:
        error_msg = f"Cannot connect to TTS service: {e}"
        logger.error(error_msg)
        raise HTTPException(status_code=503, detail=error_msg)
    except Exception as e:
        error_msg = f"TTS generation failed: {e}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


# ============================================================================
# Image Upload Endpoints
# ============================================================================

IMAGE_DATA_DIR = Path(os.getenv("DATA_PATH", "/data")) / "images"
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_IMAGES_PER_MESSAGE = 5
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}


def format_messages_for_vision(messages: list, image_data_dir: Path) -> list:
    """
    Convert messages with image_refs to OpenAI vision format.
    
    Transforms messages like:
        {"role": "user", "content": "What's in this image?", "image_refs": [...]}
    
    Into vision format:
        {"role": "user", "content": [
            {"type": "text", "text": "What's in this image?"},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
        ]}
    """
    import base64
    
    formatted = []
    for msg in messages:
        if not isinstance(msg, dict):
            formatted.append(msg)
            continue
            
        image_refs = msg.get("image_refs", [])
        if not image_refs:
            formatted.append(msg)
            continue
        
        content_parts = []
        text_content = msg.get("content", "")
        if text_content:
            content_parts.append({"type": "text", "text": text_content})
        
        for ref in image_refs:
            try:
                filepath = image_data_dir.parent / ref.get("path", "")
                if not filepath.exists():
                    logger.warning(f"Image not found: {filepath}")
                    continue
                    
                with open(filepath, "rb") as f:
                    image_data = f.read()
                
                b64_data = base64.b64encode(image_data).decode("utf-8")
                mime_type = ref.get("mimeType", "image/png")
                
                content_parts.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{b64_data}"
                    }
                })
                logger.debug(f"Added image to message: {ref.get('filename', 'unknown')}")
            except Exception as e:
                logger.error(f"Failed to encode image {ref}: {e}")
        
        if content_parts:
            new_msg = {"role": msg.get("role", "user"), "content": content_parts}
            formatted.append(new_msg)
        else:
            formatted.append(msg)
    
    return formatted


def messages_have_images(messages: list) -> bool:
    """Check if any message contains image_refs."""
    for msg in messages:
        if isinstance(msg, dict) and msg.get("image_refs"):
            return True
    return False


@app.post("/v1/images/upload")
async def upload_image(
    conversation_id: str,
    message_id: str,
    file: UploadFile = File(...),
    api_key: ApiKey = Depends(validate_api_key_header),
):
    """Upload an image for a message (multimodal support)."""
    from PIL import Image
    import io

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )

    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Image too large. Max size: {MAX_IMAGE_SIZE // (1024*1024)}MB"
        )

    image_dir = IMAGE_DATA_DIR / conversation_id / message_id
    image_dir.mkdir(parents=True, exist_ok=True)

    existing_images = list(image_dir.glob("*"))
    if len(existing_images) >= MAX_IMAGES_PER_MESSAGE:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_IMAGES_PER_MESSAGE} images per message"
        )

    sequence = f"{len(existing_images) + 1:03d}"
    safe_filename = "".join(c for c in file.filename if c.isalnum() or c in "._-")
    filename = f"{sequence}_{safe_filename}"
    filepath = image_dir / filename

    with open(filepath, "wb") as f:
        f.write(content)

    try:
        with Image.open(io.BytesIO(content)) as img:
            width, height = img.size
    except Exception:
        width, height = 0, 0

    logger.info(f"Image uploaded: {filepath} ({len(content)} bytes, {width}x{height})")

    return {
        "filename": filename,
        "path": str(filepath.relative_to(IMAGE_DATA_DIR.parent)),
        "size": len(content),
        "mimeType": file.content_type,
        "width": width,
        "height": height,
    }


@app.get("/v1/images/{conversation_id}/{message_id}/{filename}")
async def get_image(
    conversation_id: str,
    message_id: str,
    filename: str,
    api_key: ApiKey = Depends(validate_api_key_header),
):
    """Retrieve an uploaded image."""
    filepath = IMAGE_DATA_DIR / conversation_id / message_id / filename

    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    if not filepath.is_relative_to(IMAGE_DATA_DIR):
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(filepath)


# ============================================================================
# Agent Endpoint - Host-Controlled Agent Loop
# ============================================================================

async def call_llm_for_agent(
    messages: list,
    model: str = "auto",
    tools: list = None,
    tool_choice: str = "auto"
) -> dict:
    """Call the LLM through the router for agent use.
    
    Uses context-aware routing based on token count:
    - < 2K tokens: 3070 with qwen2.5-7b-awq (fast, always-on)
    - 2K-8K tokens: 3090 with qwen2.5-14b-awq (larger context)
    - > 8K tokens: 3090 with warning (may overflow)
    
    Returns the response with additional _routing_info for tracking.
    """
    # Estimate tokens for context-aware routing
    token_estimate = estimate_tokens(messages)
    
    # Calculate max_tokens: ensure at least 512 tokens for response
    # Context windows: 3070 (qwen2.5-7b) = 8192, 3090 (qwen2.5-14b) = 8192
    context_window = 8192
    max_tokens = max(512, min(2048, context_window - token_estimate - 500))  # Reserve 500 for safety
    
    body = {
        "model": model,
        "messages": messages,
        "tools": tools or [],
        "tool_choice": tool_choice,
        "max_tokens": max_tokens,
    }
    
    # Agent calls ALWAYS use 3090 - tool definitions add ~2500-4000 tokens overhead
    # that isn't counted in the token estimate. The 3070's 2048 context is too small.
    # 
    # Token breakdown for agent calls:
    # - System prompt + user message: ~600-1500 tokens (estimated)
    # - 24 tool definitions: ~2500-4000 tokens (NOT in estimate!)
    # - Response: ~500-2000 tokens
    # Total: easily 4000-7000+ tokens - requires 3090's larger context
    backend_id = "3090"
    actual_model = "qwen2.5-14b-awq"
    
    if token_estimate > 6000:
        logger.warning(f"Agent context very large (~{token_estimate} tokens in messages + ~3000 tool tokens), may approach limit")

    # Check backend availability with fallback
    backend = BACKENDS.get(backend_id)
    if not backend or not backend["available"]:
        # Try 3070 as fallback, but warn that it will likely fail
        fallback = BACKENDS.get("3070")
        if fallback and fallback["available"]:
            logger.warning(f"3090 unavailable for agent call - falling back to 3070. This will likely fail due to context size!")
            backend_id = "3070"
            backend = fallback
            actual_model = "qwen2.5-7b-awq"
        else:
            raise HTTPException(status_code=503, detail="No backend available for agent (3090 required for tool-heavy agent calls)")

    body["model"] = actual_model
    logger.info(f"Agent LLM call: model={actual_model}, backend={backend_id}, tokens~{token_estimate}, messages={len(messages)}")

    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{backend['url']}/v1/chat/completions",
            json=body,
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Backend error: {response.text}"
            )

        result = response.json()
        # Add routing info for agent tracking
        result["_routing_info"] = {
            "model": actual_model,
            "backend": backend_id,
            "backend_name": backend["name"],
        }
        return result


@app.post("/agent/run", response_model=AgentResponse)
async def run_agent(request: AgentRequest):
    """
    Run an autonomous agent task.

    The agent follows OpenCode's host-controlled design:
    - Host owns loop control, step count, tool execution, error handling
    - Model emits exactly ONE action per turn (tool call OR response)
    - Host validates and re-prompts on malformed output
    - Provider-agnostic: can swap models without system rewrite

    Example:
        curl -X POST http://localhost:8000/agent/run \\
            -H "Content-Type: application/json" \\
            -d '{
                "task": "Create a hello world Python script in /tmp",
                "working_directory": "/tmp",
                "model": "auto",
                "max_steps": 20
            }'
    """
    logger.info(f"Agent task started: {request.task[:100]}...")

    try:
        result = await run_agent_loop(request, call_llm_for_agent)
        logger.info(f"Agent completed: success={result.success}, steps={result.total_steps}")
        return result
    except Exception as e:
        logger.error(f"Agent error: {e}")
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {e}")


@app.get("/agent/tools")
async def list_agent_tools():
    """List available agent tools and their schemas."""
    return {
        "tools": AGENT_TOOLS,
        "description": "Tools available to the agent for task completion"
    }


@app.post("/agent/run/claude", response_model=ClaudeAgentResponse)
async def run_claude_agent(request: ClaudeAgentRequest):
    """
    Run a task using Claude Code CLI (passthrough to Claude Harness).
    
    This is a simple passthrough to Claude Harness - Claude CLI handles all
    agent logic internally (tools, loop, context, etc.). Unlike /agent/run,
    which uses our custom agent loop with local models, this endpoint
    delegates everything to Claude.
    
    Example:
        curl -X POST http://localhost:8012/agent/run/claude \\
            -H "Content-Type: application/json" \\
            -d '{"task": "Analyze the codebase and suggest improvements"}'
    """
    logger.info(f"Claude agent task: {request.task[:100]}...")
    
    # Build prompt with working directory context
    prompt = request.task
    if request.working_directory != "/tmp":
        prompt = f"Working directory: {request.working_directory}\n\n{request.task}"
    
    try:
        # Simple passthrough to Claude Harness
        async with httpx.AsyncClient(timeout=request.timeout) as client:
            response = await client.post(
                "http://host.docker.internal:8013/v1/chat/completions",
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "model": "claude-sonnet",
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Claude Harness error: {response.status_code} - {response.text}")
                return ClaudeAgentResponse(
                    success=False,
                    response="",
                    error=f"Claude Harness error ({response.status_code}): {response.text[:500]}"
                )
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            logger.info(f"Claude agent completed successfully ({len(content)} chars)")
            return ClaudeAgentResponse(
                success=True,
                response=content
            )
            
    except httpx.TimeoutException:
        logger.error(f"Claude agent timeout after {request.timeout}s")
        return ClaudeAgentResponse(
            success=False,
            response="",
            error=f"Request timed out after {request.timeout} seconds"
        )
    except httpx.ConnectError as e:
        logger.error(f"Claude Harness connection error: {e}")
        return ClaudeAgentResponse(
            success=False,
            response="",
            error="Cannot connect to Claude Harness. Is the service running? (systemctl status claude-harness)"
        )
    except Exception as e:
        logger.error(f"Claude agent error: {e}")
        return ClaudeAgentResponse(
            success=False,
            response="",
            error=str(e)
        )


# ============================================================================
# Agent Runs API Endpoints
# ============================================================================

from agent_storage import list_agent_runs, get_agent_run, get_agent_runs_stats
from models import AgentRunRecord, AgentRunWithSteps, AgentRunsStats


@app.get("/agent/runs", response_model=list[AgentRunRecord])
async def api_list_agent_runs(
    status: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """List agent runs with optional filters."""
    return list_agent_runs(status=status, source=source, limit=limit, offset=offset)


@app.get("/agent/runs/stats", response_model=AgentRunsStats)
async def api_agent_runs_stats():
    """Get aggregated statistics for agent runs."""
    return get_agent_runs_stats()


@app.get("/agent/runs/{run_id}", response_model=AgentRunWithSteps)
async def api_get_agent_run(run_id: str):
    """Get a specific agent run with all its steps."""
    run = get_agent_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return run


# ============================================================================
# Memory API Endpoints
# ============================================================================

from memory import (
    list_conversations,
    get_conversation,
    create_conversation,
    delete_conversation,
    update_conversation,
    get_conversation_messages,
    search_conversations,
    get_conversation_stats,
)
from models import ConversationCreate, ConversationUpdate, SearchQuery


@app.get("/memory/conversations")
async def api_list_conversations(
    user_id: Optional[str] = None,
    project: Optional[str] = None,
    session_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """List conversations with optional filters."""
    return list_conversations(
        user_id=user_id,
        project=project,
        session_id=session_id,
        limit=limit,
        offset=offset,
    )


@app.get("/memory/conversations/{conversation_id}")
async def api_get_conversation(conversation_id: str):
    """Get a specific conversation with its messages."""
    conversation = get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = get_conversation_messages(conversation_id)
    return {
        "conversation": conversation,
        "messages": messages,
    }


@app.post("/memory/conversations")
async def api_create_conversation(conv: ConversationCreate):
    """Create a new conversation."""
    return create_conversation(conv)


@app.delete("/memory/conversations/{conversation_id}")
async def api_delete_conversation(conversation_id: str):
    """Delete a conversation and all its messages."""
    deleted = delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted", "conversation_id": conversation_id}


@app.patch("/memory/conversations/{conversation_id}")
async def api_update_conversation(conversation_id: str, update: ConversationUpdate):
    """Update conversation metadata (title, etc.)."""
    updated = update_conversation(conversation_id, update)
    if not updated:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return updated


@app.post("/memory/search")
async def api_search_conversations(query: SearchQuery):
    """Search conversations by content."""
    return search_conversations(query)


@app.get("/memory/stats")
async def api_conversation_stats():
    """Get overall conversation statistics."""
    return get_conversation_stats()


# ============================================================================
# Metrics API Endpoints
# ============================================================================

from metrics import (
    get_metrics,
    get_daily_activity,
    get_model_usage,
    get_provider_distribution,
    get_dashboard_stats,
    get_daily_stats,
)
from datetime import datetime as dt


@app.get("/metrics/recent")
async def api_get_recent_metrics(
    limit: int = 100,
    backend: Optional[str] = None,
    user_id: Optional[str] = None,
    project: Optional[str] = None,
):
    """Get recent metrics with optional filters."""
    return get_metrics(
        backend=backend,
        user_id=user_id,
        project=project,
        limit=limit,
    )


@app.get("/metrics/daily")
async def api_get_daily_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 365,
):
    """Get daily aggregated stats."""
    return get_daily_stats(
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )


@app.get("/metrics/activity")
async def api_get_activity_chart(days: int = 365):
    """Get GitHub-style activity chart data."""
    return {
        "days": days,
        "activity": get_daily_activity(days=days),
    }


@app.get("/metrics/models")
async def api_get_model_usage(days: Optional[int] = None):
    """Get model usage statistics."""
    return {
        "models": get_model_usage(days=days),
        "provider_distribution": get_provider_distribution(days=days),
    }


@app.get("/metrics/dashboard")
async def api_get_dashboard():
    """Get complete dashboard statistics (OpenCode Wrapped style)."""
    return get_dashboard_stats()


# ============================================================================
# RAG API Endpoints
# ============================================================================

from rag import (
    search_similar_conversations,
    get_relevant_context,
    inject_context_into_messages,
)


@app.post("/rag/search")
async def api_rag_search(
    query: str,
    limit: int = 5,
    similarity_threshold: float = 0.3,
    user_id: Optional[str] = None,
    project: Optional[str] = None,
):
    """
    Search for similar conversations using RAG.

    Returns conversation IDs and similarity scores.
    """
    results = search_similar_conversations(
        query=query,
        limit=limit,
        similarity_threshold=similarity_threshold,
        user_id=user_id,
        project=project,
    )

    return {
        "query": query,
        "results": [
            {"conversation_id": conv_id, "similarity_score": score}
            for conv_id, score in results
        ],
    }


@app.post("/rag/context")
async def api_rag_context(
    query: str,
    limit: int = 3,
    similarity_threshold: float = 0.3,
    user_id: Optional[str] = None,
    project: Optional[str] = None,
):
    """
    Get relevant conversation context for RAG.

    Returns formatted context snippets ready for injection.
    """
    context = get_relevant_context(
        query=query,
        limit=limit,
        similarity_threshold=similarity_threshold,
        user_id=user_id,
        project=project,
    )

    return {
        "query": query,
        "context": context,
    }


# ============================================================================
# Beads API Endpoints - Task Management for Dashboard
# ============================================================================

from beads_cli import (
    list_tasks as beads_list_tasks,
    get_ready_tasks as beads_get_ready_tasks,
    get_task as beads_get_task,
    claim_task as beads_claim_task,
    close_task as beads_close_task,
    create_task as beads_create_task,
    update_task as beads_update_task,
    get_labels as beads_get_labels,
    get_stats as beads_get_stats,
    sync_beads,
    compute_age_days,
    BeadsError,
)


class BeadsTaskCreate(BaseModel):
    """Request body for creating a new beads task."""
    title: str
    priority: int = 2  # 0=critical, 1=high, 2=medium, 3=low
    type: str = "task"  # task, bug, feature, epic, chore
    labels: list[str] = []  # Should include at least one repo:* label
    description: Optional[str] = None
    blocked_by: list[str] = []


class BeadsTaskUpdate(BaseModel):
    """Request body for updating a beads task."""
    status: Optional[str] = None  # open, in_progress, closed
    priority: Optional[int] = None
    labels_add: list[str] = []
    labels_remove: list[str] = []


@app.get("/beads/tasks")
async def api_beads_list_tasks(
    status: Optional[str] = None,
    label: Optional[str] = None,
    priority: Optional[int] = None,
    type: Optional[str] = None,
    ready: bool = False,
):
    """
    List beads tasks with optional filters.

    Query Parameters:
        status: Filter by status (open, in_progress, closed)
        label: Filter by label
        priority: Filter by priority (0-3)
        type: Filter by type (task, bug, feature, epic, chore)
        ready: If true, only return unblocked open tasks

    Returns:
        List of tasks with computed age_days field
    """
    try:
        if ready:
            tasks = await beads_get_ready_tasks(label=label)
        else:
            tasks = await beads_list_tasks(
                status=status,
                label=label,
                priority=priority,
                task_type=type,
            )

        # Add computed age_days to each task
        for task in tasks:
            created_at = task.get("created_at", "")
            if created_at:
                task["age_days"] = compute_age_days(created_at)
            else:
                task["age_days"] = 0

        return {
            "tasks": tasks,
            "total": len(tasks),
        }

    except BeadsError as e:
        logger.error(f"Beads list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/beads/tasks/{task_id}")
async def api_beads_get_task(task_id: str):
    """
    Get a specific beads task by ID.

    Path Parameters:
        task_id: The task ID

    Returns:
        Task details including age_days
    """
    try:
        task = await beads_get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # Add computed age_days
        created_at = task.get("created_at", "")
        if created_at:
            task["age_days"] = compute_age_days(created_at)
        else:
            task["age_days"] = 0

        return task

    except BeadsError as e:
        logger.error(f"Beads get error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/beads/tasks")
async def api_beads_create_task(task: BeadsTaskCreate):
    """
    Create a new beads task.

    Request Body:
        title: Task title (required)
        priority: Priority 0-3 (default: 2)
        type: Task type (default: task)
        labels: List of labels (should include repo:* label)
        description: Optional markdown description
        blocked_by: Optional list of blocking task IDs

    Returns:
        Created task
    """
    try:
        # Validate that at least one repo label is present
        repo_labels = [l for l in task.labels if l.startswith("repo:")]
        if not repo_labels:
            logger.warning(f"Creating task without repo label: {task.title}")

        created = await beads_create_task(
            title=task.title,
            priority=task.priority,
            task_type=task.type,
            labels=task.labels,
            description=task.description,
            blocked_by=task.blocked_by if task.blocked_by else None,
        )

        # Sync after creation
        await sync_beads()

        return created

    except BeadsError as e:
        logger.error(f"Beads create error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/beads/tasks/{task_id}")
async def api_beads_update_task(task_id: str, update: BeadsTaskUpdate):
    """
    Update an existing beads task.

    Path Parameters:
        task_id: The task ID

    Request Body:
        status: New status (open, in_progress, closed)
        priority: New priority (0-3)
        labels_add: Labels to add
        labels_remove: Labels to remove

    Returns:
        Updated task
    """
    try:
        updated = await beads_update_task(
            task_id=task_id,
            status=update.status,
            priority=update.priority,
            labels_add=update.labels_add if update.labels_add else None,
            labels_remove=update.labels_remove if update.labels_remove else None,
        )

        # Sync after update
        await sync_beads()

        return updated

    except BeadsError as e:
        logger.error(f"Beads update error: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/beads/stats")
async def api_beads_stats():
    """
    Get aggregated beads task statistics.

    Returns:
        Statistics including total, by status, by label, by priority, by type
    """
    try:
        stats = await beads_get_stats()
        return stats

    except BeadsError as e:
        logger.error(f"Beads stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/beads/labels")
async def api_beads_labels():
    """
    Get all unique labels used in beads tasks.

    Returns:
        List of labels with repo labels grouped first
    """
    try:
        labels = await beads_get_labels()

        # Separate repo labels from other labels
        repo_labels = sorted([l for l in labels if l.startswith("repo:")])
        other_labels = sorted([l for l in labels if not l.startswith("repo:")])

        return {
            "labels": labels,
            "repo_labels": repo_labels,
            "other_labels": other_labels,
        }

    except BeadsError as e:
        logger.error(f"Beads labels error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/beads/sync")
async def api_beads_sync():
    """
    Sync beads database (pull and push changes).

    Useful when multiple processes are modifying tasks.

    Returns:
        Sync status message
    """
    try:
        result = await sync_beads()
        return {"status": "ok", "message": result}

    except BeadsError as e:
        logger.error(f"Beads sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
