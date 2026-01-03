---
name: docker-operations
description: Manage Docker containers on the home server via SSH
when_to_use: When asked to list, inspect, restart, or check logs of Docker containers
---

# Docker Operations

All docker commands run on the server via SSH as `claude-deploy` user.

## Connection

```bash
ssh -p 4242 claude-deploy@192.168.86.47 'COMMAND'
```

## Common Operations

### List Containers

```bash
ssh -p 4242 claude-deploy@192.168.86.47 'sudo docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
```

### View Logs

```bash
ssh -p 4242 claude-deploy@192.168.86.47 'sudo docker logs --tail 50 CONTAINER_NAME'

# Follow logs
ssh -p 4242 claude-deploy@192.168.86.47 'sudo docker logs -f --tail 20 CONTAINER_NAME'
```

### Restart Container

```bash
ssh -p 4242 claude-deploy@192.168.86.47 'sudo docker restart CONTAINER_NAME'
```

### Check Container Health

```bash
ssh -p 4242 claude-deploy@192.168.86.47 'sudo docker inspect --format "{{.State.Health.Status}}" CONTAINER_NAME'
```

### Container Stats

```bash
ssh -p 4242 claude-deploy@192.168.86.47 'sudo docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"'
```

### Inspect Container

```bash
ssh -p 4242 claude-deploy@192.168.86.47 'sudo docker inspect CONTAINER_NAME'
```

## Docker Compose Operations

Compose files are in `/home/unarmedpuppy/server/apps/*/docker-compose.yml`

### Restart a Service

```bash
ssh -p 4242 claude-deploy@192.168.86.47 'sudo docker compose -f /home/unarmedpuppy/server/apps/SERVICE/docker-compose.yml restart'
```

### Pull and Update

```bash
ssh -p 4242 claude-deploy@192.168.86.47 'sudo docker compose -f /home/unarmedpuppy/server/apps/SERVICE/docker-compose.yml pull && sudo docker compose -f /home/unarmedpuppy/server/apps/SERVICE/docker-compose.yml up -d'
```

### View Service Logs

```bash
ssh -p 4242 claude-deploy@192.168.86.47 'sudo docker compose -f /home/unarmedpuppy/server/apps/SERVICE/docker-compose.yml logs --tail 50'
```

## Blocked Operations

These commands are NOT allowed (sudoers restriction):

- `docker rm` - Cannot delete containers
- `docker rmi` - Cannot delete images  
- `docker volume rm` - Cannot delete volumes
- `docker system prune` - Cannot prune system

If you need these operations, ask the user to run them directly.
