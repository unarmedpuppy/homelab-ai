---
name: deploy-polymarket-bot
description: Deploy polymarket-bot with full Docker rebuild to ensure code changes take effect
when_to_use: When deploying any code changes to the polymarket-bot application
---

# Deploy Polymarket Bot

This skill deploys the polymarket-bot application with a full Docker image rebuild to ensure all code changes take effect. Docker's layer caching can cause stale code to persist even after `git pull`, so we use `--no-cache` to force a complete rebuild.

## Prerequisites

- Changes committed and pushed to git
- SSH access to server via `scripts/connect-server.sh`

## Deployment Steps

### 1. Pull latest code on server

```bash
scripts/connect-server.sh "cd ~/server && git pull origin main"
```

### 2. Rebuild and restart with NO CACHE

**CRITICAL**: Always use `--no-cache` to prevent stale code from Docker layer caching.

```bash
scripts/connect-server.sh "cd ~/server/apps/polymarket-bot && docker compose down && docker compose build --no-cache && docker compose up -d"
```

### 3. Verify deployment

```bash
# Check container is running
scripts/connect-server.sh "docker ps --filter name=polymarket"

# Verify the fix is in the container (example: check a specific line)
scripts/connect-server.sh "docker exec polymarket-bot grep -A5 'your_code_pattern' /app/src/path/to/file.py"

# Check logs for errors
scripts/connect-server.sh "docker logs polymarket-bot --tail 50"
```

### 4. Run regression tests (optional but recommended)

```bash
scripts/connect-server.sh "cd ~/server/apps/polymarket-bot && docker compose run --rm polymarket-bot python3 -m pytest tests/ -v"
```

## Quick One-Liner

For a complete deploy with cache clear:

```bash
scripts/connect-server.sh "cd ~/server && git pull origin main && cd apps/polymarket-bot && docker compose down && docker compose build --no-cache && docker compose up -d"
```

## Why --no-cache?

Docker's build cache uses layer hashing. If `COPY src/ ./src/` hasn't changed its layer hash (based on the COPY instruction, not file contents in some edge cases), Docker may reuse a cached layer with old code. Using `--no-cache` forces Docker to:

1. Re-download base images if updated
2. Re-run all RUN commands
3. Re-copy all files fresh

This guarantees the running container has the latest code.

## Troubleshooting

### Code changes not taking effect

If you see old behavior after deploy:

```bash
# 1. Verify git has latest
scripts/connect-server.sh "cd ~/server/apps/polymarket-bot && git log -1 --oneline"

# 2. Verify file in container matches git
scripts/connect-server.sh "docker exec polymarket-bot cat /app/src/path/to/file.py | head -50"

# 3. If mismatch, force full rebuild
scripts/connect-server.sh "cd ~/server/apps/polymarket-bot && docker compose down && docker system prune -f && docker compose build --no-cache && docker compose up -d"
```

### Container won't start

```bash
# Check build output for errors
scripts/connect-server.sh "cd ~/server/apps/polymarket-bot && docker compose build --no-cache 2>&1 | tail -50"

# Check container logs
scripts/connect-server.sh "docker logs polymarket-bot"
```
