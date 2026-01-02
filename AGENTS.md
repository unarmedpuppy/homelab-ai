# Homelab AI - Agent Instructions

**Read this file first.** This is your entry point for understanding and contributing to this project.

## Project Summary

Local AI infrastructure providing OpenAI-compatible API routing, metrics dashboard, and unified LLM orchestration. All components are published as Docker images to Harbor via CI/CD.

**Tech Stack**: Python (FastAPI), TypeScript (React/Vite), Docker

## Repository Structure

```
homelab-ai/
├── llm-router/             # OpenAI-compatible API router
│   ├── Dockerfile
│   ├── router.py           # Main application
│   ├── providers/          # Backend providers
│   └── tools/              # Agent tools
├── dashboard/              # React metrics dashboard
│   ├── Dockerfile
│   ├── src/
│   └── package.json
├── llm-manager/            # Unified LLM orchestrator
│   ├── Dockerfile
│   ├── manager.py          # Main application
│   └── models.json         # Model cards with VRAM requirements
├── image-server/           # Diffusers image inference
├── tts-server/             # Chatterbox TTS inference
├── claude-harness/         # Claude Max CLI wrapper (host systemd service)
│   ├── main.py
│   ├── claude-harness.service
│   └── manage.sh
├── agents/
│   ├── skills/             # Workflow guides
│   ├── reference/          # Documentation
│   └── plans/              # Implementation plans
├── scripts/                # Build scripts
├── docker-compose.yml          # Base (networks, volumes)
├── docker-compose.server.yml   # Server deployment
├── docker-compose.gaming.yml   # Gaming PC deployment
└── .github/workflows/      # CI/CD
```

## Deployment

### Server
```bash
docker compose -f docker-compose.yml -f docker-compose.server.yml up -d
```
Deploys: llm-router, dashboard, llm-manager (always-on mode)

### Gaming PC
```bash
docker compose -f docker-compose.yml -f docker-compose.gaming.yml up -d
```
Deploys: llm-manager (on-demand mode), image-server, tts-server

## Configuration

**All environment-specific values go in `.env`** - never hardcode IPs, domains, or secrets.

```bash
cp .env.example .env
# Edit with your values
```

Key variables:
- `HARBOR_REGISTRY` - Harbor registry URL
- `DOMAIN` - Domain for Traefik labels

## Quick Commands

```bash
# LLM Router development
cd llm-router
pip install -r requirements.txt
uvicorn router:app --reload --port 8000

# Dashboard development
cd dashboard
npm install
npm run dev

# LLM Manager development
cd llm-manager
pip install -r requirements.txt
uvicorn manager:app --reload --port 8000

# Build and push (via CI/CD)
git push origin main  # Triggers GitHub Actions
```

## Code Style

- **Python**: Use ruff for linting
- **TypeScript**: Use ESLint
- Follow existing patterns in each component

## Workflow

### Plan → Act → Test

1. **Plan**: Understand requirements, check existing code
2. **Act**: Implement incrementally, commit often
3. **Test**: Verify locally, ensure linting passes

### Committing

- Commit after each logical unit of work
- Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`
- Push to `main` triggers CI/CD to build and push to Harbor

## Boundaries

### Always Do
- Run linting before committing
- Test changes locally before pushing
- Update documentation when changing APIs
- Use environment variables for all config (no hardcoded IPs/domains/secrets)

### Ask First
- Changing API contracts
- Adding new dependencies
- Modifying CI/CD pipeline

### Never Do
- Commit secrets or credentials
- Hardcode IPs, domains, or environment-specific values
- Push broken code to main
- Skip linting/tests

## Component Details

### LLM Router (`llm-router/`)

OpenAI-compatible API that routes to multiple backends:
- llm-manager instances (server, Gaming PC)
- Cloud providers (overflow)

**Key files**:
- `router.py` - Main FastAPI application
- `providers/` - Backend implementations
- `tools/` - Agent endpoint tools

### Dashboard (`dashboard/`)

React dashboard for metrics and conversation explorer:
- Activity heatmap
- Model usage stats
- Conversation browser
- RAG search

**Key files**:
- `src/App.tsx` - Main application
- `src/components/` - UI components

### LLM Manager (`llm-manager/`)

Unified LLM orchestrator for both server and Gaming PC:
- Auto-detects GPU VRAM and filters available models
- Supports always-on (server) and on-demand (Gaming PC) modes
- Gaming mode support for shared GPU use
- Dynamic vLLM container creation

**Key files**:
- `manager.py` - Main FastAPI application
- `models.json` - Model cards with VRAM requirements

**Configuration via environment**:
- `MODE` - `always-on` or `on-demand`
- `DEFAULT_MODEL` - Model to load at startup
- `GAMING_MODE_ENABLED` - Enable gaming mode feature
- `IDLE_TIMEOUT` - Seconds before unloading idle models

### Image Server (`image-server/`)

Diffusers-based image generation (FLUX).

### TTS Server (`tts-server/`)

Chatterbox Turbo text-to-speech.

## Harbor Images

All 5 images are built via CI/CD:

| Image | Component |
|-------|-----------|
| `llm-router:latest` | LLM Router |
| `local-ai-dashboard:latest` | Dashboard |
| `llm-manager:latest` | LLM Manager |
| `image-server:latest` | Image Server |
| `tts-server:latest` | TTS Server |

## Skills

Agent-discoverable workflow guides in `agents/skills/`:

| Skill | Purpose |
|-------|---------|
| [connect-gaming-pc](agents/skills/connect-gaming-pc/) | SSH to Gaming PC (WSL) |
| [gaming-pc-manager](agents/skills/gaming-pc-manager/) | Interact with llm-manager |
| [test-local-ai-router](agents/skills/test-local-ai-router/) | Test router with memory and metrics |
| [test-tts](agents/skills/test-tts/) | Test Text-to-Speech via Chatterbox |

## Reference Documentation

| Document | Purpose |
|----------|---------|
| [local-ai-router.md](agents/reference/local-ai-router.md) | Quick reference for router API |
| [local-ai-router-usage.md](agents/reference/local-ai-router-usage.md) | Detailed usage examples |
| [local-ai-router-metrics.md](agents/reference/local-ai-router-metrics.md) | Metrics and memory system |
| [local-ai-implementation-details.md](agents/reference/local-ai-implementation-details.md) | Implementation details |
| [local-ai-architecture-audit.md](agents/reference/local-ai-architecture-audit.md) | Architecture audit |

## Related Repositories

- **home-server**: Can optionally reference this repo for deployment, but homelab-ai is now self-contained with docker-compose files
