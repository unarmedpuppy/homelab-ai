---
name: homelab-network
description: Internal Docker network URLs for homelab services - use these when running inside claude-harness or other containers
when_to_use: When making API calls or git operations from inside Docker containers on my-network
---

# Homelab Internal Network

## Overview

When running inside claude-harness or other Docker containers on `my-network`, you MUST use internal Docker network URLs instead of external URLs. External URLs (*.server.unarmedpuppy.com) go through Traefik which strips authentication headers.

## Internal Service URLs

### Git (Gitea)
```
Internal: http://gitea:3000
External: https://gitea.server.unarmedpuppy.com
```

**Clone repos:**
```bash
git clone http://gitea:3000/homelab/repo-name.git
```

**Git credentials format** (in ~/.git-credentials):
```
http://oauth2:${GITEA_TOKEN}@gitea:3000
```

### Bird API
```
Internal: http://bird-api:8000
External: https://bird-api.server.unarmedpuppy.com
```

**Example:**
```bash
curl http://bird-api:8000/digests
curl -X POST http://bird-api:8000/trigger-fetch -H "Content-Type: application/json" -d '{"mode": "auto"}'
```

### LLM Router (Local AI API)
```
Internal: http://llm-router:8000
External: https://homelab-ai-api.server.unarmedpuppy.com
```

**Example:**
```bash
curl http://llm-router:8000/health
curl -X POST http://llm-router:8000/v1/chat/completions ...
```

### Claude Harness
```
Internal: http://claude-harness:8013
External: http://192.168.86.47:8013
```

### Harbor Registry
```
Internal: http://harbor-core:8080
External: https://harbor.server.unarmedpuppy.com
```

## Service Discovery

All homelab services on `my-network` can be reached by container name:

| Service | Container Name | Port | Purpose |
|---------|---------------|------|---------|
| Gitea | `gitea` | 3000 | Git hosting |
| Bird API | `bird-api` | 8000 | Twitter bookmarks API |
| LLM Router | `llm-router` | 8000 | AI API gateway |
| Claude Harness | `claude-harness` | 8013 | Claude CLI wrapper |
| Postgres (Gitea) | `gitea-db` | 5432 | Gitea database |
| Traefik | `traefik` | 80/443 | Reverse proxy |

## When to Use Internal vs External

**Use INTERNAL URLs when:**
- Running inside claude-harness
- Running inside any container on my-network
- Making API calls from automated jobs/workflows
- Git clone/push/pull operations from containers

**Use EXTERNAL URLs when:**
- Running from your laptop/desktop
- Running from outside the Docker network
- Accessing via browser
- Documentation examples for manual use

## Troubleshooting

### "401 Unauthorized" from inside container
You're probably using the external URL. Switch to internal:
```bash
# Bad (goes through Traefik, auth stripped)
curl https://bird-api.server.unarmedpuppy.com/digests

# Good (direct container-to-container)
curl http://bird-api:8000/digests
```

### "Could not resolve host"
The container might not be on `my-network`. Check with:
```bash
docker network inspect my-network
```

### Git clone fails with auth error
Update ~/.git-credentials to use internal URL:
```
http://oauth2:YOUR_TOKEN@gitea:3000
```
