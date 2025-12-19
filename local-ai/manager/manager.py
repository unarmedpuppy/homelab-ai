import asyncio
import docker
import httpx
import json
import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse

# --- Configuration ---
IDLE_TIMEOUT = int(os.getenv("IDLE_TIMEOUT", "600"))
START_TIMEOUT = int(os.getenv("START_TIMEOUT", "180"))
MODELS_CONFIG_PATH = os.getenv("MODELS_CONFIG_PATH", "../models.json")

# --- Global State ---
docker_client = docker.from_env()
model_states = {}
gaming_mode = False  # When True, prevents new models from starting
gaming_mode_lock = None  # Initialized in lifespan

# --- Helper Functions ---
def load_models():
    """Loads model configuration and initializes state."""
    global model_states
    try:
        with open(MODELS_CONFIG_PATH) as f:
            models = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Models config file not found at '{MODELS_CONFIG_PATH}'")
        models = {}

    model_states = {
        name: {
            "config": config,
            "last_used": 0,
            "lock": asyncio.Lock(),
        }
        for name, config in models.items()
    }
    
    # Validate model types and set defaults
    for name, state in model_states.items():
        config = state["config"]
        if "type" not in config:
            # Default to "text" for backward compatibility
            config["type"] = "text"
            print(f"Warning: Model '{name}' missing 'type' field, defaulting to 'text'")
        elif config["type"] not in ["text", "image"]:
            print(f"Warning: Model '{name}' has invalid type '{config['type']}', defaulting to 'text'")
            config["type"] = "text"
    
    text_models = [name for name, s in model_states.items() if s["config"].get("type") == "text"]
    image_models = [name for name, s in model_states.items() if s["config"].get("type") == "image"]
    print(f"Loaded {len(models)} models: {len(text_models)} text, {len(image_models)} image")
    print(f"  Text models: {text_models}")
    print(f"  Image models: {image_models}")

def get_container(name: str):
    """Gets a docker container by name, returns None if not found."""
    try:
        return docker_client.containers.get(name)
    except docker.errors.NotFound:
        return None

def get_model_type(model_name: str) -> str:
    """Gets the model type (text or image) for a given model."""
    state = model_states.get(model_name)
    if not state:
        return "text"  # Default
    return state["config"].get("type", "text")

async def wait_for_ready(model_name: str):
    """Waits for a model container to become healthy."""
    state = model_states[model_name]
    container_name = state["config"]["container"]
    model_type = get_model_type(model_name)
    
    print(f"[{model_name}] Waiting for {model_type} container to be ready...")
    start_time = time.time()
    
    # Different health check endpoints for different model types
    # Both support /v1/models for OpenAI compatibility, but we can also check /health for image models
    health_endpoints = [
        f"http://{container_name}:8000/v1/models",  # OpenAI-compatible, works for both
        f"http://{container_name}:8000/health",      # Image server health check
    ]
    
    while time.time() - start_time < START_TIMEOUT:
        try:
            async with httpx.AsyncClient() as client:
                # Try /v1/models first (works for both vLLM and image server)
                res = await client.get(f"http://{container_name}:8000/v1/models", timeout=2)
                if res.status_code == 200:
                    print(f"[{model_name}] Container is ready!")
                    return True
                
                # For image models, also try /health endpoint
                if model_type == "image":
                    res = await client.get(f"http://{container_name}:8000/health", timeout=2)
                    if res.status_code == 200:
                        print(f"[{model_name}] Container is ready (via /health)!")
                        return True
        except httpx.RequestError:
            pass # Ignore connection errors while waiting
        await asyncio.sleep(1)
        
    print(f"[{model_name}] Timeout waiting for container to be ready.")
    return False


async def start_model_container(model_name: str):
    """Starts the container for a given model if not already running."""
    # Check gaming mode before starting new containers
    if gaming_mode_lock is not None:
        async with gaming_mode_lock:
            if gaming_mode:
                container = get_container(model_states[model_name]["config"]["container"])
                # Allow if container is already running (don't block existing usage)
                if container and container.status == "running":
                    pass  # Continue, container is already running
                else:
                    raise HTTPException(
                        status_code=503,
                        detail=f"Gaming mode is active. Cannot start model '{model_name}'. Use /gaming-mode?enable=false to disable gaming mode first."
                    )
    
    state = model_states[model_name]
    container_name = state["config"]["container"]
    
    async with state["lock"]:
        container = get_container(container_name)
        if container and container.status == "running":
            # Container is running, but check if it's actually ready
            if await wait_for_ready(model_name):
                return True
            else:
                # Container is running but not ready yet - wait a bit more
                print(f"[{model_name}] Container is running but not ready yet, waiting...")
                await asyncio.sleep(5)
                if await wait_for_ready(model_name):
                    return True
                raise HTTPException(status_code=503, detail=f"Model backend '{model_name}' is running but not ready. It may still be loading.")

        print(f"[{model_name}] Starting container: {container_name}")
        try:
            if not container:
                 raise docker.errors.NotFound(f"Container '{container_name}' not found.")
            container.start()
            if not await wait_for_ready(model_name):
                 raise HTTPException(status_code=503, detail=f"Model backend '{model_name}' failed to become ready.")
            return True

        except docker.errors.NotFound as e:
            print(f"Error: {e}")
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            print(f"[{model_name}] Failed to start container: {e}")
            # Best effort to stop a potentially broken container
            try: container.stop(timeout=5) 
            except: pass
            raise HTTPException(status_code=500, detail=f"Failed to start model backend '{model_name}'.")

# --- Background Task ---
async def reaper_task():
    """Periodically stops idle model containers."""
    while True:
        await asyncio.sleep(10)
        now = time.time()
        for name, state in model_states.items():
            if state["last_used"] == 0:
                continue # Model has not been used yet

            if now - state["last_used"] > IDLE_TIMEOUT:
                async with state["lock"]:
                    container_name = state["config"]["container"]
                    container = get_container(container_name)
                    if container and container.status == "running":
                        print(f"[{name}] Stopping idle container: {container_name}")
                        container.stop(timeout=10)
                        state["last_used"] = 0 # Reset timer

# --- FastAPI Application ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global gaming_mode_lock
    gaming_mode_lock = asyncio.Lock()
    load_models()
    asyncio.create_task(reaper_task())
    yield

app = FastAPI(lifespan=lifespan)

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(request: Request):
    # Handle GET requests (like /v1/models) without body
    try:
        body = await request.json() if request.method != "GET" else {}
    except:
        body = {}
    
    model_name = body.get("model")
    
    # For GET requests to /v1/models, return our own list
    if request.method == "GET" and request.url.path == "/v1/models":
        return await list_models()

    if not model_name or model_name not in model_states:
        raise HTTPException(status_code=400, detail=f"Invalid or missing 'model' in request body.")

    # Ensure model container is running
    await start_model_container(model_name)
    
    state = model_states[model_name]
    state["last_used"] = time.time() # Update timestamp on every request
    
    # Proxy the request to the backend model server
    container_name = state["config"]["container"]
    backend_url = f"http://{container_name}:8000/{request.url.path}"
    
    async with httpx.AsyncClient() as client:
        try:
            request_body = await request.body() if request.method != "GET" else None
            backend_req = client.build_request(
                method=request.method,
                url=backend_url,
                headers={h:v for h,v in request.headers.items() if h not in ("host", "content-length")},
                content=request_body,
                timeout=None, # Inference can be slow
            )
            backend_resp = await client.send(backend_req, stream=True)

            return StreamingResponse(
                backend_resp.aiter_raw(),
                status_code=backend_resp.status_code,
                headers=backend_resp.headers,
            )
        except httpx.ConnectError as e:
            raise HTTPException(status_code=503, detail=f"Could not connect to model backend: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error proxying request: {e}")


@app.get("/healthz")
async def healthz():
    running_models = []
    for name, state in model_states.items():
        container = get_container(state["config"]["container"])
        if container and container.status == "running":
            running_models.append(name)
    return {"ok": True, "running": running_models}

@app.get("/status")
async def status():
    """Get detailed status of all models and gaming mode."""
    running_models = []
    stopped_models = []
    
    for name, state in model_states.items():
        container = get_container(state["config"]["container"])
        model_info = {
            "name": name,
            "type": state["config"].get("type", "text"),
            "container": state["config"]["container"],
            "last_used": state["last_used"],
            "idle_seconds": int(time.time() - state["last_used"]) if state["last_used"] > 0 else None
        }
        
        if container and container.status == "running":
            model_info["status"] = "running"
            running_models.append(model_info)
        else:
            model_info["status"] = "stopped"
            stopped_models.append(model_info)
    
    is_gaming_mode = gaming_mode if gaming_mode_lock is not None else False
    
    # Determine if it's safe to game
    safe_to_game = len(running_models) == 0 and not is_gaming_mode
    
    return {
        "gaming_mode": is_gaming_mode,
        "safe_to_game": safe_to_game,
        "running_models": running_models,
        "stopped_models": stopped_models,
        "idle_timeout_seconds": IDLE_TIMEOUT,
        "summary": {
            "total_models": len(model_states),
            "running": len(running_models),
            "stopped": len(stopped_models)
        }
    }

@app.post("/gaming-mode")
async def set_gaming_mode(request: Request):
    """Enable or disable gaming mode. When enabled, prevents new models from starting."""
    global gaming_mode
    if gaming_mode_lock is None:
        raise HTTPException(status_code=503, detail="Manager not fully initialized")
    
    try:
        body = await request.json()
        enable = body.get("enable", True)
    except:
        # Support query parameter too
        enable = request.query_params.get("enable", "true").lower() == "true"
    
    async with gaming_mode_lock:
        old_mode = gaming_mode
        gaming_mode = enable
        mode_str = "enabled" if enable else "disabled"
        print(f"Gaming mode {mode_str}")
    
    return {
        "gaming_mode": gaming_mode,
        "previous_mode": old_mode,
        "message": f"Gaming mode {mode_str}. New model requests will {'be blocked' if enable else 'be allowed'}."
    }

@app.post("/stop-all")
async def stop_all_models():
    """Force stop all running model containers."""
    stopped = []
    failed = []
    
    for name, state in model_states.items():
        container = get_container(state["config"]["container"])
        if container and container.status == "running":
            try:
                async with state["lock"]:
                    print(f"[{name}] Force stopping container: {state['config']['container']}")
                    container.stop(timeout=10)
                    state["last_used"] = 0  # Reset timer
                    stopped.append(name)
            except Exception as e:
                print(f"[{name}] Failed to stop container: {e}")
                failed.append({"model": name, "error": str(e)})
    
    return {
        "stopped": stopped,
        "failed": failed,
        "message": f"Stopped {len(stopped)} model(s). {'Some failures occurred.' if failed else 'All models stopped successfully.'}"
    }

@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": model_id,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "local-ai"
            }
            for model_id in model_states.keys()
        ]
    }