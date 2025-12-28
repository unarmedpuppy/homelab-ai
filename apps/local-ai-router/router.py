"""Local AI Router - Intelligent routing to multiple LLM backends."""
import os
import logging
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import asyncio

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Local AI Router",
    description="OpenAI-compatible API router for multi-backend LLM inference",
    version="1.0.0"
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


async def route_request(request: Request, body: dict) -> str:
    """Determine which backend to route to."""
    model = body.get("model", "auto")

    # Resolve alias
    if model in MODEL_ALIASES:
        model = MODEL_ALIASES[model]

    # 1. Explicit model request
    if model in BACKENDS:
        backend = BACKENDS[model]
        if backend["available"]:
            logger.info(f"Routing to {model} (explicit request)")
            return model
        else:
            logger.warning(f"Backend {model} not available, falling back")

    # 2. Check gaming mode
    gaming_status = await get_gaming_pc_status()
    gaming_mode_on = gaming_status.gaming_mode if gaming_status else False

    # If gaming mode is on, only route to 3090 with force-big signal
    if gaming_mode_on:
        if has_force_big_signal(request, body):
            logger.info("Force-big signal detected, routing to 3090 despite gaming mode")
            return "3090"

        # Prefer 3070 when gaming
        if BACKENDS["3070"]["available"]:
            logger.info("Gaming mode on, routing to 3070")
            return "3070"

        # No 3070 available, check if 3090 is still healthy
        if await check_backend_health("3090"):
            logger.info("Gaming mode on but 3070 unavailable, using 3090")
            return "3090"

    # 3. Token-based routing
    messages = body.get("messages", [])
    estimated_tokens = estimate_tokens(messages)
    logger.info(f"Estimated tokens: {estimated_tokens}")

    # Small requests → 3070 (if available)
    if estimated_tokens < SMALL_TOKEN_THRESHOLD:
        if BACKENDS["3070"]["available"]:
            logger.info("Small request, routing to 3070")
            return "3070"

    # Medium requests → 3090
    if estimated_tokens < MEDIUM_TOKEN_THRESHOLD:
        if await check_backend_health("3090"):
            logger.info("Medium request, routing to 3090")
            return "3090"

    # Large/complex → OpenCode (when available)
    if estimated_tokens >= MEDIUM_TOKEN_THRESHOLD:
        if BACKENDS["opencode-glm"]["available"]:
            logger.info("Large request, routing to OpenCode")
            return "opencode-glm"

    # 4. Fallback chain
    for backend_id in ["3090", "3070", "opencode-glm"]:
        if BACKENDS[backend_id]["available"] and await check_backend_health(backend_id):
            logger.info(f"Fallback to {backend_id}")
            return backend_id

    raise HTTPException(status_code=503, detail="No healthy backends available")


@app.get("/health")
async def health_check() -> HealthResponse:
    """Health check with backend status."""
    backend_status = {}

    for backend_id, backend in BACKENDS.items():
        if backend["available"]:
            backend_status[backend_id] = {
                "name": backend["name"],
                "healthy": await check_backend_health(backend_id),
            }
        else:
            backend_status[backend_id] = {
                "name": backend["name"],
                "healthy": False,
                "reason": "not configured",
            }

    gaming_status = await get_gaming_pc_status()

    return HealthResponse(
        status="healthy",
        backends=backend_status,
        gaming_mode=gaming_status.gaming_mode if gaming_status else None,
    )


@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI-compatible)."""
    models = []

    # Add available backend models
    if BACKENDS["3090"]["available"]:
        models.extend([
            {"id": "llama3-8b", "object": "model", "owned_by": "local"},
            {"id": "qwen2.5-14b-awq", "object": "model", "owned_by": "local"},
            {"id": "deepseek-coder", "object": "model", "owned_by": "local"},
        ])

    # Add routing aliases
    models.extend([
        {"id": "auto", "object": "model", "owned_by": "router"},
        {"id": "small", "object": "model", "owned_by": "router"},
        {"id": "fast", "object": "model", "owned_by": "router"},
        {"id": "big", "object": "model", "owned_by": "router"},
    ])

    return {"object": "list", "data": models}


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """OpenAI-compatible chat completions with intelligent routing."""
    body = await request.json()

    # Determine routing
    backend_id = await route_request(request, body)
    backend = BACKENDS[backend_id]

    # Get the actual model to use from request, or default
    requested_model = body.get("model", "auto")

    # For 3090, map to actual model names
    if backend_id == "3090":
        if requested_model in ["auto", "small", "fast", "big", "3090", "gaming-pc"]:
            # Use qwen for coding/complex tasks, llama for general
            messages = body.get("messages", [])
            content = " ".join(
                str(m.get("content", ""))
                for m in messages
                if isinstance(m, dict)
            ).lower()

            # Simple heuristic: coding keywords → deepseek-coder
            coding_keywords = ["code", "function", "class", "debug", "fix", "implement", "refactor"]
            if any(kw in content for kw in coding_keywords):
                body["model"] = "deepseek-coder"
            else:
                body["model"] = "qwen2.5-14b-awq"

    logger.info(f"Routing to {backend['name']} with model {body.get('model')}")

    # Determine if streaming
    stream = body.get("stream", False)

    # Model cold starts can take 2-3 minutes, use 5 min timeout
    async with httpx.AsyncClient(timeout=300.0) as client:
        if stream:
            # Stream the response
            async def stream_response():
                async with client.stream(
                    "POST",
                    f"{backend['url']}/v1/chat/completions",
                    json=body,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    async for chunk in response.aiter_bytes():
                        yield chunk

            return StreamingResponse(
                stream_response(),
                media_type="text/event-stream",
            )
        else:
            # Non-streaming response
            response = await client.post(
                f"{backend['url']}/v1/chat/completions",
                json=body,
            )
            return response.json()


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
