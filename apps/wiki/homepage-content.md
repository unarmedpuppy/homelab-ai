# Home Server Overview

Welcome to the home server documentation! This server hosts a comprehensive suite of services for media management, automation, productivity, gaming, and more.

## 🖥️ Server Information

- **Host**: 192.168.86.47
- **SSH Port**: 4242
- **User**: unarmedpuppy
- **Domain**: server.unarmedpuppy.com
- **OS**: Debian 12 (Bookworm)

### Quick Access

- **Homepage Dashboard**: [http://192.168.86.47:3000](http://192.168.86.47:3000) or [https://server.unarmedpuppy.com](https://server.unarmedpuppy.com)
- **SSH Access**: `ssh -p 4242 unarmedpuppy@192.168.86.47`

---

## 📊 Infrastructure & Core Services

### Reverse Proxy & Networking
- **Traefik** - Reverse proxy with automatic HTTPS via Let's Encrypt
- **Cloudflare DDNS** - Dynamic DNS updater
- **AdGuard Home** - Local DNS server and ad blocker (Port 53, 8083)
- **Tailscale** - VPN mesh network service

### Monitoring & Management
- **Grafana Stack** - Complete monitoring infrastructure
  - Grafana Dashboard (Port 3010)
  - InfluxDB (Port 8086) - Time-series database
  - Loki (Port 3100) - Log aggregation
  - Telegraf - Metrics collection
- **Homepage** - Service dashboard (Port 3000)
- **Server Management MCP Server** - Standardized tools for server operations

---

## 🎬 Media & Entertainment

### Media Servers
- **Plex** - Primary media server (Port 32400)
  - Access: [plex.server.unarmedpuppy.com](https://plex.server.unarmedpuppy.com)
- **Jellyfin** - Alternative open-source media server
- **Immich** - Self-hosted photo and video backup (Port 2283)
  - Access: [photos.server.unarmedpuppy.com](https://photos.server.unarmedpuppy.com)

### Media Download & Automation
Complete automation stack with VPN protection:

**Download Clients** (Behind VPN):
- **qBittorrent** - Torrent client (Port 8880 via VPN)
- **NZBGet** - Usenet client (Port 6789 via VPN)
- **slskd** - Soulseek daemon (Port 5030 via VPN)

**Automation Services**:
- **Sonarr** - TV show automation (Port 8989)
- **Radarr** - Movie automation (Port 7878)
- **Lidarr** - Music automation (Port 8686)
- **Readarr** - Book automation (Port 8787)
- **Bazarr** - Subtitle downloader (Port 6767)
- **Overseerr** - Media request management (Port 5055)

**Indexers**:
- **NZBHydra2** - Usenet indexer aggregator (Port 5076)
- **Jackett** - Torrent indexer proxy (Port 9117)
- **Prowlarr** - Unified indexer manager (Port 9696)

**Additional Tools**:
- **MeTube** - YouTube video downloader (Port 8020)
- **SpotifyDL** - Spotify content downloader (Port 8800)
- **ytdl-sub** - Automated YouTube/media downloads with metadata
- **SoulSync** - Automated music discovery and collection manager (Port 8008)
- **Tunarr** - Live TV streaming from Plex media

**Book Management**:
- **Calibre** - E-book library management (Port 8085)
- **Calibre-Web** - Web interface for Calibre (Port 8084)
- **LazyLibrarian** - Book automation (Port 8787)

---

## 📝 Productivity & Organization

- **Wiki.js** - This wiki! Modern documentation platform (Port 3001)
  - Access: [wiki.server.unarmedpuppy.com](https://wiki.server.unarmedpuppy.com)
- **Paperless-ngx** - Document management with OCR (Port 8200)
  - Access: [paperless.server.unarmedpuppy.com](https://paperless.server.unarmedpuppy.com)
- **Mealie** - Recipe management and meal planning (Port 9925)
  - Access: [recipes.server.unarmedpuppy.com](https://recipes.server.unarmedpuppy.com)
- **Planka** - Project management with Kanban boards (Port 3006)
- **Monica** - CRM and contact management (Port 8098)
- **n8n** - Workflow automation platform (Port 5678)
  - Access: [n8n.server.unarmedpuppy.com](https://n8n.server.unarmedpuppy.com)
- **Home Assistant** - Smart home automation (Port 8123)
  - Access: [homeassistant.server.unarmedpuppy.com](https://homeassistant.server.unarmedpuppy.com)

---

## 🎮 Gaming

- **Rust Server** - Rust game server
  - Game Port: 28015 (TCP/UDP)
  - RCON: 28016 (TCP/UDP)
  - Web RCON: 8080
  - Access: [rust.server.unarmedpuppy.com](https://rust.server.unarmedpuppy.com)
- **Minecraft Bedrock Server** - Minecraft server (Port 19132 UDP)
  - Access: [minecraft.server.unarmedpuppy.com](https://minecraft.server.unarmedpuppy.com)
- **Bedrock Viz** - Minecraft map visualization (Port 8081)
  - Access: [gumberlund.server.unarmedpuppy.com](https://gumberlund.server.unarmedpuppy.com)
- **Maptap Data** - Maptap.gg score visualization (Port 8199)
  - Access: [maptapdat.server.unarmedpuppy.com](https://maptapdat.server.unarmedpuppy.com)

---

## 💰 Finance & Trading

- **Trading Bot** - Automated trading with Interactive Brokers (Port 8000)
- **Trading Journal** - Trading journal application (Port 8102)
- **Tradenote** - Trading notes and journal (Port 8099)
- **Maybe** - Personal finance management (Port 3054)

---

## 🤖 AI & Machine Learning

- **Ollama** - Local LLM runtime and API (Port 11434)
- **Local AI App** - ChatGPT-like interface for local models (Port 8067)
  - Access: [local-ai.server.unarmedpuppy.com](https://local-ai.server.unarmedpuppy.com)
- **Text Generation WebUI** - Web interface for text generation (Port 7860)

---

## 🔐 Security & Utilities

- **Vaultwarden** - Self-hosted password manager (Port 11001)
  - Access: [vaultwarden.server.unarmedpuppy.com](https://vaultwarden.server.unarmedpuppy.com)
- **AdGuard Home** - DNS-based ad blocking and privacy protection

---

## 📡 Communication & Social

- **Campfire** - Communication platform (Port 8096)
- **FreshRSS** - RSS feed aggregator (Port 8005)
- **Libreddit** - Private Reddit front-end (Port 8088)

---

## 💾 Storage & Backup

### Storage Configuration
- **Internal SSD**: 1TB
- **server-storage**: 4TB (ephemeral, for syncing)
- **server-cloud**: 8TB (Seafile sync server, backups)
- **Jenquist Cloud**: ZFS RAID (raidz1) - Primary archive storage
  - Location: `/jenquist-cloud/archive/entertainment-media`

### Backup Strategy
- Automated backups via rsnapshot
- Docker volume backups
- ZFS snapshot capabilities

---

## 🛠️ System Information

### Hardware
- **CPU**: Intel Core i7-6700K (4 cores, 8 threads)
- **RAM**: 32GB DDR4
- **Chassis**: Sliger CX3701 (3U rackmount)
- **Motherboard**: B550I AORUS Pro AX
- **Power Supply**: Corsair SF750 (750W 80+ Platinum)

### Network
- **Local IP**: 192.168.86.47
- **Router**: Google Home Mesh
- **DNS**: AdGuard Home (192.168.86.47:53)

---

## 📚 Documentation

- **Main README**: [README.md](https://github.com/unarmedpuppy/home-server/blob/main/README.md)
- **Apps Documentation**: [APPS_DOCUMENTATION.md](https://github.com/unarmedpuppy/home-server/blob/main/apps/docs/APPS_DOCUMENTATION.md)
- **Server Context**: [server.md](https://github.com/unarmedpuppy/home-server/blob/main/agents/prompts/server.md)

---

## 🔗 Quick Links

### Service Dashboards
- [Homepage](http://192.168.86.47:3000) - Main service dashboard
- [Grafana](http://192.168.86.47:3010) - System monitoring
- [Traefik Dashboard](http://192.168.86.47:8080) - Reverse proxy status

### Media Services
- [Plex](https://plex.server.unarmedpuppy.com)
- [Immich](https://photos.server.unarmedpuppy.com)
- [Overseerr](http://192.168.86.47:5055) - Media requests

### Productivity
- [Wiki.js](http://192.168.86.47:3001) - This wiki
- [Paperless](https://paperless.server.unarmedpuppy.com)
- [n8n](https://n8n.server.unarmedpuppy.com)

---

## 📝 Notes

- All services are containerized using Docker Compose
- Most services are accessible via HTTPS through Traefik
- Media download services route through VPN (Gluetun with ProtonVPN)
- Services are organized into logical groups in Homepage dashboard
- Regular backups are automated via cron jobs

---

**Last Updated**: December 2024  
**Server**: 192.168.86.47 (unarmedpuppy@home-server)

