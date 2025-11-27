# Server Context

Server-specific information for the home server.

## Server Details

- **Server Path**: `~/server` (home dir of `unarmedpuppy` user)
- **Local Repo**: `/Users/joshuajenquist/repos/personal/home-server`
- **Local IP**: `192.168.86.47`
- **SSH**: `ssh -p 4242 unarmedpuppy@192.168.86.47`
- **Network**: `my-network` (Docker external network)

## Connection

```bash
# SSH to server
ssh -p 4242 unarmedpuppy@192.168.86.47

# Or use helper script
bash scripts/connect-server.sh "command"
```

## Deployment Workflow

1. Make changes locally
2. Commit and push:
   ```bash
   git add . && git commit -m "message" && git push
   ```
3. Pull on server:
   ```bash
   ssh -p 4242 unarmedpuppy@192.168.86.47 "cd ~/server && git pull"
   ```
4. Restart services:
   ```bash
   ssh -p 4242 unarmedpuppy@192.168.86.47 "cd ~/server/apps/APP_NAME && docker compose restart"
   ```

**Never make direct changes on the server without explicit permission.**

## Project Structure

```
home-server/
├── apps/                    # Docker Compose applications
│   ├── trading-bot/         # Trading bot (port 8000)
│   ├── monica/              # Relationship management (port 8098)
│   ├── traefik/             # Reverse proxy
│   ├── homepage/            # Service dashboard
│   └── [other apps]/
├── scripts/
│   └── connect-server.sh    # SSH helper
└── agents/                  # This directory
```

See `apps/docs/APPS_DOCUMENTATION.md` for complete app list with ports.

## Docker Compose Patterns

### Required Network
```yaml
networks:
  my-network:
    external: true
```

### Homepage Labels
```yaml
labels:
  - "homepage.group=Category"
  - "homepage.name=Service Name"
  - "homepage.icon=icon.png"
  - "homepage.href=http://192.168.86.47:PORT"
```

### Traefik Labels (HTTPS)
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.SERVICE.rule=Host(`subdomain.server.unarmedpuppy.com`)"
  - "traefik.http.routers.SERVICE.entrypoints=websecure"
  - "traefik.http.routers.SERVICE.tls.certresolver=myresolver"
  - "traefik.http.services.SERVICE.loadbalancer.server.port=PORT"
```

**Note**: New subdomains need to be added to `apps/cloudflare-ddns/` config.

## Common Variables

```yaml
environment:
  - TZ=America/New_York
  - PUID=1000
  - PGID=1000
```

## Quick Commands

```bash
# Check all containers
ssh -p 4242 unarmedpuppy@192.168.86.47 "docker ps"

# View logs
ssh -p 4242 unarmedpuppy@192.168.86.47 "docker logs CONTAINER --tail 100"

# Restart service
ssh -p 4242 unarmedpuppy@192.168.86.47 "cd ~/server/apps/APP && docker compose restart"

# Check disk space
ssh -p 4242 unarmedpuppy@192.168.86.47 "df -h"
```
