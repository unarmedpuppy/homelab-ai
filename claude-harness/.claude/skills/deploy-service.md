---
name: deploy-service
description: Deploy or update services on the home server
when_to_use: When asked to deploy, update, or restart services
---

# Deploy Service

## SSH Connection

All server commands use:
```bash
ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal 'COMMAND'
```

## Deployment Workflow

### For homelab-ai Services (llm-router, dashboard, claude-harness, etc.)

These use GitHub Actions CI/CD:

1. **Make changes** in `/workspace/homelab-ai/`
2. **Commit and push** to trigger build:
   ```bash
   cd /workspace/homelab-ai
   git add .
   git commit -m "description of changes"
   git push origin main
   ```
3. **Wait for GitHub Actions** (~2 minutes)
4. **Deploy on server**:
   ```bash
   ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal << 'EOF'
   cd /home/unarmedpuppy/server/apps/homelab-ai
   sudo docker compose pull SERVICE_NAME
   sudo docker compose up -d SERVICE_NAME
   EOF
   ```

### For home-server Services (other apps)

These deploy via git pull:

1. **Make changes** in `/workspace/home-server/`
2. **Commit and push**:
   ```bash
   cd /workspace/home-server
   git add .
   git commit -m "description"
   git push origin main
   ```
3. **Pull and restart on server**:
   ```bash
   ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal << 'EOF'
   sudo git -C /home/unarmedpuppy/server pull
   sudo docker compose -f /home/unarmedpuppy/server/apps/SERVICE/docker-compose.yml up -d
   EOF
   ```

## Quick Restart (No Code Changes)

```bash
ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal \
  'sudo docker restart SERVICE_NAME'
```

## Pull Latest Image and Restart

```bash
ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal << 'EOF'
sudo docker compose -f /home/unarmedpuppy/server/apps/SERVICE/docker-compose.yml pull
sudo docker compose -f /home/unarmedpuppy/server/apps/SERVICE/docker-compose.yml up -d
EOF
```

## Verify Deployment

```bash
# Check container is running
ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal \
  'sudo docker ps | grep SERVICE_NAME'

# Check logs for errors
ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal \
  'sudo docker logs --tail 20 SERVICE_NAME'

# Check health (if healthcheck configured)
ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal \
  'sudo docker inspect --format "{{.State.Health.Status}}" SERVICE_NAME'
```

## Service Locations

| Service Type | Docker Compose Location |
|--------------|------------------------|
| homelab-ai | `/home/unarmedpuppy/server/apps/homelab-ai/docker-compose.yml` |
| traefik | `/home/unarmedpuppy/server/apps/traefik/docker-compose.yml` |
| Other apps | `/home/unarmedpuppy/server/apps/APP_NAME/docker-compose.yml` |

## Troubleshooting

### Permission Denied (publickey)
SSH key not authorized. Ask user to add container's key to `/home/claude-deploy/.ssh/authorized_keys`

### Command blocked by sudoers
Only whitelisted commands work. Check exact syntax matches sudoers rules.
