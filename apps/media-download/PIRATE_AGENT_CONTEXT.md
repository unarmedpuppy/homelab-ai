# Media Download Stack - Agent Context Document

## Overview
This document provides context for AI agents working with the media download automation stack. The system uses Docker Compose to run Sonarr, Radarr, NZBGet, and related services with VPN protection via Gluetun.

## Server Access

### Connection Method
All commands must be executed on the remote server, NOT locally. Use the connection script:

```bash
bash scripts/connect-server.sh '<command>'
```

### Server Details
- **Host**: 192.168.86.47
- **Port**: 4242
- **User**: unarmedpuppy
- **SSH Command**: `ssh unarmedpuppy@192.168.86.47 -p 4242`

### Example Commands
```bash
# Check Docker containers
bash scripts/connect-server.sh "cd ~/server/apps/media-download && docker-compose ps"

# View logs
bash scripts/connect-server.sh "cd ~/server/apps/media-download && docker-compose logs -f sonarr"

# Execute commands inside containers
bash scripts/connect-server.sh "docker exec media-download-sonarr curl -s 'http://127.0.0.1:8989/api/v3/system/status?apikey=API_KEY'"
```

## Architecture

### VPN Kill Switch Setup
**CRITICAL**: The VPN kill switch is a security requirement. Download clients MUST route through Gluetun.

- **Gluetun** (`media-download-gluetun`): VPN gateway using ProtonVPN via OpenVPN
- **NZBGet** and **qBittorrent**: Use `network_mode: "service:gluetun"` to route all traffic through VPN
- **Sonarr/Radarr**: Connect to NZBGet via `media-download-gluetun:6789` (NOT `media-download-nzbget`)
  - This is intentional and correct - it maintains the VPN kill switch
  - The hostname `media-download-gluetun` is the correct endpoint

### Network Structure
- **Bridge Network**: `media-download-network` - connects all services
- **VPN Network**: Services using `network_mode: "service:gluetun"` share Gluetun's network namespace
- **Port Mapping**: Gluetun exposes ports 6789 (NZBGet) and 8080 (qBittorrent) to the bridge network

### Service Communication
- **Sonarr/Radarr → NZBGet**: `http://media-download-gluetun:6789/jsonrpc`
- **Sonarr/Radarr → qBittorrent**: `http://media-download-gluetun:8080/api/v2`
- **Sonarr/Radarr → NZBHydra2**: `http://media-download-nzbhydra2:5076`
- **Sonarr/Radarr → Jackett**: `http://media-download-jackett:9117`

## API Keys

### Sonarr
- **API Key**: `dd7148e5a3dd4f7aa0c579194f45edff`
- **Base URL**: `http://127.0.0.1:8989` (from within container)
- **External URL**: `http://192.168.86.47:8989`

### Radarr
- **API Key**: `afb58cf1eaee44208099b403b666e29c`
- **Base URL**: `http://127.0.0.1:7878` (from within container)
- **External URL**: `http://192.168.86.47:7878`

### NZBGet
- **Control Username**: `nzbget`
- **Control Password**: `nzbget`
- **Control Port**: `6789`
- **Access**: Via `media-download-gluetun:6789` from Sonarr/Radarr

### qBittorrent
- **WebUI Username**: `admin`
- **WebUI Password**: `adminadmin` (permanent password set via API)
- **WebUI Port**: `8080`
- **Access**: Via `media-download-gluetun:8080` from Sonarr/Radarr
- **Note**: qBittorrent generates temporary passwords on each restart if no permanent password is set. The permanent password must be set via API or WebUI.

## Path Configuration

### Docker Volume Mounts
- **Media Path**: `/jenquist-cloud/archive/entertainment-media` → mounted as `/tv`, `/movies`, `/music`, `/books` in containers
- **Download Path**: `./downloads` (relative to docker-compose.yml) → mounted as `/downloads` in containers

### Sonarr Configuration
- **Root Folder**: `/tv/Shows`
- **Remote Path Mapping**: 
  - Host: `media-download-gluetun`
  - Remote: `/downloads/`
  - Local: `/downloads/`
- **Download Client Path**: `/downloads/completed/tv`
- **Final Media Path**: `/tv/Shows/{Series Name}/` (inside container)
- **Download Clients**:
  - **NZBGet** (Usenet): `media-download-gluetun:6789`, category `tv`
  - **qBittorrent** (Torrent): `media-download-gluetun:8080`, category `tv`

### Radarr Configuration
- **Root Folders**: 
  - `/movies/Films` (ID: 4) - Main movies folder
  - `/movies/Kids/Films` (ID: 5) - Kids movies folder
- **Remote Path Mapping**: 
  - Host: `media-download-gluetun`
  - Remote: `/downloads/`
  - Local: `/downloads/`
- **Download Client Path**: `/downloads/completed/movies`
- **Final Media Path**: `/movies/{Category}/{Movie Name (Year)}/` (inside container)
  - Note: Movies may be in subdirectories like `/movies/Kids/Films/` or `/movies/Films/`
  - Collections in `/movies/Kids/Films` require this root folder to be configured

### NZBGet Configuration
- **Main Directory**: `/downloads`
- **Completed Directory**: `/downloads/completed`
- **Intermediate Directory**: `/downloads/intermediate`
- **Categories**:
  - `tv` → `/downloads/completed/tv`
  - `movies` → `/downloads/completed/movies`
  - `music` → `/downloads/completed/music`
  - `books` → `/downloads/completed/books`

## Usenet Servers (NZBGet)

### Server Priority (Lower Level = Higher Priority)
1. **Server 4 - UsenetServer** (Level 0, Active)
   - Host: `news.usenetserver.com`
   - Port: 563 (SSL)
   - Username: `9rehdoqtx2`
   - Password: `Anaerobic2-Scapegoat-Sixtyfold`
   - Connections: 10
   - Retention: 5000 days

2. **Server 1 - Frugal US** (Level 1, Active)
   - Host: `news.frugalusenet.com`
   - Port: 563 (SSL)
   - Connections: 60
   - Retention: 1100 days

3. **Server 2 - Frugal EU** (Level 2, Active)
   - Host: `eunews.frugalusenet.com`
   - Port: 563 (SSL)
   - Connections: 30
   - Retention: 1100 days

4. **Server 3 - Frugal Bonus** (Level 3, Inactive)
   - Host: `bonus.frugalusenet.com`
   - Port: 563 (SSL)
   - Active: `no`

## Current State (As of Last Update)

### Successfully Imported
- ✅ **Aladdin (1992)** → `/movies/Kids/Films/Aladdin (1992)/`

### Pending Imports
- **Movies** (8 remaining in `/downloads/completed/movies/`):
  - Cinderella.1950.UHD.BluRay.2160p.DTS-HD.MA.5.1.DV.HEVC.HYBRID.REMUX-FraMeSToR
  - Hocus.Pocus.2.2022.2160p.DSNP.WEB-DL.DDPA.5.1.DV.H.265-PiRaTeS
  - Jurassic.World.Rebirth.2025.2160p.GER.UHD.Blu-ray.REMUX.HEVC.Atmos.TrueHD7.1-HDH
  - Lilo.and.Stitch.2002.UHD.US.BluRay.2160p.HEVC.DV.HDR.DTSHR.DL.Remux-TvR
  - Mulan.1998.2160p.UHD.BluRay.REMUX.HDR.HEVC.Atmos-EPSiLON
  - Tangled.2010.2160p.UHD.Bluray.REMUX.HDR10.HEVC.TrueHD.Atmos.7.1-4K4U
  - The.Jungle.Book.1967.Upscale.[2160p].[AV1-10bit.Opus 5.1]
  - The.Lion.King.1994.2160p.BluRay.REMUX.HEVC.DTS-HD.MA.TrueHD.7.1.Atmos-FGT
  - The.Nightmare.Before.Christmas.1993.UHD.BluRay.2160p.DTS-HD.MA.7.1.DV.HEVC.HYBRID.REMUX-FraMeSToR

- **TV Shows** (3 remaining in `/downloads/completed/tv/`):
  - Avatar.The.Last.Airbender.S03.Bluray.EAC3.2.0.1080p.x265-iVy
  - Spongebob.Squarepants.S01.1080p.JC.WEB-DL.AAC2.0.x.264-Saon
  - Star.Wars.Young.Jedi.Adventures.S02.1080p.WEBRip.x265-KONTRAST

### Disk Space
- **Status**: 78% used (freed ~200GB by cleaning archive files)
- **Location**: Root partition (`/`)
- **Action Taken**: Removed unpacked `.rar`, `.par2`, and `.nzb` files from completed downloads

## Common Operations

### Trigger Import Scans

#### Sonarr
```bash
bash scripts/connect-server.sh "docker exec media-download-sonarr curl -s -X POST 'http://127.0.0.1:8989/api/v3/command?apikey=dd7148e5a3dd4f7aa0c579194f45edff' -H 'Content-Type: application/json' -d '{\"name\":\"DownloadedEpisodesScan\",\"path\":\"/downloads/completed/tv\"}'"
```

#### Radarr
```bash
bash scripts/connect-server.sh "docker exec media-download-radarr curl -s -X POST 'http://127.0.0.1:7878/api/v3/command?apikey=afb58cf1eaee44208099b403b666e29c' -H 'Content-Type: application/json' -d '{\"name\":\"DownloadedMoviesScan\",\"path\":\"/downloads/completed/movies\"}'"
```

### Check Queue Status

#### Sonarr
```bash
bash scripts/connect-server.sh "docker exec media-download-sonarr curl -s 'http://127.0.0.1:8989/api/v3/queue?apikey=dd7148e5a3dd4f7aa0c579194f45edff' | python3 -m json.tool"
```

#### Radarr
```bash
bash scripts/connect-server.sh "docker exec media-download-radarr curl -s 'http://127.0.0.1:7878/api/v3/queue?apikey=afb58cf1eaee44208099b403b666e29c' | python3 -m json.tool"
```

### Clear Queue

#### Sonarr - Remove All Items
```bash
# Get all queue item IDs
bash scripts/connect-server.sh "docker exec media-download-sonarr curl -s 'http://127.0.0.1:8989/api/v3/queue?apikey=dd7148e5a3dd4f7aa0c579194f45edff' | python3 -c \"import sys, json; data=json.load(sys.stdin); ids = [str(r['id']) for r in data['records']]; print(' '.join(ids))\""

# Remove all items (replace with actual IDs from above)
bash scripts/connect-server.sh "for id in ID_LIST; do docker exec media-download-sonarr curl -s -X DELETE \"http://127.0.0.1:8989/api/v3/queue/\$id?apikey=dd7148e5a3dd4f7aa0c579194f45edff&removeFromClient=true&blocklist=false\"; done"
```

### Check Library Contents

#### Sonarr Series
```bash
bash scripts/connect-server.sh "docker exec media-download-sonarr curl -s 'http://127.0.0.1:8989/api/v3/series?apikey=dd7148e5a3dd4f7aa0c579194f45edff' | python3 -m json.tool"
```

#### Radarr Movies
```bash
bash scripts/connect-server.sh "docker exec media-download-radarr curl -s 'http://127.0.0.1:7878/api/v3/movie?apikey=afb58cf1eaee44208099b403b666e29c' | python3 -m json.tool"
```

### View Logs
```bash
# Sonarr logs
bash scripts/connect-server.sh "docker logs media-download-sonarr --tail 50"

# Radarr logs
bash scripts/connect-server.sh "docker logs media-download-radarr --tail 50"

# NZBGet logs
bash scripts/connect-server.sh "docker logs media-download-nzbget --tail 50"
```

## Known Issues & Solutions

### 1. Radarr 401 Unauthorized Errors
**Symptom**: Radarr logs show `401.Unauthorized` when connecting to NZBGet via `media-download-gluetun:6789`

**Status**: This is a known issue that doesn't block manual imports. The authentication appears to work for manual scans but fails for periodic monitoring.

**Workaround**: Manual import scans work correctly. The 401 errors are from background monitoring tasks and don't prevent file imports.

**Do NOT**: Change the hostname from `media-download-gluetun` to `media-download-nzbget` - this would break the VPN kill switch.

### 2. Import Scans Show "Failed to import"
**Symptom**: Import scans complete with status "unsuccessful" or "Failed to import"

**Reality**: Files ARE being imported successfully. The error messages are misleading.

**Verification**: Check if files exist in the final media library locations:
```bash
bash scripts/connect-server.sh "docker exec media-download-radarr ls -la '/movies/Kids/Films/Aladdin (1992)/'"
```

### 3. Disk Space Issues
**Symptom**: Disk at 100% usage, services fail with "disk I/O error"

**Solution**: Clean up unpacked archive files from completed downloads:
```bash
bash scripts/connect-server.sh "cd ~/server/apps/media-download/downloads/completed && find . -type f \( -name '*.rar' -o -name '*.par2' -o -name '*.nzb' \) -delete"
```

**Prevention**: NZBGet is configured with `UnpackCleanupDisk=yes` to automatically clean up archives after unpacking.

### 4. Files Not Importing
**Common Causes**:
1. Series/Movie not in library - Sonarr/Radarr only import files for items already in the library
2. Path mismatch - Check root folders and remote path mappings
3. File naming doesn't match - Sonarr/Radarr may not recognize the file

**Verification**:
```bash
# Check if series/movie is in library
bash scripts/connect-server.sh "docker exec media-download-sonarr curl -s 'http://127.0.0.1:8989/api/v3/series?apikey=dd7148e5a3dd4f7aa0c579194f45edff' | python3 -c \"import sys, json; series=json.load(sys.stdin); print('\\n'.join([s['title'] for s in series]))\" | grep -i 'series name'"
```

### 5. Sonarr Queue Stuck - "downloadClientUnavailable"
**Symptom**: Queue items stuck with status "downloadClientUnavailable", especially torrents

**Root Cause**: Sonarr may only have NZBGet configured but queue contains torrents requiring qBittorrent. Or qBittorrent password not set/configured correctly.

**Solution**:
1. Verify qBittorrent is configured in Sonarr:
   ```bash
   bash scripts/connect-server.sh "docker exec media-download-sonarr curl -s 'http://127.0.0.1:8989/api/v3/downloadclient?apikey=dd7148e5a3dd4f7aa0c579194f45edff' | python3 -c \"import sys, json; clients=json.load(sys.stdin); print('\\n'.join([c['name'] + ' (' + c['protocol'] + ')' for c in clients]))\""
   ```

2. If qBittorrent is missing, add it:
   - Host: `media-download-gluetun`
   - Port: `8080`
   - Username: `admin`
   - Password: `adminadmin` (or set permanent password via qBittorrent API/WebUI)
   - Category: `tv`

3. Set permanent qBittorrent password (if using temporary password):
   ```bash
   # Get current temp password from logs
   bash scripts/connect-server.sh "docker logs media-download-qbittorrent 2>&1 | grep -i 'temporary password' | tail -1"
   
   # Login and set permanent password
   bash scripts/connect-server.sh "docker exec media-download-qbittorrent curl -s -X POST 'http://127.0.0.1:8080/api/v2/auth/login' -d 'username=admin&password=TEMP_PASSWORD' -c /tmp/cookies.txt && docker exec media-download-qbittorrent curl -s -X POST 'http://127.0.0.1:8080/api/v2/app/setPreferences' -b /tmp/cookies.txt -d 'json={\"web_ui_password\":\"adminadmin\"}'"
   ```

4. Restart Sonarr to refresh download client connections:
   ```bash
   bash scripts/connect-server.sh "docker restart media-download-sonarr"
   ```

5. Clear stuck queue items if needed:
   ```bash
   # Get stuck item IDs
   bash scripts/connect-server.sh "docker exec media-download-sonarr curl -s 'http://127.0.0.1:8989/api/v3/queue?apikey=dd7148e5a3dd4f7aa0c579194f45edff&status=downloadClientUnavailable' | python3 -c \"import sys, json; data=json.load(sys.stdin); print(','.join([str(r['id']) for r in data['records']]))\""
   
   # Remove each item (replace ID_LIST with comma-separated IDs)
   bash scripts/connect-server.sh "for id in ID_LIST; do docker exec media-download-sonarr curl -s -X DELETE \"http://127.0.0.1:8989/api/v3/queue/\$id?apikey=dd7148e5a3dd4f7aa0c579194f45edff&removeFromClient=true&blocklist=false\"; done"
   ```

## Important Configuration Notes

### VPN & DNS
- **DNS**: Plain UDP DNS (not DoT) for reliability - `DNS_ADDRESS=1.1.1.1`, `DOT=off`
- **DNS Leak Prevention**: All DNS queries go through VPN - no leaks possible
- **Unblocked Domains**: `UNBLOCK=news.usenetserver.com,news-us.usenetserver.com,news-eu.usenetserver.com`
- **Kill Switch**: Always enabled - `KILL_SWITCH=on`, `KILL_SWITCH_ACTIVATE=on`

### NZBGet Settings
- **Unpacking**: Enabled with cleanup - `Unpack=yes`, `UnpackPauseQueue=no`, `UnpackCleanupDisk=yes`
- **Article Retries**: Reduced to fail faster - `ArticleRetries=3`, `ArticleTimeout=60`, `RetryInterval=10`
- **API Authentication**: Explicitly set - `ControlUsername=nzbget`, `ControlPassword=nzbget`

### File Permissions
- **User/Group**: `PUID=1000`, `PGID=1000` (unarmedpuppy user)
- **Ownership**: All files should be owned by `unarmedpuppy:unarmedpuppy`

## Troubleshooting Workflow

1. **Check Service Status**
   ```bash
   bash scripts/connect-server.sh "cd ~/server/apps/media-download && docker-compose ps"
   ```

2. **Check Disk Space**
   ```bash
   bash scripts/connect-server.sh "df -h /"
   ```

3. **Check Logs for Errors**
   ```bash
   bash scripts/connect-server.sh "docker logs media-download-sonarr --tail 100 | grep -i error"
   ```

4. **Verify VPN Connection**
   ```bash
   bash scripts/connect-server.sh "docker logs media-download-gluetun --tail 50"
   ```

5. **Test Download Client Connections**
   ```bash
   # Test NZBGet
   bash scripts/connect-server.sh "docker exec media-download-radarr curl -s 'http://media-download-gluetun:6789/jsonrpc' -H 'Content-Type: application/json' -d '{\"method\":\"status\",\"params\":[],\"id\":1}' -u nzbget:nzbget"
   
   # Test qBittorrent
   bash scripts/connect-server.sh "docker exec media-download-sonarr curl -s -X POST 'http://media-download-gluetun:8080/api/v2/auth/login' -d 'username=admin&password=adminadmin'"
   ```

6. **Check Completed Downloads**
   ```bash
   bash scripts/connect-server.sh "ls -lh ~/server/apps/media-download/downloads/completed/tv/ ~/server/apps/media-download/downloads/completed/movies/"
   ```

7. **Trigger Manual Import Scan**
   - Use the commands in "Common Operations" section above

## File Locations Reference

### On Server (Host)
- **Docker Compose**: `~/server/apps/media-download/docker-compose.yml`
- **NZBGet Config**: `~/server/apps/media-download/nzbget/config/nzbget.conf`
- **Downloads**: `~/server/apps/media-download/downloads/`
- **Media Library**: `/jenquist-cloud/archive/entertainment-media/`

### In Containers
- **Sonarr Media**: `/tv/Shows/` (maps to `/jenquist-cloud/archive/entertainment-media/tv/Shows/`)
- **Radarr Media**: `/movies/Films/` or `/movies/Kids/Films/` (maps to `/jenquist-cloud/archive/entertainment-media/movies/`)
- **Downloads**: `/downloads/completed/{category}/` (maps to `./downloads/completed/{category}/`)

## Security Considerations

1. **VPN Kill Switch**: Never bypass or disable - all download traffic must go through Gluetun
2. **DNS Leak Prevention**: DNS queries are routed through VPN - verified working
3. **API Keys**: Stored in config files - do not expose in logs or documentation
4. **Credentials**: Usenet server credentials in `nzbget.conf` - keep secure

## Next Steps for Continuing Work

1. **Monitor Import Progress**: Check completed directories periodically to see files being processed
2. **Investigate Failed Imports**: Some files may not match library items or have naming issues
3. **Resolve 401 Errors**: Investigate why Radarr authentication fails for monitoring but works for manual scans
4. **Optimize Import Process**: Consider automating cleanup of archive files or improving import success rate

## Additional Resources

- **Sonarr API Docs**: https://sonarr.tv/docs/api/
- **Radarr API Docs**: https://radarr.video/docs/api/
- **NZBGet Docs**: https://nzbget.net/documentation
- **Gluetun Docs**: https://github.com/qdm12/gluetun

---

**Last Updated**: 2025-11-13
**Agent**: Auto (Cursor AI)
**Status**: System operational, imports working. qBittorrent configured for torrent downloads. Queue cleared and ready for fresh downloads.

