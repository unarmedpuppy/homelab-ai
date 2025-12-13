---
name: standard-deployment
description: Deploy code changes to server with proper Docker rebuild
when_to_use: Deploying code changes, updating service configurations, restarting services after config changes
script: scripts/deploy-to-server.sh
---

# Standard Deployment

Deploy code changes to the home server.

## When to Use

- Deploying code changes
- Updating service configurations
- Restarting services after config changes

## CRITICAL: Docker Cache Issue

**Always use `--no-cache` when deploying code changes to Docker containers.**

Docker's layer caching can cause deployed containers to run stale code even after `git pull`. This happens because Docker may reuse cached `COPY` layers if it thinks the instruction hasn't changed.

```bash
# WRONG - may use cached layers with old code
docker compose up -d --build

# CORRECT - forces fresh copy of all files
docker compose build --no-cache && docker compose up -d
```

## Quick Deploy (One-Liner)

For apps with Docker containers, use this pattern:

```bash
# Replace APP_NAME with the app directory name (e.g., polymarket-bot, trading-bot)
scripts/connect-server.sh "cd ~/server && git pull origin main && cd apps/APP_NAME && docker compose down && docker compose build --no-cache && docker compose up -d"
```

## Automated Deployment Script

Use the deployment script for complete workflow:

```bash
# Deploy all changes
bash scripts/deploy-to-server.sh "Your commit message"

# Deploy and restart specific app
bash scripts/deploy-to-server.sh "Update config" --app APP_NAME

# Deploy without restarting services
bash scripts/deploy-to-server.sh "Docs update" --no-restart
```

**What the script does:**
1. Stages all changes (`git add .`)
2. Commits with your message
3. Pushes to remote
4. Pulls on server
5. Optionally restarts specified app or all apps

## Manual Steps (Full Control)

### 1. Local: Commit and Push

```bash
git status
git add .
git commit -m "Description of changes"
git push origin main
```

### 2. Server: Pull and Rebuild

```bash
# Pull latest code
scripts/connect-server.sh "cd ~/server && git pull origin main"

# Rebuild with NO CACHE and restart (for Docker apps)
scripts/connect-server.sh "cd ~/server/apps/APP_NAME && docker compose down && docker compose build --no-cache && docker compose up -d"
```

### 3. Verify Deployment

```bash
# Check container is running
scripts/connect-server.sh "docker ps | grep APP_NAME"

# Verify code is updated in container
scripts/connect-server.sh "docker exec CONTAINER_NAME grep -n 'your_pattern' /app/path/to/file.py"

# Check logs for errors
scripts/connect-server.sh "docker logs CONTAINER_NAME --tail 50"
```

## Non-Docker Apps

For apps without Docker (static configs, etc.):

```bash
# Just pull - no rebuild needed
scripts/connect-server.sh "cd ~/server && git pull origin main"

# Restart if needed (e.g., traefik)
scripts/connect-server.sh "cd ~/server/apps/traefik && docker compose restart"
```

## Troubleshooting

### Code changes not taking effect

```bash
# 1. Verify git has latest commit
scripts/connect-server.sh "cd ~/server && git log -1 --oneline"

# 2. Verify file in container matches git
scripts/connect-server.sh "docker exec CONTAINER cat /app/path/to/file.py | head -50"

# 3. If mismatch, nuclear option - clear everything
scripts/connect-server.sh "cd ~/server/apps/APP_NAME && docker compose down && docker system prune -f && docker compose build --no-cache && docker compose up -d"
```

### Container won't start

```bash
# Check build output for errors
scripts/connect-server.sh "cd ~/server/apps/APP_NAME && docker compose build --no-cache 2>&1 | tail -50"

# Check container logs
scripts/connect-server.sh "docker logs CONTAINER_NAME"
```

### Rollback

```bash
# Revert last commit and redeploy
git revert HEAD
git push origin main
scripts/connect-server.sh "cd ~/server && git pull origin main && cd apps/APP_NAME && docker compose down && docker compose build --no-cache && docker compose up -d"
```

