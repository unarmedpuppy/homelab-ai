import os, time, threading, requests, subprocess
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

IDLE_TIMEOUT = int(os.getenv("IDLE_TIMEOUT", "600"))  # seconds
START_TIMEOUT = int(os.getenv("START_TIMEOUT", "180"))

MODELS = {
    # exposed "model" name  -> container + port mapping
    "llama3-8b":       {"container": "vllm-llama3-8b",   "port": 8001},
    "qwen2.5-14b-awq": {"container": "vllm-qwen14b-awq", "port": 8002},
    "deepseek-coder":  {"container": "vllm-coder7b",     "port": 8003},
    "qwen-image-edit": {"container": "vllm-qwen-image", "port": 8004},
}

last_used = {k: 0 for k in MODELS}
app = FastAPI()

def docker_running(name: str) -> bool:
    ps = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", name],
        capture_output=True, text=True
    )
    return (ps.returncode == 0 and ps.stdout.strip() == "true")

def docker_start(name: str):
    try:
        subprocess.check_call(["docker", "start", name])
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to start container {name}: {e}")

def docker_stop(name: str):
    try:
        subprocess.call(["docker", "stop", name])
    except Exception as e:
        print(f"Warning: Failed to stop container {name}: {e}")

def wait_ready(container: str, timeout: int) -> bool:
    url = f"http://{container}:8000/v1/models"
    end = time.time() + timeout
    while time.time() < end:
        try:
            r = requests.get(url, timeout=2)
            if r.ok:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False

def reaper():
    while True:
        now = time.time()
        for k, v in MODELS.items():
            # stop only if running and idle for > timeout
            if last_used[k] and now - last_used[k] > IDLE_TIMEOUT:
                docker_stop(v["container"])
                last_used[k] = 0
        time.sleep(10)

threading.Thread(target=reaper, daemon=True).start()

@app.post("/v1/chat/completions")
async def chat(req: Request):
    body = await req.json()
    model = body.get("model")
    if model not in MODELS:
        return JSONResponse({"error": f"unknown model '{model}'"}, status_code=400)

    m = MODELS[model]
    if not docker_running(m["container"]):
        try:
            docker_start(m["container"])
        except subprocess.CalledProcessError as e:
            return JSONResponse({"error": f"start failed: {e}"}, status_code=500)
        if not wait_ready(m["container"], START_TIMEOUT):
            return JSONResponse({"error": "backend not ready"}, status_code=503)

    # forward to selected vLLM backend
    url = f"http://{m['container']}:8000/v1/chat/completions"
    try:
        r = requests.post(url, json=body, timeout=None)
        last_used[model] = time.time()
        return JSONResponse(r.json(), status_code=r.status_code)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/healthz")
def healthz():
    return {"ok": True, "running": [k for k,v in MODELS.items() if docker_running(v["container"])]}

@app.get("/v1/models")
def models():
    return {
        "object": "list",
        "data": [
            {
                "id": model_id,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "local-ai"
            }
            for model_id in MODELS.keys()
        ]
    }
