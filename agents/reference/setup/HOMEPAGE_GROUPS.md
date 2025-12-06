# Homepage Groups Organization

All apps have been organized into logical categories for better navigation in the Homepage dashboard.

## Categories

### 📁 Infrastructure (9 apps)
Core system services, infrastructure, automation, and security:
- **adguard-home** - Local DNS & Ad blocking
- **cloudflare-ddns** - Dynamic DNS service
- **grafana** - Home Server telemetry & metrics
- **homeassistant** - Smart home devices & automations
- **homepage** - Service dashboard
- **n8n** - Workflow automation
- **tailscale** - VPN service
- **traefik** - Reverse proxy
- **vaultwarden** - Password manager (Bitwarden-compatible)

### 📁 Media & Entertainment (7 apps)
Media servers, entertainment, and media download tools:
- **immich** - Family photos & videos
- **jellyfin** - Media server
- **media-download** - Media download automation (Sonarr, Radarr, etc.)
- **metube** - Download & Save Youtube videos
- **plex** - Media server
- **spotifydl** - Spotify downloader
- **tunarr** - Live TV streaming from Plex media

### 📁 Productivity & Organization (5 apps)
Task management, notes, document management, and productivity tools:
- **mealie** - Recipes, meal planning & shopping list
- **monica** - CRM and contact management
- **open-archiver** - Archiving tool
- **paperless-ngx** - Document management system
- **planka** - Project management (Kanban)

### 📁 Gaming (4 apps)
Game servers and gaming-related tools:
- **bedrock-viz** - Minecraft Bedrock visualization
- **maptapdat** - Maptap.gg score visualization dashboard
- **minecraft** - Minecraft server
- **rust** - Rust game server

### 📁 Finance & Trading (4 apps)
Trading and finance-related applications:
- **maybe** - Personal finance management
- **tradenote** - Trading notes and journal
- **trading-bot** - Trading bot API and dashboard
- **trading-journal** - Trading journal application

### 📁 Communication & Social (4 apps)
Communication and social tools:
- **campfire** - Communication platform
- **freshRSS** - RSS feed reader
- **ghost** - Blogging platform
- **libreddit** - Reddit frontend

### 📁 AI & Machine Learning (3 apps)
AI and machine learning services:
- **local-ai-app** - Local AI application
- **ollama-docker** - Ollama AI model interface
- **open-health** - AI Health Assistant powered by your data

## Notes

- **tradingagents** is CLI-based and doesn't have a web UI, so it doesn't have homepage labels
- All other apps have been categorized and will appear in their respective groups in Homepage
- Groups are organized alphabetically within each category
- Categories have been consolidated to avoid having groups with only 1-2 apps

## Updating Groups

To change a group, edit the `homepage.group` label in the app's `docker-compose.yml` file:

```yaml
labels:
  - "homepage.group=Your Category Name"
```
