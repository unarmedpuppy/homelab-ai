"""Local AI Router - Intelligent routing to multiple LLM backends."""
import os
import json
import logging
import httpx
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import asyncio

from agent import AgentRequest, AgentResponse, run_agent_loop, AGENT_TOOLS
from auth import ApiKey, validate_api_key_header, get_request_priority
from dependencies import get_request_tracker, log_chat_completion, RequestTracker
from memory import generate_conversation_id
from providers import ProviderManager, HealthChecker, ProviderSelection
from stream import stream_chat_completion, stream_chat_completion_passthrough, StreamAccumulator
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
        "https://local-ai-dashboard.server.unarmedpuppy.com",
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",   # Common dev port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration from environment
GAMING_PC_URL = os.getenv("GAMING_PC_URL", "http://192.168.86.63:8000")
LOCAL_3070_URL = os.getenv("LOCAL_3070_URL", "http://local-ai-server:8001")
OPENCODE_URL = os.getenv("OPENCODE_URL", "http://opencode-service:8002")

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
        "available": False,  # Not set up yet
    },
    "3090": {
        "url": GAMING_PC_URL,
        "name": "Gaming PC (3090)",
        "available": True,
    },
    "opencode-glm": {
        "url": OPENCODE_URL,
        "name": "OpenCode (GLM-4.7)",
        "available": False,  # Not set up yet
    },
    "opencode-claude": {
        "url": OPENCODE_URL,
        "name": "OpenCode (Claude)",
        "available": False,  # Not set up yet
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

    Supports multiple selection modes:
    1. Auto routing: {"model": "auto"}
    2. Explicit provider: {"provider": "server-3070"}
    3. Explicit provider + model: {"provider": "server-3070", "modelId": "qwen2.5-7b"}
    4. Shorthand: {"model": "server-3070/qwen2.5-14b"}

    Args:
        request: FastAPI Request object
        body: Request body dict
        priority: Request priority (0=high, 1=normal, 2=low). Used for routing decisions.

    Returns:
        ProviderSelection with provider and model information
    """
    if not provider_manager:
        raise HTTPException(status_code=503, detail="Provider manager not initialized")

    # Extract selection parameters
    requested_model = body.get("model", "auto")
    requested_provider = body.get("provider")  # Explicit provider ID
    requested_model_id = body.get("modelId")   # Explicit model ID

    # Parse shorthand notation: "provider/model"
    if "/" in requested_model:
        parts = requested_model.split("/", 1)
        requested_provider = parts[0]
        requested_model_id = parts[1]
        requested_model = "auto"  # Override since we have explicit provider/model

    # Handle model aliases (maintain backward compatibility)
    if requested_model in MODEL_ALIASES:
        # Resolve old alias to model ID
        alias_target = MODEL_ALIASES[requested_model]
        # Map old backend IDs to model IDs
        if alias_target == "3090":
            requested_model = "qwen2.5-14b-awq"  # Default 3090 model
        elif alias_target == "3070":
            requested_model = "llama3-8b"  # Default 3070 model
        elif alias_target == "opencode-glm":
            requested_model = "glm-4-flash"
        elif alias_target == "opencode-claude":
            requested_model = "claude-3-5-haiku"
    # For "auto", "small", "fast", "medium", "big", pass through as-is
    # The ProviderManager will handle them

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
            "agent": "/v1/agent/chat",
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

    return HealthResponse(
        status="healthy" if any(s["healthy"] for s in backend_status.values()) else "degraded",
        backends=backend_status,
        gaming_mode=gaming_status.gaming_mode if gaming_status else None,
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

        providers_info.append({
            "id": provider.id,
            "name": provider.name,
            "type": provider.type.value,
            "description": provider.description,
            "endpoint": provider.endpoint,
            "priority": provider.priority,
            "enabled": provider.enabled,
            "health": {
                "is_healthy": provider.is_healthy,
                "consecutive_failures": provider.consecutive_failures,
                "last_check": health_info,
            },
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

    # Build endpoint URL
    endpoint_url = f"{selection.provider.endpoint.rstrip('/')}/v1/chat/completions"

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
                        }
                    log_chat_completion(tracker, body, response_data, error=None)
                    logger.info(f"Logged streaming response (conversation: {tracker.conversation_id})")
                except Exception as e:
                    logger.error(f"Failed to log streaming completion: {e}")

            background_tasks.add_task(log_stream_completion)

            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream",
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
                    )
                    response_data = response.json()

                    # Inject provider info into response
                    # This allows clients to see which provider was used
                    response_data["provider"] = selection.provider.id

                    # Log metrics and memory in background
                    background_tasks.add_task(
                        log_chat_completion,
                        tracker,
                        body,
                        response_data,
                        error=None
                    )

                    return response_data

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
    """Call the LLM through the router for agent use."""
    body = {
        "model": model,
        "messages": messages,
        "tools": tools or [],
        "tool_choice": tool_choice,
    }

    # Route to appropriate backend
    # For agent calls, we always use the 3090 with tool support
    backend = BACKENDS["3090"]
    if not backend["available"]:
        raise HTTPException(status_code=503, detail="No backend available for agent")

    # Determine actual model - prefer qwen for tool calling
    if model in ["auto", "small", "fast", "big", "3090"]:
        body["model"] = "qwen2.5-14b-awq"

    logger.info(f"Agent LLM call: model={body['model']}, messages={len(messages)}")

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

        return response.json()


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
