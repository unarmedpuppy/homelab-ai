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
├── agent-gateway/          # Agent fleet status aggregator
│   ├── Dockerfile
│   ├── gateway.py          # Main FastAPI application
│   ├── config.yaml         # Agent registry configuration
│   └── health.py           # Background health monitor
├── image-server/           # Diffusers image inference
├── tts-server/             # Chatterbox TTS inference
├── claude-harness/         # DEPRECATED - see agent-harness repo
│   └── README.md           # Contains migration notice
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
Deploys: llm-router, dashboard, llm-manager (always-on mode), agent-gateway

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
- `routers/anthropic.py` - Anthropic Messages API compatibility layer
- `tools/` - Agent endpoint tools

**Anthropic Compatibility (`/v1/messages`)**:

The router speaks both OpenAI format (`/v1/chat/completions`) and Anthropic format (`/v1/messages`). Point Claude Code here to route to local models by default.

Endpoints:
- `POST /v1/messages` — Anthropic Messages API (translates to OpenAI, routes via ProviderManager)
- `POST /v1/messages/count_tokens` — Token counting pre-flight

Auth: Accepts `x-api-key: <llm-router-key>` (Anthropic SDK default) or `Authorization: Bearer`.

Routing chain (priority order):
1. gaming-pc-3090 (`qwen3.5-27b-abliterated`) — default (dual-GPU TP=2, 65K context)
2. zai (`glm-5`) — escalation / gaming mode
3. claude-harness (`claude-sonnet-4-5`) — last resort

Claude Code config:
```bash
export ANTHROPIC_BASE_URL=https://homelab-ai.server.unarmedpuppy.com
export ANTHROPIC_API_KEY=<your-llm-router-api-key>
```

Claude model names accepted by the OpenAI endpoint (via `MODEL_ALIASES`):
- `claude-sonnet-4-6` → `qwen3.5-27b-abliterated`
- `claude-opus-4-6` → `qwen3.5-27b-abliterated`
- `claude-haiku-4-5` → `qwen2.5-14b-awq`
- `claude-3-5-sonnet` → `qwen3.5-27b-abliterated`

### Dashboard (`dashboard/`)

React dashboard with retro/pixel-art "command center" UI for AI infrastructure management:

**Routes**:
| Route | View | Description |
|-------|------|-------------|
| `/` | Chat | Streaming chat with provider selection, TTS toggle, image upload |
| `/chat/:conversationId` | Chat | Resume existing conversation |
| `/providers` | Providers | Provider health monitoring and utilization |
| `/stats` | Stats | Activity heatmap, model usage charts |
| `/agents` | Agents | Agent run history and logs |
| `/sessions` | Sessions | Claude Code session traces — tool calls, spans, transcripts |
| `/command` | Command | AoE2-style agent command interface (Phaser 3 isometric map) |

**Command page** (`src/command/`) — lazy-loaded Phaser 3 game embedded in the dashboard:
- Isometric map with named agent units (Avery, Gilfoyle, Ralph, Jobin) + villagers
- Buildings represent projects; right-click to assign agents and dispatch jobs
- Live job polling from agent-harness; unit animations reflect job state
- React HUD overlay (top bar: tokens/credits/jobs, bottom panel: selected unit/job details, prompt bar)
- Assets in `public/assets/`: `units/`, `buildings/`, `tiles/`
- API calls proxied through nginx: `/api/harness/` → agent-harness, `/api/router/` → llm-router, `/api/tasks/` → tasks-api

**Key files**:
- `src/App.tsx` - Main application and routing
- `src/components/ui/` - Retro design system components
- `src/styles/retro-theme.css` - CSS custom properties for retro theme

**Retro Design System** (`src/components/ui/`):

Reusable UI component library with pixel-art styling:

| Component | Description |
|-----------|-------------|
| `RetroCard` | Pixelated border card with variants (default, highlight, warning, success) |
| `RetroButton` | Action buttons (primary, secondary, danger, ghost, success, warning) |
| `RetroBadge` | Status/priority badges with semantic variants |
| `RetroPanel` | Bordered panel with optional title |
| `RetroProgress` | Segmented progress bar |
| `RetroInput` | Text input field |
| `RetroSelect` | Dropdown selector |
| `RetroModal` | Dialog with mobile fullscreen support |
| `RetroCheckbox` | Styled checkbox |
| `RetroStats` | Stats display bar |
| `MobileNav` | Bottom navigation for mobile devices |
| `ResponsiveLayout` | Mobile-first layout wrapper with sidebar support |

See `dashboard/src/components/ui/README.md` for component documentation.

### Hardware

| Host | GPU | VRAM | Role |
|------|-----|------|------|
| Gaming PC (192.168.86.63) | 2x RTX 3090 | 48GB total | Primary inference (dual-GPU TP=2) |
| Home Server | RTX 3070 | 8GB | Always-on small models (manual access only) |

**Gaming PC GPU note**: `llm-manager` reports `gpu_vram_gb: 24` — this is the **primary GPU only**. Total VRAM is 48GB. Models with `gpu_count: 2` use tensor parallel across both cards and get `ipc_mode=host`. Always use `gpu_count: 2` for large models on the gaming PC.

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

### Fleet Gateway (`fleet-gateway/`)

Agent fleet status aggregator and LLM trace pipeline. Provides:
- Agent registry + health monitoring (all agents: Ralph, Avery, Jobin, Gilfoyle)
- Trace ingestion from Claude Code hooks (POST /traces/events)
- Session and span storage in SQLite (`traces.db`)
- Transcript reading from Claude Code JSONL session files
- REST API for dashboard queries

**Key files**:
- `gateway.py` - Main FastAPI application (agents API + traces API)
- `traces.py` - SQLite schema + query functions for session/span storage
- `config.yaml` - Agent registry with endpoints
- `health.py` - Background health monitor

**Trace API Endpoints**:
- `POST /traces/events` — Ingest hook payload (called by claude-trace-forwarder.sh)
- `GET /traces` — List sessions with filters (machine_id, agent_label, from/to date)
- `GET /traces/{session_id}` — Session detail + all spans
- `GET /traces/stats` — Counts by machine/day, active sessions
- `GET /traces/{session_id}/transcript` — Parsed conversation from JSONL (server sessions only)

**Volume mounts** (in `home-server/apps/homelab-ai/docker-compose.yml`):
- `./fleet-gateway-data:/app/data` — SQLite traces.db persisted on host
- `homelab-ai_claude-credentials:/claude-sessions:ro` — Claude Code session files for transcript reading

**Port**: 8016 (host: 8017)

**Full reference**: `home-server/agents/reference/agent-trace-pipeline.md`

### Agent Gateway (`agent-gateway/`)

Fleet status aggregator for Claude Code agents. Monitors health of all registered agents (Ralph, Avery, Jobin, Gilfoyle) and provides a unified API.

**Key files**:
- `gateway.py` - Main FastAPI application
- `config.yaml` - Agent registry with endpoints
- `health.py` - Background health monitor

**API Endpoints**:
- `GET /api/agents` - List all agents with current status
- `GET /api/agents/{id}` - Get single agent details
- `GET /api/agents/stats` - Fleet-wide statistics
- `POST /api/agents/{id}/check` - Force immediate health check

**Configuration via environment**:
- `CONFIG_PATH` - Path to config.yaml (default: `./config.yaml`)
- `LOG_LEVEL` - Logging level (default: `INFO`)

**Port**: 8016

## Harbor Images

All 6 images are built via CI/CD:

| Image | Component |
|-------|-----------|
| `llm-router:latest` | LLM Router |
| `local-ai-dashboard:latest` | Dashboard |
| `llm-manager:latest` | LLM Manager |
| `agent-gateway:latest` | Agent Gateway |
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
