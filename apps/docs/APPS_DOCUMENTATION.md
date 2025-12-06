# Home Server Applications Documentation

This document provides an overview of all applications deployed on the home server, including their exposed ports and active status.

**Server Details:**
- Host: 192.168.86.47
- SSH Port: 4242
- User: unarmedpuppy
- Access: `bash scripts/connect-server.sh '<command>'`

**⚠️ IMPORTANT**: Before using SSH commands, **check the MCP Server tools first** (`agents/apps/agent-mcp/`). MCP tools provide standardized, type-safe operations for server management. See `agents/docs/SERVER_AGENT_PROMPT.md` for tool discovery workflow.

---

## Infrastructure & Services

### Server Management MCP Server
- **Description**: Model Context Protocol (MCP) server providing standardized tools for managing the entire home server infrastructure
- **Location**: `agents/apps/agent-mcp/` (in repository root)
- **Container**: `agents/apps/agent-mcp`
- **Status**: ✅ **ACTIVE**
- **Documentation**: 
  - `agents/apps/agent-mcp/README.md` - Tool reference and usage
  - `agents/apps/agent-mcp/DOCKER_SETUP.md` - Docker setup guide
  - `apps/docs/MCP_SERVER_PLAN.md` - Complete architecture and tool catalog
- **Notes**: 
  - Provides type-safe, standardized tools for server operations
  - **Agents should use MCP tools first** before writing custom scripts or SSH commands
  - Tools available: Docker management, media download operations, system monitoring, troubleshooting
  - Accessible via MCP protocol (Claude Desktop, GPT-4 with MCP) or via SSH tunnel
  - See `agents/docs/SERVER_AGENT_PROMPT.md` for tool discovery workflow

### Traefik
- **Description**: Reverse proxy with automatic HTTPS via Let's Encrypt
- **Ports**: 
  - `80` (HTTP)
  - `443` (HTTPS)
- **Status**: ✅ **ACTIVE**
- **Notes**: Routes traffic to other services via domain names. Domain: `server.unarmedpuppy.com`

### Cloudflare DDNS
- **Description**: Dynamic DNS updater for Cloudflare domains
- **Ports**: None (uses host network mode)
- **Status**: ✅ **ACTIVE**
- **Notes**: Updates DNS records automatically when server IP changes

### Tailscale
- **Description**: VPN mesh network service
- **Ports**: None (uses host network via /dev/net/tun)
- **Status**: ✅ **ACTIVE**
- **Notes**: Provides secure remote access via Tailscale network

### AdGuard Home
- **Description**: Local DNS server and ad blocker
- **Ports**: 
  - `53` (TCP/UDP) - DNS
  - `8083` - Web interface (after initial setup)
  - `3003` - Setup interface (initial setup only)
- **Status**: ✅ **ACTIVE**
- **Notes**: Acts as local DNS resolver for the network

### Grafana Stack
- **Description**: Monitoring, metrics, and logging infrastructure
- **Components**:
  - **Grafana**: `3010` - Dashboard UI
  - **InfluxDB**: `8086` - Time-series database
  - **Loki**: `3100` (localhost only) - Log aggregation
  - **Promtail**: No exposed ports - Log shipper
  - **Telegraf**: `9126` - Metrics collection
- **Status**: ✅ **ACTIVE**
- **Notes**: All components running. Grafana accessible at port 3010

---

## Media & Entertainment

### Plex Media Server
- **Description**: Media server for movies, TV shows, and music
- **Ports**: 
  - `32400` - Main web interface
  - `3005`, `8324`, `32469` - Additional services
  - `1900` (UDP) - DLNA discovery
  - `32410`, `32412-32414` (UDP) - Additional UDP ports
- **Status**: ✅ **ACTIVE**
- **Notes**: Accessible via `plex.server.unarmedpuppy.com` (HTTPS)

### Jellyfin
- **Description**: Alternative open-source media server
- **Ports**: `8096` (configured but not exposed in docker-compose, likely not running main instance)
- **Status**: ⚠️ **PARTIAL** (unlock service only)
- **Notes**: Main Jellyfin container not running, but `jellyfin-unlock` service is active

### Jellyfin Unlock
- **Description**: ZFS filesystem unlock service for Jellyfin
- **Ports**: `8889` - Web interface
- **Status**: ✅ **ACTIVE**
- **Notes**: Manages ZFS dataset unlocking for media access

### Immich
- **Description**: Self-hosted photo and video backup solution
- **Services**:
  - **immich-server**: `2283` - Main API/server
  - **immich-database**: PostgreSQL (internal)
  - **immich-redis**: Redis (internal)
  - **immich-ml**: Machine learning service (internal)
- **Status**: ✅ **ACTIVE**
- **Notes**: Accessible via `photos.server.unarmedpuppy.com` (HTTPS)

---

## Media Download & Automation

### Media Download Stack
Complete automation stack for media acquisition. All services on `media-download-network`.

#### Gluetun (VPN Gateway)
- **Description**: VPN gateway with kill switch for download clients
- **Ports**: 
  - `8880` - qBittorrent web UI (routed through VPN)
  - `6789` - NZBGet web UI (routed through VPN)
- **Status**: ✅ **ACTIVE**
- **Notes**: Uses ProtonVPN via OpenVPN. All download traffic routes through VPN.

#### Sonarr
- **Description**: TV show automation and management
- **Ports**: `8989` - Web interface
- **Status**: ✅ **ACTIVE**

#### Radarr
- **Description**: Movie automation and management
- **Ports**: `7878` - Web interface
- **Status**: ✅ **ACTIVE**

#### Lidarr
- **Description**: Music automation and management
- **Ports**: `8686` - Web interface
- **Status**: ✅ **ACTIVE**

#### Readarr
- **Description**: Book automation and management
- **Ports**: `8787` - Web interface
- **Status**: ✅ **ACTIVE**

#### Bazarr
- **Description**: Subtitle downloader and manager
- **Ports**: `6767` - Web interface
- **Status**: ✅ **ACTIVE**

#### Overseerr
- **Description**: Media request management (for users to request content)
- **Ports**: `5055` - Web interface
- **Status**: ✅ **ACTIVE**

#### NZBHydra2
- **Description**: Usenet indexer aggregator
- **Ports**: `5076` - Web interface
- **Status**: ✅ **ACTIVE**
- **Notes**: NOT on VPN (only searches, doesn't download)

#### Jackett
- **Description**: Torrent indexer proxy
- **Ports**: `9117` - Web interface
- **Status**: ✅ **ACTIVE**
- **Notes**: NOT on VPN (only searches, doesn't download)

#### qBittorrent
- **Description**: Torrent download client
- **Ports**: `8880` (via Gluetun) - Web interface
- **Status**: ✅ **ACTIVE**
- **Notes**: Behind VPN (kill switch active). Access via Gluetun port mapping.

#### NZBGet
- **Description**: Usenet download client
- **Ports**: `6789` (via Gluetun) - Web interface
- **Status**: ✅ **ACTIVE**
- **Notes**: Behind VPN (kill switch active). Access via Gluetun port mapping.

#### Calibre
- **Description**: E-book library management
- **Ports**: `8085` - Web interface
- **Status**: ✅ **ACTIVE**

#### Calibre-Web
- **Description**: Web interface for Calibre library
- **Ports**: `8084` - Web interface
- **Status**: ✅ **ACTIVE**

#### SABnzbd
- **Description**: Alternative Usenet download client
- **Ports**: `8079` - Web interface
- **Status**: ❌ **INACTIVE** (configured but not running - alternative profile)

---

## Applications & Tools

### Homepage
- **Description**: Service dashboard and homepage
- **Ports**: `3000` - Web interface
- **Status**: ✅ **ACTIVE**
- **Notes**: Accessible via `server.unarmedpuppy.com` (HTTPS with auth)

### Home Assistant
- **Description**: Smart home automation and device management
- **Ports**: `8123` - Web interface
- **Status**: ✅ **ACTIVE**
- **Notes**: Accessible via `homeassistant.server.unarmedpuppy.com` (HTTPS)

### Paperless-ngx
- **Description**: Document management system with OCR
- **Services**:
  - **webserver**: `8200` - Main web interface
  - **db**: PostgreSQL (internal)
  - **broker**: Redis (internal)
- **Status**: ✅ **ACTIVE**
- **Notes**: Accessible via `paperless.server.unarmedpuppy.com` (HTTPS)

### Wiki.js
- **Description**: Modern wiki application for documentation and knowledge bases
- **Services**:
  - **wiki**: `3001` - Main web interface
  - **db**: PostgreSQL (internal)
- **Status**: ✅ **ACTIVE**
- **Notes**: 
  - Accessible via `wiki.server.unarmedpuppy.com` (HTTPS)
  - Built on Node.js with Markdown support
  - Supports Git storage backend for version control

### n8n
- **Description**: Workflow automation platform
- **Ports**: `5678` - Web interface
- **Status**: ✅ **ACTIVE**
- **Notes**: Accessible via `n8n.server.unarmedpuppy.com` (HTTPS)

### Mealie
- **Description**: Recipe management, meal planning, and shopping lists
- **Ports**: `9925` - Web interface
- **Status**: ✅ **ACTIVE**
- **Notes**: Accessible via `recipes.server.unarmedpuppy.com` (HTTPS) and `recipes.local.unarmedpuppy.com` (HTTP)

### Planka
- **Description**: Project management with Kanban boards
- **Services**:
  - **planka**: `3006` - Web interface
  - **postgres**: PostgreSQL (internal)
- **Status**: ✅ **ACTIVE**

### LubeLogger
- **Description**: Vehicle maintenance and fuel mileage tracker
- **Ports**: `8010` - Web interface
- **Status**: ✅ **ACTIVE**
- **Notes**: Accessible via `lubelog.server.unarmedpuppy.com` (HTTPS)

### Excalidraw
- **Description**: Virtual whiteboard for sketching hand-drawn like diagrams
- **Ports**: `5000` - Web interface
- **Status**: ✅ **ACTIVE**
- **Notes**: Accessible via `excalidraw.server.unarmedpuppy.com` (HTTPS)

### Vaultwarden
- **Description**: Self-hosted password manager (Bitwarden compatible)
- **Ports**: `11001` - Web interface
- **Status**: ✅ **ACTIVE**
- **Notes**: Accessible via `vaultwarden.server.unarmedpuppy.com` (HTTPS)

### Grist
- **Description**: Spreadsheet application (like Google Sheets)
- **Ports**: `8484` - Web interface
- **Status**: ✅ **ACTIVE**

### FreshRSS
- **Description**: RSS feed aggregator
- **Services**:
  - **freshrss**: `8005` - Web interface
  - **db**: PostgreSQL (internal)
- **Status**: ✅ **ACTIVE**

### Maybe
- **Description**: Personal finance management
- **Services**:
  - **web**: `3054` - Web interface
  - **worker**: Background worker (internal)
  - **db**: PostgreSQL (internal)
  - **redis**: `6379` - Redis cache
- **Status**: ✅ **ACTIVE**
- **Notes**: Redis is exposed on host port 6379

### Libreddit
- **Description**: Private front-end for Reddit
- **Ports**: `8088` - Web interface
- **Status**: ✅ **ACTIVE**

### MeTube
- **Description**: YouTube video downloader
- **Ports**: `8020` - Web interface
- **Status**: ✅ **ACTIVE**

### ytdl-sub
- **Description**: Automated YouTube/media downloads with metadata generation for media servers
- **Ports**: None (headless CLI tool)
- **Status**: ✅ **ACTIVE**
- **Notes**: 
  - Downloads YouTube channels, playlists, SoundCloud discographies, and more
  - Formats media for Plex, Jellyfin, Kodi, Emby with proper metadata
  - Access via SSH: `docker exec -it ytdl-sub ytdl-sub <command>`
  - Configured via YAML subscription files in `subscriptions/` directory

### SpotifyDL
- **Description**: Spotify content downloader
- **Ports**: `8800` - Web interface
- **Status**: ✅ **ACTIVE**

### SoulSync
- **Description**: Automated music discovery and collection manager
- **Ports**: `8008` - Web interface
- **Status**: ⚠️ **CONFIGURED** (requires slskd setup)
- **Notes**: 
  - Integrates with Spotify, Tidal, Soulseek (via slskd), and media servers (Plex/Jellyfin/Navidrome)
  - Requires slskd (Soulseek daemon) running on port 5030
  - Accessible via `soulsync.server.unarmedpuppy.com` (HTTPS)
  - Automatically organizes downloaded music and syncs with media servers

---

## Gaming

### Rust Server
- **Description**: Rust game server
- **Ports**: 
  - `8080` - Web RCON interface
  - `28015` (TCP/UDP) - Game server
  - `28016` (TCP/UDP) - RCON port
  - `28017` (UDP) - Query port
  - `28082` - Rust+ app port
- **Status**: ✅ **ACTIVE**
- **Notes**: Accessible via `rust.server.unarmedpuppy.com` and `rcon-rust.server.unarmedpuppy.com`

### Minecraft Bedrock Server
- **Description**: Minecraft Bedrock Edition server
- **Ports**: `19132` (UDP) - Game server
- **Status**: ✅ **ACTIVE**
- **Notes**: UDP traffic only. Accessible via `minecraft.server.unarmedpuppy.com`

### Bedrock Viz
- **Description**: Minecraft server map visualization
- **Ports**: `8081` - Web interface
- **Status**: ✅ **ACTIVE**
- **Notes**: Accessible via `gumberlund.server.unarmedpuppy.com` (HTTPS)

### Maptap Data
- **Description**: Maptap.gg score visualization dashboard
- **Ports**: `8199` - Web interface
- **Status**: ✅ **ACTIVE**
- **Notes**: Accessible via `maptapdat.server.unarmedpuppy.com` (HTTPS)

---

## AI & Machine Learning

### Ollama
- **Description**: Local LLM runtime and API
- **Ports**: `11434` - API
- **Status**: ✅ **ACTIVE**
- **Notes**: Running Ollama service for local AI models. Exposed on host port 11434.

### Local AI App
- **Description**: ChatGPT-like interface for local LLM models
- **Ports**: `8067` - Web interface
- **Status**: ✅ **ACTIVE**
- **Notes**: Accessible via `local-ai.server.unarmedpuppy.com` (HTTPS with auth) and `local-ai.local.unarmedpuppy.com` (HTTP)

### Text Generation WebUI
- **Description**: Web interface for text generation models
- **Ports**: 
  - `7860` - Web interface
  - `5000`, `5005` - Internal services
- **Status**: ✅ **ACTIVE**
- **Notes**: Not found in apps directory - may be manually configured or from external docker-compose

### Deepseek Model
- **Description**: DeepSeek AI model container
- **Ports**: None exposed
- **Status**: ✅ **ACTIVE**
- **Notes**: Not found in apps directory - may be manually configured or part of another service

---

## Trading & Finance

### Trading Bot
- **Description**: Automated trading bot with Interactive Brokers integration
- **Services**:
  - **trading-bot** (main): `8000` - API interface
  - Note: Alternative docker-compose.yml in `docker/` directory with full stack (API, worker, DB, Redis) exists but not currently active
- **Status**: ✅ **ACTIVE** (single container mode)
- **Notes**: Connects to IBKR TWS/Gateway running on host. Alternative multi-container setup available but not deployed.

### Trading Agents
- **Description**: Trading agents framework (LangGraph-based)
- **Ports**: None (CLI/batch profile only)
- **Status**: ❌ **INACTIVE** (configured but uses profiles - not started by default)

### Tradenote
- **Description**: Trading journal application
- **Services**:
  - **tradenote**: `8099` - Web interface
  - **mongo**: MongoDB (internal)
- **Status**: ❌ **INACTIVE** (not in docker ps output)

---

## Other Services

### AI Service (apps/ai/)
- **Description**: AI service with Ollama integration
- **Ports**: 
  - `8000` - Main API
  - `5678` - Additional service
  - `7869` - Ollama
  - `8080` - Ollama WebUI
- **Status**: ❌ **INACTIVE** (different from ollama-docker, not running)

### Stable Diffusion
- **Description**: AI image generation service
- **Ports**: `8006` - Web interface
- **Status**: ❌ **INACTIVE** (not in docker ps output)

### TCGPlayer Scraper
- **Description**: Web scraper service for TCGPlayer.com (container name: `tcgplayer-scraper-web-1`)
- **Ports**: None exposed externally
- **Status**: ✅ **ACTIVE**
- **Notes**: Not found in apps directory - may be manually configured or from external docker-compose file

---

## Summary Statistics

- **Total Apps Documented**: 50+
- **Active Services**: ~45
- **Inactive Services**: ~5
- **Total Exposed Ports**: 60+ unique ports

### Port Usage Summary (Common Ports)
- `80`, `443` - Traefik (reverse proxy)
- `3000` - Homepage
- `8000` - Trading Bot, Local AI App
- `8080-8099` - Various web services
- `53` - AdGuard DNS
- `19132` - Minecraft (UDP)
- `28015-28017` - Rust Server
- `32400` - Plex

---

## Notes

1. **Network Isolation**: Media download services use `media-download-network` and VPN routing via Gluetun for security.

2. **Traefik Routing**: Most services are accessible via HTTPS through Traefik at `*.server.unarmedpuppy.com` domains.

3. **Local Access**: Some services are accessible via direct IP: `http://192.168.86.47:<port>`

4. **VPN Services**: Download clients (qBittorrent, NZBGet) route through Gluetun VPN with kill switch enabled.

5. **Service Dependencies**: 
   - Immich requires database and Redis
   - Paperless requires PostgreSQL and Redis
   - Planka requires PostgreSQL
   - Media automation services depend on indexers (NZBHydra2, Jackett)

6. **Inactive Services**: Some services are configured but not currently running (SABnzbd, Stable Diffusion, Trading Agents, Tradenote).

---

**Last Updated**: Generated from docker-compose.yml files and `docker ps` output
**Server**: 192.168.86.47 (unarmedpuppy@home-server)

