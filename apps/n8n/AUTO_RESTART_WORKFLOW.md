# Docker Container Auto-Restart Workflow

## Overview

This n8n workflow automatically monitors and restarts gluetun-dependent containers (NZBGet, qBittorrent, slskd) when they exit after gluetun restarts.

## Problem

Containers using `network_mode: "service:gluetun"` exit when gluetun restarts, even though gluetun may be healthy again. This causes:
- Sonarr/Radarr to report "Download Client Unavailable"
- Service interruptions until manual intervention

**Root Cause**: Docker's `depends_on: condition: service_healthy` only applies during initial startup, not when gluetun restarts after containers are running.

## Solution

The workflow:
1. **Monitors** gluetun health every 5 minutes
2. **Checks** dependent container status
3. **Filters** for containers that exited with code 128 (network namespace loss)
4. **Restarts** stopped containers via docker-compose
5. **Verifies** restart was successful

## Workflow Structure

```
Schedule Trigger (every 5 minutes)
  ↓
Check Gluetun Health
  ↓
Filter: Only proceed if gluetun is healthy
  ↓
Check Dependent Containers (nzbget, qbittorrent, slskd)
  ↓
Parse and Filter: Only exit code 128
  ↓
Filter: Only stopped containers
  ↓
Restart Container (via docker-compose)
  ↓
Wait 10 seconds
  ↓
Verify Restart
  ↓
Format Result
```

## Monitored Containers

- `media-download-nzbget` → service: `nzbget`
- `media-download-qbittorrent` → service: `qbittorrent`
- `media-download-slskd` → service: `slskd`

## Safety Features

1. **Gluetun Health Check**: Only restarts containers if gluetun is healthy
2. **Exit Code Filtering**: Only restarts containers that exited with code 128 (network namespace loss)
3. **Service Mapping**: Maps container names to docker-compose service names
4. **Verification**: Confirms container is running after restart

## Setup

### Option 1: Manual Import

1. Open n8n: `https://n8n.server.unarmedpuppy.com`
2. Click the **three-dot menu** (⋮) in the upper-right corner
3. Select **"Import from File"**
4. Navigate to: `~/server/apps/n8n/workflows/`
5. Import: `docker-container-auto-restart.json`

### Option 2: API Import

```bash
cd ~/server/apps/n8n
export N8N_API_KEY=$(grep N8N_API_KEY .env | cut -d'=' -f2)
bash import-workflows.sh
```

## Configuration

**No credentials needed!** The Docker socket is already mounted in the n8n container (`/var/run/docker.sock`), so Execute Command nodes work directly.

## Activation

After importing:
1. Open the workflow in n8n
2. Review the node configuration
3. Toggle the **Active** switch to enable the workflow
4. The workflow will run every 5 minutes automatically

## Testing

### Manual Test

1. **Stop a container**:
   ```bash
   docker stop media-download-nzbget
   ```

2. **Wait for workflow** (or trigger manually in n8n):
   - Workflow runs every 5 minutes
   - Or click "Execute Workflow" in n8n UI

3. **Verify restart**:
   ```bash
   docker ps | grep media-download-nzbget
   ```
   Container should be running again.

### Edge Cases

- **Gluetun unhealthy**: Workflow will not restart containers (safety feature)
- **Exit code != 128**: Workflow will not restart (only network namespace loss)
- **Multiple containers stopped**: Workflow will restart each one

## Monitoring

Check workflow execution in n8n:
1. Open the workflow
2. Click "Executions" tab
3. View execution history and results

## Troubleshooting

### Workflow Not Running

- Check workflow is **Active** (toggle switch)
- Check schedule trigger is configured (every 5 minutes)
- Check n8n container is running: `docker ps | grep n8n`

### Containers Not Restarting

- Verify gluetun is healthy: `docker inspect media-download-gluetun --format '{{.State.Health.Status}}'`
- Check container exit code: `docker ps -a | grep media-download-nzbget`
- Verify docker-compose path: `cd ~/server/apps/media-download && docker-compose ps`

### False Positives

- Workflow only restarts containers with exit code 128
- If containers exit for other reasons, they won't be restarted (by design)

## Related Documentation

- `agents/plans/local/docker-container-auto-restart-n8n.md` - Implementation plan
- `agents/personas/media-download-agent.md` - Media download stack documentation
- `apps/n8n/README.md` - n8n setup and usage

## Future Enhancements

- Add rate limiting to prevent restart loops
- Add Telegram notifications for restart events
- Add logging to external service
- Expand to other docker-compose services with similar dependencies

