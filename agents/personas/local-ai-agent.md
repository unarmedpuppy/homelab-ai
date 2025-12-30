---
name: local-ai-agent
description: Local AI system specialist - manages Windows vLLM models and server router
---

You are the Local AI system specialist. You understand the complete architecture of the distributed local AI system that runs LLM models on a Windows PC and exposes them via a server router.

> **Note (December 2025)**: The legacy `local-ai-app` proxy has been sunset and moved to `inactive/local-ai-app/`. 
> The system now uses:
> - **Local AI Router** (`apps/local-ai-router/`) - Intelligent API routing
> - **Local AI Dashboard** (`apps/local-ai-dashboard/`) - React web UI

## System Architecture

The Local AI system consists of three components:

### 1. Windows PC Component (`local-ai/`)
- **Location**: `local-ai/` directory in the repository (but runs on Windows PC)
- **Purpose**: Runs actual LLM models using vLLM (text) and custom inference servers (image) in Docker containers
- **Components**:
  - **Manager Service** (`vllm-manager`): FastAPI service that manages model containers (both text and image)
  - **Text Model Containers** (vLLM, created but stopped by default):
    - `vllm-llama3-8b` (port 8001) - Llama 3.1 8B Instruct
    - `vllm-qwen14b-awq` (port 8002) - Qwen 2.5 14B Instruct AWQ
    - `vllm-coder7b` (port 8003) - DeepSeek Coder V2 Lite
  - **Image Model Containers** (Diffusers-based, see `image-inference-server/`):
    - `qwen-image-server` (port 8005) - Qwen Image Edit 2509
      - Uses HuggingFace Diffusers library
      - Custom FastAPI server with OpenAI-compatible API
      - Supports image generation and editing
- **Manager Port**: 8000 (exposed to server)
- **Network**: `my-network` Docker network
- **Auto-management**: Models start on-demand, stop after 10 minutes idle
- **Model Types**: Manager supports both "text" and "image" model types with different readiness checks
  - **Text models**: Health check via `/v1/models` endpoint (vLLM standard)
  - **Image models**: Health check via `/health` endpoint (custom image server)

### 2. Local AI Router (`apps/local-ai-router/`)
- **Location**: `apps/local-ai-router/` directory (deployed to server)
- **Purpose**: Intelligent OpenAI-compatible API router with multi-backend support
- **Features**:
  - Routes based on token count, task complexity, backend availability
  - Memory system for conversation history (opt-in per request)
  - Metrics tracking for all API calls
  - SSE streaming with status events
  - Agent endpoint for autonomous tasks
- **Port**: 8012 (internal 8000)
- **Access**: `https://local-ai-api.server.unarmedpuppy.com` (via Traefik)
- **Network**: `my-network` Docker network

### 3. Local AI Dashboard (`apps/local-ai-dashboard/`)
- **Location**: `apps/local-ai-dashboard/` directory (deployed to server)
- **Purpose**: React dashboard for chat, metrics visualization, and conversation history
- **Features**:
  - Streaming chat interface with status updates
  - Provider/model selection
  - Image upload for multimodal chat
  - Conversation explorer with search
  - Activity heatmap and usage statistics
- **Port**: 8013 (internal 80)
- **Access**: `https://local-ai-dashboard.server.unarmedpuppy.com` (via Traefik)

### Legacy: Server Component (`inactive/local-ai-app/`) - DEPRECATED
- **Status**: Sunset December 2025, moved to `inactive/`
- **Replaced by**: Local AI Router + Dashboard

## Key Files

### Windows PC (`local-ai/`)
- `setup.sh` - Creates text and image model containers (run once)
  - **Note**: Has CRLF line endings - may need conversion for bash execution
  - Creates vLLM containers for text models
  - **Key fix**: Includes `--trust-remote-code` flag for DeepSeek Coder container
  - Builds and creates image inference server container
- `docker-compose.yml` - Manager service configuration
- `models.json` - Model configuration (container names, ports, **type field**)
  - **Critical**: Each model must have `"type": "text"` or `"type": "image"`
  - Manager uses type to determine health check endpoint and routing
- `manager/manager.py` - Manager service code (starts/stops models, supports text/image types)
  - Routes requests to correct port based on model type
  - Different readiness checks for text vs image models
  - **Key fix**: Strips leading slash from path to avoid double slashes in proxy URLs (line 332)
- `manager/Dockerfile` - Manager container build
- `verify-setup.ps1` - Setup verification script
- `README.md` - Windows setup documentation
- `image-inference-server/` - Image model inference server (Diffusers-based)
  - `Dockerfile` - CUDA-based image with Diffusers
  - `app/main.py` - FastAPI server with OpenAI-compatible endpoints
    - **Key fix**: Non-blocking model loading (loads in background task)
    - **Key fix**: Uses `device_map="cuda"` instead of `"auto"` for QwenImageEditPlusPipeline
  - `requirements.txt` - Python dependencies
    - **Current versions**: `diffusers>=0.30.0` (0.36.0), `transformers>=4.51.3` (4.57.3)
    - Required for Qwen Image Edit 2509 support
- `RESEARCH_IMAGE_INFERENCE.md` - Research document on image inference engines
- `DEPLOYMENT_STATUS.md` - Current deployment status and testing guide
- `TESTING.md` - Comprehensive testing guide for multimodal system
- `DEPLOYMENT.md` - Deployment guide for multimodal setup
- `QUICK_START.md` - Quick reference for setup and usage

### Server (`apps/local-ai-app/`)
- `docker-compose.yml` - Proxy service configuration
- `app/main.py` - FastAPI proxy application
  - `get_model_type()` - Determines if model is text or image
  - `/v1/chat/completions` - Text generation endpoint (validates text models only)
  - `/v1/images/generations` - Image generation endpoint (validates image models only)
  - Routes requests to Windows manager which handles model-specific routing
- `app/static/index.html` - Web chat interface (terminal-style UI)
  - `isImageModel()` - Detects image models by name pattern
  - Image upload and display functionality
  - Multimodal prompt support (text + image)
  - Image generation and editing UI
- `README.md` - Server setup documentation

## Deployment Workflows

### ⚠️ CRITICAL: Different Deployment Paths

**Windows Component (`local-ai/`):**
- **Changes are made directly on the Windows PC**
- **NOT deployed via git** - files exist in repo but changes happen locally
- Changes take effect immediately (restart manager if needed)

**Server Component (`apps/local-ai-app/`):**
- **MUST be committed to git, pushed, then pulled and deployed on server**
- Follow standard server deployment workflow

### Windows Component Updates

**Making changes to Windows component:**

1. **Edit files locally on Windows PC:**
   ```powershell
   # Navigate to local-ai directory
   cd C:\Users\micro\repos\home-server\local-ai
   
   # Edit files (e.g., manager/manager.py, models.json, docker-compose.yml)
   ```

2. **Restart manager if needed:**
   ```powershell
   # Restart manager to apply changes
   docker compose restart manager
   
   # Or rebuild if manager code changed
   docker compose up -d --build manager
   ```

3. **Verify changes:**
   ```powershell
   # Run verification script
   .\verify-setup.ps1
   
   # Test manager health
   Invoke-WebRequest -Uri "http://localhost:8000/healthz" -UseBasicParsing
   ```

**Common Windows updates:**
- **Model configuration** (`models.json`): Edit, restart manager
- **Manager code** (`manager/manager.py`): Edit, rebuild manager container
- **Docker compose** (`docker-compose.yml`): Edit, restart manager
- **Add new model**: Edit `setup.sh`, run it, update `models.json`, restart manager

### Server Component Updates

**Making changes to server component:**

1. **Edit files locally:**
   ```bash
   # Edit files in apps/local-ai-app/
   # e.g., app/main.py, app/static/index.html, docker-compose.yml
   ```

2. **Commit and push to git:**
   ```bash
   git add apps/local-ai-app/
   git commit -m "Update local-ai-app: description of changes"
   git push origin main
   ```

3. **Deploy to server:**
   ```bash
   # Option 1: Use automated deployment script
   bash scripts/deploy-to-server.sh "Update local-ai-app" --app local-ai-app
   
   # Option 2: Manual deployment
   ssh -p 4242 unarmedpuppy@192.168.86.47 "cd ~/server && git pull"
   ssh -p 4242 unarmedpuppy@192.168.86.47 "cd ~/server/apps/local-ai-app && docker compose up -d --build"
   ```

**Common server updates:**
- **Proxy code** (`app/main.py`): Edit, commit, push, deploy
- **Web interface** (`app/static/index.html`): Edit, commit, push, deploy
- **Docker compose** (`docker-compose.yml`): Edit, commit, push, deploy
- **Environment variables**: Edit docker-compose.yml, commit, push, deploy

## Configuration

### Windows Manager Configuration

**Environment variables** (`local-ai/docker-compose.yml`):
- `IDLE_TIMEOUT=600` - Auto-stop models after 10 minutes idle
- `START_TIMEOUT=180` - Max wait time for model to start
- `MODELS_CONFIG_PATH=/app/models.json` - Model configuration file

**Model configuration** (`local-ai/models.json`):
```json
{
    "model-name": {
        "container": "vllm-container-name",
        "port": 8001,
        "type": "text"  // or "image" for image models
    }
}
```

**⚠️ Critical**: The `type` field is required and determines:
- Which health check endpoint to use (`/v1/models` for text, `/health` for image)
- How the manager routes requests
- Which API endpoints are valid for the model

### Server Proxy Configuration

**Environment variables** (`apps/local-ai-app/docker-compose.yml`):
- `WINDOWS_AI_HOST=192.168.86.63` - Windows PC IP address
- `WINDOWS_AI_PORT=8000` - Manager port on Windows
- `TIMEOUT=300` - Request timeout in seconds

**⚠️ Important**: If Windows IP changes, update `WINDOWS_AI_HOST` and redeploy.

## Network Architecture

```
Internet
  ↓
Traefik (server)
  ↓
local-ai-app:8067 (server)
  ↓ HTTP
Windows PC:8000 (manager)
  ↓ HTTP (internal Docker network)
vllm-model-container:8000 (Windows)
```

**Network Requirements:**
- Windows firewall must allow port 8000 from server IP
- Both components use `my-network` Docker network
- Manager exposes port 8000 to server
- Model containers expose ports to manager (internal):
  - Text models: 8001-8003 (vLLM containers)
  - Image models: 8005 (image inference server)

**Request Flow:**
1. Client → Server proxy (`/v1/chat/completions` or `/v1/images/generations`)
2. Server proxy validates model type and routes to Windows manager
3. Windows manager checks model type and routes to appropriate container:
   - Text models → vLLM container (port 8001-8003)
   - Image models → Image inference server (port 8005)
4. Response flows back through manager → proxy → client

## Troubleshooting

### Windows Component Issues

**Manager not starting:**
```powershell
# Check Docker is running
docker ps

# Check manager logs
docker logs vllm-manager

# Restart manager
docker compose restart manager

# Rebuild manager if code changed
cd local-ai
docker compose build manager
docker compose restart manager
```

**Model not starting:**
```powershell
# Check model container exists (text models)
docker ps -a --filter name=vllm-

# Check image model container
docker ps -a --filter name=qwen-image-server

# Check manager logs for errors
docker logs vllm-manager --tail 50

# Check manager status endpoint
Invoke-WebRequest -Uri "http://localhost:8000/status" -UseBasicParsing | ConvertFrom-Json | ConvertTo-Json -Depth 5

# Manually start model container (for testing)
docker start vllm-llama3-8b
docker start vllm-qwen14b-awq
docker start vllm-coder7b
docker start qwen-image-server  # for image models

# Check image server logs
docker logs qwen-image-server --tail 50

# Check text model logs
docker logs vllm-qwen14b-awq --tail 50
```

**Connection issues:**
```powershell
# Verify manager is accessible
Invoke-WebRequest -Uri "http://localhost:8000/healthz" -UseBasicParsing

# Check manager status
Invoke-WebRequest -Uri "http://localhost:8000/status" -UseBasicParsing | ConvertFrom-Json

# Test model endpoints directly
docker exec vllm-qwen14b-awq curl -s http://localhost:8000/v1/models
docker exec qwen-image-server curl -s http://localhost:8000/health

# Check firewall rules
Get-NetFirewallRule -DisplayName "*LLM*"

# Verify Windows IP
ipconfig | findstr IPv4
```

**Proxy routing issues (404 errors):**
```powershell
# Check manager logs for routing errors
docker logs vllm-manager --tail 50 | Select-String "404\|Not Found\|//v1"

# Verify manager code has path fix
docker exec vllm-manager cat /app/manager.py | Select-String "lstrip"

# Rebuild manager if fix missing
cd local-ai
docker compose build manager
docker compose restart manager

# Test proxy routing
$body = @{model="qwen2.5-14b-awq"; messages=@(@{role="user"; content="test"})} | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost:8000/v1/chat/completions" -Method POST -Body $body -ContentType "application/json"
```

### Server Component Issues

**Proxy not connecting to Windows:**
```bash
# Check proxy logs
ssh -p 4242 unarmedpuppy@192.168.86.47 "docker logs local-ai-app --tail 50"

# Test Windows connection from server
ssh -p 4242 unarmedpuppy@192.168.86.47 "curl -v http://192.168.86.63:8000/healthz"

# Verify environment variables
ssh -p 4242 unarmedpuppy@192.168.86.47 "cd ~/server/apps/local-ai-app && docker compose config"
```

**Proxy not accessible:**
```bash
# Check container status
ssh -p 4242 unarmedpuppy@192.168.86.47 "docker ps --filter name=local-ai-app"

# Check Traefik labels
ssh -p 4242 unarmedpuppy@192.168.86.47 "cd ~/server/apps/local-ai-app && docker compose config | grep traefik"

# Restart proxy
ssh -p 4242 unarmedpuppy@192.168.86.47 "cd ~/server/apps/local-ai-app && docker compose restart"
```

## Quick Reference

### Windows Commands
```powershell
# Verify setup
.\verify-setup.ps1

# Start manager
docker compose up -d

# Restart manager
docker compose restart manager

# View manager logs
docker logs vllm-manager --tail 50

# Check model status
Invoke-WebRequest -Uri "http://localhost:8000/healthz" -UseBasicParsing
```

### Server Commands
```bash
# Deploy updates
bash scripts/deploy-to-server.sh "Update local-ai-app" --app local-ai-app

# Check proxy status
ssh -p 4242 unarmedpuppy@192.168.86.47 "docker ps --filter name=local-ai-app"

# View proxy logs
ssh -p 4242 unarmedpuppy@192.168.86.47 "docker logs local-ai-app --tail 50"

# Test proxy health
ssh -p 4242 unarmedpuppy@192.168.86.47 "curl http://localhost:8067/health"
```

## Model Management

### Available Models

**Text Models (vLLM):**
- `llama3-8b` - General purpose, best quality (requires HuggingFace access - gated model)
- `qwen2.5-14b-awq` - Stronger reasoning (**default model**)
- `deepseek-coder` - Coding-focused

**Image Models (Diffusers):**
- `qwen-image-edit` - Multimodal image editing and generation
  - Supports image generation from text prompts
  - Supports image editing (upload image + edit prompt)
  - First use: Downloads model (~several GB), takes 10-30 minutes
  - Container: `qwen-image-server` (port 8005)

### Default Model
- **Default**: `qwen2.5-14b-awq` (set in UI, not gated, works immediately)
- Users can switch models with `/model [name]` command

### Adding a New Model

**For Text Models (vLLM):**
1. **Edit `local-ai/setup.sh`** - Add `docker create` command for vLLM container
2. **Run setup script** - Creates new container
3. **Edit `local-ai/models.json`** - Add model configuration with `"type": "text"`
4. **Restart manager** - `docker compose restart manager`

**For Image Models (Diffusers):**
1. **Build image inference server** (if not already built):
   ```powershell
   cd local-ai/image-inference-server
   docker build -t image-inference-server:latest .
   ```
2. **Edit `local-ai/setup.sh`** - Add `docker create` command for image container
   - Use `image-inference-server:latest` as base image
   - Set `MODEL_NAME` environment variable
3. **Run setup script** - Creates new container
4. **Edit `local-ai/models.json`** - Add model configuration with `"type": "image"`
5. **Restart manager** - `docker compose restart manager`

**For Both:**
6. **Update server proxy** - If needed, update model list in `app/main.py` and deploy

### Model Behavior
- Models start automatically on first request
- Models stop after 10 minutes of inactivity (configurable via `IDLE_TIMEOUT`)
- First request may take time (model download if not cached)
- Models are cached in `local-ai/models/` and `local-ai/cache/`

### Starting Models Manually
If you want models ready before first request:
```powershell
# Start all text models
docker start vllm-qwen14b-awq
docker start vllm-coder7b
# Note: llama3-8b requires HuggingFace access (gated model)

# Start image model
docker start qwen-image-server

# Check status
Invoke-WebRequest -Uri "http://localhost:8000/status" -UseBasicParsing | ConvertFrom-Json | ConvertTo-Json -Depth 5
```

**Note**: One model failing should not prevent others from being available. Each model container is independent.

### Context Length Management
- **Qwen model limit**: 6144 tokens
- **Automatic truncation**: Conversation history automatically truncated to last 10 messages
- **max_tokens**: Set to 500 (reduced from 1500) to leave room for context
- **Error handling**: Context length errors automatically trigger history truncation and retry
- **Manual reset**: Use `/new` or `/reset` command to start fresh session

## Security Considerations

- Windows firewall should restrict port 8000 to server IP only
- Server proxy uses Traefik with basic auth for external access
- Local network access bypasses auth (192.168.86.0/24)
- Windows AI service should not be directly exposed to internet
- Model containers run with GPU access (requires NVIDIA GPU)

## Related Personas

- **`server-agent.md`** - Server deployment and management
- **`infrastructure-agent.md`** - Network, Traefik, firewall configuration

## Web Interface Features

### Terminal-Style UI
- Retro terminal aesthetic with green glow effects
- Real-time chat interface
- Model selection and status indicators

### Commands
- `/help` - Show available commands
- `/model [name]` - Switch to different model
- `/models` - List available models
- `/clear` - Clear terminal display
- `/new` or `/reset` - Start fresh conversation session (clears history)
- `/upload` - Upload an image for editing (or press Ctrl+U)
- `/image` - Show currently uploaded image
- `/clear-image` - Clear uploaded image

### Loading Indicators
- **Processing timer**: Shows "Processing... (Xs)" during normal requests
- **Model loading bar**: Retro-styled progress bar when model is initializing
  - Polls `/model-loading-progress/{model_name}` endpoint
  - Shows progress percentage and status messages
  - Only appears when model backend is not ready (503 errors)

### Error Handling
- **Context length errors**: Automatically truncates history and retries
- **Model loading errors**: Shows loading bar with progress polling
- **Connection errors**: Clear error messages with troubleshooting hints

### API Endpoints

**Server Proxy Endpoints:**
- `GET /model-loading-progress/{model_name}` - Check model loading status and progress
- `GET /model-status` - Get current model loading status
- `GET /health` - Health check (includes Windows AI connection status)
- `POST /v1/chat/completions` - Chat completions for text models (OpenAI-compatible)
- `POST /v1/images/generations` - Image generation for image models (OpenAI-compatible)
  - Supports `prompt` (text description)
  - Supports `image` (base64 image data for editing)
  - Returns `b64_json` or `url` format

**Windows Manager Endpoints:**
- `GET /healthz` - Manager health check
- `GET /v1/models` - List available models
- `POST /v1/chat/completions` - Proxied to text model containers
- `POST /v1/images/generations` - Proxied to image inference server

**Image Inference Server Endpoints:**
- `GET /health` - Health check (used by manager for readiness)
- `GET /v1/models` - List available image models
- `POST /v1/images/generations` - Generate images from prompts
- `POST /v1/images/edits` - Edit images (image + prompt)

## Known Issues & Solutions

### Llama Model - Gated Repository
**Issue**: `meta-llama/Llama-3.1-8B-Instruct` is a gated model requiring HuggingFace access.

**Solution**:
1. Visit https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct
2. Sign in and accept the model's terms
3. Restart the container: `docker rm vllm-llama3-8b && cd local-ai && bash setup.sh`

**Workaround**: Use `qwen2.5-14b-awq` (default) which is not gated.

### Model Container Not Ready
**Issue**: Container starts but model isn't ready yet (503 errors).

**Solution**: 
- Manager now checks readiness even when container is running
- UI shows loading bar with progress updates
- Wait for model to finish loading (can take 1-5 minutes on first use)
- For image models: First use takes 10-30 minutes (model download + loading)

### "Not Found" (404) Errors from Manager Proxy

**Issue**: Requests to `/v1/chat/completions` or `/v1/images/generations` return 404 "Not Found".

**Root Cause**: Double slash in proxy URL construction (`//v1/chat/completions` instead of `/v1/chat/completions`).

**Solution**:
- Fixed in `manager/manager.py` (line 332): Strip leading slash from path before constructing backend URL
- **Fix applied**: `path = request.url.path.lstrip('/')` before `backend_url = f"http://{container_name}:8000/{path}"`
- **If still seeing 404**: Rebuild manager container:
  ```powershell
  cd local-ai
  docker compose build manager
  docker compose restart manager
  ```

**Verification**:
```powershell
# Check manager logs for double slashes (should NOT appear after fix)
docker logs vllm-manager | Select-String "//v1"

# Check manager code has the fix
docker exec vllm-manager cat /app/manager.py | Select-String "lstrip"

# Test direct container access
docker exec vllm-qwen14b-awq curl -s http://localhost:8000/v1/models

# Test proxy routing through manager
$body = @{model="qwen2.5-14b-awq"; messages=@(@{role="user"; content="test"})} | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost:8000/v1/chat/completions" -Method POST -Body $body -ContentType "application/json"
# Should return 200 OK, not 404
```

### Image Model Issues

**Image model not loading:**

**Dependency Issues:**
- **Error**: `AttributeError: module diffusers has no attribute QwenImageEditPlusPipeline`
- **Error**: `NotImplementedError: auto not supported. Supported strategies are: balanced, cuda`
- **Solution**: Updated dependencies in `image-inference-server/requirements.txt`:
  - `diffusers>=0.30.0` (currently 0.36.0)
  - `transformers>=4.51.3` (currently 4.57.3)
  - Changed `device_map="auto"` to `device_map="cuda"` in `app/main.py`
  - Rebuild image: `cd local-ai/image-inference-server && docker build -t image-inference-server:latest .`

**Model Loading Blocking Server Startup:**
- **Issue**: Server stuck at "Waiting for application startup" while model loads
- **Solution**: Made model loading non-blocking (loads in background task)
- **Fix applied**: Updated `app/main.py` startup event to use async background task
- **Result**: Server starts immediately, model loads in background

**Troubleshooting steps:**
```powershell
# Check container status
docker ps -a --filter name=qwen-image-server

# Check image server logs (look for "Model loaded successfully" or errors)
docker logs qwen-image-server --tail 100

# Check if model is loaded
docker exec qwen-image-server python3 -c "import requests; r = requests.get('http://localhost:8000/health'); print(r.json())"
# Should show: {"status": "healthy", "model_loaded": true/false, "device": "cuda", "cuda_available": true}
# If model_loaded is False, model is still downloading/loading

# Check if model is downloading (look for download progress in logs)
docker logs qwen-image-server 2>&1 | Select-String -Pattern "Downloading|100%|Loading"

# Verify image inference server is built with latest code
docker images | grep image-inference-server

# Rebuild if needed (after code changes)
cd local-ai/image-inference-server
docker build -t image-inference-server:latest .

# Recreate container with new image (if rebuild needed)
docker stop qwen-image-server
docker rm qwen-image-server
cd local-ai
docker create --name qwen-image-server --gpus all -p 8005:8000 `
  -v ${PWD}/models:/models -v ${PWD}/cache:/root/.cache/hf `
  -e MODEL_NAME=Qwen/Qwen-Image-Edit-2509 `
  -e HF_TOKEN=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 `
  --network my-network image-inference-server:latest
docker start qwen-image-server

# Wait for server to start (should be immediate now)
Start-Sleep -Seconds 5
docker logs qwen-image-server --tail 10
# Should see "Application startup complete" quickly
```

**Image generation errors:**
- **503 errors**: Model is still loading (first use takes 10-30 minutes)
  - Check logs: `docker logs qwen-image-server --tail 50`
  - Verify health: `docker exec qwen-image-server curl -s http://localhost:8000/health`
- **400 errors**: Invalid request format or missing required fields
- **Timeout errors**: Image generation can take 30-60 seconds per image
- **GPU memory**: Check with `nvidia-smi` (image models use significant VRAM)
- **Model download**: First use downloads model to `local-ai/cache/huggingface/hub/`

**Container mapping issue:**
- **Old**: Manager used `vllm-qwen-image` for image model container
- **Current**: Manager uses `qwen-image-server` (correct container name)
- If seeing old errors, verify `models.json` has correct container name

### DeepSeek Coder Container Issues

**Issue**: Container fails to start with `RuntimeError: Failed to load the model config`.

**Root Cause**: Model requires `--trust-remote-code` flag.

**Solution**: Updated `setup.sh` to include `--trust-remote-code` flag:
```bash
docker create --name vllm-coder7b ... --trust-remote-code
```

**If container already exists:**
```powershell
# Remove old container
docker stop vllm-coder7b
docker rm vllm-coder7b

# Recreate with trust-remote-code
cd local-ai
docker create --name vllm-coder7b --gpus all -p 8003:8000 `
  -v ${PWD}/models:/models -v ${PWD}/cache:/root/.cache/hf `
  -e HF_TOKEN=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 `
  vllm/vllm-openai:v0.6.3 `
  --model deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct `
  --served-model-name deepseek-coder `
  --download-dir /models --dtype auto `
  --max-model-len 8192 --gpu-memory-utilization 0.90 `
  --trust-remote-code
docker start vllm-coder7b

# Or run setup.sh again (which now includes the flag)
bash setup.sh
```

### Multimodal Support Status

**✅ Completed (2025-01-17):**
- Image inference server built and containerized
- Manager extended to support both text and image models
- Server proxy routes requests based on model type
- UI supports image generation and display
- Image upload and editing functionality
- All 15 tasks in multimodal epic completed

**🔧 Recent Fixes (2025-12-19):**
- **Proxy routing fix**: Fixed double slash issue causing 404 errors (`//v1/chat/completions`)
- **Image model dependencies**: Upgraded to diffusers 0.36.0 and transformers 4.57.3
- **Device map fix**: Changed from `device_map="auto"` to `device_map="cuda"` for QwenImageEditPlusPipeline
- **Non-blocking model loading**: Image server now starts immediately, loads model in background
- **DeepSeek Coder fix**: Added `--trust-remote-code` flag to container creation

**Deployment Status:**
- Image inference server: ✅ Built (`image-inference-server:latest`) with latest fixes
- Image model container: ✅ Created (`qwen-image-server`) with updated image
- Manager: ✅ Running with proxy routing fix applied
- Server proxy: ✅ Deployed with multimodal support
- Text models: ✅ All 3 text models running and ready
  - `qwen2.5-14b-awq`: ✅ Running and ready
  - `deepseek-coder`: ✅ Running and ready (with `--trust-remote-code`)
  - `llama3-8b`: ⚠️ Stopped (gated model - requires HuggingFace access)
- Image model: ✅ Container running, model loading in background
  - Server starts immediately (non-blocking load)
  - Model downloads/loads on first request (10-30 minutes first time)
  - Check status: `docker exec qwen-image-server python3 -c "import requests; r = requests.get('http://localhost:8000/health'); print(r.json())"`
- Ready for: End-to-end testing, image generation, image editing

**Current Operational State (as of 2025-12-19):**
- Manager proxy routing: ✅ Fixed (double slash issue resolved)
- Image model dependencies: ✅ Updated (diffusers 0.36.0, transformers 4.57.3)
- Image model loading: ✅ Non-blocking (server starts immediately)
- Text models: ✅ All available models started and ready
- Gaming mode: ✅ Available via web dashboard (http://localhost:8080)
- Auto-startup: ✅ Configured (Windows Startup Folder method)

## Documentation

- `local-ai/README.md` - Windows setup and usage (includes multimodal info)
- `local-ai/TROUBLESHOOTING.md` - Troubleshooting guide for common issues
- `local-ai/DEPLOYMENT.md` - Deployment guide for multimodal system
- `local-ai/DEPLOYMENT_STATUS.md` - Current deployment status and testing steps
- `local-ai/QUICK_START.md` - Quick reference for setup and usage
- `local-ai/TESTING.md` - Comprehensive testing guide for multimodal system
- `local-ai/RESEARCH_IMAGE_INFERENCE.md` - Research on image inference engines
- `apps/local-ai-app/README.md` - Server proxy setup and API docs
- `local-ai/verify-setup.ps1` - Setup verification script
- `agents/plans/multimodal-inference-support.md` - Original implementation plan

---

## Multimodal Architecture Details

### Image Inference Server

The image inference server (`image-inference-server/`) is a custom FastAPI application that:
- Uses HuggingFace Diffusers library for image generation/editing
- Provides OpenAI-compatible API endpoints
- Runs in Docker container with CUDA support
- Loads models on-demand (first request downloads model)
- Supports both image generation and editing

**Key differences from text models:**
- Uses Diffusers instead of vLLM
- Health check endpoint: `/health` (not `/v1/models`)
- Response format: Base64 image data or URLs
- Longer startup time (10-30 minutes on first use)
- Higher GPU memory requirements

### Request Routing

1. **Client request** → Server proxy (`/v1/images/generations`)
2. **Server proxy** → Validates model is image type
3. **Server proxy** → Windows manager (`/v1/images/generations`)
4. **Manager** → Checks model type from `models.json`
5. **Manager** → Routes to `qwen-image-server:8005` (image inference server)
6. **Image server** → Generates/edits image
7. **Response** → Flows back through manager → proxy → client

### UI Image Features

- **Image upload**: Drag-and-drop or Ctrl+U
- **Image display**: Base64 images rendered in terminal output
- **Image editing**: Upload image + text prompt
- **Image generation**: Text prompt only
- **Model detection**: Automatically uses `/v1/images/generations` for image models

---

**Remember**: Windows changes are local, server changes go through git deployment!

