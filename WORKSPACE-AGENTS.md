# Homelab Workspace - Agent Instructions

**Read this file first.** Entry point for working across all homelab repositories.

## Overview

This is a multi-repository workspace containing homelab projects. Each repo has its own `AGENTS.md` for repo-specific guidance. This file covers cross-project conventions, deployment patterns, and how repositories relate.

**Domain**: `server.unarmedpuppy.com`
**Registry**: `harbor.server.unarmedpuppy.com`
**Git Server**: `gitea.server.unarmedpuppy.com` (source of truth)
**Git Org**: `homelab`

> **IMPORTANT**: Gitea (`homelab` org) is the source of truth. GitHub is auto-synced backup.

## Repository Structure

All repos are siblings in the workspace directory:

```
<workspace>/
├── AGENTS.md              ← Symlink to home-server/WORKSPACE-AGENTS.md
├── home-server/           ← Server infrastructure + beads database
│   ├── .beads/            ← Task tracking (source of truth)
│   └── AGENTS.md
├── homelab-ai/            ← AI services (LLM router, claude-harness)
├── polyjuiced/            ← Trading bot
├── pokedex/               ← Pokemon app
├── trading-journal/       ← Trade tracking
├── agent-gateway/         ← Agent gateway
├── beads-viewer/          ← Task graph viewer
├── maptapdat/             ← Maptap dashboard
├── shua-ledger/           ← Personal finance
├── bird/                  ← Twitter/X data
└── workflows/             ← Shared CI/CD
```

## Task Management (Beads)

**Source of truth**: `./home-server/.beads/`

All tasks across ALL projects are tracked centrally in home-server. Run `bd` commands from that directory:

```bash
cd ./home-server
bd ready              # Find unblocked work
bd list               # View all tasks
bd create "title" -p 1 -l "label"  # Create task
bd close <id>         # Complete task
```

### Ralph Wiggum (Autonomous Task Loop)

Process tasks automatically via API:

```bash
# Start processing tasks with a label
curl -X POST http://claude-harness.server.unarmedpuppy.com/v1/ralph/start \
  -H "Content-Type: application/json" \
  -d '{"label": "mercury"}'

# Check progress
curl http://claude-harness.server.unarmedpuppy.com/v1/ralph/status

# Stop gracefully
curl -X POST http://claude-harness.server.unarmedpuppy.com/v1/ralph/stop
```

See `./homelab-ai/agents/reference/ralph-wiggum.md` for details.

## Repository Inventory

### Infrastructure

| Repo | Purpose | Deployment |
|------|---------|------------|
| **home-server** | Server config, scripts, Traefik, beads | Direct on server |
| **homelab-ai** | LLM router, dashboard, claude-harness | Tag release |
| **shared-agent-skills** | Shared npm package for agent skills | Harbor npm |

### Applications

| Repo | Purpose | Tech Stack |
|------|---------|------------|
| **polyjuiced** | Trading/prediction automation | Python |
| **trading-journal** | Trade tracking and analytics | Python/FastAPI + React |
| **shua-ledger** | Personal finance tracking | TBD |
| **pokedex** | Pokemon sprite viewer | Static HTML |
| **maptapdat** | Maptap.gg score dashboard | Node.js |
| **beads-viewer** | Beads task graph viewer | React |
| **agent-gateway** | Agent gateway service | TBD |
| **bird** | Twitter/X data tools | Python |

## Deployment Architecture

```
Developer Workstation
         │ git push + tag release
         ▼
┌────────────────────────────────────────────────────────────────┐
│                        Home Server                              │
│  ┌─────────────┐    push    ┌─────────────┐                    │
│  │   Gitea     │───mirror──▶│   GitHub    │                    │
│  │  (source)   │            │  (backup)   │                    │
│  └──────┬──────┘            └─────────────┘                    │
│         │ on tag: triggers Actions                              │
│         ▼                                                       │
│  ┌─────────────┐    push    ┌─────────────┐    deploy          │
│  │   Gitea     │───image───▶│   Harbor    │───────────▶ Docker │
│  │   Actions   │            │  Registry   │   (automatic)      │
│  └─────────────┘            └─────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

### Key Patterns

1. **All Docker images through Harbor** - Never pull directly from Docker Hub/GHCR
2. **Tag-based deployment**: `git tag v1.0.0 && git push origin v1.0.0` triggers build + deploy
3. **No SSH for deployments** - Everything automated via Gitea Actions
4. **Push mirrors**: Gitea auto-pushes to GitHub as backup

### Image Mapping

| Original | Harbor Path |
|----------|-------------|
| `postgres:17-alpine` | `harbor.server.unarmedpuppy.com/docker-hub/library/postgres:17-alpine` |
| `ghcr.io/org/image:tag` | `harbor.server.unarmedpuppy.com/ghcr/org/image:tag` |
| `lscr.io/linuxserver/app:tag` | `harbor.server.unarmedpuppy.com/lscr/linuxserver/app:tag` |
| Custom images | `harbor.server.unarmedpuppy.com/library/app:tag` |

## Quick Commands

```bash
# Deploy an app (tag triggers Gitea Actions)
git tag v1.0.0 && git push origin v1.0.0

# Check what's running (via SSH for debugging only)
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# View logs
docker logs <container> --tail 100 -f
```

## Cross-Project Workflow

### Working on a Single Repo

1. Read that repo's `AGENTS.md` first
2. Follow repo-specific conventions
3. Commit and push to Gitea
4. Tag a release to trigger deployment
5. Track work using beads in `./home-server/`

### Adding a New App

1. Create repo under `homelab` org in Gitea
2. Add Dockerfile and docker-compose.yml
3. Set up Gitea Actions workflow for tag-based deployment
4. Use Harbor registry paths for all images
5. Add Traefik labels for routing
6. Add to homepage if user-facing

## Conventions

### Repo Structure

Every repo should have:
```
repo/
├── AGENTS.md           # Required - AI agent entry point
├── README.md           # Human documentation
├── docker-compose.yml  # If deployable
├── Dockerfile          # If containerized
└── agents/             # Optional - extended agent docs
    ├── skills/
    ├── reference/
    └── plans/
```

### Code Style

- **Python**: Use ruff for linting
- **TypeScript**: Use ESLint
- **Docker**: Multi-stage builds, non-root users, health checks

### Commits

Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`

## Boundaries

### Always Do
- Read repo-specific `AGENTS.md` before working
- Use Harbor registry for all Docker images
- Run `bd` commands from `./home-server/`
- Commit after each logical unit of work

### Ask First
- Adding new apps
- Changing CI/CD pipelines
- Modifying shared infrastructure (Traefik, networks)
- Cross-repo refactoring

### Never Do
- SSH to server for deployments (use tag-based Gitea Actions)
- Hardcode IPs, domains, or secrets in code
- Pull Docker images directly from Docker Hub (use Harbor)
- Skip reading the repo's AGENTS.md

## Critical Warnings

### Docker Cache Issue

**ALWAYS use `--no-cache` when deploying code changes:**
```bash
docker compose build --no-cache && docker compose up -d
```

### New Subdomain DNS

When creating new apps with Traefik routing, add subdomain to cloudflare-ddns config.

### Network Creation

If `my-network` doesn't exist:
```bash
docker network create my-network
```

## Reference Documentation

| Document | Location |
|----------|----------|
| Server setup, skills | `./home-server/AGENTS.md` |
| AI infrastructure | `./homelab-ai/AGENTS.md` |
| Ralph Wiggum | `./homelab-ai/agents/reference/ralph-wiggum.md` |
| Beads task management | `./home-server/agents/skills/beads-task-management/` |
| Deployment patterns | `./home-server/agents/reference/` |

---

*For server-specific work, see `./home-server/AGENTS.md`*
*For AI infrastructure, see `./homelab-ai/AGENTS.md`*
