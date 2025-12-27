# App Extraction & Private Registry Architecture Plan

## Problem Statement

The `apps/` directory in the home-server monorepo is growing unwieldy. Custom-built apps are mixed with third-party app configurations, making it difficult to:
- Version and release individual apps independently
- Manage app-specific CI/CD
- Eventually open-source individual projects
- Keep the home-server repo focused on orchestration

## Goal

Extract custom-built apps into independent repositories, publish them as Docker images to a private registry, and consume them on the server via docker-compose (like any other third-party image).

---

## Current State Analysis

### Custom Apps (Candidates for Extraction)

| App | Description | Complexity |
|-----|-------------|------------|
| `trading-bot` | Python trading automation | High (src/, tests/, migrations, monitoring) |
| `polymarket-bot` | Prediction market bot | Medium (src/, tests/) |
| `trading-journal` | Trading journal (frontend + backend) | High (multi-container) |
| `pokedex` | Pokemon data app | Low-Medium |
| `maptapdat` | Custom app | Medium |
| `smart-home-3d` | 3D home visualization | Medium |
| `beads-viewer` | Beads task viewer | Low |
| `opencode-terminal` | Terminal in browser | Low |
| `tradingagents` | Trading agents | Medium |

### Third-Party Apps (Stay in home-server)

Apps like `jellyfin`, `plex`, `traefik`, `homepage`, etc. are just docker-compose configurations pointing to upstream images. These stay in the monorepo.

---

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Development Flow                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐ │
│  │  App Repo    │────▶│   GitHub     │────▶│   Private Registry   │ │
│  │  (trading-   │     │   Actions    │     │   (registry.server.  │ │
│  │   bot)       │     │   CI/CD      │     │    unarmedpuppy.com) │ │
│  └──────────────┘     └──────────────┘     └──────────┬───────────┘ │
│                                                        │             │
│                                                        │             │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     Home Server                               │   │
│  │  ┌─────────────────────────────────────────────────────────┐ │   │
│  │  │  home-server repo (orchestration only)                  │ │   │
│  │  │                                                         │ │   │
│  │  │  apps/                                                  │ │   │
│  │  │  ├── trading-bot/                                       │ │   │
│  │  │  │   └── docker-compose.yml  ◀───────────────────────────┼───┘
│  │  │  │       (image: registry.../trading-bot:v1.2.3)        │ │
│  │  │  ├── jellyfin/                                          │ │
│  │  │  │   └── docker-compose.yml                             │ │
│  │  │  │       (image: jellyfin/jellyfin:latest)              │ │
│  │  │  └── ...                                                │ │
│  │  └─────────────────────────────────────────────────────────┘ │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Private Docker Registry

**Recommended: Docker Registry + Registry UI**

Simple, lightweight, sufficient for home use. Can upgrade to Harbor later if needed.

```yaml
# apps/registry/docker-compose.yml
services:
  registry:
    image: registry:2
    container_name: registry
    restart: unless-stopped
    volumes:
      - ./data:/var/lib/registry
      - ./auth:/auth
    environment:
      REGISTRY_AUTH: htpasswd
      REGISTRY_AUTH_HTPASSWD_REALM: Registry Realm
      REGISTRY_AUTH_HTPASSWD_PATH: /auth/htpasswd
      REGISTRY_STORAGE_DELETE_ENABLED: "true"
    networks:
      - my-network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.registry.rule=Host(`registry.server.unarmedpuppy.com`)"
      - "traefik.http.routers.registry.tls.certresolver=myresolver"
      - "traefik.http.services.registry.loadbalancer.server.port=5000"

  registry-ui:
    image: joxit/docker-registry-ui:latest
    container_name: registry-ui
    restart: unless-stopped
    environment:
      - REGISTRY_TITLE=Home Server Registry
      - REGISTRY_URL=https://registry.server.unarmedpuppy.com
      - SINGLE_REGISTRY=true
    networks:
      - my-network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.registry-ui.rule=Host(`registry-ui.server.unarmedpuppy.com`)"
      - "traefik.http.routers.registry-ui.tls.certresolver=myresolver"
      - "traefik.http.services.registry-ui.loadbalancer.server.port=80"

networks:
  my-network:
    external: true
```

**Storage considerations:**
- Registry data stored in `./data` volume
- Include in backup strategy
- Consider storage limits/cleanup policy

### 2. App Repository Structure

Each extracted app follows this structure:

```
my-app/
├── .github/
│   └── workflows/
│       └── build.yml           # CI: build & push to registry
├── src/                        # Application source code
├── tests/                      # Test suite
├── Dockerfile                  # Production Dockerfile
├── docker-compose.yml          # Local development
├── docker-compose.dev.yml      # Dev overrides (mounts, hot reload)
├── requirements.txt            # (or package.json, go.mod, etc.)
├── README.md
├── CHANGELOG.md
└── .env.example
```

### 3. CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/build.yml
name: Build and Push

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:
    inputs:
      tag:
        description: 'Tag to build'
        required: true

env:
  REGISTRY: registry.server.unarmedpuppy.com
  IMAGE_NAME: ${{ github.event.repository.name }}

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to private registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ secrets.REGISTRY_USERNAME }}
          password: ${{ secrets.REGISTRY_PASSWORD }}

      - name: Extract version from tag
        id: version
        run: echo "VERSION=${GITHUB_REF#refs/tags/}" >> $GITHUB_OUTPUT

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ steps.version.outputs.VERSION }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### 4. Server-Side Configuration

On the server, configure Docker to authenticate with the private registry:

```bash
# One-time setup on server
docker login registry.server.unarmedpuppy.com
# Enter username and password
# Credentials stored in ~/.docker/config.json
```

### 5. Migrated App Structure (home-server repo)

After extraction, the home-server repo keeps minimal orchestration files:

```
apps/
├── trading-bot/
│   ├── docker-compose.yml      # Points to registry image
│   ├── .env                    # Runtime configuration (gitignored)
│   └── data/                   # Persistent data (gitignored)
│
├── jellyfin/                   # Third-party: unchanged
│   └── docker-compose.yml
```

**Example migrated docker-compose.yml:**

```yaml
# apps/trading-bot/docker-compose.yml
services:
  trading-bot:
    image: registry.server.unarmedpuppy.com/trading-bot:v1.2.3
    container_name: trading-bot
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./data:/app/data
    networks:
      - my-network
    labels:
      # Traefik labels...

networks:
  my-network:
    external: true
```

---

## Workflow

### Development Workflow

```
1. Make changes in app repo (e.g., trading-bot)
2. Test locally: docker compose up
3. Commit and push
4. Create release tag: git tag v1.2.3 && git push --tags
5. CI builds and pushes to registry
6. Update home-server docker-compose with new version
7. Deploy: git pull && docker compose pull && docker compose up -d
```

### Version Management

**Option A: Manual Version Updates**
- Edit docker-compose.yml to specify version
- Explicit, traceable, rollback-friendly

**Option B: Automated Updates (Watchtower)**
- Watchtower can auto-update from `latest` tag
- Less control, but convenient for dev

**Recommendation:** Use explicit versions for production stability, `latest` for dev/testing.

---

## Implementation Phases

### Phase 1: Infrastructure Setup
1. [ ] Deploy private Docker registry on server
2. [ ] Configure Traefik routing for registry
3. [ ] Add DNS entry to Cloudflare DDNS
4. [ ] Set up authentication (htpasswd)
5. [ ] Test push/pull locally

### Phase 2: Pilot Extraction (1 app)
1. [ ] Choose pilot app (suggest: `beads-viewer` - simplest)
2. [ ] Create new GitHub repo
3. [ ] Move source code (preserve git history with `git filter-repo`)
4. [ ] Set up GitHub Actions CI
5. [ ] Configure secrets for registry auth
6. [ ] Test full workflow: push → build → deploy

### Phase 3: Extract Remaining Apps
1. [ ] Extract apps in order of complexity (simple → complex)
2. [ ] Update home-server docker-compose files
3. [ ] Remove source code from home-server repo
4. [ ] Document each app's new location

### Phase 4: Cleanup & Documentation
1. [ ] Update home-server README with new architecture
2. [ ] Create app registry/index (which apps, which repos)
3. [ ] Document deployment workflow
4. [ ] Set up backup for registry data

---

## Alternatives Considered

### GitHub Container Registry (ghcr.io)
- **Pros:** No self-hosting, free for private packages
- **Cons:** Requires GitHub auth on server, internet dependency
- **Verdict:** Good fallback if self-hosting is too much maintenance

### Harbor
- **Pros:** Enterprise features, vulnerability scanning, RBAC
- **Cons:** Heavier resource usage, more complex
- **Verdict:** Overkill for home use, consider if scaling up

### Gitea + Gitea Registry
- **Pros:** Git + Registry in one, full self-hosted dev platform
- **Cons:** More to maintain, already using GitHub
- **Verdict:** Consider if want to self-host git too

---

## Open Questions

1. **Git history preservation:** Do you want to preserve git history when extracting apps? (Requires `git filter-repo`)

2. **Registry location:** Run registry on the same server, or separate?

3. **CI platform:** GitHub Actions (simplest), or self-hosted runner for private network builds?

4. **Multi-arch builds:** Need ARM images too, or just x86_64?

5. **Which app first?** Suggest `beads-viewer` as pilot (smallest, lowest risk)

---

## Next Steps

1. Review and refine this plan
2. Answer open questions above
3. Create implementation tasks in Beads
4. Execute Phase 1 (infrastructure)
