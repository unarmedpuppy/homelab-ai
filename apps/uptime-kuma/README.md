# Uptime Kuma

Self-hosted monitoring tool with Discord notifications.

## Setup

1. Start the container:
   ```bash
   docker compose up -d
   ```

2. Access web UI at `https://uptime.server.unarmedpuppy.com` (or `http://192.168.86.47:3004`)

3. Create admin account on first login

## Discord Notifications

1. In Discord, go to Server Settings → Integrations → Webhooks
2. Create a webhook, copy the URL
3. In Uptime Kuma: Settings → Notifications → Add → Discord
4. Paste webhook URL

## Recommended Monitors

| Service | Type | URL/Host |
|---------|------|----------|
| Valheim | Game Server (UDP) | `192.168.86.47:2457` |
| Plex | HTTP | `https://plex.server.unarmedpuppy.com` |
| Traefik | HTTP | `http://traefik:8080/health` |
| Homepage | HTTP | `http://homepage:3000` |

## Features

- Push notifications (Discord, Telegram, Slack, etc.)
- Status pages
- Ping, HTTP, DNS, Docker, Game Server monitoring
- Maintenance windows
- Multiple notification channels per monitor

## Data

Stored in `./data/` - SQLite database and configurations.
