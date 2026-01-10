---
name: gitea-deploy-workflow
description: Auto-deploy docker-compose changes via Gitea Actions on tag push
when_to_use: When you need to deploy configuration changes (docker-compose.yml, env vars, labels) to the server
---

# Gitea Deploy Workflow

Automatically deploys docker-compose configuration changes to the server when a version tag is pushed.

## How It Works

```
git tag v1.0.x → push → Gitea Actions → SSH to server → git pull → restart changed apps
```

1. **Trigger**: Push a tag matching `v*` pattern
2. **Detection**: Workflow compares current tag to previous tag
3. **Change Analysis**: Identifies which `apps/` directories have changes
4. **Deployment**: SSHs to server, pulls code, restarts only affected services
5. **Notification**: Sends success/failure to Mattermost

## Usage

### Deploy Changes

```bash
# 1. Make your changes to docker-compose files
vim apps/traefik/docker-compose.yml

# 2. Commit
git add .
git commit -m "fix: update traefik labels for overseerr"

# 3. Tag and push
git tag v1.0.5
git push origin main --tags
```

The workflow will:
- Detect that `apps/traefik/` changed
- SSH to server
- Run `git pull`
- Run `docker compose up -d` in `apps/traefik/`
- Notify Mattermost

### Multiple Apps

If you change multiple apps in one release:

```bash
# Changes to apps/traefik/ and apps/media-download/
git add .
git commit -m "fix: update traefik and media-download configs"
git tag v1.0.6
git push origin main --tags
```

Both `traefik` and `media-download` will be restarted.

### Non-App Changes

Changes outside `apps/` (scripts, docs, agents) won't trigger any restarts:

```bash
# Only scripts/ changed
git add scripts/
git commit -m "chore: update backup script"
git tag v1.0.7
git push origin main --tags
# Result: "No apps changed between tags. Nothing to deploy."
```

## Workflow File

**Location**: `.gitea/workflows/deploy-changed-apps.yml`

## Required Secrets

### Organization Secrets (homelab org)

Configure in Gitea (homelab org > Settings > Actions > Secrets):

| Secret | Description |
|--------|-------------|
| `DEPLOY_HOST` | Server IP (`192.168.86.47`) |
| `DEPLOY_PORT` | SSH port (`4242`) |
| `DEPLOY_USER` | Deploy user (`github-deploy`) |
| `DEPLOY_SSH_KEY` | Private SSH key for `github-deploy` |

These are shared across all homelab repos.

### Repository Secrets (home-server repo)

Configure in Gitea (home-server repo > Settings > Actions > Secrets):

| Secret | Description |
|--------|-------------|
| `MATTERMOST_WEBHOOK_URL` | Webhook for notifications (repo-specific) |

## Change Detection Logic

The workflow:
1. Finds the previous tag: `git tag --sort=-v:refname | head -n2`
2. Diffs between tags: `git diff --name-only PREV..CURRENT -- apps/`
3. Extracts app names: `apps/traefik/docker-compose.yml` → `traefik`
4. Restarts each unique app

## Comparison: This vs Watchtower

| Aspect | This Workflow | Watchtower |
|--------|---------------|------------|
| **Triggers on** | Git tag push | Docker image digest change |
| **Detects** | docker-compose.yml changes | New Docker images |
| **Use for** | Config changes (labels, env vars, ports) | Code changes in custom apps |
| **Restarts** | `docker compose up -d` | Container recreation |

**Use this workflow for**: Traefik labels, environment variables, volume mounts, port changes, adding/removing services.

**Use Watchtower for**: Custom app code changes (trading-bot, pokedex, etc.) that build new images.

## Troubleshooting

### Workflow not triggering

- Ensure tag matches `v*` pattern (e.g., `v1.0.5`, not `release-1.0.5`)
- Check Gitea Actions is enabled for the repo
- Verify runner is online in Gitea

### SSH connection failed

- Verify `github-deploy` user exists on server
- Check SSH key is correctly stored in secrets
- Ensure port 4242 is accessible from runner network

### App not restarting

- Confirm changes are in `apps/APP_NAME/` directory
- Check the app has a `docker-compose.yml` file
- Review workflow logs for skip messages

### Check workflow logs

1. Go to Gitea > home-server repo > Actions
2. Click on the workflow run
3. Expand job steps to see output

## Security

- **SSH Key**: Stored encrypted in Gitea secrets
- **github-deploy user**: Has restricted sudo permissions:
  - `sudo docker compose *`
  - `sudo docker pull *`
  - `sudo git -C /home/unarmedpuppy/server *`
- **No root access**: Cannot run arbitrary commands
- **Internal network**: Uses `192.168.86.47`, not exposed externally
