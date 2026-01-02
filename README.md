# Homelab AI

Local AI infrastructure for home server deployment. OpenAI-compatible API routing, metrics dashboard, and unified vLLM orchestration.

## Components

| Component | Description | Harbor Image |
|-----------|-------------|--------------|
| **llm-router** | OpenAI-compatible API router with intelligent backend selection | `llm-router:latest` |
| **dashboard** | React metrics dashboard with conversation explorer | `local-ai-dashboard:latest` |
| **llm-manager** | Unified LLM orchestrator with GPU auto-detection and model cards | `llm-manager:latest` |
| **image-server** | Diffusers-based image generation (FLUX) | `image-server:latest` |
| **tts-server** | Chatterbox Turbo text-to-speech | `tts-server:latest` |

All images are built via CI/CD and pushed to Harbor on merge to main.

## Quick Start

### Server Deployment

```bash
# Clone and configure
git clone git@github.com:unarmedpuppy/homelab-ai.git
cd homelab-ai
cp .env.example .env
# Edit .env with your Harbor registry URL

# Deploy server stack (router, dashboard, llm-manager)
docker compose -f docker-compose.yml -f docker-compose.server.yml up -d
```

### Gaming PC Deployment

```bash
# Same repo, different compose file
docker compose -f docker-compose.yml -f docker-compose.gaming.yml up -d
```

### Local Development

```bash
# LLM Router
cd llm-router
pip install -r requirements.txt
uvicorn router:app --host 0.0.0.0 --port 8000

# Dashboard
cd dashboard
npm install
npm run dev

# LLM Manager
cd llm-manager
pip install -r requirements.txt
uvicorn manager:app --host 0.0.0.0 --port 8000
```

## Architecture

```
                                    ┌─────────────────┐
                                    │   Clients       │
                                    │ (Apps, Agents)  │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │   LLM Router    │
                                    │ (OpenAI API)    │
                                    └────────┬────────┘
                         ┌───────────────────┼───────────────────┐
                         │                   │                   │
                ┌────────▼────────┐ ┌────────▼────────┐ ┌────────▼────────┐
                │  Gaming PC      │ │  Server         │ │  Cloud          │
                │  llm-manager    │ │  llm-manager    │ │  (Overflow)     │
                │  (on-demand)    │ │  (always-on)    │ │                 │
                │  + image-server │ │                 │ │                 │
                │  + tts-server   │ │                 │ │                 │
                └─────────────────┘ └─────────────────┘ └─────────────────┘
```

## LLM Manager

The unified model orchestrator that runs on both server and Gaming PC:

### Configuration via Environment Variables

| Variable | Server | Gaming PC | Description |
|----------|--------|-----------|-------------|
| `MODE` | `always-on` | `on-demand` | Keep model loaded vs load on request |
| `DEFAULT_MODEL` | `qwen2.5-7b-awq` | `qwen2.5-14b-awq` | Model to load at startup |
| `GAMING_MODE_ENABLED` | `false` | `true` | Enable gaming mode feature |
| `IDLE_TIMEOUT` | `0` | `600` | Seconds before unloading idle models |

### Model Cards

Models are defined in `llm-manager/models.json` with VRAM requirements:

```json
{
  "models": [
    {
      "id": "qwen2.5-7b-awq",
      "hf_model": "Qwen/Qwen2.5-7B-Instruct-AWQ",
      "vram_gb": 5,
      "type": "text"
    }
  ]
}
```

At startup, the manager detects GPU VRAM and filters to models that fit.

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /status` | Detailed status of all models and GPU |
| `GET /v1/models` | OpenAI-compatible model list |
| `POST /start/{model_id}` | Explicitly start a model |
| `POST /stop/{model_id}` | Stop a model |
| `POST /gaming-mode` | Toggle gaming mode |
| `POST /v1/chat/completions` | Proxy to running model |

## Docker Compose Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Base (networks, volumes) |
| `docker-compose.server.yml` | Server stack (router, dashboard, llm-manager) |
| `docker-compose.gaming.yml` | Gaming PC stack (llm-manager, image-server, tts-server) |

## CI/CD

GitHub Actions builds all 5 images on merge to main:

- **llm-router** - Python FastAPI
- **dashboard** - React/Vite + nginx
- **llm-manager** - Python FastAPI
- **image-server** - Python + Diffusers (CUDA)
- **tts-server** - Python + Chatterbox (CUDA)

Required GitHub Secrets:
- `HARBOR_REGISTRY` - Harbor registry URL
- `HARBOR_USERNAME` - Harbor username
- `HARBOR_PASSWORD` - Harbor password

## Configuration

All environment-specific configuration is done via `.env` file:

```bash
cp .env.example .env
```

Key variables:
- `HARBOR_REGISTRY` - Your Harbor registry URL
- `DOMAIN` - Your domain for Traefik labels
- `SERVER_IP` - Server IP for homepage labels

## Documentation

- [LLM Router Documentation](llm-router/README.md)
- [Dashboard Documentation](dashboard/README.md)
- [Agent Skills](agents/skills/)
- [Reference Docs](agents/reference/)
