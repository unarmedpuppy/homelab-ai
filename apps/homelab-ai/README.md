# Homelab AI

Local AI infrastructure deployment for home server. Pulls pre-built Docker images from Harbor.

## Components

| Component | Description | Port | Image |
|-----------|-------------|------|-------|
| **llm-router** | OpenAI-compatible API router | 8012 | `library/llm-router:latest` |
| **dashboard** | React metrics dashboard | 8014 | `library/local-ai-dashboard:latest` |
| **llm-manager** | Unified LLM orchestrator (RTX 3070) | 8015 | `library/llm-manager:latest` |

## Usage

```bash
# Start all services
docker compose -f apps/homelab-ai/docker-compose.yml up -d

# Check status
docker compose -f apps/homelab-ai/docker-compose.yml ps

# View logs
docker logs llm-router -f
docker logs llm-manager -f

# Restart
docker compose -f apps/homelab-ai/docker-compose.yml restart
```

## Endpoints

| Service | URL | Purpose |
|---------|-----|---------|
| LLM Router | https://local-ai-api.server.unarmedpuppy.com | OpenAI-compatible API |
| Dashboard | https://local-ai-dashboard.server.unarmedpuppy.com | Metrics and conversation explorer |
| LLM Manager | http://192.168.86.47:8015/status | Model status and control |

## API Quick Reference

```bash
# Health check
curl https://local-ai-api.server.unarmedpuppy.com/health

# List models
curl https://local-ai-api.server.unarmedpuppy.com/v1/models

# Chat completion
curl https://local-ai-api.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen2.5-7b-awq", "messages": [{"role": "user", "content": "Hello"}]}'
```

## Source Code

Source code and development happens in the [homelab-ai](https://github.com/unarmedpuppy/homelab-ai) repository.

Images are built via CI/CD and pushed to Harbor on merge to main.

## Volumes

| Volume | Purpose |
|--------|---------|
| `huggingface-cache` | Model weights cache |
| `router-data` | Router metrics and memory database |

Both volumes are external and should be created before first run:

```bash
docker volume create huggingface-cache
docker volume create router-data
```

## Network

Uses `my-network` (external) for inter-service communication and Traefik routing.
