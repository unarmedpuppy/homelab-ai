# How The Media Download System Works

## Architecture Overview

```
You (Browser)
    ↓
[Sonarr/Radarr UI] ← Main entry point for users
    ↓ (searches)
[NZBHydra2] ← Usenet search aggregator
    ↓ (gets NZB files)
[NZBGet] ← Downloads through VPN
    ↓
[Frugal Usenet] via [ProtonVPN]
    ↓
Downloads complete → Sonarr moves to media library
```

## Main Entry Point: Sonarr & Radarr

**This is where YOU interact with the system.**

### Sonarr (TV Shows)
- **Access:** http://YOUR_SERVER:8989
- **Purpose:** Manage your TV show library
- **What you do:**
  1. Click "Add Series"
  2. Search for a show (e.g., "Game of Thrones")
  3. Click "Add"
  4. System automatically:
     - Searches for new episodes
     - Downloads them
     - Organizes into folders
     - Renames files properly

### Radarr (Movies)
- **Access:** http://YOUR_SERVER:7878
- **Purpose:** Manage your movie library
- **What you do:**
  1. Click "Add Movie"
  2. Search for a movie
  3. Click "Add"
  4. System automatically downloads when available

## How The Download Process Works

### 1. You Add Content
- Open Sonarr (http://server:8989)
- Add a TV show (e.g., "Breaking Bad")
- Sonarr monitors for new episodes

### 2. Automated Search
When a new episode releases:
- Sonarr asks NZBHydra2: "Find episodes for Breaking Bad S01E01"
- NZBHydra2 searches NZBGeek indexer
- Finds NZB files

### 3. Download Through VPN
- Sonarr sends NZB to NZBGet
- NZBGet connects to Frugal Usenet servers
- **All traffic routes through ProtonVPN**
- Downloads the actual content (via Usenet newsgroups)
- Repairs with par2 if needed

### 4. Automatic Organization
- Download completes
- Sonarr moves file to media library
- Renames properly (e.g., "Breaking Bad - S01E01 - Pilot.mkv")
- Sonarr marks as "Downloaded"

### 5. Optional: Subtitles
- Bazarr detects new file
- Downloads subtitles automatically

## Component Roles

### Sonarr/Radarr (Automation Layer)
- **Entry point for users**
- Manages wishlist of content
- Monitors for releases
- Downloads and organizes automatically
- Web UI for management

### NZBHydra2 (Search Aggregator)
- Searches multiple Usenet indexers
- Finds NZB files
- Provides API to Sonarr/Radarr
- Access: http://server:5076

### Jackett (Torrent Aggregator)
- Searches torrent indexers
- Alternative to NZBHydra2 for torrents
- Access: http://server:9117

### NZBGet (Download Client)
- Downloads from Usenet servers
- Routes ALL traffic through VPN
- Handles repair and extraction
- Access: http://server:6789

### qBittorrent (Torrent Client)
- Downloads torrents
- Also routes through VPN
- Access: http://server:8080

### WireGuard (VPN Gateway)
- VPN client running in container
- All downloads go through this
- Kill switch protection
- Swiss server (privacy)

### Frugal Usenet (Content Source)
- Usenet provider
- Multiple server locations
- Primary + backup servers
- SSL encryption

## Security Layers

1. **VPN Kill Switch** - If VPN drops, downloads stop
2. **DNS Leak Prevention** - All DNS queries through VPN
3. **SSL/TLS Encryption** - Usenet connections encrypted
4. **Network Isolation** - Download clients isolated
5. **Private Credentials** - Not in Git

## What You Actually Do

### For TV Shows:
1. Open http://server:8989 (Sonarr)
2. Click "Add Series"
3. Search and add shows
4. Wait for downloads (automatic)
5. Watch media in your library

### For Movies:
1. Open http://server:7878 (Radarr)
2. Click "Add Movie"
3. Search and add movies
4. Wait for downloads (automatic)
5. Watch in your library

### To Check Status:
- **Downloads:** http://server:6789 (NZBGet web UI)
- **Search:** http://server:5076 (NZBHydra2)
- **VPN Status:** Check WireGuard container

## Typical User Workflow

```
Monday: Add "The Witcher" season 3 in Sonarr
Tuesday: New episode releases
Tuesday 10am: Sonarr detects it
Tuesday 10:01am: Downloads start
Tuesday 10:05am: Download complete
Tuesday 10:06am: Moved to media library
Tuesday 10:07am: Available in Plex/your media player
```

## Configuration Flow

1. **WireGuard** - VPN connection (automatic startup)
2. **NZBGet** - Add Usenet servers (configure manually)
3. **NZBHydra2** - Add indexers like NZBGeek (configure manually)
4. **Sonarr** - Add NZBHydra2 + NZBGet (configure manually)
5. **Done** - Start adding content!

## Why This Architecture?

- **Separation of concerns:** Each tool does one thing well
- **VPN protection:** All downloads routed through VPN
- **Redundancy:** Multiple servers + backup servers
- **Automation:** Set it and forget it
- **Privacy:** DNS leak prevention, kill switch, encryption

## Common Questions

**Q: Do I need to configure all these services?**
A: Mainly: NZBGet (Usenet), NZBHydra2 (search), Sonarr/Radarr (automation)

**Q: What if VPN disconnects?**
A: Kill switch stops all downloads immediately

**Q: Can I add content manually?**
A: Yes, but automation is the whole point!

**Q: How do I know it's working?**
A: Check http://server:6789 to see active downloads

**Q: What about legal content?**
A: Only download content you have rights to (public domain, Creative Commons, etc.)

