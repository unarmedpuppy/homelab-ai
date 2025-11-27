# Troubleshoot Container Failure

Debug why a Docker container won't start or is unhealthy.

## When to Use

- Container won't start
- Container crashes or exits
- Container is unhealthy
- Service not responding

## Steps

### 1. Check Container Status

```bash
docker ps -a | grep CONTAINER_NAME
docker inspect CONTAINER_NAME --format '{{.State.Status}} {{.State.Health.Status}}'
```

### 2. View Logs

```bash
docker logs CONTAINER_NAME --tail 100
docker logs CONTAINER_NAME --tail 100 2>&1 | grep -i error
```

### 3. Check Resources

```bash
df -h                    # Disk space
docker system df         # Docker disk usage
free -h                  # Memory (Linux) or vm_stat (macOS)
```

### 4. Check Dependencies

```bash
# Is the network accessible?
docker network ls
docker network inspect NETWORK_NAME

# Are dependent services running?
docker ps | grep postgres  # or whatever dependency
```

### 5. Check Configuration

```bash
# Validate docker-compose
docker compose -f docker-compose.yml config

# Check environment variables
docker inspect CONTAINER_NAME --format '{{.Config.Env}}'
```

## Common Issues

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Exits immediately | Missing config/env | Check logs for missing vars |
| Port already in use | Port conflict | Change port or stop other service |
| OOMKilled | Out of memory | Increase memory limit |
| Unhealthy | App not responding | Check app logs, dependencies |
| Permission denied | Volume permissions | Check mount permissions |

## Quick Fixes

```bash
# Restart container
docker restart CONTAINER_NAME

# Recreate container
docker compose -f apps/X/docker-compose.yml up -d --force-recreate

# Remove and recreate
docker rm -f CONTAINER_NAME
docker compose -f apps/X/docker-compose.yml up -d
```
