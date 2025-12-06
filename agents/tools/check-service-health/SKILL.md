---
name: check-service-health
description: Quick health check for all Docker services
when_to_use: Regular monitoring, after deployments, troubleshooting service issues, system status checks
script: scripts/check-service-health.sh
---

# Check Service Health

Quick health check for all Docker services.

## When to Use

- Regular monitoring (daily/weekly)
- After deployments
- Troubleshooting service issues
- System status checks
- Pre-maintenance verification

## Usage

```bash
# From local machine
bash scripts/check-service-health.sh

# On server
bash scripts/connect-server.sh "~/server/scripts/check-service-health.sh"
```

## Output

The script provides:

- **Container status** - Running, stopped, restarting, exited
- **Port mappings** - Exposed ports for each service
- **Health check status** - If health checks are configured
- **Recent restart counts** - Containers that have restarted frequently

## Example Output

```
Service: plex
Status: running
Ports: 32400:32400
Health: healthy
Restarts: 0

Service: traefik
Status: running
Ports: 80:80, 443:443
Health: healthy
Restarts: 0
```

## Interpreting Results

- **Running + Healthy** - Service is working correctly
- **Running + Unhealthy** - Service is up but not responding correctly
- **Restarting** - Service is having issues and restarting
- **Stopped** - Service is not running
- **High restart count** - Service may be crashing repeatedly

## Next Steps

If issues are found:
1. Check logs: `bash scripts/connect-server.sh "docker logs SERVICE_NAME --tail 100"`
2. Use `troubleshoot-container-failure` tool
3. Check system resources: `bash scripts/connect-server.sh "df -h && free -h"`

## Related Tools

- `troubleshoot-container-failure` - Debug container issues
- `system-health-check` - Comprehensive system status
- `connect-server` - Execute commands on server

