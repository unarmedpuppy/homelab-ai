---
name: docker-container-management
description: Manage Docker containers - list, logs, restart, inspect, stats
when_to_use: Need to check container status, view logs, restart services, debug container issues
---

# Docker Container Management

Manage Docker containers on the server.

## When to Use

- Check container status (running, stopped, unhealthy)
- View container logs for debugging
- Restart containers after config changes
- Inspect container details (ports, mounts, networks)
- Monitor resource usage (CPU, memory)

## Prerequisites

For server containers, use the `connect-server` skill to SSH first:

```bash
bash scripts/connect-server.sh "docker command here"
```

## Common Commands

### List Containers

```bash
# Running containers
docker ps

# All containers (including stopped)
docker ps -a

# Filter by name
docker ps --filter "name=homepage"

# Custom format
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### View Logs

```bash
# Last 100 lines
docker logs <container> --tail 100

# Follow logs (live)
docker logs <container> -f

# Logs since time
docker logs <container> --since 1h

# Logs with timestamps
docker logs <container> -t --tail 50
```

### Restart Containers

```bash
# Restart single container
docker restart <container>

# Restart with timeout
docker restart -t 30 <container>

# Using docker-compose (recommended for services)
cd ~/server/apps/<app-name>
docker compose restart
```

### Inspect Container

```bash
# Full inspection (JSON)
docker inspect <container>

# Specific fields
docker inspect --format '{{.State.Status}}' <container>
docker inspect --format '{{.NetworkSettings.IPAddress}}' <container>
docker inspect --format '{{json .Mounts}}' <container>
```

### Resource Stats

```bash
# Live stats (all containers)
docker stats

# One-time snapshot
docker stats --no-stream

# Specific container
docker stats <container> --no-stream
```

### Start/Stop Containers

```bash
# Stop container
docker stop <container>

# Start container
docker start <container>

# Kill (force stop)
docker kill <container>
```

## Docker Compose Operations

For services managed by docker-compose:

```bash
# Navigate to app directory
cd ~/server/apps/<app-name>

# Start services
docker compose up -d

# Stop services
docker compose down

# Restart services
docker compose restart

# Rebuild and restart
docker compose up -d --build

# View compose logs
docker compose logs -f
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs <container>

# Check if port is in use
docker ps --filter "publish=8080"
netstat -tlnp | grep 8080

# Check container events
docker events --filter container=<container> --since 1h
```

### Container Keeps Restarting

```bash
# Check restart count
docker inspect --format '{{.RestartCount}}' <container>

# Check exit code
docker inspect --format '{{.State.ExitCode}}' <container>

# View last logs before crash
docker logs <container> --tail 50
```

### Out of Memory

```bash
# Check memory usage
docker stats <container> --no-stream

# Check memory limit
docker inspect --format '{{.HostConfig.Memory}}' <container>
```

## Server-Specific Commands

When managing containers on the home server:

```bash
# List all running containers
bash scripts/connect-server.sh "docker ps"

# Check specific container logs
bash scripts/connect-server.sh "docker logs homepage --tail 100"

# Restart a container
bash scripts/connect-server.sh "docker restart homepage"

# Full service restart with compose
bash scripts/connect-server.sh "cd ~/server/apps/homepage && docker compose restart"
```

## Related Skills

- `connect-server` - SSH to server
- `standard-deployment` - Deploy code changes
- `troubleshoot-container-failure` - Deep container debugging
- `check-service-health` - Health monitoring
