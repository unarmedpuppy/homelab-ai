---
name: standard-deployment
description: Deploy code changes to server
when_to_use: Deploying code changes, updating service configurations, restarting services after config changes
script: scripts/deploy-to-server.sh
---

# Standard Deployment

Deploy code changes to the home server.

## When to Use

- Deploying code changes
- Updating service configurations
- Restarting services after config changes

## Automated Deployment (Recommended)

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

## Manual Steps (Alternative)

If you need more control:

### 1. Check Current State

```bash
git status
git diff
```

### 2. Commit and Push

```bash
git add .
git commit -m "Description of changes"
git push
```

### 3. Pull on Server and Restart

```bash
# SSH to server and pull
bash scripts/connect-server.sh "cd ~/server && git pull"

# Restart affected service
bash scripts/connect-server.sh "cd ~/server/apps/SERVICE_NAME && docker compose restart"
```

### 4. Verify

```bash
# Check container is running
bash scripts/connect-server.sh "docker ps | grep SERVICE_NAME"

# Check logs for errors
bash scripts/connect-server.sh "docker logs SERVICE_NAME --tail 50"
```

## If Something Goes Wrong

1. Check logs: `docker logs SERVICE_NAME --tail 100`
2. Check container status: `docker inspect SERVICE_NAME`
3. Rollback if needed: `git revert HEAD && git push`

