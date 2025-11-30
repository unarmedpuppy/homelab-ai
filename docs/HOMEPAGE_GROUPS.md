# Homepage Groups Organization

All apps have been organized into logical categories for better navigation in the Homepage dashboard.

## Categories

### 📁 Infrastructure & Services (6 apps)
Core system services and infrastructure:
- **adguard-home** - Local DNS & Ad blocking
- **cloudflare-ddns** - Dynamic DNS service
- **grafana** - Home Server telemetry & metrics
- **homepage** - Service dashboard
- **tailscale** - VPN service
- **traefik** - Reverse proxy

### 📁 Media & Entertainment (6 apps)
Media servers and entertainment:
- **immich** - Family photos & videos
- **jellyfin** - Media server
- **metube** - Download & Save Youtube videos
- **plex** - Media server
- **spotifydl** - Spotify downloader
- **tunarr** - Live TV streaming from Plex media

### 📁 Media Management (2 apps)
Tools for organizing and managing media:
- **media-download** - Media download automation (Sonarr, Radarr, etc.)
- **paperless-ngx** - Document management system

### 📁 Gaming (4 apps)
Game servers and gaming-related tools:
- **bedrock-viz** - Minecraft Bedrock visualization
- **maptapdat** - Maptap.gg score visualization dashboard
- **minecraft** - Minecraft server
- **rust** - Rust game server

### 📁 Productivity & Organization (4 apps)
Task management, notes, and productivity tools:
- **grist** - Spreadsheet/database tool
- **mealie** - Recipes, meal planning & shopping list
- **monica** - CRM and contact management
- **open-archiver** - Archiving tool
- **planka** - Project management (Kanban)

### 📁 Finance & Trading (4 apps)
Trading and finance-related applications:
- **maybe** - Personal finance management
- **tradenote** - Trading notes and journal
- **trading-bot** - Trading bot API and dashboard
- **trading-journal** - Trading journal application

**Note:** tradingagents is CLI-based and doesn't have a web UI, so it's not included in homepage.

### 📁 AI & Machine Learning (3 apps)
AI and machine learning services:
- **local-ai-app** - Local AI application
- **ollama-docker** - Ollama AI model interface
- **open-health** - AI Health Assistant powered by your data

### 📁 Automation & Workflows (2 apps)
Automation and workflow tools:
- **homeassistant** - Smart home devices & automations
- **n8n** - Workflow automation

### 📁 Communication & Social (4 apps)
Communication and social tools:
- **campfire** - Communication platform
- **freshRSS** - RSS feed reader
- **ghost** - Blogging platform
- **libreddit** - Reddit frontend

### 📁 Security & Privacy (1 app)
Security and privacy tools:
- **vaultwarden** - Password manager (Bitwarden-compatible)

## Notes

- **tradingagents** is CLI-based and doesn't have a web UI, so it doesn't have homepage labels
- All other apps have been categorized and will appear in their respective groups in Homepage
- Groups are organized alphabetically within each category

## Updating Groups

To change a group, edit the `homepage.group` label in the app's `docker-compose.yml` file:

```yaml
labels:
  - "homepage.group=Your Category Name"
```

