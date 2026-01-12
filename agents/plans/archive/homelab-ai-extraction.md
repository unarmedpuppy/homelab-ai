# Homelab AI Extraction Plan

> **✅ COMPLETED (January 2025)**
> 
> This migration has been completed:
> - homelab-ai repo created and code migrated
> - CI/CD builds images and pushes to Harbor
> - home-server now uses `apps/homelab-ai/docker-compose.yml` to pull pre-built images
> - Old source code moved to `inactive/` directories
> 
> See [homelab-ai repo](https://github.com/unarmedpuppy/homelab-ai) for current source code.

Extract all Local AI components from home-server into a standalone monorepo that publishes Docker images to Harbor.

## Overview

**Repository**: `git@github.com:unarmedpuppy/homelab-ai.git`

**Goal**: Decouple Local AI code from home-server. Home-server becomes a consumer of published Docker images rather than building from source.

**Strategy**: Non-destructive migration - keep home-server working as-is, create new repo, build/push images, then update home-server to pull from Harbor.

## Components to Migrate

| Component | Source Location | Target Location | Harbor Image |
|-----------|-----------------|-----------------|--------------|
| Router | `apps/local-ai-router/` | `router/` | `harbor.../library/local-ai-router` |
| Dashboard | `apps/local-ai-dashboard/` | `dashboard/` | `harbor.../library/local-ai-dashboard` |
| Manager | `local-ai/manager/` | `manager/` | Built locally (Gaming PC) |
| Image Server | `local-ai/image-inference-server/` | `image-server/` | Built locally (Gaming PC) |
| TTS Server | `local-ai/tts-inference-server/` | `tts-server/` | Built locally (Gaming PC) |

**Omitted**: `local-ai/web-dashboard/` (not needed, existing dashboard suffices)

## Target Repository Structure

```
homelab-ai/
├── router/                          # OpenAI-compatible API router
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── router.py
│   ├── memory.py
│   ├── metrics.py
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── gaming_pc.py
│   │   ├── local_3070.py
│   │   ├── zai.py
│   │   ├── claude_harness.py
│   │   └── anthropic.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── file_tools.py
│   │   ├── git_tools.py
│   │   ├── shell_tools.py
│   │   └── skill_tools.py
│   ├── config/
│   │   └── providers.yaml
│   ├── scripts/
│   │   └── manage-api-keys.py
│   ├── alembic/
│   │   ├── env.py
│   │   ├── versions/
│   │   └── alembic.ini
│   ├── data/                        # .gitignore (runtime data)
│   └── README.md
│
├── dashboard/                       # React metrics dashboard
│   ├── Dockerfile
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── nginx.conf.template
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── types/
│   │   └── utils/
│   ├── public/
│   └── README.md
│
├── manager/                         # Container lifecycle manager (Gaming PC)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manager.py
│   ├── models.json
│   └── README.md
│
├── image-server/                    # Diffusers image inference (Gaming PC)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py
│   └── README.md
│
├── tts-server/                      # Chatterbox TTS inference (Gaming PC)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py
│   └── README.md
│
├── agents/                          # Agent system (mirroring home-server structure)
│   ├── skills/
│   │   ├── test-local-ai-router/
│   │   │   └── SKILL.md
│   │   ├── gaming-pc-manager/
│   │   │   └── SKILL.md
│   │   └── test-tts/
│   │       └── SKILL.md
│   ├── reference/
│   │   ├── router.md
│   │   ├── router-metrics.md
│   │   ├── router-usage.md
│   │   ├── architecture.md
│   │   └── implementation-details.md
│   └── plans/
│       └── future-simplification.md
│
├── scripts/                         # Build/deployment scripts (Gaming PC)
│   ├── build-image-server.ps1
│   ├── build-image-server.sh
│   ├── build-tts-server.ps1
│   ├── build-tts-server.sh
│   ├── start-all.ps1
│   ├── stop-all.ps1
│   └── setup.sh
│
├── .github/
│   └── workflows/
│       └── build-and-push.yml       # CI/CD for Harbor
│
├── docker-compose.yml               # Local development (all services)
├── docker-compose.gaming-pc.yml     # Gaming PC deployment
├── .gitignore
├── .env.example
├── AGENTS.md                        # Agent instructions for this repo
└── README.md
```

## CI/CD Pipeline

### GitHub Actions Workflow

**File**: `.github/workflows/build-and-push.yml`

```yaml
name: Build and Push to Harbor

on:
  push:
    branches: [main]
    paths:
      - 'router/**'
      - 'dashboard/**'
  workflow_dispatch:
    inputs:
      component:
        description: 'Component to build (router, dashboard, all)'
        required: true
        default: 'all'

env:
  HARBOR_REGISTRY: harbor.server.unarmedpuppy.com
  HARBOR_PROJECT: library

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      router: ${{ steps.changes.outputs.router }}
      dashboard: ${{ steps.changes.outputs.dashboard }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: changes
        with:
          filters: |
            router:
              - 'router/**'
            dashboard:
              - 'dashboard/**'

  build-router:
    needs: detect-changes
    if: needs.detect-changes.outputs.router == 'true' || github.event.inputs.component == 'router' || github.event.inputs.component == 'all'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Harbor
        uses: docker/login-action@v3
        with:
          registry: ${{ env.HARBOR_REGISTRY }}
          username: ${{ secrets.HARBOR_USERNAME }}
          password: ${{ secrets.HARBOR_PASSWORD }}
      
      - name: Build and push router
        uses: docker/build-push-action@v5
        with:
          context: ./router
          push: true
          tags: |
            ${{ env.HARBOR_REGISTRY }}/${{ env.HARBOR_PROJECT }}/local-ai-router:latest
            ${{ env.HARBOR_REGISTRY }}/${{ env.HARBOR_PROJECT }}/local-ai-router:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  build-dashboard:
    needs: detect-changes
    if: needs.detect-changes.outputs.dashboard == 'true' || github.event.inputs.component == 'dashboard' || github.event.inputs.component == 'all'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Harbor
        uses: docker/login-action@v3
        with:
          registry: ${{ env.HARBOR_REGISTRY }}
          username: ${{ secrets.HARBOR_USERNAME }}
          password: ${{ secrets.HARBOR_PASSWORD }}
      
      - name: Build and push dashboard
        uses: docker/build-push-action@v5
        with:
          context: ./dashboard
          push: true
          tags: |
            ${{ env.HARBOR_REGISTRY }}/${{ env.HARBOR_PROJECT }}/local-ai-dashboard:latest
            ${{ env.HARBOR_REGISTRY }}/${{ env.HARBOR_PROJECT }}/local-ai-dashboard:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      # Router linting/testing
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install router dependencies
        run: |
          cd router
          pip install -r requirements.txt
          pip install ruff pytest
      
      - name: Lint router
        run: |
          cd router
          ruff check .
      
      - name: Test router
        run: |
          cd router
          pytest -v || true  # Don't fail if no tests yet
      
      # Dashboard linting/testing
      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install dashboard dependencies
        run: |
          cd dashboard
          npm ci
      
      - name: Lint dashboard
        run: |
          cd dashboard
          npm run lint || true  # Don't fail if no lint script
      
      - name: Build dashboard
        run: |
          cd dashboard
          npm run build
```

### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `HARBOR_USERNAME` | Harbor registry username |
| `HARBOR_PASSWORD` | Harbor registry password/token |

## Migration Steps

### Phase 1: Repository Setup

1. **Create empty repo on GitHub**
   ```bash
   # Already exists: git@github.com:unarmedpuppy/homelab-ai.git
   ```

2. **Clone and initialize**
   ```bash
   cd ~/repos/personal
   git clone git@github.com:unarmedpuppy/homelab-ai.git
   cd homelab-ai
   ```

3. **Create directory structure**
   ```bash
   mkdir -p router dashboard manager image-server tts-server
   mkdir -p agents/{skills,reference,plans}
   mkdir -p scripts .github/workflows
   ```

4. **Create base files**
   - `.gitignore`
   - `README.md`
   - `AGENTS.md`
   - `.env.example`

### Phase 2: Copy Router

1. **Copy source files**
   ```bash
   # From home-server/apps/local-ai-router/
   cp -r apps/local-ai-router/*.py homelab-ai/router/
   cp -r apps/local-ai-router/providers homelab-ai/router/
   cp -r apps/local-ai-router/tools homelab-ai/router/
   cp -r apps/local-ai-router/config homelab-ai/router/
   cp -r apps/local-ai-router/scripts homelab-ai/router/
   cp -r apps/local-ai-router/alembic* homelab-ai/router/
   cp apps/local-ai-router/Dockerfile homelab-ai/router/
   cp apps/local-ai-router/requirements.txt homelab-ai/router/
   cp apps/local-ai-router/README.md homelab-ai/router/
   ```

2. **Update paths in Dockerfile** (if needed)
   - Skills mount path will change

3. **Create router-specific .gitignore**
   ```
   data/
   *.db
   __pycache__/
   ```

### Phase 3: Copy Dashboard

1. **Copy source files**
   ```bash
   # From home-server/apps/local-ai-dashboard/
   cp -r apps/local-ai-dashboard/src homelab-ai/dashboard/
   cp -r apps/local-ai-dashboard/public homelab-ai/dashboard/
   cp apps/local-ai-dashboard/Dockerfile homelab-ai/dashboard/
   cp apps/local-ai-dashboard/package*.json homelab-ai/dashboard/
   cp apps/local-ai-dashboard/tsconfig*.json homelab-ai/dashboard/
   cp apps/local-ai-dashboard/vite.config.ts homelab-ai/dashboard/
   cp apps/local-ai-dashboard/tailwind.config.js homelab-ai/dashboard/
   cp apps/local-ai-dashboard/nginx.conf.template homelab-ai/dashboard/
   cp apps/local-ai-dashboard/README.md homelab-ai/dashboard/
   ```

2. **Create dashboard-specific .gitignore**
   ```
   node_modules/
   dist/
   ```

### Phase 4: Copy Gaming PC Components

1. **Copy Manager**
   ```bash
   cp -r local-ai/manager/* homelab-ai/manager/
   cp local-ai/models.json homelab-ai/manager/
   ```

2. **Copy Image Server**
   ```bash
   cp -r local-ai/image-inference-server/* homelab-ai/image-server/
   ```

3. **Copy TTS Server**
   ```bash
   cp -r local-ai/tts-inference-server/* homelab-ai/tts-server/
   ```

4. **Copy Scripts**
   ```bash
   cp local-ai/*.ps1 homelab-ai/scripts/
   cp local-ai/*.sh homelab-ai/scripts/
   ```

### Phase 5: Copy Documentation

1. **Copy Skills**
   ```bash
   cp -r agents/skills/test-local-ai-router homelab-ai/agents/skills/
   cp -r agents/skills/gaming-pc-manager homelab-ai/agents/skills/
   cp -r agents/skills/test-tts homelab-ai/agents/skills/
   ```

2. **Copy Reference Docs**
   ```bash
   cp agents/reference/local-ai-router.md homelab-ai/agents/reference/router.md
   # Copy other local-ai-* reference docs
   ```

3. **Update internal links** in copied docs

### Phase 6: Create CI/CD

1. **Create workflow file** (as shown above)
2. **Add GitHub secrets** for Harbor credentials
3. **Test with manual dispatch**

### Phase 7: Initial Build & Push

1. **Commit and push to main**
   ```bash
   cd homelab-ai
   git add .
   git commit -m "Initial migration from home-server"
   git push origin main
   ```

2. **Verify GitHub Actions runs**
3. **Verify images appear in Harbor**
   - `harbor.server.unarmedpuppy.com/library/local-ai-router:latest`
   - `harbor.server.unarmedpuppy.com/library/local-ai-dashboard:latest`

### Phase 8: Update home-server

1. **Update Router docker-compose.yml**
   ```yaml
   # apps/local-ai-router/docker-compose.yml
   services:
     local-ai-router:
       # Remove: build: .
       image: harbor.server.unarmedpuppy.com/library/local-ai-router:latest
       # ... rest stays the same
   ```

2. **Update Dashboard docker-compose.yml**
   ```yaml
   # apps/local-ai-dashboard/docker-compose.yml
   services:
     local-ai-dashboard:
       # Remove: build: .
       image: harbor.server.unarmedpuppy.com/library/local-ai-dashboard:latest
       # ... rest stays the same
   ```

3. **Test on server**
   ```bash
   cd apps/local-ai-router
   docker compose pull
   docker compose up -d
   # Verify functionality
   
   cd ../local-ai-dashboard
   docker compose pull
   docker compose up -d
   # Verify functionality
   ```

### Phase 9: Clean Up home-server

1. **Remove source code** (keep docker-compose.yml)
   ```bash
   # apps/local-ai-router/ - remove all except docker-compose.yml, .env
   # apps/local-ai-dashboard/ - remove all except docker-compose.yml
   ```

2. **Remove local-ai/ directory**
   ```bash
   rm -rf local-ai/
   ```

3. **Update/remove reference docs**
   - Update `agents/reference/local-ai-router.md` to point to new repo
   - Or remove and reference new repo's docs

4. **Update AGENTS.md**
   - Remove local-ai skill references
   - Add note about homelab-ai repo

### Phase 10: Gaming PC Migration

1. **Clone homelab-ai to Gaming PC**
   ```powershell
   cd C:\Users\YourUser\repos
   git clone git@github.com:unarmedpuppy/homelab-ai.git
   ```

2. **Update scripts for new paths**
   - Build scripts reference new locations
   - docker-compose.gaming-pc.yml uses new structure

3. **Test builds**
   ```powershell
   cd homelab-ai\scripts
   .\build-tts-server.ps1
   ```

4. **Verify operation**

## Rollback Procedures

### If Harbor images fail

1. **Revert docker-compose.yml** to use `build: .`
2. **Restore source code** from git history or backup

### If functionality breaks

1. **Check image SHA** - pin to known-good SHA tag
   ```yaml
   image: harbor.server.unarmedpuppy.com/library/local-ai-router:abc123f
   ```

2. **Compare configs** - ensure env vars match

### Full rollback

```bash
# In home-server repo
git checkout HEAD~1 -- apps/local-ai-router/
git checkout HEAD~1 -- apps/local-ai-dashboard/
git checkout HEAD~1 -- local-ai/
```

## Post-Migration: Future Simplification

Once the 3090 is moved to the server and Gaming PC is removed from the stack:

1. **Remove Gaming PC components** from homelab-ai (or archive)
2. **Simplify Router** - remove gaming-pc provider, gaming mode logic
3. **Add Manager to CI/CD** - if running on server
4. **Update documentation**

This is tracked separately - focus on clean migration first.

## Success Criteria

- [ ] homelab-ai repo created with all components
- [ ] GitHub Actions successfully builds and pushes to Harbor
- [ ] Router image works when pulled from Harbor
- [ ] Dashboard image works when pulled from Harbor
- [ ] home-server source code removed (only docker-compose.yml remains)
- [ ] Gaming PC builds from new repo location
- [ ] All documentation updated

## Related

- [Harbor Registry](../apps/harbor/README.md) - Image registry setup
- [Local AI Router](../apps/local-ai-router/README.md) - Current router docs (will be removed)
- [Gaming PC Setup](../local-ai/README.md) - Current gaming PC docs (will be removed)
