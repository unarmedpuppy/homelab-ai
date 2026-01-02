# Local AI Server (RTX 3070)

Always-on vLLM inference server running on the home server's RTX 3070 (8GB VRAM).

## Overview

| Attribute | Value |
|-----------|-------|
| **GPU** | RTX 3070 (8GB VRAM) |
| **Default Model** | Qwen2.5-7B-Instruct-AWQ |
| **Port** | 8001 |
| **API** | OpenAI-compatible (`/v1/chat/completions`) |
| **Status** | Always-on (warm model) |

## Quick Start

```bash
# Start the server
docker compose up -d

# Check status
docker compose logs -f

# Verify model is loaded
curl http://localhost:8001/v1/models
```

## API Usage

```bash
# Chat completion
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-7b-awq",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'

# Streaming
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-7b-awq",
    "messages": [{"role": "user", "content": "Write a haiku"}],
    "stream": true
  }'
```

## Models

### Default: Qwen2.5-7B-Instruct-AWQ

- **Model ID**: `Qwen/Qwen2.5-7B-Instruct-AWQ`
- **Served Name**: `qwen2.5-7b-awq`
- **VRAM**: ~5GB (AWQ 4-bit quantization)
- **Context**: 8,192 tokens (limited for VRAM)
- **Use Case**: Chat, coding, general tasks

### Alternative: Llama 3.1 8B AWQ

To switch to Llama, edit `docker-compose.yml`:

```yaml
command: >
  --model hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4
  --quantization awq
  --max-model-len 8192
  --gpu-memory-utilization 0.85
  --host 0.0.0.0
  --port 8000
  --served-model-name llama3.1-8b-awq
```

Then restart:

```bash
docker compose down && docker compose up -d
```

## Integration

This server integrates with the Local AI Router (`apps/local-ai-router/`):

- Router endpoint: `http://local-ai-server:8001` (Docker network)
- Provider ID: `server-3070`
- Priority: 2 (fallback after 3090)

The router automatically routes requests here when:
1. 3090 (gaming PC) is unavailable
2. Gaming mode is enabled on 3090
3. Explicit `server-3070` provider is requested

## Troubleshooting

### Model Loading Slow

First startup downloads the model (~4GB). Subsequent starts are faster due to cached weights.

```bash
# Monitor download progress
docker compose logs -f
```

### Out of Memory (OOM)

If the container crashes with OOM:

1. Reduce context length:
   ```yaml
   --max-model-len 4096  # Instead of 8192
   ```

2. Reduce GPU memory utilization:
   ```yaml
   --gpu-memory-utilization 0.80  # Instead of 0.85
   ```

### GPU Not Detected

Verify NVIDIA runtime is configured:

```bash
# Test GPU access
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi

# Check Docker runtime
docker info | grep -i nvidia
```

### Health Check Failing

Model loading takes ~60-120 seconds. Check logs:

```bash
docker compose logs --tail 50
```

## Maintenance

### View Logs

```bash
docker compose logs -f
```

### Restart

```bash
docker compose restart
```

### Update Model

```bash
# Pull latest vLLM image
docker compose pull

# Restart with new image
docker compose down && docker compose up -d
```

### Clear Cache

```bash
# Remove cached models (will re-download on next start)
docker volume rm local-ai-huggingface-cache
```

## Related

- [Local AI Router](../local-ai-router/README.md) - API router
- [Local AI Dashboard](../local-ai-dashboard/README.md) - Web UI
- [Gaming PC Setup](../../local-ai/README.md) - RTX 3090 backend
