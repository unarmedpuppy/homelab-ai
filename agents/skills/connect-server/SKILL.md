---
name: connect-server
description: Execute commands on the server via SSH wrapper
when_to_use: Need to run commands on the server, check server status, execute server-side scripts
script: scripts/connect-server.sh
---

# Connect to Server

Execute commands on the home server via SSH wrapper.

## When to Use

- Need to run commands on the server
- Check server status
- Execute server-side scripts
- Debug server issues

## Usage

### Basic Command Execution

```bash
bash scripts/connect-server.sh "command"
```

### Examples

```bash
# Check Docker containers
bash scripts/connect-server.sh "docker ps"

# Check specific service
bash scripts/connect-server.sh "cd ~/server/apps/plex && docker compose ps"

# View logs
bash scripts/connect-server.sh "docker logs plex --tail 50"

# Check disk space
bash scripts/connect-server.sh "df -h"

# Run server-side script
bash scripts/connect-server.sh "~/server/scripts/check-service-health.sh"
```

## What It Does

The script wraps SSH connection details (host, port, user) to simplify server access:
- **Host**: `192.168.86.47`
- **Port**: `4242`
- **User**: `unarmedpuppy`

## Related Tools

- `standard-deployment` - Deploy code changes
- `check-service-health` - Health monitoring
- `troubleshoot-container-failure` - Debug containers

