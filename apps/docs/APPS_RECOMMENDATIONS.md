# Self-Hosted Apps Recommendations

Comparison of installed apps vs. popular self-hosted applications from [selfh.st/apps](https://selfh.st/apps/), with recommendations for new additions.

**Last Updated**: 2025-12-04

---

## Current App Inventory

### ✅ Installed & Active (50+ apps)

#### Infrastructure & Services
- Traefik (reverse proxy)
- Cloudflare DDNS
- Tailscale (VPN)
- AdGuard Home (DNS/ad blocking)
- Grafana Stack (monitoring)
- Homepage (dashboard)

#### Media & Entertainment
- Plex (media server)
- Jellyfin (media server - partial)
- Immich (photo/video backup)
- Complete media download stack (Sonarr, Radarr, Lidarr, Readarr, Bazarr, Overseerr, qBittorrent, NZBGet, etc.)

#### Productivity & Organization
- Home Assistant (smart home)
- Paperless-ngx (document management)
- Wiki.js (documentation)
- n8n (workflow automation)
- Mealie (recipe management)
- Planka (project management)
- Vaultwarden (password manager)
- Grist (spreadsheets)
- FreshRSS (RSS reader)
- Maybe (personal finance)
- Monica (relationship management)
- Beaver Habits (habit tracking) ⭐ **NEW**
- Ghost (blogging platform)

#### Gaming
- Rust Server
- Minecraft Bedrock Server
- Bedrock Viz
- Maptap Data

#### AI & Machine Learning
- Ollama (local LLMs)
- Local AI App (ChatGPT interface)
- Text Generation WebUI

#### Trading & Finance
- Trading Bot
- Trading Journal
- Trading Agents

#### Other
- Libreddit (Reddit frontend)
- MeTube (YouTube downloader)
- ytdl-sub (automated YouTube downloads)
- SpotifyDL
- SoulSync (music discovery)
- Tunarr (TV channel generation)

---

## Recommended Apps to Add

### 🎵 **Music Streaming** (High Priority)

#### Navidrome
- **Why**: You have Lidarr for music management but no music streaming server
- **Description**: Self-hosted music streaming server, Subsonic-compatible
- **Use Case**: Stream your music collection to any device
- **GitHub**: https://github.com/navidrome/navidrome
- **Integration**: Works with SoulSync, Lidarr, and Plex/Jellyfin

#### Alternative: Funkwhale
- **Why**: Federated music streaming (ActivityPub)
- **Description**: Social music streaming platform
- **Use Case**: Share music with friends/family, discover new music

---

### 📁 **File Storage & Sharing** (High Priority)

#### Nextcloud (Reactivate from inactive/)
- **Why**: You have it in inactive/ - comprehensive file sync, sharing, and collaboration
- **Description**: Self-hosted cloud storage with calendar, contacts, notes, and more
- **Use Case**: Replace Google Drive/Dropbox, sync files across devices
- **Status**: Already configured in `inactive/nextcloud/`

#### Alternative: Seafile (Reactivate from inactive/)
- **Why**: Faster, more efficient than Nextcloud for pure file sync
- **Description**: High-performance file sync and sharing
- **Status**: Already configured in `inactive/seafile/`

---

### 💻 **Code Hosting** (Medium Priority)

#### Gitea or Forgejo
- **Why**: Self-hosted Git hosting (alternative to GitHub/GitLab)
- **Description**: Lightweight Git server with web UI
- **Use Case**: Host private repositories, manage code projects
- **GitHub**: https://github.com/go-gitea/gitea or https://codeberg.org/forgejo/forgejo

---

### 📝 **Note-Taking & Knowledge Management** (Medium Priority)

#### Obsidian (Reactivate from inactive/)
- **Why**: You have obsidian-remote in inactive/ - powerful markdown-based note-taking
- **Description**: Knowledge base with graph view, plugins, and local-first approach
- **Status**: Already configured in `inactive/obsidian-remote/`

#### Colanode ⭐ (New from selfh.st)
- **Why**: Modern alternative to Notion with real-time collaboration
- **Description**: Open-source Notion alternative with chat capabilities
- **Use Case**: Team wikis, documentation, project planning
- **Features**: S3 storage support, pgvector for AI features

---

### 📊 **Analytics & Monitoring** (Medium Priority)

#### Rybbit ⭐ (New from selfh.st)
- **Why**: Privacy-focused web analytics (alternative to Google Analytics)
- **Description**: Cookie-less tracking, GDPR compliant
- **Use Case**: Track website/app usage without privacy concerns
- **GitHub**: https://github.com/rybbit/rybbit

#### Plausible Analytics
- **Why**: Simple, privacy-focused analytics
- **Description**: Lightweight alternative to Google Analytics
- **Use Case**: Track website visitors without cookies

---

### 🔐 **Authentication & Security** (Medium Priority)

#### Tinyauth ⭐ (New from selfh.st)
- **Why**: Simple authentication middleware (lighter than Authentik/Authelia)
- **Description**: Easy-to-configure auth for reverse proxies
- **Use Case**: Add authentication to services behind Traefik
- **Integration**: Works with Traefik, Nginx, Caddy

#### Authentik
- **Why**: Full-featured identity provider (SSO, OAuth, SAML)
- **Description**: Enterprise-grade authentication platform
- **Use Case**: Single sign-on for all your services

---

### 📦 **Asset & Warranty Tracking** (Low Priority)

#### Warracker ⭐ (New from selfh.st)
- **Why**: Track warranties, receipts, expiration dates
- **Description**: Warranty and asset management with Paperless-ngx integration
- **Use Case**: Never lose a warranty, track product expiration dates
- **Integration**: Works with Paperless-ngx (you already have this!)

#### DumbAssets ⭐ (New from selfh.st)
- **Why**: Track assets, warranties, and maintenance
- **Description**: Simple asset management system
- **Use Case**: Inventory management for home/office

---

### 🔄 **Task & Project Management** (Low Priority)

#### Vikunja (Reactivate from inactive/)
- **Why**: You have it in inactive/ - powerful task management
- **Description**: To-do lists, Kanban boards, project management
- **Status**: Already configured in `inactive/vikunja/`
- **Note**: You already have Planka, but Vikunja offers more features

---

### 📤 **File Sharing** (Low Priority)

#### Palmr ⭐ (New from selfh.st)
- **Why**: Privacy-focused file sharing with flexible access controls
- **Description**: Simple file sharing with S3-compatible storage
- **Use Case**: Share files with custom expiration, passwords, etc.

---

### 🖼️ **Image Processing** (Low Priority)

#### Mazanoke ⭐ (New from selfh.st)
- **Why**: Convert and optimize images from browser
- **Description**: Local image conversion tool
- **Use Case**: Optimize images before uploading, convert formats

---

### 🔔 **Notifications & Logging** (Low Priority)

#### LoggiFly ⭐ (New from selfh.st)
- **Why**: Generate notifications from log patterns
- **Description**: Lightweight log monitoring with notifications
- **Use Case**: Get alerts when specific log patterns occur
- **Integration**: Works with various notification services

---

### 📄 **Document Management** (Low Priority)

#### Papra ⭐ (New from selfh.st)
- **Why**: Minimalist document management
- **Description**: Simple document handling for important records
- **Use Case**: Alternative to Paperless-ngx if you want something simpler
- **Note**: You already have Paperless-ngx, so this might be redundant

---

### 🐳 **Docker Management** (Low Priority)

#### Portainer (Reactivate from inactive/)
- **Why**: You have it in inactive/ - visual Docker management
- **Description**: Web-based Docker container management
- **Status**: Already configured in `inactive/portainer/`
- **Note**: Free Business license available at portainer.io/take-5

---

## Priority Recommendations

### 🔥 **Top 5 Must-Have Additions**

1. **Navidrome** - Music streaming (complements your Lidarr setup)
2. **Nextcloud** - File storage (reactivate from inactive/)
3. **Gitea/Forgejo** - Code hosting (if you code)
4. **Rybbit** - Privacy-focused analytics
5. **Tinyauth** - Simple authentication for services

### ⚡ **Quick Wins** (Already Configured)

1. **Nextcloud** - Just move from `inactive/` to `apps/`
2. **Vikunja** - Task management (move from `inactive/`)
3. **Obsidian** - Note-taking (move from `inactive/`)
4. **Portainer** - Docker management (move from `inactive/`)

---

## Apps You Have That Are Popular on selfh.st

✅ **Already Installed** (from selfh.st popular apps):
- AdGuard Home
- FreshRSS
- Grist
- Home Assistant
- Immich
- Jellyfin
- Mealie
- n8n
- Paperless-ngx
- Plex
- Planka
- Traefik
- Vaultwarden
- Wiki.js

---

## Missing Categories

### Communication
- **Matrix/Element** - Secure messaging
- **Jitsi** - Video conferencing
- **Mattermost** - Slack alternative

### Social Media Alternatives
- **Mastodon** - Twitter alternative
- **Lemmy** - Reddit alternative
- **Pixelfed** - Instagram alternative

### Backup Solutions
- **Duplicati** - Backup software
- **Restic** - Fast, secure backup

### Development Tools
- **Drone CI** - CI/CD platform
- **Jenkins** - Automation server

---

## Notes

- Apps marked with ⭐ are new/trending on selfh.st
- Apps in `inactive/` can be easily reactivated
- Consider server resources before adding resource-intensive apps
- Some apps may overlap with existing functionality (e.g., Vikunja vs Planka)

---

## References

- [selfh.st/apps](https://selfh.st/apps/) - Comprehensive directory of self-hosted apps
- [selfh.st 2025 Favorite New Apps](https://selfh.st/post/2025-favorite-new-apps-so-far/) - Trending new apps

