# Watchtower Auto-Deployment Plan

## Status: IMPLEMENTED

**Last Updated**: 2026-01-10

## Implementation Progress

| Step | Status | Notes |
|------|--------|-------|
| Add Watchtower to home-server | Done | Running, polling every 60s |
| Update reusable workflow | Done | SSH deploy removed, pushes :latest tag |
| Add labels to custom apps | Done | 9 containers now watched |
| Test deployment pipeline | Done | Tested with pokedex v1.0.3 |
| Mattermost notifications | Pending | Shoutrrr format issues, disabled for now |

### Currently Auto-Deploying (9 containers)

| Container | Image |
|-----------|-------|
| agent-core | library/agent-core:latest |
| agent-gateway | library/agent-gateway:latest |
| llm-router | library/llm-router:latest |
| homelab-ai-dashboard | library/local-ai-dashboard:latest |
| llm-manager | library/llm-manager:latest |
| claude-harness | library/claude-harness:latest |
| pokedex | library/pokedex:latest |
| polymarket-bot | library/polymarket-bot:latest |
| trading-bot | library/trading-bot:latest |

### Pending First Build

These apps have Watchtower labels but need their first CI build to Harbor:

| App | Reason |
|-----|--------|
| beads-viewer | Image not in Harbor yet |
| maptapdat | Image not in Harbor yet |
| smart-home-3d | Image not in Harbor yet |
| trading-journal | Images (frontend/backend) not in Harbor yet |

---

## Overview

Replace SSH-based deployments with automated image updates using Watchtower. When a new image is pushed to Harbor, Watchtower automatically pulls and restarts the affected containers.

## How It Works Now

```
Developer pushes tag → Gitea Actions builds → Pushes to Harbor (v1.0.x + :latest)
                                                        ↓
                                        Watchtower polls every 60 seconds
                                                        ↓
                                        Detects new :latest digest → pulls → restarts
```

**No SSH required. No manual deployment steps.**

## Previous State (Deprecated)

```
Developer pushes tag → Gitea Actions builds → Pushes to Harbor → SSH to server → docker compose pull/up
                                                                        ↑
                                                            FAILING (auth issues)
```

This approach was fragile due to SSH key management and tight CI/server coupling.

## Architecture

### Repository Responsibilities

| Repository | Contains | Purpose |
|------------|----------|---------|
| **home-server** | docker-compose.yml for ALL apps | Single source of truth for deployments |
| **homelab/\*** (custom apps) | Source code + Dockerfile | Code and build instructions only |
| **unarmedpuppy/workflows** | Reusable Gitea Actions | Build and push images to Harbor |

### Image Tagging Strategy

Every build pushes TWO tags:
```
harbor.server.unarmedpuppy.com/library/polyjuiced:v1.0.2   ← version (for rollback/reference)
harbor.server.unarmedpuppy.com/library/polyjuiced:latest  ← mutable (Watchtower watches this)
```

### Server Directory Structure

```
~/server/                          # home-server repo clone
├── apps/
│   ├── traefik/                   # Infrastructure
│   ├── watchtower/                # NEW - auto-deployment
│   ├── plex/                      # Third-party app (config only)
│   ├── sonarr/                    # Third-party app (config only)
│   ├── polyjuiced/                # Custom app (docker-compose only, no code)
│   │   ├── docker-compose.yml     # References harbor image :latest
│   │   └── .env                   # App secrets
│   ├── agent-gateway/             # Custom app
│   │   └── docker-compose.yml
│   └── ...
├── scripts/
└── ...
```

## How Watchtower Works

### Basic Operation

1. Watchtower runs as a container alongside your apps
2. Every N minutes (default: 5), it checks Harbor for each running container's image
3. Compares image **digest** (SHA hash), not just tag name
4. If digest differs → new image available → pull and restart

### What Triggers an Update

| Scenario | Update? |
|----------|---------|
| Push new `polyjuiced:latest` with different content | Yes |
| Push `polyjuiced:v1.0.3` (container runs `:latest`) | No (different tag) |
| Rebuild same code, push `polyjuiced:latest` | No (same digest) |
| Change docker-compose.yml (new env var) | No (Watchtower doesn't read compose files) |

### What Watchtower Does on Update

1. Pulls new image from Harbor
2. Stops the running container gracefully (SIGTERM, then SIGKILL after timeout)
3. Creates new container with **identical configuration**:
   - Same name
   - Same volumes (data preserved)
   - Same environment variables
   - Same network connections
   - Same labels
4. Starts the new container
5. Optionally removes the old image (to save disk space)

### What Watchtower Does NOT Do

- Read or apply docker-compose.yml changes
- Clone git repos
- Run migrations
- Send deployment notifications (unless configured)

### Handling docker-compose.yml Changes

When you need to change docker-compose.yml (new env var, port, volume):

```bash
# On server
cd ~/server/apps/polyjuiced
git pull                           # Get latest docker-compose.yml
docker compose up -d               # Apply changes
```

This is rare (most deploys are just code changes = new image).

## Implementation Steps

### Step 1: Add Watchtower to home-server

Create `apps/watchtower/docker-compose.yml`:

```yaml
services:
  watchtower:
    image: harbor.server.unarmedpuppy.com/docker-hub/containrrr/watchtower:latest
    container_name: watchtower
    restart: unless-stopped
    environment:
      - TZ=America/Chicago
      - WATCHTOWER_CLEANUP=true                    # Remove old images
      - WATCHTOWER_POLL_INTERVAL=60                # Check every 1 minute
      - WATCHTOWER_INCLUDE_RESTARTING=true
      - WATCHTOWER_ROLLING_RESTART=true            # Restart one at a time
      - WATCHTOWER_LABEL_ENABLE=true               # Only watch labeled containers
      # Mattermost notifications
      - WATCHTOWER_NOTIFICATIONS=shoutrrr
      - WATCHTOWER_NOTIFICATION_URL=mattermosthttp://${MATTERMOST_WEBHOOK_URL}
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /etc/localtime:/etc/localtime:ro
    networks:
      - my-network

networks:
  my-network:
    external: true
```

Create `apps/watchtower/.env`:
```bash
MATTERMOST_WEBHOOK_URL=mattermost.server.unarmedpuppy.com/hooks/your-webhook-id
```

### Step 2: Label Containers for Watchtower

Only custom apps (with Harbor images) should be watched. Add label to each:

```yaml
# In apps/polyjuiced/docker-compose.yml
services:
  polyjuiced:
    image: harbor.server.unarmedpuppy.com/library/polyjuiced:latest
    labels:
      - "com.centurylinklabs.watchtower.enable=true"
    # ... rest of config
```

Third-party apps (Plex, Sonarr) don't need this label - they update on their own schedule or manually.

### Step 3: Update Reusable Workflow

Modify `unarmedpuppy/workflows/.gitea/workflows/docker-build.yml`:

1. Push both version tag AND `latest` tag
2. Remove SSH deploy step entirely

```yaml
# Pseudocode for changes
- name: Push to Harbor
  run: |
    docker push ${{ inputs.image_name }}:${{ github.ref_name }}
    docker tag ${{ inputs.image_name }}:${{ github.ref_name }} ${{ inputs.image_name }}:latest
    docker push ${{ inputs.image_name }}:latest

# DELETE the "Deploy to server" SSH step
```

### Step 4: Update App docker-compose Files

Ensure all custom apps in home-server use `:latest` tag:

```yaml
# apps/polyjuiced/docker-compose.yml
services:
  polyjuiced:
    image: harbor.server.unarmedpuppy.com/library/polyjuiced:latest  # NOT :v1.0.2
```

### Step 5: Deploy Watchtower

```bash
ssh server
cd ~/server/apps/watchtower
docker compose up -d
```

### Step 6: Test the Pipeline

```bash
# On dev machine
cd ~/repos/personal/homelab/polyjuiced
# Make a small change
git add . && git commit -m "test: verify watchtower deployment"
git tag v1.0.3 && git push origin main v1.0.3

# Wait ~1 minute, then check Mattermost for notification
# Or check Watchtower logs:
ssh server
docker logs watchtower --tail 50

# Should see:
# Found new image for polyjuiced
# Stopping polyjuiced
# Starting polyjuiced
```

## Rollback Procedure

If a bad image is deployed:

```bash
# On server
docker pull harbor.server.unarmedpuppy.com/library/polyjuiced:v1.0.2  # Previous good version
docker tag harbor.server.unarmedpuppy.com/library/polyjuiced:v1.0.2 \
           harbor.server.unarmedpuppy.com/library/polyjuiced:latest
docker push harbor.server.unarmedpuppy.com/library/polyjuiced:latest

# Watchtower will pick up the "new" latest and rollback
# OR force immediate restart:
docker compose -f ~/server/apps/polyjuiced/docker-compose.yml up -d --force-recreate
```

## Monitoring

### Watchtower Logs

```bash
docker logs watchtower -f
```

### Check What Watchtower is Watching

```bash
docker ps --filter "label=com.centurylinklabs.watchtower.enable=true" --format "table {{.Names}}\t{{.Image}}"
```

### Notifications

Watchtower sends Mattermost notifications on every update via Shoutrrr.

Message format:
```
Watchtower: Updated polyjuiced (harbor.server.unarmedpuppy.com/library/polyjuiced:latest)
```

To test notifications:
```bash
docker exec watchtower /watchtower --run-once --debug
```

## Apps to Update

Custom apps needing Watchtower label and `:latest` tag:

| App | Has Workflow | Needs Label | Needs :latest |
|-----|--------------|-------------|---------------|
| agent-gateway | Yes | Yes | Yes |
| polyjuiced | Yes | Yes | Yes |
| trading-bot | Yes | Yes | Yes |
| trading-journal | Yes | Yes | Yes |
| beads-viewer | Yes | Yes | Yes |
| maptapdat | Yes | Yes | Yes |
| maptapper | Pending | Yes | Yes |
| pokedex | Yes | Yes | Yes |
| smart-home-3d | Yes | Yes | Yes |
| homelab-ai (multiple) | Yes | Yes | Yes |

## Summary

| Component | Change |
|-----------|--------|
| **unarmedpuppy/workflows** | Push `:latest` tag, remove SSH deploy |
| **home-server** | Add Watchtower, add labels to custom apps |
| **App repos** | No changes needed |
| **Deployment process** | Push tag → wait ~1 min → done (+ Mattermost notification) |

## Decisions

1. **Scope**: Only labeled containers (`com.centurylinklabs.watchtower.enable=true`)
2. **Poll interval**: 1 minute (60 seconds)
3. **Notifications**: Yes, Mattermost alerts on deploys
4. **Third-party apps**: No, update manually (no Watchtower label)
5. **homelab-ai**: All 6 services auto-update independently
