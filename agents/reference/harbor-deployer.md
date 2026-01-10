# Harbor Deployer

Custom Python service for auto-deploying container updates from Harbor registry.

## Overview

Harbor Deployer replaces Watchtower as the auto-deployment solution for custom apps. It polls the Harbor registry for image digest changes and automatically updates containers when new images are pushed.

## Why Not Watchtower?

Watchtower was [archived by CenturyLink in December 2025](https://github.com/containrrr/watchtower). While it worked for basic deployments, we encountered issues:

1. **Project abandoned** - No longer maintained, security updates, or bug fixes
2. **Notification failures** - Shoutrrr integration with Mattermost was unreliable (`notify=no` in logs despite correct config)
3. **Black box debugging** - Difficult to troubleshoot issues inside the container
4. **Container-in-container complexity** - Running as a container with Docker socket access creates chicken/egg problems

## Harbor Deployer Advantages

| Aspect | Watchtower | Harbor Deployer |
|--------|------------|-----------------|
| Maintenance | Archived (Dec 2025) | Custom, full control |
| Notifications | Shoutrrr (flaky) | Direct HTTP POST to Mattermost |
| Debugging | Container logs only | Full Python debugging, custom logging |
| Runtime | Docker container | systemd service (simpler) |
| Updates | Use docker compose restart | docker compose for containers |
| Configuration | Environment variables | JSON file + env overrides |

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    harbor-deployer.py                        │
│                   (systemd service)                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. List containers with label                               │
│     com.centurylinklabs.watchtower.enable=true               │
│                         ↓                                    │
│  2. For each container:                                      │
│     - Get current image digest (docker inspect)              │
│     - Query Harbor API for remote digest                     │
│                         ↓                                    │
│  3. If digest differs:                                       │
│     - docker pull <image>:latest                             │
│     - docker stop <container>                                │
│     - docker rm <container>                                  │
│     - docker compose up -d (from compose file path)          │
│                         ↓                                    │
│  4. POST to Mattermost webhook                               │
│                                                              │
│  5. Sleep 60 seconds, repeat                                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Flow

```
git tag v1.0.x → push → Gitea Actions builds → Harbor (:latest) → Harbor Deployer auto-deploys (~1 min)
```

1. Developer pushes tag to app repo
2. Gitea Actions builds Docker image
3. Image pushed to Harbor (version tag + `:latest`)
4. Harbor Deployer polls every 60 seconds
5. Detects new digest, pulls, and restarts via docker compose
6. Mattermost notification sent

## Files

| File | Purpose |
|------|---------|
| `scripts/harbor-deployer.py` | Main Python service (~350 lines) |
| `scripts/harbor-deployer.json` | Configuration file |
| `scripts/harbor-deployer.service` | systemd unit template |
| `scripts/install-harbor-deployer.sh` | Installation script |
| `/etc/systemd/system/harbor-deployer.service` | Installed systemd unit |
| `/home/unarmedpuppy/server/logs/harbor-deployer.log` | Application log |

## Configuration

`scripts/harbor-deployer.json`:

```json
{
  "poll_interval": 60,
  "harbor_url": "https://harbor.server.unarmedpuppy.com",
  "mattermost_webhook": "https://mattermost.server.unarmedpuppy.com/hooks/xxx",
  "label": "com.centurylinklabs.watchtower.enable",
  "log_file": "/home/unarmedpuppy/server/logs/harbor-deployer.log",
  "compose_base_path": "/home/unarmedpuppy/server/apps",
  "container_to_app": {
    "llm-router": "homelab-ai",
    "llm-manager": "homelab-ai",
    "homelab-ai-dashboard": "homelab-ai",
    "claude-harness": "homelab-ai",
    "agent-core": "agent-gateway",
    "agent-gateway": "agent-gateway",
    "polymarket-bot": "polyjuiced"
  }
}
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `poll_interval` | Seconds between checks | 60 |
| `harbor_url` | Harbor registry URL | - |
| `mattermost_webhook` | Webhook URL for notifications | - |
| `label` | Container label to watch | `com.centurylinklabs.watchtower.enable` |
| `log_file` | Log file path | - |
| `compose_base_path` | Base path for app directories | - |
| `container_to_app` | Maps container names to app directories | {} |

### Container to App Mapping

Most containers derive their compose path from their name:
- Container `pokedex` → `/home/unarmedpuppy/server/apps/pokedex/docker-compose.yml`

For containers with different names than their app directory, use `container_to_app`:
- Container `llm-router` → maps to `homelab-ai` → `/home/unarmedpuppy/server/apps/homelab-ai/docker-compose.yml`

## Management Commands

```bash
# Check service status
sudo systemctl status harbor-deployer

# View systemd logs
journalctl -u harbor-deployer -f

# View application logs
tail -f ~/server/logs/harbor-deployer.log

# Restart service
sudo systemctl restart harbor-deployer

# Stop service
sudo systemctl stop harbor-deployer

# Enable on boot
sudo systemctl enable harbor-deployer
```

## CLI Options

```bash
# Run as daemon (default)
python3 harbor-deployer.py

# Check once without deploying
python3 harbor-deployer.py --dry-run --once

# Enable debug logging
python3 harbor-deployer.py --debug

# Check specific container
python3 harbor-deployer.py --container pokedex

# Use different config file
python3 harbor-deployer.py --config /path/to/config.json
```

## Testing

### Dry Run Test

```bash
python3 ~/server/scripts/harbor-deployer.py --dry-run --once --debug
```

Expected output:
```
2026-01-10 15:43:55 INFO  Starting Harbor Deployer (poll_interval=60s)
2026-01-10 15:43:55 INFO  Running in DRY-RUN mode - no changes will be made
2026-01-10 15:43:55 INFO  Checking 9 containers...
2026-01-10 15:43:55 DEBUG Checking pokedex (harbor.server.unarmedpuppy.com/library/pokedex:latest)
2026-01-10 15:43:55 DEBUG   Local:  sha256:abc123...
2026-01-10 15:43:55 DEBUG   Remote: sha256:abc123...
2026-01-10 15:43:55 DEBUG   No update needed for pokedex
...
2026-01-10 15:43:55 INFO  Session done: checked=9, updated=0, failed=0
```

### Force Update Test

To test a real deployment:

```bash
# Push a new tag to any watched app
cd ~/repos/personal/homelab/pokedex
# Make a small change (bump version in Dockerfile)
git add . && git commit -m "test: verify harbor-deployer"
git tag v1.0.8 && git push origin main v1.0.8

# Wait for Gitea Actions to build (~2 min)
# Harbor Deployer will pick up the new image within 60 seconds
# Check Mattermost for notification
```

## Watched Containers

Containers with this label are watched:

```yaml
labels:
  - "com.centurylinklabs.watchtower.enable=true"
```

Current watched containers (9):
- agent-core
- agent-gateway
- llm-router
- homelab-ai-dashboard
- llm-manager
- claude-harness
- pokedex
- polymarket-bot
- trading-bot

List watched containers:
```bash
docker ps --filter "label=com.centurylinklabs.watchtower.enable=true" --format "table {{.Names}}\t{{.Image}}"
```

## Mattermost Notifications

On successful update:
```
**Harbor Deployer** updated `pokedex`
┌──────────────────────────────────────┐
│ Container: pokedex                   │
│ Image: library/pokedex:latest        │
│ New Digest: sha256:abc123...         │
└──────────────────────────────────────┘
```

On failure:
```
**Harbor Deployer** failed to update `pokedex`
┌──────────────────────────────────────┐
│ Error: Docker compose failed: ...    │
└──────────────────────────────────────┘
```

## Troubleshooting

### Service Not Starting

```bash
# Check systemd status
sudo systemctl status harbor-deployer

# Check for Python errors
journalctl -u harbor-deployer --since "5 minutes ago"

# Verify dependencies
python3 -c "import docker; import requests; print('OK')"
```

### Container Not Updating

```bash
# Check if container has the label
docker inspect <container> | grep watchtower

# Check Harbor API manually
curl -I https://harbor.server.unarmedpuppy.com/v2/library/pokedex/manifests/latest \
  -H "Accept: application/vnd.docker.distribution.manifest.v2+json"

# Run dry-run on specific container
python3 ~/server/scripts/harbor-deployer.py --dry-run --once --container pokedex --debug
```

### Compose Path Wrong

If Harbor Deployer can't find the compose file:

1. Check if container name is in `container_to_app` mapping
2. Verify the compose file exists at the expected path
3. Add mapping to `harbor-deployer.json` if needed

## Dependencies

System packages (via apt):
- `python3-docker` - Docker SDK for Python

## Installation

```bash
cd ~/server/scripts
chmod +x install-harbor-deployer.sh
./install-harbor-deployer.sh
```

The script:
1. Checks prerequisites (Python 3, docker package, docker socket)
2. Creates logs directory
3. Copies systemd service file
4. Enables and starts the service

To uninstall:
```bash
./install-harbor-deployer.sh uninstall
```

## Security

The systemd service runs with security hardening:

```ini
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/home/unarmedpuppy/server/logs
```

The service:
- Runs as `unarmedpuppy` user (not root)
- Has read-only access to most of the system
- Can only write to the logs directory
- Requires Docker socket access for container operations

## Migration from Watchtower

1. Install Harbor Deployer: `./install-harbor-deployer.sh`
2. Verify it's working: `sudo systemctl status harbor-deployer`
3. Stop Watchtower: `docker compose -f apps/watchtower/docker-compose.yml down`
4. Remove Watchtower container and image

No changes needed to existing container labels - Harbor Deployer uses the same `com.centurylinklabs.watchtower.enable` label.
