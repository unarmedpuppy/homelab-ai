# Automated Deployment System Plan

**Created**: 2025-01-02
**Status**: Draft
**Goal**: Replace manual SSH deployments with GitHub Actions-driven automation

## Problem Statement

Current workflow:
```bash
# Manual process for every change
ssh -p 4242 unarmedpuppy@192.168.86.47
cd ~/server/apps/<app>
docker compose down && docker compose up -d --build
```

Issues:
1. Requires manual SSH for every deployment
2. Agent can't deploy without user intervention (AGENTS.md forbids direct server changes)
3. No automation for upstream image updates (new `postgres:latest`)
4. No coordination between external repos (trading-bot, homelab-ai) and home-server

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DEPLOYMENT TRIGGERS                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │ trading-bot  │    │ homelab-ai   │    │ home-server  │              │
│  │    repo      │    │    repo      │    │    repo      │              │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘              │
│         │                   │                   │                       │
│         ▼                   ▼                   ▼                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │ Build Image  │    │ Build Image  │    │ Detect       │              │
│  │ Push Harbor  │    │ Push Harbor  │    │ Changed Apps │              │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘              │
│         │                   │                   │                       │
│         └───────────────────┴───────────────────┘                       │
│                             │                                            │
│                             ▼                                            │
│              ┌──────────────────────────────┐                           │
│              │  Reusable Deploy Action      │                           │
│              │  home-server/.github/actions │                           │
│              └──────────────┬───────────────┘                           │
│                             │                                            │
└─────────────────────────────┼────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           SERVER                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐        │
│  │ Watchtower     │    │ claude-deploy  │    │ Docker Engine  │        │
│  │ (auto-update   │    │ (SSH user)     │    │                │        │
│  │  opt-in apps)  │    │                │    │                │        │
│  └────────────────┘    └────────────────┘    └────────────────┘        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Deployment Categories

| Category | Example Apps | Trigger | Who Deploys |
|----------|--------------|---------|-------------|
| **External Build** | trading-bot, homelab-ai | Push to app repo | App repo workflow |
| **Internal Build** | bird, agent-core, n8n | Push to home-server | home-server workflow |
| **Config Only** | plex, grafana, traefik | Push to home-server | home-server workflow |
| **Auto-Update** | postgres, redis, nginx | New upstream image | Watchtower (opt-in) |

## Component 1: Reusable Deploy Action

Create a standardized action that any repo can call.

### File: `.github/actions/deploy-app/action.yml`

```yaml
name: 'Deploy App to Home Server'
description: 'SSH to server and deploy/restart a Docker Compose app'

inputs:
  app_name:
    description: 'App directory name under ~/server/apps/'
    required: true
  ssh_key:
    description: 'SSH private key for claude-deploy user'
    required: true
  server_host:
    description: 'Server hostname or IP'
    default: '192.168.86.47'
  server_port:
    description: 'SSH port'
    default: '4242'
  server_user:
    description: 'SSH username'
    default: 'claude-deploy'
  action:
    description: 'Action to perform: pull, restart, rebuild, down-up'
    default: 'pull'
  pre_deploy_script:
    description: 'Optional script to run before deployment'
    required: false

runs:
  using: 'composite'
  steps:
    - name: Validate inputs
      shell: bash
      run: |
        if [[ ! "${{ inputs.action }}" =~ ^(pull|restart|rebuild|down-up)$ ]]; then
          echo "::error::Invalid action: ${{ inputs.action }}"
          exit 1
        fi

    - name: Deploy via SSH
      uses: appleboy/ssh-action@v1
      with:
        host: ${{ inputs.server_host }}
        port: ${{ inputs.server_port }}
        username: ${{ inputs.server_user }}
        key: ${{ inputs.ssh_key }}
        script_stop: true
        script: |
          set -euo pipefail
          
          APP_DIR="$HOME/server/apps/${{ inputs.app_name }}"
          
          if [[ ! -d "$APP_DIR" ]]; then
            echo "::error::App directory not found: $APP_DIR"
            exit 1
          fi
          
          cd "$APP_DIR"
          echo "Deploying ${{ inputs.app_name }} with action: ${{ inputs.action }}"
          
          # Pre-deploy script if provided
          if [[ -n "${{ inputs.pre_deploy_script }}" ]]; then
            echo "Running pre-deploy script..."
            ${{ inputs.pre_deploy_script }}
          fi
          
          case "${{ inputs.action }}" in
            pull)
              # Pull latest images, recreate only if changed
              sudo docker compose pull
              sudo docker compose up -d
              ;;
            restart)
              # Just restart without pulling
              sudo docker compose restart
              ;;
            rebuild)
              # Rebuild from Dockerfile and restart
              sudo docker compose build --pull
              sudo docker compose up -d --force-recreate
              ;;
            down-up)
              # Full down/up cycle (for major changes)
              sudo docker compose down
              sudo docker compose up -d
              ;;
          esac
          
          # Wait for health checks
          echo "Waiting for containers to be healthy..."
          sleep 5
          sudo docker compose ps
          
          echo "Deployment complete for ${{ inputs.app_name }}"
```

## Component 2: Home Server Workflow

Handles config changes and internal builds.

### File: `.github/workflows/deploy.yml`

```yaml
name: Deploy Changed Apps

on:
  push:
    branches: [main]
    paths:
      - 'apps/**'
  workflow_dispatch:
    inputs:
      app_name:
        description: 'Specific app to deploy (or "all" for changed apps)'
        required: false
        default: ''
      action:
        description: 'Deploy action'
        required: false
        default: 'pull'
        type: choice
        options:
          - pull
          - restart
          - rebuild
          - down-up

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      changed_apps: ${{ steps.detect.outputs.apps }}
      has_changes: ${{ steps.detect.outputs.has_changes }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2

      - name: Detect changed apps
        id: detect
        run: |
          if [[ -n "${{ github.event.inputs.app_name }}" ]]; then
            # Manual trigger with specific app
            echo "apps=[\"${{ github.event.inputs.app_name }}\"]" >> $GITHUB_OUTPUT
            echo "has_changes=true" >> $GITHUB_OUTPUT
          else
            # Detect from git diff
            CHANGED_APPS=$(git diff --name-only HEAD~1 HEAD | \
              grep '^apps/' | \
              cut -d'/' -f2 | \
              sort -u | \
              jq -R -s -c 'split("\n") | map(select(length > 0))')
            
            echo "apps=$CHANGED_APPS" >> $GITHUB_OUTPUT
            
            if [[ "$CHANGED_APPS" == "[]" ]]; then
              echo "has_changes=false" >> $GITHUB_OUTPUT
            else
              echo "has_changes=true" >> $GITHUB_OUTPUT
            fi
          fi

      - name: Show detected changes
        run: |
          echo "Changed apps: ${{ steps.detect.outputs.apps }}"
          echo "Has changes: ${{ steps.detect.outputs.has_changes }}"

  deploy:
    needs: detect-changes
    if: needs.detect-changes.outputs.has_changes == 'true'
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        app: ${{ fromJson(needs.detect-changes.outputs.changed_apps) }}
    steps:
      - uses: actions/checkout@v4

      - name: Check if app should be deployed
        id: check
        run: |
          APP_DIR="apps/${{ matrix.app }}"
          
          # Skip if no docker-compose.yml
          if [[ ! -f "$APP_DIR/docker-compose.yml" ]]; then
            echo "skip=true" >> $GITHUB_OUTPUT
            echo "Skipping ${{ matrix.app }}: no docker-compose.yml"
            exit 0
          fi
          
          # Check for x-auto-deploy label
          if grep -q 'x-auto-deploy: false' "$APP_DIR/docker-compose.yml" 2>/dev/null; then
            echo "skip=true" >> $GITHUB_OUTPUT
            echo "Skipping ${{ matrix.app }}: x-auto-deploy: false"
            exit 0
          fi
          
          # Determine action based on changes
          if git diff --name-only HEAD~1 HEAD | grep -q "^$APP_DIR/Dockerfile"; then
            echo "action=rebuild" >> $GITHUB_OUTPUT
          else
            echo "action=${{ github.event.inputs.action || 'pull' }}" >> $GITHUB_OUTPUT
          fi
          
          echo "skip=false" >> $GITHUB_OUTPUT

      - name: Pull latest server config
        if: steps.check.outputs.skip != 'true'
        uses: appleboy/ssh-action@v1
        with:
          host: 192.168.86.47
          port: 4242
          username: claude-deploy
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: |
            cd ~/server
            sudo git pull origin main

      - name: Deploy ${{ matrix.app }}
        if: steps.check.outputs.skip != 'true'
        uses: ./.github/actions/deploy-app
        with:
          app_name: ${{ matrix.app }}
          ssh_key: ${{ secrets.SERVER_SSH_KEY }}
          action: ${{ steps.check.outputs.action }}

  notify:
    needs: [detect-changes, deploy]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Notify on failure
        if: needs.deploy.result == 'failure'
        run: |
          echo "::error::Deployment failed for one or more apps"
          # Add Mattermost/Discord notification here
```

## Component 3: External Repo Workflow Template

For repos like trading-bot, homelab-ai that build their own images.

### Template for external repos:

```yaml
# .github/workflows/build-and-deploy.yml
name: Build and Deploy

on:
  push:
    branches: [main]
    paths:
      - 'src/**'
      - 'Dockerfile'
      - 'requirements.txt'
  workflow_dispatch:

env:
  HARBOR_REGISTRY: harbor.server.unarmedpuppy.com
  IMAGE_NAME: library/trading-bot  # Change per repo

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      image_tag: ${{ steps.meta.outputs.tags }}
    steps:
      - uses: actions/checkout@v4

      - name: Log in to Harbor
        uses: docker/login-action@v3
        with:
          registry: ${{ env.HARBOR_REGISTRY }}
          username: ${{ secrets.HARBOR_USERNAME }}
          password: ${{ secrets.HARBOR_PASSWORD }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ env.HARBOR_REGISTRY }}/${{ env.IMAGE_NAME }}:latest
            ${{ env.HARBOR_REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Checkout home-server for action
        uses: actions/checkout@v4
        with:
          repository: unarmedpuppy/home-server
          path: home-server
          sparse-checkout: .github/actions

      - name: Deploy to server
        uses: ./home-server/.github/actions/deploy-app
        with:
          app_name: trading-bot  # Change per repo
          ssh_key: ${{ secrets.SERVER_SSH_KEY }}
          action: pull
```

## Component 4: Watchtower for Auto-Updates

For apps that should auto-update when upstream images change.

### File: `apps/watchtower/docker-compose.yml`

```yaml
version: "3.8"

x-enabled: true

services:
  watchtower:
    image: harbor.server.unarmedpuppy.com/docker-hub/containrrr/watchtower:latest
    container_name: watchtower
    restart: unless-stopped
    environment:
      - TZ=America/Chicago
      - WATCHTOWER_CLEANUP=true
      - WATCHTOWER_POLL_INTERVAL=86400  # Check daily
      - WATCHTOWER_LABEL_ENABLE=true    # Only update labeled containers
      - WATCHTOWER_INCLUDE_STOPPED=false
      - WATCHTOWER_REVIVE_STOPPED=false
      - WATCHTOWER_NOTIFICATIONS=shoutrrr
      - WATCHTOWER_NOTIFICATION_URL=generic+https://mattermost.server.unarmedpuppy.com/hooks/xxx
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - my-network
    labels:
      - "homepage.group=Infrastructure"
      - "homepage.name=Watchtower"
      - "homepage.icon=si-docker"
      - "homepage.description=Automatic container updates"

networks:
  my-network:
    external: true
```

### Opt-in via Labels

Apps that want auto-updates add this label:

```yaml
services:
  postgres:
    image: harbor.server.unarmedpuppy.com/docker-hub/library/postgres:17-alpine
    labels:
      - "com.centurylinklabs.watchtower.enable=true"
```

### Apps to EXCLUDE from auto-update (stateful/critical):

| App | Reason |
|-----|--------|
| harbor-* | Registry - could break pulls |
| traefik | Reverse proxy - could break all access |
| *-db, postgres, mysql | Databases - data integrity |
| vaultwarden | Passwords - too critical |
| immich-* | Photo library - complex upgrade process |

## Component 5: Deployment Control Labels

Add these labels to docker-compose.yml files for deployment control:

```yaml
# Prevent auto-deployment on push
x-auto-deploy: false

# Mark as essential (extra caution)
x-essential: true

# Enable Watchtower auto-update
labels:
  - "com.centurylinklabs.watchtower.enable=true"
```

### Recommended settings by app type:

| App Type | x-auto-deploy | x-essential | Watchtower |
|----------|---------------|-------------|------------|
| Infrastructure (traefik, harbor) | false | true | false |
| Databases | false | true | false |
| Stateful (immich, vaultwarden) | false | true | false |
| Media (plex, jellyfin) | true | false | false |
| Utilities (metube, n8n) | true | false | true |
| Game servers | true | false | false |

## Implementation Roadmap

### Phase 1: Foundation (Week 1)
- [ ] Create `.github/actions/deploy-app/action.yml`
- [ ] Create `.github/workflows/deploy.yml` for home-server
- [ ] Add SSH key for claude-deploy to GitHub secrets
- [ ] Test with one low-risk app (e.g., metube)

### Phase 2: External Repos (Week 2)
- [ ] Add workflow to trading-bot repo
- [ ] Add workflow to homelab-ai repo
- [ ] Test end-to-end: code change → build → deploy

### Phase 3: Watchtower (Week 3)
- [ ] Deploy Watchtower with label-based opt-in
- [ ] Add watchtower labels to appropriate apps
- [ ] Configure notifications
- [ ] Monitor for 1 week

### Phase 4: Refinement (Week 4)
- [ ] Add `x-auto-deploy` labels to sensitive apps
- [ ] Create Mattermost notifications for deploys
- [ ] Document all patterns in AGENTS.md
- [ ] Create skill in `agents/skills/github-actions-deploy/`

## Security Considerations

1. **SSH Key Management**
   - Store in GitHub Secrets as `SERVER_SSH_KEY`
   - Use dedicated `claude-deploy` user (already exists)
   - Key should have limited sudo access (already configured)

2. **No Secrets in Workflows**
   - All secrets via GitHub Secrets or server .env files
   - Never echo or log secrets

3. **Deployment User Restrictions**
   - claude-deploy can only run whitelisted docker commands
   - No `docker rm`, `docker rmi`, `docker system prune`
   - git operations only in ~/server

## Rollback Strategy

If a deployment fails:

```bash
# Manual rollback
ssh -p 4242 claude-deploy@192.168.86.47
cd ~/server
git log --oneline -5  # Find previous commit
git checkout <commit> -- apps/<app>/docker-compose.yml
sudo docker compose -f apps/<app>/docker-compose.yml up -d
```

Future enhancement: Add `workflow_dispatch` for rollback with commit SHA input.

## Open Questions

1. **Harbor image cleanup**: When do we prune old images from Harbor?
2. **Deployment windows**: Should we restrict deploys to certain hours?
3. **Approval gates**: Should production-critical apps require manual approval?
4. **Health check timeout**: How long to wait for containers to become healthy?

---

## References

- [appleboy/ssh-action](https://github.com/appleboy/ssh-action)
- [Watchtower Documentation](https://containrrr.dev/watchtower/)
- [GitHub Actions Reusable Workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows)
