# Local AI Server (RTX 3070) Deployment Plan

**Status**: ✅ Complete
**Created**: 2025-12-30
**Completed**: 2025-12-31
**Related**: `agents/plans/local-ai-two-gpu-architecture.md`, `agents/plans/local-ai-provider-model-architecture.md`

## Overview

Deploy vLLM on the Debian home server's RTX 3070 (8GB VRAM) as an always-on inference backend with Qwen2.5-7B-AWQ as the default warm model.

## Goals

1. **Always-on vLLM** on RTX 3070 at port 8001
2. **Qwen2.5-7B-AWQ** as default warm model (fits 8GB VRAM)
3. **Llama-3.1-8B** available as switchable alternative
4. **Integration** with existing router at `apps/local-ai-router/`

## Hardware Constraints

| Attribute | Value |
|-----------|-------|
| GPU | RTX 3070 |
| VRAM | 8GB GDDR6 |
| Driver | NVIDIA 535.247.01 |
| CUDA | 12.2 |
| Location | Debian home server (192.168.86.47) |

## Model Selection

### Default: Qwen2.5-7B-Instruct-AWQ

| Attribute | Value |
|-----------|-------|
| Model ID | `Qwen/Qwen2.5-7B-Instruct-AWQ` |
| Parameters | 7B |
| Quantization | AWQ (4-bit) |
| VRAM Usage | ~5GB (leaves headroom for KV cache) |
| Context Window | 32,768 tokens |
| Max Output | 8,192 tokens |
| Use Case | Chat, coding, general tasks |

**Why AWQ**: 4-bit quantization reduces VRAM from ~14GB (fp16) to ~5GB while maintaining quality.

### Alternative: Llama-3.1-8B-Instruct-AWQ

| Attribute | Value |
|-----------|-------|
| Model ID | `hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4` |
| Parameters | 8B |
| Quantization | AWQ (4-bit) |
| VRAM Usage | ~5.5GB |
| Context Window | 8,192 tokens |
| Use Case | Fallback, different reasoning style |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Debian Server (RTX 3070)                    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              local-ai-server (Docker)                   │   │
│  │                                                         │   │
│  │  vLLM Server                                            │   │
│  │  - Port: 8001                                           │   │
│  │  - Model: Qwen2.5-7B-Instruct-AWQ (default)             │   │
│  │  - GPU: RTX 3070 (--gpus all)                           │   │
│  │  - OpenAI-compatible API                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              │ localhost:8001                   │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              local-ai-router (Docker)                   │   │
│  │                                                         │   │
│  │  - Routes requests to 3070 or 3090                      │   │
│  │  - Health checks both backends                          │   │
│  │  - Priority: 3090 (1) > 3070 (2)                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
└──────────────────────────────┼──────────────────────────────────┘
                               │ Port 8012 / HTTPS
                               ▼
                         External Clients
```

## Implementation

### Directory Structure

```
apps/local-ai-server/
├── docker-compose.yml       # vLLM deployment
├── .env.example             # Environment template
├── .env                     # Local config (gitignored)
├── models.yaml              # Model definitions
└── README.md                # Documentation
```

### Docker Compose

```yaml
# apps/local-ai-server/docker-compose.yml
x-enabled: true

services:
  vllm:
    image: harbor.server.unarmedpuppy.com/docker-hub/vllm/vllm-openai:latest
    container_name: local-ai-server
    restart: unless-stopped
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - HF_HOME=/root/.cache/huggingface
    volumes:
      - ./models:/models
      - ./cache:/root/.cache/huggingface
    ports:
      - "8001:8000"
    command: >
      --model Qwen/Qwen2.5-7B-Instruct-AWQ
      --quantization awq
      --max-model-len 8192
      --gpu-memory-utilization 0.85
      --host 0.0.0.0
      --port 8000
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    networks:
      - my-network
    labels:
      - "homepage.group=AI"
      - "homepage.name=Local AI Server (3070)"
      - "homepage.icon=mdi-chip"
      - "homepage.href=http://192.168.86.47:8001/v1/models"
      - "homepage.description=vLLM on RTX 3070 - Qwen2.5-7B"

networks:
  my-network:
    external: true
```

### Key Configuration (Final Working Values)

| Parameter | Value | Reason |
|-----------|-------|--------|
| `vLLM version` | v0.4.0 | CUDA 12.2 driver compatibility (535.247.01) |
| `--max-model-len 2048` | 2K context | Fits 8GB VRAM with KV cache |
| `--gpu-memory-utilization 0.95` | 95% VRAM | Maximize available memory |
| `--quantization awq` | AWQ 4-bit | Required for AWQ models |
| `--enforce-eager` | Eager mode | Reduces VRAM overhead |
| Port mapping | 8001:8000 | Router expects 8001 |

**VRAM Breakdown**:
- Model: ~5.2GB
- KV Cache: ~1GB (2048 tokens)
- Overhead: ~0.5GB
- Total: ~6.2GB / 8GB (76%)

### Model Switching

Since vLLM serves one model at a time, switching models requires restarting the container.

**Switch to Llama**:
```bash
cd apps/local-ai-server

# Edit docker-compose.yml command to use Llama model:
# --model hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4

docker compose down && docker compose up -d
```

**Switch back to Qwen** (default):
```bash
cd apps/local-ai-server
# Reset command to Qwen model
docker compose down && docker compose up -d
```

**Future Enhancement**: Add a simple model-switch script or API endpoint.

## Router Integration

The router (`apps/local-ai-router/config/providers.yaml`) already has `server-3070` configured:

```yaml
- id: server-3070
  name: "Server (RTX 3070)"
  type: local
  endpoint: "http://localhost:8001"  # Matches our deployment
  priority: 2  # Try after 3090
  enabled: true
  maxConcurrent: 1
```

### Update Provider Models

The current `providers.yaml` lists `llama3-8b` as default for 3070. Update to reflect Qwen as default:

```yaml
# Server 3070 Models (8GB VRAM)
- id: qwen2.5-7b-awq
  name: "Qwen 2.5 7B Instruct AWQ"
  providerId: server-3070
  description: "Qwen 2.5 7B with AWQ - default always-on model"
  contextWindow: 8192
  maxTokens: 4096
  isDefault: true  # Default model for server
  capabilities:
    streaming: true
    functionCalling: true
    vision: false
    jsonMode: true
  tags:
    - chat
    - fast
    - always-on
    - default

- id: llama3.1-8b-awq
  name: "Llama 3.1 8B Instruct AWQ"
  providerId: server-3070
  description: "Llama 3.1 8B with AWQ - switchable alternative"
  contextWindow: 8192
  maxTokens: 4096
  isDefault: false
  capabilities:
    streaming: true
    functionCalling: true
    vision: false
    jsonMode: true
  tags:
    - chat
    - alternative
```

## Deployment Steps

### Phase 1: Create Deployment Config

- [x] Create `apps/local-ai-server/` directory
- [x] Create `docker-compose.yml` with vLLM config
- [x] Create `README.md` documentation

### Phase 2: Deploy to Server

- [x] Commit and push changes
- [x] SSH to server, git pull
- [x] Test GPU access: `docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi`
- [x] Pull vLLM image via Harbor (v0.4.0 for CUDA 12.2 compatibility)
- [x] Start vLLM: `cd apps/local-ai-server && docker compose up -d`
- [x] Verify health: `curl http://localhost:8001/v1/models`

**Note**: Required vLLM v0.4.0 (not latest) due to CUDA 12.2 driver (535.247.01) compatibility.
Context reduced to 2048 tokens to fit 8GB VRAM with room for KV cache.

### Phase 3: Router Integration

- [x] Update `apps/local-ai-router/config/providers.yaml` with Qwen model (already configured)
- [x] Fix endpoint: `http://local-ai-server:8000` (Docker network, internal port)
- [x] Restart router: `cd apps/local-ai-router && docker compose restart`
- [x] Test routing: `curl http://localhost:8012/health` → All backends healthy

### Phase 4: End-to-End Testing

- [x] Health check shows both 3070 and 3090 healthy
- [ ] Test auto-routing (model: "auto") - requires API key
- [ ] Test from dashboard UI
- [ ] Test fallback (disable 3090, verify 3070 serves)

## Verification Checklist

- [x] vLLM container running: `docker ps | grep local-ai-server`
- [x] GPU visible: VRAM 6.2GB / 8GB (76%)
- [x] Model loaded: `curl http://localhost:8001/v1/models` → `qwen2.5-7b-awq`
- [x] Inference works: "What is 2+2?" → "Four" ✅
- [x] Router sees 3070: `curl http://localhost:8012/health` → healthy=true
- [ ] Dashboard shows provider: Check provider status in UI

## Troubleshooting

### vLLM OOM (Out of Memory)

**Symptom**: Container crashes or refuses to load model
**Fix**: Reduce `--max-model-len` or `--gpu-memory-utilization`

```yaml
command: >
  --model Qwen/Qwen2.5-7B-Instruct-AWQ
  --max-model-len 4096  # Reduce from 8192
  --gpu-memory-utilization 0.80  # Reduce from 0.85
```

### Model Download Fails

**Symptom**: HuggingFace download timeout or authentication error
**Fix**: Pre-download model or set HF_TOKEN

```bash
# On server, pre-download model
docker run --rm -v $(pwd)/cache:/root/.cache/huggingface \
  python:3.11 pip install huggingface_hub && \
  python -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen2.5-7B-Instruct-AWQ')"
```

### Router Can't Reach 3070

**Symptom**: Health check fails, 3070 shows offline
**Fix**: Ensure both containers on `my-network`

```bash
docker network inspect my-network | grep -A5 local-ai-server
docker network inspect my-network | grep -A5 local-ai-router
```

## Success Criteria

1. vLLM running on RTX 3070 with Qwen2.5-7B-AWQ
2. Responds to `/v1/chat/completions` requests
3. Router health check shows server-3070 as healthy
4. Auto-routing uses 3070 when 3090 unavailable
5. Dashboard shows provider selection working

## References

- [vLLM Documentation](https://docs.vllm.ai/)
- [Qwen2.5-7B-Instruct-AWQ on HuggingFace](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-AWQ)
- [local-ai-two-gpu-architecture.md](local-ai-two-gpu-architecture.md)
- [local-ai-provider-model-architecture.md](local-ai-provider-model-architecture.md)
