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
import threading
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
CPU_OFFLOAD_GB = float(os.getenv("CPU_OFFLOAD_GB", "0"))  # vLLM cpu-offload-gb (0 = disabled)

# --- Global State ---
docker_client = docker.from_env()
model_cards = {}  # Model definitions from models.json
model_states = {}  # Runtime state for each model
available_models = []  # Models that fit in GPU VRAM
gpu_vram_gb = 0  # Detected GPU VRAM (primary)
num_gpus = 1  # Number of GPUs detected
gaming_mode = False
gaming_mode_lock = None


def detect_gpu_vram() -> int:
    """Detect available GPU VRAM in GB using nvidia-smi."""
    global num_gpus
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
            num_gpus = len(lines)
            # Primary GPU VRAM (used for single-GPU model filtering)
            vram_mib = int(lines[0])
            vram_gb = vram_mib // 1024
            print(f"Detected {num_gpus} GPU(s), primary VRAM: {vram_gb}GB ({vram_mib}MiB)")
            return vram_gb
    except Exception as e:
        print(f"Warning: Could not detect GPU VRAM: {e}")

    # Fallback: assume 8GB (RTX 3070 tier)
    num_gpus = 1
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
    
    # Filter models that fit in GPU VRAM (with 1GB headroom per GPU)
    usable_vram = gpu_vram_gb - 1
    available_models = []
    for m in models_list:
        model_gpu_count = m.get("gpu_count", 1)
        if model_gpu_count > num_gpus:
            continue  # Not enough GPUs
        if model_gpu_count > 1:
            # Multi-GPU: model VRAM is split across GPUs
            total_usable = usable_vram * model_gpu_count
            if m.get("vram_gb", 0) <= total_usable:
                available_models.append(m["id"])
        else:
            if m.get("vram_gb", 0) <= usable_vram:
                available_models.append(m["id"])
    
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
    
    if CPU_OFFLOAD_GB > 0:
        cmd.extend(["--cpu-offload-gb", str(int(CPU_OFFLOAD_GB))])

    # enforce-eager for AWQ (not awq_marlin which handles this natively)
    if card.get("quantization") == "awq":
        cmd.extend(["--enforce-eager"])

    # On 8GB GPUs, disable custom all-reduce to save memory
    if gpu_vram_gb <= 8:
        cmd.extend(["--disable-log-stats"])

    # Multi-GPU tensor parallelism
    gpu_count = card.get("gpu_count", 1)
    if gpu_count > 1:
        cmd.extend(["--tensor-parallel-size", str(gpu_count)])

    # Model-specific extra vLLM args (e.g. --enable-auto-tool-choice --tool-call-parser hermes)
    if card.get("extra_args"):
        cmd.extend(card["extra_args"])

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
        gpu_count = card.get("gpu_count", 1)
        container = docker_client.containers.create(
            image=VLLM_IMAGE,
            name=container_name,
            command=cmd,
            detach=True,
            device_requests=[
                DeviceRequest(count=gpu_count, capabilities=[['gpu']])
            ],
            environment={
                "NVIDIA_VISIBLE_DEVICES": "all",
                "CUDA_DEVICE_ORDER": "PCI_BUS_ID",
                "HF_HOME": "/root/.cache/huggingface",
                "VLLM_USE_V1": "0" if CPU_OFFLOAD_GB > 0 else "1",
                # Per-model env overrides (e.g. BNB quantization needs VLLM_USE_V1=0)
                **{k: str(v) for k, v in card.get("env_overrides", {}).items()},
            },
            volumes={
                "huggingface-cache": {"bind": "/root/.cache/huggingface", "mode": "rw"}
            },
            network=DOCKER_NETWORK,
            # Shared memory needed for multi-GPU NCCL communication
            ipc_mode="host" if gpu_count > 1 else None,
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
    """Start the default model(s) for always-on mode. Supports comma-separated list."""
    if MODE != "always-on" or not DEFAULT_MODEL:
        return
    models = [m.strip() for m in DEFAULT_MODEL.split(",") if m.strip()]
    for model_id in models:
        if model_id not in model_states:
            print(f"WARNING: Default model '{model_id}' not available on this GPU, skipping")
            if available_models:
                print(f"Available models: {available_models}")
            continue
        print(f"Starting default model: {model_id}")
        try:
            await start_model(model_id)
        except Exception as e:
            print(f"Failed to start default model '{model_id}': {e}")


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
        for model_id in [m.strip() for m in DEFAULT_MODEL.split(",") if m.strip()]:
            state = model_states.get(model_id)
            if state:
                container = get_container(state["container_name"])
                if not (container and container.status == "running"):
                    return JSONResponse(
                        status_code=503,
                        content={"status": "degraded", "mode": MODE, "reason": f"Model '{model_id}' is not running"}
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


# --- Model Garden: Cache Detection & Prefetch ---

def _check_model_cached(hf_model: str) -> tuple[bool, float | None]:
    """Check if a HuggingFace model is cached locally."""
    cache_dir_name = f"models--{hf_model.replace('/', '--')}"
    cache_path = os.path.join(HF_CACHE_PATH, "hub", cache_dir_name)

    if not os.path.isdir(cache_path):
        return False, None

    total_size = 0
    for dirpath, _, filenames in os.walk(cache_path):
        for f in filenames:
            total_size += os.path.getsize(os.path.join(dirpath, f))

    return True, round(total_size / (1024 ** 3), 2)


@app.get("/v1/models/cache")
async def cache_summary():
    """List cached models in the HuggingFace cache volume."""
    hub_path = os.path.join(HF_CACHE_PATH, "hub")
    cached_models = []
    total_size = 0

    if os.path.isdir(hub_path):
        for entry in os.listdir(hub_path):
            if not entry.startswith("models--"):
                continue
            dir_path = os.path.join(hub_path, entry)
            if not os.path.isdir(dir_path):
                continue
            size = sum(
                os.path.getsize(os.path.join(dp, f))
                for dp, _, fnames in os.walk(dir_path)
                for f in fnames
            )
            hf_name = entry.replace("models--", "").replace("--", "/", 1)
            cached_models.append({"hf_model": hf_name, "size_gb": round(size / (1024**3), 2)})
            total_size += size

    return {
        "total_cached_gb": round(total_size / (1024**3), 2),
        "cached_models": cached_models,
    }


@app.get("/v1/models/cards")
async def model_cards_endpoint():
    """Full model card listing with live status and cache info."""
    models = []
    for model_id, card in model_cards.items():
        hf_model = card.get("hf_model", "")
        cached, cache_size = _check_model_cached(hf_model) if hf_model else (False, None)

        state = model_states.get(model_id)
        if state:
            container = get_container(state["container_name"])
            status = "running" if container and container.status == "running" else "stopped"
            idle_seconds = int(time.time() - state["last_used"]) if state["last_used"] > 0 else None
        else:
            status = "unavailable"
            idle_seconds = None

        models.append({
            "id": model_id,
            "name": card.get("name", model_id),
            "hf_model": hf_model,
            "type": card.get("type", "text"),
            "quantization": card.get("quantization"),
            "vram_gb": card.get("vram_gb", 0),
            "max_context": card.get("max_context"),
            "default_context": card.get("default_context"),
            "gpu_count": card.get("gpu_count", 1),
            "description": card.get("description", ""),
            "architecture": card.get("architecture", ""),
            "license": card.get("license", ""),
            "tags": card.get("tags", []),
            "status": status,
            "cached": cached,
            "cache_size_gb": cache_size,
            "idle_seconds": idle_seconds,
        })

    return {
        "models": models,
        "gpu_vram_gb": gpu_vram_gb,
        "num_gpus": num_gpus,
        "mode": MODE,
        "gaming_mode_active": gaming_mode,
        "summary": {
            "total": len(model_cards),
            "available": len(available_models),
            "running": sum(1 for m in models if m["status"] == "running"),
            "cached": sum(1 for m in models if m["cached"]),
        },
    }


# Prefetch state tracking
_prefetch_tasks: dict[str, dict] = {}


@app.post("/v1/models/{model_id}/prefetch")
async def prefetch_model(model_id: str):
    """Download model weights in the background without starting vLLM."""
    if model_id not in model_cards:
        raise HTTPException(status_code=404, detail=f"Unknown model: {model_id}")

    if model_id in _prefetch_tasks and _prefetch_tasks[model_id]["status"] == "downloading":
        return {"status": "already_downloading", "model": model_id}

    card = model_cards[model_id]
    hf_model = card["hf_model"]

    def do_prefetch():
        _prefetch_tasks[model_id] = {"status": "downloading", "progress": "starting"}
        try:
            result = subprocess.run(
                ["huggingface-cli", "download", hf_model],
                capture_output=True, text=True, timeout=7200,
                env={**os.environ, "HF_HOME": HF_CACHE_PATH},
            )
            if result.returncode == 0:
                _prefetch_tasks[model_id] = {"status": "completed", "progress": "done"}
            else:
                _prefetch_tasks[model_id] = {"status": "failed", "progress": result.stderr[:500]}
        except Exception as e:
            _prefetch_tasks[model_id] = {"status": "failed", "progress": str(e)}

    thread = threading.Thread(target=do_prefetch, daemon=True)
    thread.start()

    _prefetch_tasks[model_id] = {"status": "downloading", "progress": "starting"}
    return {"status": "downloading", "model": model_id}


@app.get("/v1/models/{model_id}/prefetch")
async def prefetch_status(model_id: str):
    """Check prefetch status for a model."""
    if model_id in _prefetch_tasks:
        return {**_prefetch_tasks[model_id], "model": model_id}
    return {"status": "idle", "model": model_id}


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
