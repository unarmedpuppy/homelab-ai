# Homelab AI

Local AI infrastructure for home server deployment. OpenAI-compatible API routing, metrics dashboard, and inference servers.

## Components

| Component | Description | Deployment |
|-----------|-------------|------------|
| **Router** | OpenAI-compatible API router with intelligent backend selection | Home Server (Docker) |
| **Dashboard** | React metrics dashboard with conversation explorer | Home Server (Docker) |
| **Manager** | Container lifecycle manager for GPU inference | Gaming PC (local build) |
| **Image Server** | Diffusers-based image generation | Gaming PC (local build) |
| **TTS Server** | Chatterbox Turbo text-to-speech | Gaming PC (local build) |

## Quick Start

### Home Server (via Harbor)

The router and dashboard are published to Harbor and consumed by home-server:

```yaml
# In home-server/apps/local-ai-router/docker-compose.yml
services:
  local-ai-router:
    image: ${HARBOR_REGISTRY}/${HARBOR_PROJECT}/local-ai-router:latest
```

### Local Development

```bash
# Clone the repo
git clone git@github.com:unarmedpuppy/homelab-ai.git
cd homelab-ai

# Copy environment and configure
cp .env.example .env
# Edit .env with your values

# Run router locally
cd router
pip install -r requirements.txt
uvicorn router:app --host 0.0.0.0 --port 8000

# Run dashboard locally
cd dashboard
npm install
npm run dev
```

### Gaming PC

```powershell
# Clone and build
git clone git@github.com:unarmedpuppy/homelab-ai.git
cd homelab-ai\scripts
.\build-tts-server.ps1
```

## Configuration

All environment-specific configuration is done via `.env` file. Copy `.env.example` and fill in your values:

```bash
cp .env.example .env
```

Key configuration:
- `HARBOR_REGISTRY` - Your Harbor registry URL
- `GAMING_PC_URL` - IP/port of your gaming PC running the manager
- `SERVER_SSH_*` - SSH access for agent endpoint
- `DOMAIN` - Your domain for Traefik labels

## Architecture

```
                                    ┌─────────────────┐
                                    │   Clients       │
                                    │ (Apps, Agents)  │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │   Router        │
                                    │ (OpenAI API)    │
                                    └────────┬────────┘
                         ┌───────────────────┼───────────────────┐
                         │                   │                   │
                ┌────────▼────────┐ ┌────────▼────────┐ ┌────────▼────────┐
                │  Gaming PC      │ │  Server GPU     │ │  Cloud          │
                │  (Primary GPU)  │ │  (Fallback)     │ │  (Overflow)     │
                │  - Manager      │ │  - vLLM         │ │                 │
                │  - TTS          │ │                 │ │                 │
                │  - Image        │ │                 │ │                 │
                └─────────────────┘ └─────────────────┘ └─────────────────┘
```

## Harbor Images

Images are tagged with both `:latest` and `:SHA`:

```
${HARBOR_REGISTRY}/${HARBOR_PROJECT}/local-ai-router:latest
${HARBOR_REGISTRY}/${HARBOR_PROJECT}/local-ai-dashboard:latest
```

## CI/CD

GitHub Actions automatically builds and pushes to Harbor on merge to main:

- **Trigger**: Push to `main` with changes in `router/` or `dashboard/`
- **Steps**: Lint → Test → Build → Push to Harbor
- **Tags**: `:latest` and `:SHA`

Required GitHub Secrets:
- `HARBOR_USERNAME`
- `HARBOR_PASSWORD`

## Documentation

- [Router Documentation](router/README.md)
- [Dashboard Documentation](dashboard/README.md)
- [Agent Skills](agents/skills/)
- [Reference Docs](agents/reference/)
