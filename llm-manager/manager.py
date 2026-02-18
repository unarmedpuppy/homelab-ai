"""
vLLM Manager - Unified model orchestrator for Local AI infrastructure.

Manages vLLM containers dynamically based on model cards and GPU capabilities.
Supports both always-on (server) and on-demand (gaming PC) modes.
"""
import asyncio
import docker
from docker.types import DeviceRequest
import httpx
import json
import os
import subprocess
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional

# --- Configuration ---
MODE = os.getenv("MODE", "on-demand")  # "always-on" or "on-demand"
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "")  # Model to load at startup (always-on mode)
GAMING_MODE_ENABLED = os.getenv("GAMING_MODE_ENABLED", "true").lower() == "true"
IDLE_TIMEOUT = int(os.getenv("IDLE_TIMEOUT", "600"))
START_TIMEOUT = int(os.getenv("START_TIMEOUT", "180"))
MODELS_CONFIG_PATH = os.getenv("MODELS_CONFIG_PATH", "/app/models.json")
VLLM_IMAGE = os.getenv("VLLM_IMAGE", "vllm/vllm-openai:latest")
HF_CACHE_PATH = os.getenv("HF_CACHE_PATH", "/root/.cache/huggingface")
DOCKER_NETWORK = os.getenv("DOCKER_NETWORK", "ai-network")  # Network for spawned containers
GPU_MEMORY_UTILIZATION = float(os.getenv("GPU_MEMORY_UTILIZATION", "0.95"))  # vLLM gpu-memory-utilization

# --- Global State ---
docker_client = docker.from_env()
model_cards = {}  # Model definitions from models.json
model_states = {}  # Runtime state for each model
available_models = []  # Models that fit in GPU VRAM
gpu_vram_gb = 0  # Detected GPU VRAM
gaming_mode = False
gaming_mode_lock = None


def detect_gpu_vram() -> int:
    """Detect available GPU VRAM in GB using nvidia-smi."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            # nvidia-smi returns memory in MiB
            vram_mib = int(result.stdout.strip().split("\n")[0])
            vram_gb = vram_mib // 1024
            print(f"Detected GPU VRAM: {vram_gb}GB ({vram_mib}MiB)")
            return vram_gb
    except Exception as e:
        print(f"Warning: Could not detect GPU VRAM: {e}")
    
    # Fallback: assume 8GB (RTX 3070 tier)
    print("Falling back to 8GB VRAM assumption")
    return 8


def load_models():
    """Load model definitions and filter by GPU capability."""
    global model_cards, model_states, available_models, gpu_vram_gb
    
    gpu_vram_gb = detect_gpu_vram()
    
    try:
        with open(MODELS_CONFIG_PATH) as f:
            data = json.load(f)
            models_list = data.get("models", [])
    except FileNotFoundError:
        print(f"ERROR: Models config not found at '{MODELS_CONFIG_PATH}'")
        models_list = []
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in models config: {e}")
        models_list = []
    
    # Convert list to dict keyed by id
    model_cards = {m["id"]: m for m in models_list}
    
    # Filter models that fit in GPU VRAM (with 1GB headroom)
    usable_vram = gpu_vram_gb - 1
    available_models = [
        m["id"] for m in models_list
        if m.get("vram_gb", 0) <= usable_vram
    ]
    
    # Initialize runtime state for available models
    model_states = {
        model_id: {
            "container_name": f"vllm-{model_id}",
            "last_used": 0,
            "lock": asyncio.Lock(),
            "status": "stopped"
        }
        for model_id in available_models
    }
    
    print(f"GPU VRAM: {gpu_vram_gb}GB (usable: {usable_vram}GB)")
    print(f"Available models ({len(available_models)}/{len(models_list)}): {available_models}")
    
    excluded = [m["id"] for m in models_list if m["id"] not in available_models]
    if excluded:
        print(f"Excluded (insufficient VRAM): {excluded}")


def get_container(name: str):
    """Get a Docker container by name, returns None if not found."""
    try:
        return docker_client.containers.get(name)
    except docker.errors.NotFound:
        return None


def create_vllm_container(model_id: str):
    """Create a vLLM container for the given model."""
    if model_id not in model_cards:
        raise ValueError(f"Unknown model: {model_id}")
    
    card = model_cards[model_id]
    state = model_states[model_id]
    container_name = state["container_name"]
    
    existing = get_container(container_name)
    if existing:
        if existing.status == "running":
            return existing
        # Remove dead/exited container so we can recreate it
        print(f"[{model_id}] Removing dead container ({existing.status})")
        existing.remove(force=True)
    
    cmd = [
        "--model", card["hf_model"],
        "--host", "0.0.0.0",
        "--port", "8000",
        "--served-model-name", model_id,
    ]
    
    if card.get("quantization"):
        cmd.extend(["--quantization", card["quantization"]])
    
    # Determine context length - use card's default, but cap based on VRAM for safety
    context_len = card.get("default_context", 4096)
    if gpu_vram_gb <= 8:
        # 8GB cards need reduced context for KV cache to fit
        context_len = min(context_len, 2048)
    
    cmd.extend(["--max-model-len", str(context_len)])
    cmd.extend(["--gpu-memory-utilization", str(GPU_MEMORY_UTILIZATION)])
    
    # enforce-eager for AWQ (not awq_marlin which handles this natively)
    if card.get("quantization") == "awq":
        cmd.extend(["--enforce-eager"])

    # On 8GB GPUs, disable custom all-reduce to save memory
    if gpu_vram_gb <= 8:
        cmd.extend(["--disable-log-stats"])
    
    print(f"[{model_id}] Creating container: {container_name}")
    print(f"[{model_id}] Image: {VLLM_IMAGE}")
    print(f"[{model_id}] Network: {DOCKER_NETWORK}")
    print(f"[{model_id}] Command: {' '.join(cmd)}")

    # Pull image if not present
    try:
        docker_client.images.get(VLLM_IMAGE)
    except docker.errors.ImageNotFound:
        print(f"[{model_id}] Pulling image {VLLM_IMAGE}...")
        docker_client.images.pull(VLLM_IMAGE)
        print(f"[{model_id}] Image pulled successfully")

    try:
        container = docker_client.containers.create(
            image=VLLM_IMAGE,
            name=container_name,
            command=cmd,
            detach=True,
            device_requests=[
                DeviceRequest(count=1, capabilities=[['gpu']])
            ],
            environment={
                "NVIDIA_VISIBLE_DEVICES": "all",
                "HF_HOME": "/root/.cache/huggingface",
            },
            volumes={
                "huggingface-cache": {"bind": "/root/.cache/huggingface", "mode": "rw"}
            },
            network=DOCKER_NETWORK,
            labels={
                "managed-by": "vllm-manager",
                "model-id": model_id,
            }
        )
        print(f"[{model_id}] Container created: {container.id[:12]}")
        return container
    except Exception as e:
        print(f"[{model_id}] Failed to create container: {e}")
        raise


async def wait_for_ready(model_id: str, timeout: int = None) -> bool:
    """Wait for a model container to become healthy."""
    if timeout is None:
        timeout = START_TIMEOUT
    
    state = model_states[model_id]
    container_name = state["container_name"]
    
    print(f"[{model_id}] Waiting for container to be ready...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(
                    f"http://{container_name}:8000/v1/models",
                    timeout=2
                )
                if res.status_code == 200:
                    print(f"[{model_id}] Container is ready!")
                    return True
        except httpx.RequestError:
            pass
        await asyncio.sleep(2)
    
    print(f"[{model_id}] Timeout waiting for container to be ready.")
    return False


async def start_model(model_id: str) -> bool:
    """Start a model container, creating it if necessary."""
    if model_id not in model_states:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{model_id}' is not available on this GPU ({gpu_vram_gb}GB VRAM)"
        )
    
    # Check gaming mode
    if gaming_mode_lock is not None:
        async with gaming_mode_lock:
            if gaming_mode:
                container = get_container(model_states[model_id]["container_name"])
                if not (container and container.status == "running"):
                    raise HTTPException(
                        status_code=503,
                        detail=f"Gaming mode active. Cannot start '{model_id}'. Disable gaming mode first."
                    )
    
    state = model_states[model_id]
    
    async with state["lock"]:
        container = get_container(state["container_name"])

        # Remove dead containers and recreate fresh (new image, clean state)
        if container and container.status != "running":
            print(f"[{model_id}] Removing stale container ({container.status})")
            container.remove(force=True)
            container = None

        # Create container if it doesn't exist
        if not container:
            container = create_vllm_container(model_id)

        # Start if not running
        if container.status != "running":
            print(f"[{model_id}] Starting container...")
            container.start()
        
        # Wait for ready
        if await wait_for_ready(model_id):
            state["status"] = "running"
            state["last_used"] = time.time()
            return True
        
        # Failed to become ready
        try:
            container.stop(timeout=5)
        except:
            pass
        raise HTTPException(
            status_code=503,
            detail=f"Model '{model_id}' failed to become ready"
        )


async def stop_model(model_id: str) -> bool:
    """Stop a model container."""
    if model_id not in model_states:
        return False
    
    state = model_states[model_id]
    
    async with state["lock"]:
        container = get_container(state["container_name"])
        if container and container.status == "running":
            print(f"[{model_id}] Stopping container...")
            try:
                container.stop(timeout=10)
                state["status"] = "stopped"
                state["last_used"] = 0
                return True
            except Exception as e:
                print(f"[{model_id}] Failed to stop: {e}")
                return False
    return False


async def stop_all_models():
    """Stop all running model containers."""
    stopped = []
    for model_id in model_states:
        if await stop_model(model_id):
            stopped.append(model_id)
    return stopped


async def start_default_model():
    """Start the default model (for always-on mode)."""
    if MODE != "always-on" or not DEFAULT_MODEL:
        return
    
    if DEFAULT_MODEL not in model_states:
        print(f"WARNING: Default model '{DEFAULT_MODEL}' not available on this GPU")
        if available_models:
            print(f"Available models: {available_models}")
        return
    
    print(f"Starting default model: {DEFAULT_MODEL}")
    try:
        await start_model(DEFAULT_MODEL)
    except Exception as e:
        print(f"Failed to start default model: {e}")


# --- Background Tasks ---
async def idle_reaper():
    """Stop idle models (only in on-demand mode)."""
    while True:
        await asyncio.sleep(60)
        
        if MODE != "on-demand" or IDLE_TIMEOUT <= 0:
            continue
        
        now = time.time()
        for model_id, state in model_states.items():
            if state["status"] != "running":
                continue
            
            idle_time = now - state["last_used"]
            if idle_time > IDLE_TIMEOUT:
                print(f"[{model_id}] Idle for {int(idle_time)}s, stopping...")
                await stop_model(model_id)


# --- FastAPI Application ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global gaming_mode_lock
    gaming_mode_lock = asyncio.Lock()
    
    load_models()
    asyncio.create_task(idle_reaper())
    
    # Start default model for always-on mode
    await start_default_model()
    
    yield


app = FastAPI(
    title="vLLM Manager",
    description="Unified vLLM orchestrator for Local AI infrastructure",
    lifespan=lifespan
)


@app.get("/health")
async def health():
    """Health check endpoint - reports degraded if expected models aren't running."""
    if MODE == "always-on" and DEFAULT_MODEL:
        state = model_states.get(DEFAULT_MODEL)
        if state:
            container = get_container(state["container_name"])
            if not (container and container.status == "running"):
                return JSONResponse(
                    status_code=503,
                    content={"status": "degraded", "mode": MODE, "reason": f"Default model '{DEFAULT_MODEL}' is not running"}
                )
    return {"status": "healthy", "mode": MODE}


@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI-compatible)."""
    return {
        "object": "list",
        "data": [
            {
                "id": model_id,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "vllm-manager",
                "type": model_cards[model_id].get("type", "text"),
                "vram_gb": model_cards[model_id].get("vram_gb", 0),
            }
            for model_id in available_models
        ]
    }


@app.get("/status")
async def status():
    """Get detailed status of all models and system state."""
    running = []
    stopped = []
    
    for model_id, state in model_states.items():
        container = get_container(state["container_name"])
        card = model_cards.get(model_id, {})
        
        info = {
            "id": model_id,
            "name": card.get("name", model_id),
            "type": card.get("type", "text"),
            "vram_gb": card.get("vram_gb", 0),
            "container": state["container_name"],
            "status": "running" if container and container.status == "running" else "stopped",
            "last_used": state["last_used"],
            "idle_seconds": int(time.time() - state["last_used"]) if state["last_used"] > 0 else None,
        }
        
        if info["status"] == "running":
            running.append(info)
        else:
            stopped.append(info)
    
    return {
        "mode": MODE,
        "gaming_mode_enabled": GAMING_MODE_ENABLED,
        "gaming_mode_active": gaming_mode,
        "gpu_vram_gb": gpu_vram_gb,
        "idle_timeout": IDLE_TIMEOUT,
        "default_model": DEFAULT_MODEL,
        "running": running,
        "stopped": stopped,
        "summary": {
            "total": len(model_states),
            "available": len(available_models),
            "running": len(running),
        }
    }


@app.post("/gaming-mode")
async def set_gaming_mode(request: Request):
    """Enable or disable gaming mode."""
    global gaming_mode
    
    if not GAMING_MODE_ENABLED:
        raise HTTPException(
            status_code=400,
            detail="Gaming mode is disabled on this instance"
        )
    
    if gaming_mode_lock is None:
        raise HTTPException(status_code=503, detail="Manager not initialized")
    
    try:
        body = await request.json()
        enable = body.get("enable", True)
    except:
        enable = request.query_params.get("enable", "true").lower() == "true"
    
    async with gaming_mode_lock:
        old_mode = gaming_mode
        gaming_mode = enable
        
        if enable and not old_mode:
            # Just turned on - stop all models
            stopped = await stop_all_models()
            return {
                "gaming_mode": True,
                "stopped_models": stopped,
                "message": "Gaming mode enabled. All models stopped."
            }
        elif not enable and old_mode:
            # Just turned off - restart default model if always-on
            await start_default_model()
            return {
                "gaming_mode": False,
                "message": f"Gaming mode disabled. {'Default model starting.' if MODE == 'always-on' and DEFAULT_MODEL else 'Models available on-demand.'}"
            }
    
    return {"gaming_mode": gaming_mode}


@app.post("/stop-all")
async def stop_all():
    """Force stop all running model containers."""
    stopped = await stop_all_models()
    return {
        "stopped": stopped,
        "message": f"Stopped {len(stopped)} model(s)"
    }


@app.post("/start/{model_id}")
async def start_model_endpoint(model_id: str):
    """Explicitly start a model."""
    await start_model(model_id)
    return {"status": "running", "model": model_id}


@app.post("/stop/{model_id}")
async def stop_model_endpoint(model_id: str):
    """Explicitly stop a model."""
    if await stop_model(model_id):
        return {"status": "stopped", "model": model_id}
    raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found or not running")


@app.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(request: Request, path: str):
    """Proxy requests to the appropriate model container."""
    # Parse request body to get model
    try:
        body = await request.json() if request.method != "GET" else {}
    except:
        body = {}
    
    model_id = body.get("model")
    
    if not model_id:
        raise HTTPException(status_code=400, detail="Missing 'model' in request body")
    
    if model_id not in model_states:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{model_id}' not available. Available: {available_models}"
        )
    
    # Ensure model is running
    await start_model(model_id)
    
    state = model_states[model_id]
    state["last_used"] = time.time()
    
    # Proxy to backend
    container_name = state["container_name"]
    backend_url = f"http://{container_name}:8000/v1/{path}"
    
    print(f"[{model_id}] Proxying {request.method} /v1/{path}")
    
    request_body = await request.body() if request.method != "GET" else None
    request_headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length")
    }
    
    async def stream_response():
        async with httpx.AsyncClient(timeout=None) as client:
            try:
                async with client.stream(
                    request.method,
                    backend_url,
                    headers=request_headers,
                    content=request_body
                ) as resp:
                    async for chunk in resp.aiter_raw():
                        yield chunk
            except httpx.ConnectError as e:
                error = {"error": f"Could not connect to model backend: {e}"}
                yield f"data: {json.dumps(error)}\n\n".encode()
            except Exception as e:
                error = {"error": f"Proxy error: {e}"}
                yield f"data: {json.dumps(error)}\n\n".encode()
    
    content_type = "text/event-stream" if body.get("stream") else "application/json"
    return StreamingResponse(stream_response(), media_type=content_type)
