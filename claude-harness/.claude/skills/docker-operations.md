---
name: docker-operations
description: Manage Docker containers on the home server via SSH
when_to_use: When asked to list, inspect, restart, or check logs of Docker containers
---

# Docker Operations

All docker commands run on the server via SSH as `claude-deploy` user.

## Connection

```bash
SSH_CMD="ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal"
$SSH_CMD 'sudo docker COMMAND'
```

Or inline:
```bash
ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal 'sudo docker COMMAND'
```

## Common Operations

### List Containers

```bash
ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal \
  'sudo docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
```

### View Logs

```bash
# Last 50 lines
ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal \
  'sudo docker logs --tail 50 CONTAINER_NAME'

# Follow logs (use timeout to avoid hanging)
timeout 30 ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal \
  'sudo docker logs -f --tail 20 CONTAINER_NAME'
```

### Restart Container

```bash
ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal \
  'sudo docker restart CONTAINER_NAME'
```

### Check Container Health

```bash
ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal \
  'sudo docker inspect --format "{{.State.Health.Status}}" CONTAINER_NAME'
```

### Container Stats

```bash
ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal \
  'sudo docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"'
```

### Inspect Container

```bash
ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal \
  'sudo docker inspect CONTAINER_NAME'
```

## Docker Compose Operations

Compose files are in `/home/unarmedpuppy/server/apps/*/docker-compose.yml`

### Restart a Service

```bash
ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal \
  'sudo docker compose -f /home/unarmedpuppy/server/apps/SERVICE/docker-compose.yml restart'
```

### Pull and Update

```bash
ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal \
  'sudo docker compose -f /home/unarmedpuppy/server/apps/SERVICE/docker-compose.yml pull && \
   sudo docker compose -f /home/unarmedpuppy/server/apps/SERVICE/docker-compose.yml up -d'
```

### View Service Logs

```bash
ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal \
  'sudo docker compose -f /home/unarmedpuppy/server/apps/SERVICE/docker-compose.yml logs --tail 50'
```

## Blocked Operations

These commands are NOT allowed (sudoers restriction):

- `docker rm` - Cannot delete containers
- `docker rmi` - Cannot delete images  
- `docker volume rm` - Cannot delete volumes
- `docker system prune` - Cannot prune system

If you need these operations, ask the user to run them directly.

## Troubleshooting

### Permission Denied (publickey)
SSH key not authorized for claude-deploy user. Ask user to add:
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIH9qRw+hzNh8GVFv3Ec89mQh4n247nvSoJBhWkUpknob claude-harness@container
```
to `/home/claude-deploy/.ssh/authorized_keys`

### sudo: docker: command not found
The sudoers whitelist only allows specific docker commands. Check the exact command syntax.
