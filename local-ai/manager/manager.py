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
    print(f"Loaded {len(models)} models: {list(models.keys())}")

def get_container(name: str):
    """Gets a docker container by name, returns None if not found."""
    try:
        return docker_client.containers.get(name)
    except docker.errors.NotFound:
        return None

async def wait_for_ready(model_name: str):
    """Waits for a model container to become healthy."""
    state = model_states[model_name]
    container_name = state["config"]["container"]
    url = f"http://{container_name}:8000/health" # vLLM standard
    
    print(f"[{model_name}] Waiting for container to be ready...")
    start_time = time.time()
    while time.time() - start_time < START_TIMEOUT:
        try:
            async with httpx.AsyncClient() as client:
                # vLLM OpenAI-compatible endpoint is at /v1/models
                res = await client.get(f"http://{container_name}:8000/v1/models", timeout=2)
                if res.status_code == 200:
                    print(f"[{model_name}] Container is ready!")
                    return True
        except httpx.RequestError:
            pass # Ignore connection errors while waiting
        await asyncio.sleep(1)
        
    print(f"[{model_name}] Timeout waiting for container to be ready.")
    return False


async def start_model_container(model_name: str):
    """Starts the container for a given model if not already running."""
    state = model_states[model_name]
    container_name = state["config"]["container"]
    
    async with state["lock"]:
        container = get_container(container_name)
        if container and container.status == "running":
            return True

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
    load_models()
    asyncio.create_task(reaper_task())
    yield

app = FastAPI(lifespan=lifespan)

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(request: Request):
    body = await request.json()
    model_name = body.get("model")

    if not model_name or model_name not in model_states:
        return HTTPException(status_code=400, detail=f"Invalid or missing 'model' in request body.")

    # Ensure model container is running
    await start_model_container(model_name)
    
    state = model_states[model_name]
    state["last_used"] = time.time() # Update timestamp on every request
    
    # Proxy the request to the backend model server
    container_name = state["config"]["container"]
    backend_url = f"http://{container_name}:8000/{request.url.path}"
    
    async with httpx.AsyncClient() as client:
        try:
            backend_req = client.build_request(
                method=request.method,
                url=backend_url,
                headers={h:v for h,v in request.headers.items() if h not in ("host", "content-length")},
                content=await request.body(),
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