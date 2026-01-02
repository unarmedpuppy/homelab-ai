# Homelab-AI Stack Debugging Plan

**Created**: 2025-01-02
**Status**: In Progress
**Issue**: server-3070 backend unhealthy - vLLM containers fail with CUDA errors

## Problem Summary

The `server-3070` backend in the homelab-ai stack is unhealthy. The llm-manager tries to spawn vLLM containers dynamically, but they fail with:

```
RuntimeError: Error 804: forward compatibility was attempted on non supported HW
```

This is a CUDA driver/runtime mismatch error caused by improper GPU exposure when spawning containers programmatically.

## Root Cause (IDENTIFIED)

The `llm-manager` component was using the **deprecated** `runtime="nvidia"` parameter when spawning vLLM containers via Docker SDK. Modern Docker requires `device_requests` from `docker.types.DeviceRequest` for proper GPU access.

**Old (broken):**
```python
container = docker_client.containers.create(
    image=VLLM_IMAGE,
    runtime="nvidia",  # Legacy - doesn't work reliably
    ...
)
```

**New (fixed):**
```python
from docker.types import DeviceRequest

container = docker_client.containers.create(
    image=VLLM_IMAGE,
    device_requests=[
        DeviceRequest(count=1, capabilities=[['gpu']])
    ],
    ...
)
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      home-server repo                        │
│         ~/repos/personal/home-server                         │
│                                                              │
│  apps/homelab-ai/docker-compose.yml                          │
│    - Pulls pre-built images from Harbor                      │
│    - Configures for home-server environment (my-network)     │
│    - Sets DOCKER_NETWORK=my-network for spawned containers   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ pulls images from
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     homelab-ai repo                          │
│         ~/repos/personal/homelab-ai                          │
│                                                              │
│  Source code for:                                            │
│    - llm-router (API gateway)                                │
│    - llm-manager (vLLM orchestrator) ◄── THE FIX IS HERE     │
│    - dashboard (React metrics UI)                            │
│                                                              │
│  CI/CD: Push to main → GitHub Actions → Build → Harbor       │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ pushes to
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Harbor Registry                           │
│       harbor.server.unarmedpuppy.com/library/                │
│                                                              │
│  - llm-router:latest                                         │
│  - llm-manager:latest                                        │
│  - local-ai-dashboard:latest                                 │
└─────────────────────────────────────────────────────────────┘
```

## Repository Locations

| Repo | Local Path | Purpose |
|------|------------|---------|
| **home-server** | `~/repos/personal/home-server` | Deployment configs, orchestration |
| **homelab-ai** | `~/repos/personal/homelab-ai` | Source code for AI stack components |

## Key Files

### home-server repo
- `apps/homelab-ai/docker-compose.yml` - Deployment config for server
- `apps/homelab-ai/.env` - Environment variables (API keys, etc.)

### homelab-ai repo
- `llm-manager/manager.py` - **vLLM orchestrator (where GPU fix was applied)**
- `llm-manager/models.json` - Model definitions with VRAM requirements
- `llm-router/router.py` - API gateway
- `docker-compose.server.yml` - Native homelab-ai deployment config
- `.github/workflows/build-and-push.yml` - CI/CD pipeline

## Deployment Workflow

### Making Code Changes (llm-manager, llm-router, dashboard)

1. **Edit source in homelab-ai repo:**
   ```bash
   cd ~/repos/personal/homelab-ai
   # Make changes to llm-manager/manager.py, etc.
   ```

2. **Commit and push to trigger CI/CD:**
   ```bash
   git add -A && git commit -m "fix: description"
   git push origin main
   ```

3. **Wait for GitHub Actions build** (~1-2 minutes):
   - Check: https://github.com/unarmedpuppy/homelab-ai/actions
   - Build pushes new images to Harbor

4. **Deploy to server:**
   ```bash
   # SSH to server
   ssh -p 4242 unarmedpuppy@192.168.86.47
   
   # Pull latest compose config
   cd ~/server && git pull
   
   # Pull new image(s)
   docker compose -f apps/homelab-ai/docker-compose.yml pull
   
   # Restart stack
   docker compose -f apps/homelab-ai/docker-compose.yml up -d
   
   # Verify
   docker logs llm-manager -f
   ```

### Making Config-Only Changes (env vars, compose settings)

1. **Edit in home-server repo:**
   ```bash
   cd ~/repos/personal/home-server
   # Edit apps/homelab-ai/docker-compose.yml
   ```

2. **Commit and push:**
   ```bash
   git add -A && git commit -m "config: description"
   git push origin main
   ```

3. **Deploy to server:**
   ```bash
   ssh -p 4242 unarmedpuppy@192.168.86.47
   cd ~/server && git pull
   docker compose -f apps/homelab-ai/docker-compose.yml up -d
   ```

## Fix Applied (2025-01-02)

### Changes in homelab-ai repo (commit b4966ee):

1. **llm-manager/manager.py:**
   - Added `from docker.types import DeviceRequest`
   - Added `DOCKER_NETWORK` env var (configurable network for spawned containers)
   - Changed `runtime="nvidia"` → `device_requests=[DeviceRequest(count=1, capabilities=[['gpu']])]`
   - Changed hardcoded `network="ai-network"` → `network=DOCKER_NETWORK`

2. **docker-compose.server.yml:**
   - Added `DOCKER_NETWORK=ai-network` to llm-manager env

### Changes in home-server repo (commit 4f4a968d):

1. **apps/homelab-ai/docker-compose.yml:**
   - Added `DOCKER_NETWORK=my-network` to llm-manager env

## Verification Steps

After deploying the fix:

1. **Check llm-manager logs:**
   ```bash
   docker logs llm-manager -f
   ```
   Should see:
   ```
   [qwen2.5-7b-awq] Creating container: vllm-qwen2.5-7b-awq
   [qwen2.5-7b-awq] Image: harbor.server.unarmedpuppy.com/docker-hub/vllm/vllm-openai:v0.4.0
   [qwen2.5-7b-awq] Network: my-network
   [qwen2.5-7b-awq] Container created: abc123...
   [qwen2.5-7b-awq] Container is ready!
   ```

2. **Check spawned vLLM container:**
   ```bash
   docker ps | grep vllm
   docker logs vllm-qwen2.5-7b-awq
   ```

3. **Test API:**
   ```bash
   curl http://localhost:8012/health
   curl http://localhost:8015/status
   ```

4. **Test inference:**
   ```bash
   curl -X POST http://localhost:8012/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "qwen2.5-7b-awq", "messages": [{"role": "user", "content": "Hello"}]}'
   ```

## Server Details

- **SSH**: `ssh -p 4242 unarmedpuppy@192.168.86.47`
- **GPU**: RTX 3070 (8GB VRAM)
- **NVIDIA Driver**: 535.247.01 (CUDA 12.2)
- **Docker Network**: `my-network`

## Current Backend Status (as of issue start)

| Backend | Status | Notes |
|---------|--------|-------|
| gaming-pc-3090 | healthy | RTX 3090 on gaming PC |
| server-3070 | **unhealthy** | Fix in progress |
| zai | healthy | Cloud provider |
| claude-harness | healthy | Claude Max wrapper |

## Next Steps

- [ ] Wait for CI/CD build to complete
- [ ] Pull new llm-manager image on server
- [ ] Restart homelab-ai stack
- [ ] Verify server-3070 becomes healthy
- [ ] Test inference through the router

## Troubleshooting

### If vLLM still fails after fix:

1. **Check if old vLLM container exists:**
   ```bash
   docker rm -f vllm-qwen2.5-7b-awq
   ```

2. **Verify GPU access from llm-manager:**
   ```bash
   docker exec llm-manager nvidia-smi
   ```

3. **Check Docker network exists:**
   ```bash
   docker network ls | grep my-network
   ```

4. **Manual vLLM test (bypass llm-manager):**
   ```bash
   docker run --rm --gpus all \
     harbor.server.unarmedpuppy.com/docker-hub/vllm/vllm-openai:v0.4.0 \
     --model Qwen/Qwen2.5-7B-Instruct-AWQ \
     --quantization awq \
     --max-model-len 4096
   ```

### If network mismatch:

Spawned containers must be on same network as llm-manager to communicate. Verify `DOCKER_NETWORK` env var matches the network llm-manager is on.

## Related Documentation

- [homelab-ai README](https://github.com/unarmedpuppy/homelab-ai)
- [llm-manager source](~/repos/personal/homelab-ai/llm-manager/manager.py)
- [Docker SDK DeviceRequest docs](https://docker-py.readthedocs.io/en/stable/api.html#docker.types.DeviceRequest)
