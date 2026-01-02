---
name: deploy-homelab-ai-service
description: Deploy homelab-ai services (llm-router, dashboard, llm-manager, claude-harness) via GitHub Actions CI/CD
when_to_use: When deploying changes to any homelab-ai component
---

# Deploy Homelab-AI Service

## Overview

The homelab-ai repo uses GitHub Actions CI/CD to build Docker images and push them to Harbor. **NEVER manually build and push images.**

## Workflow

### 1. Make Changes in homelab-ai Repo

```bash
cd ~/repos/personal/homelab-ai
# Edit files in llm-router/, dashboard/, llm-manager/, or claude-harness/
```

### 2. Commit and Push

```bash
git add .
git commit -m "feat(component): description"
git push origin main
```

### 3. GitHub Actions Builds Automatically

The workflow at `.github/workflows/build-and-push.yml`:
- Detects which components changed
- Builds only the changed components
- Pushes to Harbor with tags: `latest` and `${{ github.sha }}`

**Monitored paths:**
- `llm-router/**`
- `dashboard/**`
- `llm-manager/**`
- `image-server/**`
- `tts-server/**`
- `claude-harness/**`

### 4. Wait for Build to Complete

Check GitHub Actions: https://github.com/unarmedpuppy/homelab-ai/actions

Or use gh CLI:
```bash
gh run list --repo unarmedpuppy/homelab-ai
gh run watch  # Watch latest run
```

### 5. Deploy on Server

Once the build succeeds, deploy the new image:

```bash
ssh -p 4242 unarmedpuppy@192.168.86.47

cd ~/server/apps/homelab-ai
docker compose pull <service-name>  # e.g., claude-harness
docker compose up -d <service-name>
```

Or deploy all services:
```bash
docker compose pull
docker compose up -d
```

## Manual Trigger

If you need to rebuild without code changes:

1. Go to https://github.com/unarmedpuppy/homelab-ai/actions
2. Select "Build and Push Docker Images"
3. Click "Run workflow"

## Component Images

| Component | Harbor Image |
|-----------|-------------|
| llm-router | `harbor.server.unarmedpuppy.com/library/llm-router:latest` |
| dashboard | `harbor.server.unarmedpuppy.com/library/local-ai-dashboard:latest` |
| llm-manager | `harbor.server.unarmedpuppy.com/library/llm-manager:latest` |
| claude-harness | `harbor.server.unarmedpuppy.com/library/claude-harness:latest` |
| image-server | `harbor.server.unarmedpuppy.com/library/image-server:latest` |
| tts-server | `harbor.server.unarmedpuppy.com/library/tts-server:latest` |

## Troubleshooting

### Build Failed
Check the GitHub Actions log for errors. Common issues:
- Dockerfile syntax errors
- Missing dependencies
- Harbor credentials issues

### Image Not Updating on Server
```bash
# Force pull latest
docker compose pull --ignore-pull-failures
docker compose up -d --force-recreate
```

### Check Current Running Version
```bash
docker inspect <container> --format '{{.Image}}'
```
