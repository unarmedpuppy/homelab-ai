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

## Data Migration (IMPORTANT)

**Before first deploy**, copy existing data from the old local-ai-router:

```bash
# On the server, create data directory and copy existing data
mkdir -p ~/server/apps/homelab-ai/data
cp -r ~/server/apps/local-ai-router/data/* ~/server/apps/homelab-ai/data/

# Verify the database was copied
ls -la ~/server/apps/homelab-ai/data/
# Should show: local-ai-router.db (contains conversations, metrics, etc.)
```

This preserves all your:
- Conversation history
- Metrics data  
- RAG search embeddings

## Environment Variables

Create `.env` from the example template:

```bash
# On the server
cd ~/server/apps/homelab-ai
cp .env.example .env
nano .env  # Fill in your API keys
```

**Required variables:**

| Variable | Description | Required |
|----------|-------------|----------|
| `ZAI_API_KEY` | Z.ai API key for GLM models | Yes (if using Z.ai) |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude | Optional (if using Claude Harness) |
| `GAMING_PC_URL` | Gaming PC endpoint | No (defaults to `http://192.168.86.63:8000`) |

**Get API keys:**
- Z.ai: https://z.ai (use existing key from 1Password)
- Anthropic: https://console.anthropic.com/settings/keys

## Volumes

| Volume | Location | Purpose |
|--------|----------|---------|
| `./data` | Bind mount | Router database (conversations, metrics) |
| `huggingface-cache` | Named volume | Model weights cache |

Create the external volume before first run:

```bash
docker volume create huggingface-cache
```

## Network

Uses `my-network` (external) for inter-service communication and Traefik routing.
