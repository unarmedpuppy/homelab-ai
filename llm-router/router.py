"""Local AI Router - Intelligent routing to multiple LLM backends."""
import os
import json
import logging
import time
import httpx
import tiktoken
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
from complexity import classify_request, ComplexityTier, TIER_MODEL_MAP
import prometheus_metrics as prom
from routers.docs import router as docs_router
# from middleware import MemoryMetricsMiddleware  # Replaced with dependency injection

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Global provider manager and health checker
provider_manager: Optional[ProviderManager] = None
health_checker: Optional[HealthChecker] = None

# Gaming PC status cache (updated by background poller, not per-request)
_gaming_cache: dict = {
    "status": None,
    "updated_at": 0.0,
    "consecutive_failures": 0,
}
_gaming_poller_task: Optional[asyncio.Task] = None


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

    # Start gaming PC status poller (outside try block — non-fatal if gaming PC is down)
    global _gaming_poller_task
    _gaming_poller_task = asyncio.create_task(_gaming_status_poller())

    yield

    # Shutdown: stop background tasks
    if _gaming_poller_task:
        _gaming_poller_task.cancel()
        try:
            await _gaming_poller_task
        except asyncio.CancelledError:
            pass

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

# Include sub-routers
app.include_router(docs_router, prefix="/docs", tags=["docs"])


# Configuration from environment
GAMING_PC_URL = os.getenv("GAMING_PC_URL", "http://gaming-pc.local:8000")
GAMING_PC_POLL_INTERVAL = int(os.getenv("GAMING_PC_POLL_INTERVAL", "30"))   # seconds
GAMING_PC_STALE_THRESHOLD = int(os.getenv("GAMING_PC_STALE_THRESHOLD", "180"))  # seconds (6 missed polls)
LOCAL_3070_URL = os.getenv("LOCAL_3070_URL", "http://llm-manager:8000")
OPENCODE_URL = os.getenv("OPENCODE_URL", "http://opencode-service:8002")
TTS_ENDPOINT = os.getenv("TTS_ENDPOINT", GAMING_PC_URL)  # TTS runs on Gaming PC

# Token thresholds for context-aware routing
SMALL_TOKEN_THRESHOLD = int(os.getenv("SMALL_TOKEN_THRESHOLD", "2000"))
MEDIUM_TOKEN_THRESHOLD = int(os.getenv("MEDIUM_TOKEN_THRESHOLD", "16000"))  # 3090 limit (32K context / 2)
LARGE_TOKEN_THRESHOLD = int(os.getenv("LARGE_TOKEN_THRESHOLD", "100000"))   # GLM-5 limit (205K context / 2)

# Tiktoken tokenizer (lazy loaded)
_tokenizer = None

def get_tokenizer():
    """Get or initialize tiktoken tokenizer (cl100k_base for GPT-4/Claude compatibility)."""
    global _tokenizer
    if _tokenizer is None:
        _tokenizer = tiktoken.get_encoding("cl100k_base")
    return _tokenizer

# Model aliases for routing
# NOTE: 3070 removed from auto-routing aliases - now manual only
MODEL_ALIASES = {
    "small": "3090",      # was 3070 - now routes to 3090
    "fast": "3090",       # was 3070 - now routes to 3090
    "medium": "3090",
    "big": "glm-5",       # was 3090 - now routes to GLM-5 for large context
    "large": "glm-5",
    "gaming-pc": "3090",
    "glm": "glm-5",       # updated to GLM-5
    "claude": "claude-sonnet",
    # Manual 3070 access (explicit only)
    "3070": "qwen2.5-7b-awq",
    "server": "qwen2.5-7b-awq",
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
    gaming_pc_reachable: Optional[bool] = None
    gaming_cache_age: Optional[float] = None


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
    """Return cached gaming PC status. Returns None if cache is stale or PC unreachable."""
    if _gaming_cache["updated_at"] == 0.0:
        return None  # never successfully polled
    age = time.time() - _gaming_cache["updated_at"]
    if age > GAMING_PC_STALE_THRESHOLD:
        return None  # cache too old — treat as unreachable, fall through to local GPUs
    return _gaming_cache["status"]


async def _poll_gaming_pc_status() -> None:
    """Fetch gaming PC status and update the cache. Called by background poller."""
    global _gaming_cache
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{GAMING_PC_URL}/status")
            if response.status_code == 200:
                _gaming_cache = {
                    "status": GamingModeStatus(**response.json()),
                    "updated_at": time.time(),
                    "consecutive_failures": 0,
                }
                return
    except Exception as e:
        failures = _gaming_cache["consecutive_failures"] + 1
        _gaming_cache["consecutive_failures"] = failures
        # Log warning on first failure, error every 10 after that to reduce noise
        if failures == 1:
            logger.warning(f"Gaming PC unreachable ({GAMING_PC_URL}): {e}")
        elif failures % 10 == 0:
            logger.error(f"Gaming PC still unreachable after {failures} poll attempts")


async def _gaming_status_poller() -> None:
    """Background task: keep gaming PC status cache fresh."""
    logger.info(f"Gaming PC status poller started (interval={GAMING_PC_POLL_INTERVAL}s, url={GAMING_PC_URL})")
    await _poll_gaming_pc_status()  # warm cache immediately on startup
    while True:
        await asyncio.sleep(GAMING_PC_POLL_INTERVAL)
        await _poll_gaming_pc_status()


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
    """Accurate token estimation using tiktoken (cl100k_base encoding)."""
    enc = get_tokenizer()
    total = 0
    for msg in messages:
        if isinstance(msg, dict):
            content = msg.get("content", "") or ""
            if isinstance(content, str):
                total += len(enc.encode(content))
            # Handle vision/multimodal content lists
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        total += len(enc.encode(part.get("text", "")))
    return total


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


async def route_request(request: Request, body: dict, priority: int = 1, api_key=None) -> ProviderSelection:
    """
    Determine which provider and model to route to using ProviderManager.

    Routing logic (2026-02-22 redesign with gaming mode + complexity classification):

    1. Explicit model/provider requests are ALWAYS honored (even in gaming mode)
    2. Gaming mode check determines local GPU availability
    3. When gaming mode OFF: use complexity classification for smart routing
    4. When gaming mode ON: skip local GPUs, use cloud only
    5. Fallback chain: 3090 → GLM-5 → Claude Sonnet
    """
    if not provider_manager:
        raise HTTPException(status_code=503, detail="Provider manager not initialized")

    requested_model = body.get("model", "auto")
    requested_provider = body.get("provider")
    requested_model_id = body.get("modelId")

    # Handle provider/model format: "provider/model"
    if "/" in requested_model:
        parts = requested_model.split("/", 1)
        requested_provider = parts[0]
        requested_model_id = parts[1]
        requested_model = "auto"

    # Resolve model aliases
    if requested_model in MODEL_ALIASES:
        alias_target = MODEL_ALIASES[requested_model]
        if alias_target == "3090":
            requested_model = "qwen2.5-14b-awq"
        elif alias_target == "qwen2.5-7b-awq":
            requested_model = "qwen2.5-7b-awq"
        elif alias_target == "glm-5":
            requested_model = "glm-5"
        elif alias_target == "claude-sonnet":
            requested_model = "claude-sonnet"

    # Auto routing logic
    is_auto = requested_model == "auto" and not requested_provider
    classification = None

    if is_auto:
        # Check gaming mode status first
        gaming_status = await get_gaming_pc_status()
        gaming_mode_on = gaming_status and gaming_status.gaming_mode

        # Token estimation for context-aware routing
        token_estimate = estimate_tokens(body.get("messages", []))

        if gaming_mode_on:
            # Gaming mode ON → skip local GPUs, use cloud only
            if token_estimate < LARGE_TOKEN_THRESHOLD:  # < 100K
                requested_model = "glm-5"
                logger.info(f"Gaming mode ON: routing to GLM-5 (cloud), tokens={token_estimate}")
            else:
                requested_model = "claude-sonnet"
                logger.info(f"Gaming mode ON: routing to Claude (very large context), tokens={token_estimate}")
        else:
            # Gaming mode OFF → use complexity classification
            classification = classify_request(request, body, api_key)
            requested_model = TIER_MODEL_MAP[classification.tier]
            primary_signal = classification.signals[0] if classification.signals else "default"
            logger.info(
                f"Classified: tier={classification.tier.name}, score={classification.score:.2f}, "
                f"signals={classification.signals}"
            )
            prom.record_complexity_classification(classification.tier.name, primary_signal)

            # Override for very large context (>16K → GLM-5, >100K → Claude)
            if token_estimate >= LARGE_TOKEN_THRESHOLD:
                requested_model = "claude-sonnet"
                logger.info(f"Context override: routing to Claude (tokens={token_estimate} > 100K)")
            elif token_estimate >= MEDIUM_TOKEN_THRESHOLD:
                requested_model = "glm-5"
                logger.info(f"Context override: routing to GLM-5 (tokens={token_estimate} > 16K)")

    try:
        # Select provider using ProviderManager (it's async)
        selection = await provider_manager.select_provider_and_model(
            requested_model,
            provider_id=requested_provider,
            model_id=requested_model_id
        )

        if not selection:
            raise ValueError(f"No healthy provider available for model '{requested_model}'")

        if classification:
            selection.complexity_tier = classification.tier.name.lower()
            selection.complexity_score = round(classification.score, 3)

        logger.info(
            f"Routed to provider '{selection.provider.name}' "
            f"with model '{selection.model.name}' "
            f"(requested: model='{requested_model}', provider='{requested_provider}', modelId='{requested_model_id}')"
        )

        return selection

    except (ValueError, Exception) as e:
        if not is_auto:
            logger.error(f"Routing error: {e}")
            raise HTTPException(status_code=503, detail=f"Failed to route request: {str(e)}")

        # Auto mode: try fallback chain (GLM-5 → Claude)
        logger.warning(f"Primary auto route failed ({e}), trying fallback chain...")
        fallback_chain = ["glm-5", "claude-sonnet"]
        for fallback_model in fallback_chain:
            try:
                selection = await provider_manager.select_provider_and_model(fallback_model)
                if selection:
                    logger.info(f"Fallback to {fallback_model} succeeded")
                    return selection
            except Exception:
                continue

        # All fallbacks failed - try any available provider
        all_providers = sorted(provider_manager.providers.values(), key=lambda p: p.priority)
        for provider in all_providers:
            if not provider.enabled or not provider.is_healthy:
                continue
            provider_models = [m for m in provider_manager.models.values() if m.provider_id == provider.id]
            default_model = next((m for m in provider_models if m.is_default), None) or (provider_models[0] if provider_models else None)
            if default_model:
                logger.info(f"Last resort fallback: routing to {provider.name} with {default_model.name}")
                return ProviderSelection(provider=provider, model=default_model, reason="last resort fallback")

        logger.error("Auto routing: no providers available after all fallbacks")
        raise HTTPException(status_code=503, detail="No healthy providers available")


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


@app.get("/services")
async def get_services():
    """Return homelab service definitions for dashboard and iOS app."""
    return {
        "services": [
            {"id": "plex", "name": "Movies & TV", "appName": "Plex", "url": "https://plex.server.unarmedpuppy.com", "category": "media", "icon": "film", "description": "Watch movies and TV shows"},
            {"id": "overseerr", "name": "Request Media", "appName": "Overseerr", "url": "https://overseerr.server.unarmedpuppy.com", "category": "media", "icon": "plus.circle", "description": "Request new movies and shows"},
            {"id": "mealie", "name": "Recipes", "appName": "Mealie", "url": "https://recipes.server.unarmedpuppy.com", "category": "home", "icon": "fork.knife", "description": "Meal planning and recipes"},
            {"id": "homeassistant", "name": "Smart Home", "appName": "Home Assistant", "url": "https://homeassistant.server.unarmedpuppy.com", "category": "home", "icon": "house", "description": "Lights, automations, and more"},
            {"id": "frigate", "name": "Security Cameras", "appName": "Frigate", "url": "https://frigate.server.unarmedpuppy.com", "category": "home", "icon": "video", "description": "Live feeds and motion detection"},
            {"id": "immich", "name": "Photos", "appName": "Immich", "url": "https://photos.server.unarmedpuppy.com", "category": "docs", "icon": "photo", "description": "Photo backup and browsing"},
            {"id": "paperless", "name": "Documents", "appName": "Paperless", "url": "https://paperless.server.unarmedpuppy.com", "category": "docs", "icon": "doc.text", "description": "Scanned document management"},
            {"id": "planka", "name": "Project Board", "appName": "Planka", "url": "https://planka.server.unarmedpuppy.com", "category": "productivity", "icon": "checklist", "description": "Kanban-style project management"},
            {"id": "vaultwarden", "name": "Passwords", "appName": "Vaultwarden", "url": "https://vaultwarden.server.unarmedpuppy.com", "category": "productivity", "icon": "lock.shield", "description": "Password manager"},
            {"id": "ai-chat", "name": "AI Chat", "appName": "homelab-ai", "url": "/chat", "category": "ai", "icon": "brain", "description": "Chat with AI models"},
        ],
        "categories": [
            {"id": "media", "name": "Media & Entertainment", "order": 1},
            {"id": "home", "name": "Home & Kitchen", "order": 2},
            {"id": "docs", "name": "Documents & Photos", "order": 3},
            {"id": "productivity", "name": "Productivity & Security", "order": 4},
            {"id": "ai", "name": "AI & Tools", "order": 5},
        ],
    }


# --- Push notification token storage ---
PUSH_TOKENS_FILE = Path(os.getenv("DATA_PATH", "/data")) / "push_tokens.json"


def _load_push_tokens() -> list[dict]:
    if PUSH_TOKENS_FILE.exists():
        try:
            return json.loads(PUSH_TOKENS_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _save_push_tokens(tokens: list[dict]):
    PUSH_TOKENS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PUSH_TOKENS_FILE.write_text(json.dumps(tokens, indent=2))


class PushTokenRequest(BaseModel):
    token: str
    platform: str = "ios"
    device_name: Optional[str] = None
    bundle_id: Optional[str] = None


@app.post("/api/push/register")
async def register_push_token(req: PushTokenRequest):
    """Register or update a device push token."""
    tokens = _load_push_tokens()
    # Update existing token for this device or add new
    existing = next((t for t in tokens if t["token"] == req.token), None)
    if existing:
        existing["device_name"] = req.device_name
        existing["bundle_id"] = req.bundle_id
        existing["platform"] = req.platform
    else:
        tokens.append({
            "token": req.token,
            "platform": req.platform,
            "device_name": req.device_name,
            "bundle_id": req.bundle_id,
        })
    _save_push_tokens(tokens)
    return {"status": "ok", "total_tokens": len(tokens)}


@app.get("/api/push/tokens")
async def get_push_tokens():
    """List all registered push tokens."""
    return {"tokens": _load_push_tokens()}


@app.delete("/api/push/tokens/{token}")
async def delete_push_token(token: str):
    """Remove a push token."""
    tokens = _load_push_tokens()
    tokens = [t for t in tokens if t["token"] != token]
    _save_push_tokens(tokens)
    return {"status": "ok", "total_tokens": len(tokens)}


@app.get("/api/activity-feed")
async def get_activity_feed(limit: int = 20, before: Optional[str] = None):
    """Unified activity feed from homelab services."""
    from database import get_db_connection
    from datetime import datetime, timedelta

    items = []

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cutoff = before or datetime.utcnow().isoformat()
            feed_limit = min(limit, 50)

            # Agent runs
            cursor.execute("""
                SELECT id, task, status, started_at, completed_at, duration_ms, source, total_steps
                FROM agent_runs
                WHERE started_at < ?
                ORDER BY started_at DESC LIMIT ?
            """, [cutoff, feed_limit])
            for row in cursor.fetchall():
                r = dict(row)
                status_emoji = {"completed": "done", "failed": "error", "running": "active"}.get(r["status"], r["status"])
                task_preview = (r["task"] or "")[:80]
                items.append({
                    "id": f"agent-{r['id']}",
                    "service": "agent",
                    "icon": "brain",
                    "title": f"Agent: {task_preview}" if task_preview else "Agent Run",
                    "description": f"{status_emoji} — {r['total_steps']} steps" + (f" in {r['duration_ms'] // 1000}s" if r.get('duration_ms') else ""),
                    "timestamp": r["started_at"],
                    "deepLink": "jenquisthome://service/ai-chat",
                    "status": r["status"],
                })

            # Harness sessions (Ralph loops, task completions)
            cursor.execute("""
                SELECT id, source, event, label, task_title, timestamp, duration_ms, success
                FROM harness_sessions
                WHERE timestamp < ? AND event IN ('task_completed', 'task_failed', 'session_completed')
                ORDER BY timestamp DESC LIMIT ?
            """, [cutoff, feed_limit])
            for row in cursor.fetchall():
                r = dict(row)
                title = r.get("task_title") or r.get("label") or r["event"].replace("_", " ").title()
                source_label = r.get("source", "harness").title()
                if r["event"] == "task_completed":
                    desc = f"{source_label} completed task"
                elif r["event"] == "task_failed":
                    desc = f"{source_label} task failed"
                else:
                    dur = f" in {r['duration_ms'] // 1000}s" if r.get("duration_ms") else ""
                    desc = f"{source_label} session finished{dur}"
                items.append({
                    "id": f"harness-{r['id']}",
                    "service": "agent",
                    "icon": "terminal",
                    "title": title,
                    "description": desc,
                    "timestamp": r["timestamp"],
                    "deepLink": "jenquisthome://service/ai-chat",
                    "status": "completed" if r.get("success", True) else "failed",
                })

    except Exception as e:
        logger.warning(f"Activity feed DB error: {e}")

    # Sort all items by timestamp descending, take top N
    items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    items = items[:feed_limit]

    next_cursor = items[-1]["timestamp"] if items else None

    return {
        "items": items,
        "next_cursor": next_cursor,
        "has_more": len(items) == feed_limit,
    }


@app.get("/api/dashboard")
async def get_dashboard(feed_limit: int = 20, feed_before: Optional[str] = None):
    """Aggregated dashboard: server health + meal plan + activity feed."""
    from service_feeds import fetch_frigate_events, fetch_immich_recent, fetch_mealie_today

    # Parallel fetch everything
    health_coro = health_check()
    feed_coro = get_activity_feed(limit=feed_limit, before=feed_before)
    frigate_coro = fetch_frigate_events(limit=10)
    immich_coro = fetch_immich_recent(limit=10)
    mealie_coro = fetch_mealie_today()

    results = await asyncio.gather(
        health_coro, feed_coro, frigate_coro, immich_coro, mealie_coro,
        return_exceptions=True,
    )

    # Unpack results, using safe defaults on failure
    health_result = results[0] if not isinstance(results[0], Exception) else None
    feed_result = results[1] if not isinstance(results[1], Exception) else None
    frigate_items = results[2] if not isinstance(results[2], Exception) else []
    immich_items = results[3] if not isinstance(results[3], Exception) else []
    mealie_meals = results[4] if not isinstance(results[4], Exception) else []

    # Build server status
    if health_result:
        server = {
            "status": health_result.status,
            "backends": health_result.backends,
        }
    else:
        server = {"status": "unknown", "backends": {}}

    # Merge feed items from all sources
    agent_items = feed_result.get("items", []) if isinstance(feed_result, dict) else []
    all_items = agent_items + list(frigate_items) + list(immich_items)
    all_items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    all_items = all_items[:feed_limit]

    next_cursor = all_items[-1]["timestamp"] if all_items else None

    return {
        "server": server,
        "meal_plan": {"meals": list(mealie_meals)},
        "feed": {
            "items": all_items,
            "next_cursor": next_cursor,
            "has_more": len(all_items) == feed_limit,
        },
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

    # Gaming PC status — derive from cache directly so health check is always fast
    gaming_status = await get_gaming_pc_status()
    cache_age = round(time.time() - _gaming_cache["updated_at"], 1) if _gaming_cache["updated_at"] else None
    gaming_pc_reachable = _gaming_cache["consecutive_failures"] == 0 and _gaming_cache["updated_at"] > 0

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
        gaming_pc_reachable=gaming_pc_reachable,
        gaming_cache_age=cache_age,
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
    selection = await route_request(request, body, priority=priority, api_key=api_key)

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
            if selection.complexity_tier:
                response_headers["X-Complexity-Tier"] = selection.complexity_tier

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

                    if response.status_code != 200:
                        error_detail = response.text[:500] if response.text else "Empty response"
                        logger.error(
                            f"Backend error from {selection.provider.name}: "
                            f"HTTP {response.status_code} - {error_detail}"
                        )
                        raise HTTPException(
                            status_code=502,
                            detail=f"Backend {selection.provider.name} returned HTTP {response.status_code}: {error_detail}"
                        )

                    try:
                        response_data = response.json()
                    except Exception:
                        logger.error(f"Backend {selection.provider.name} returned non-JSON response: {response.text[:200]}")
                        raise HTTPException(
                            status_code=502,
                            detail=f"Backend {selection.provider.name} returned invalid response"
                        )

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
                    if selection.complexity_tier:
                        response_headers["X-Complexity-Tier"] = selection.complexity_tier

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


@app.get("/gaming-pc/status")
async def get_gaming_pc_status_endpoint():
    """Get cached gaming PC status including gaming mode, running models, etc."""
    status = await get_gaming_pc_status()
    if status is None:
        raise HTTPException(status_code=503, detail="Gaming PC is unreachable")
    age = time.time() - _gaming_cache["updated_at"]
    return {**status.model_dump(), "cache_age_seconds": round(age, 1)}


@app.post("/gaming-mode")
async def toggle_gaming_mode(enable: bool = True):
    """Proxy gaming mode toggle to Windows PC and update local cache immediately."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{GAMING_PC_URL}/gaming-mode",
                json={"enable": enable},
            )
            result = response.json()
            # Update cache immediately so routing reflects the change before next poll
            if _gaming_cache["status"] is not None:
                updated = _gaming_cache["status"].model_copy(update={"gaming_mode": enable})
                _gaming_cache["status"] = updated
                _gaming_cache["updated_at"] = time.time()
            return result
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

    Uses complexity classification for routing. Agent calls with tools
    floor at MODERATE (tools always present), so they route to 3090 —
    but now it's data-driven instead of hardcoded.

    Returns the response with additional _routing_info for tracking.
    """
    token_estimate = estimate_tokens(messages)

    context_window = 8192
    max_tokens = max(512, min(2048, context_window - token_estimate - 500))

    body = {
        "model": model,
        "messages": messages,
        "tools": tools or [],
        "tool_choice": tool_choice,
        "max_tokens": max_tokens,
    }

    # Use complexity classification — agent calls with tools will score MODERATE+
    # because tools present adds +0.1 per tool (max 0.4), clearing the 0.25 threshold
    class _FakeRequest:
        headers = {}
    classification = classify_request(_FakeRequest(), body)
    actual_model = TIER_MODEL_MAP[classification.tier]
    backend_id = "3090" if classification.tier >= ComplexityTier.MODERATE else "3070"

    logger.info(f"Agent classification: tier={classification.tier.name}, score={classification.score:.2f}")

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
# Harness Metrics API Endpoints (Claude Code CLI observability)
# ============================================================================

class HarnessMetric(BaseModel):
    """Metric from Claude Code CLI / Ralph Wiggum."""
    source: str  # 'ralph', 'api', 'interactive'
    event: str  # 'session_started', 'task_started', 'task_completed', 'task_failed', 'session_completed'
    label: Optional[str] = None
    task_id: Optional[str] = None
    task_title: Optional[str] = None
    duration_ms: int = 0
    success: bool = True
    error: Optional[str] = None
    completed_tasks: int = 0
    failed_tasks: int = 0
    timestamp: Optional[str] = None


@app.post("/metrics/harness")
async def log_harness_metric(metric: HarnessMetric):
    """
    Log a metric from Claude Code CLI / Ralph Wiggum.

    This endpoint receives metrics emitted by:
    - Ralph Wiggum autonomous task loop
    - Claude Harness API wrapper
    - Future: Claude Code hooks
    """
    from database import get_db_connection
    from datetime import datetime

    try:
        timestamp = metric.timestamp or datetime.utcnow().isoformat()

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO harness_sessions
                (timestamp, source, event, label, task_id, task_title,
                 duration_ms, success, error, completed_tasks, failed_tasks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp,
                metric.source,
                metric.event,
                metric.label,
                metric.task_id,
                metric.task_title,
                metric.duration_ms,
                metric.success,
                metric.error,
                metric.completed_tasks,
                metric.failed_tasks,
            ))
            conn.commit()

        logger.info(f"Harness metric logged: {metric.source}/{metric.event} task={metric.task_id}")
        return {"status": "ok", "event": metric.event}

    except Exception as e:
        logger.error(f"Failed to log harness metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics/harness")
async def get_harness_metrics(
    source: Optional[str] = None,
    label: Optional[str] = None,
    event: Optional[str] = None,
    limit: int = 100,
    days: int = 7,
):
    """
    Get harness session metrics.

    Returns recent harness activity for dashboard display.
    """
    from database import get_db_connection
    from datetime import datetime, timedelta

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Build query with filters
            query = """
                SELECT * FROM harness_sessions
                WHERE timestamp >= ?
            """
            params = [(datetime.utcnow() - timedelta(days=days)).isoformat()]

            if source:
                query += " AND source = ?"
                params.append(source)
            if label:
                query += " AND label = ?"
                params.append(label)
            if event:
                query += " AND event = ?"
                params.append(event)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            metrics = [dict(row) for row in rows]

            return {"metrics": metrics, "count": len(metrics)}

    except Exception as e:
        logger.error(f"Failed to get harness metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics/harness/stats")
async def get_harness_stats(days: int = 7):
    """
    Get aggregated harness statistics.

    Returns summary stats for Ralph Wiggum and other harness activity.
    """
    from database import get_db_connection
    from datetime import datetime, timedelta

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

            # Get task completion stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total_events,
                    SUM(CASE WHEN event = 'task_completed' THEN 1 ELSE 0 END) as tasks_completed,
                    SUM(CASE WHEN event = 'task_failed' THEN 1 ELSE 0 END) as tasks_failed,
                    SUM(CASE WHEN event = 'session_started' THEN 1 ELSE 0 END) as sessions_started,
                    SUM(CASE WHEN event = 'session_completed' THEN 1 ELSE 0 END) as sessions_completed,
                    AVG(CASE WHEN event IN ('task_completed', 'task_failed') THEN duration_ms END) as avg_task_duration_ms,
                    SUM(CASE WHEN event IN ('task_completed', 'task_failed') THEN duration_ms ELSE 0 END) as total_duration_ms
                FROM harness_sessions
                WHERE timestamp >= ?
            """, (cutoff,))

            row = cursor.fetchone()

            # Get per-label breakdown
            cursor.execute("""
                SELECT
                    label,
                    COUNT(*) as events,
                    SUM(CASE WHEN event = 'task_completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN event = 'task_failed' THEN 1 ELSE 0 END) as failed
                FROM harness_sessions
                WHERE timestamp >= ? AND label IS NOT NULL
                GROUP BY label
                ORDER BY events DESC
            """, (cutoff,))

            labels = [dict(r) for r in cursor.fetchall()]

            # Calculate success rate
            tasks_completed = row["tasks_completed"] or 0
            tasks_failed = row["tasks_failed"] or 0
            total_tasks = tasks_completed + tasks_failed
            success_rate = (tasks_completed / total_tasks * 100) if total_tasks > 0 else 0

            return {
                "days": days,
                "total_events": row["total_events"] or 0,
                "tasks_completed": tasks_completed,
                "tasks_failed": tasks_failed,
                "success_rate": round(success_rate, 1),
                "sessions_started": row["sessions_started"] or 0,
                "sessions_completed": row["sessions_completed"] or 0,
                "avg_task_duration_ms": round(row["avg_task_duration_ms"] or 0),
                "total_duration_ms": row["total_duration_ms"] or 0,
                "by_label": labels,
            }

    except Exception as e:
        logger.error(f"Failed to get harness stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
