# Homelab AI - Agent Instructions

**Read this file first.** This is your entry point for understanding and contributing to this project.

## Project Summary

Local AI infrastructure providing OpenAI-compatible API routing, metrics dashboard, and inference servers. Published as Docker images to Harbor for consumption by home-server.

**Tech Stack**: Python (FastAPI), TypeScript (React/Vite), Docker

## Repository Structure

```
homelab-ai/
├── router/                 # OpenAI-compatible API router
│   ├── Dockerfile
│   ├── router.py          # Main application
│   ├── providers/         # Backend providers
│   ├── tools/             # Agent tools
│   └── config/            # Configuration
├── dashboard/             # React metrics dashboard
│   ├── Dockerfile
│   ├── src/
│   └── package.json
├── manager/               # Container lifecycle manager (Gaming PC)
├── image-server/          # Diffusers image inference (Gaming PC)
├── tts-server/            # Chatterbox TTS inference (Gaming PC)
├── agents/
│   ├── skills/            # Workflow guides
│   ├── reference/         # Documentation
│   └── plans/             # Implementation plans
├── scripts/               # Build scripts (Gaming PC)
└── .github/workflows/     # CI/CD
```

## Configuration

**All environment-specific values go in `.env`** - never hardcode IPs, domains, or secrets.

```bash
cp .env.example .env
# Edit with your values
```

## Quick Commands

```bash
# Router development
cd router
pip install -r requirements.txt
uvicorn router:app --reload --port 8000

# Dashboard development
cd dashboard
npm install
npm run dev

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

### Router (`router/`)

OpenAI-compatible API that routes to multiple backends:
- Gaming PC GPU - primary for large models
- Server GPU - fallback for small models
- Cloud providers - overflow

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

### Gaming PC Components

Built locally on Gaming PC, not via CI/CD:
- `manager/` - Manages GPU container lifecycle
- `image-server/` - Diffusers image generation
- `tts-server/` - Chatterbox TTS

## Harbor Integration

Images are pushed to Harbor on merge to main. The registry URL is configured via environment variables.

Home-server pulls these images via docker-compose.

## Related Repositories

- **home-server**: Deployment configuration, pulls images from Harbor
- Uses `apps/local-ai-router/docker-compose.yml` to deploy router
- Uses `apps/local-ai-dashboard/docker-compose.yml` to deploy dashboard
