---
name: troubleshoot-stuck-downloads
description: Fix stuck downloads in Sonarr/Radarr
when_to_use: Downloads stuck in queue, download client unavailable errors, downloads not importing
---

# Troubleshoot Stuck Downloads

Fix stuck downloads in Sonarr/Radarr.

## When to Use

- Downloads stuck in queue
- "Download client unavailable" errors
- Downloads not importing

## Steps

### 1. Check Queue Status

**Sonarr:**
```bash
curl -s "http://SERVER:8989/api/v3/queue?apikey=API_KEY" | jq '.records[] | {title: .title, status: .status, errorMessage: .errorMessage}'
```

**Radarr:**
```bash
curl -s "http://SERVER:7878/api/v3/queue?apikey=API_KEY" | jq '.records[] | {title: .title, status: .status, errorMessage: .errorMessage}'
```

### 2. Check Download Client

```bash
# Check if download client container is running
docker ps | grep -E "nzbget|sabnzbd|qbittorrent|transmission"

# Check download client logs
docker logs DOWNLOAD_CLIENT --tail 50
```

### 3. Check Disk Space

```bash
df -h /path/to/downloads
```

### 4. Common Fixes

**Restart download client:**
```bash
docker restart nzbget  # or sabnzbd, qbittorrent, etc.
```

**Clear stuck queue items:**
```bash
# Sonarr - remove and blocklist
curl -X DELETE "http://SERVER:8989/api/v3/queue/QUEUE_ID?removeFromClient=true&blocklist=false&apikey=API_KEY"

# Radarr - same pattern
curl -X DELETE "http://SERVER:7878/api/v3/queue/QUEUE_ID?removeFromClient=true&blocklist=false&apikey=API_KEY"
```

**Force import scan:**
```bash
# Sonarr
curl -X POST "http://SERVER:8989/api/v3/command" -H "Content-Type: application/json" -d '{"name":"DownloadedEpisodesScan"}' --data-urlencode "apikey=API_KEY"
```

### 5. Check Permissions

```bash
# Check download directory permissions
ls -la /path/to/downloads

# Check if Sonarr/Radarr can access the path
docker exec sonarr ls -la /downloads
```

## Common Issues

| Error | Cause | Fix |
|-------|-------|-----|
| Download client unavailable | Client offline | Restart client container |
| Import failed | Permission issue | Fix directory permissions |
| Disk space | Full disk | Run cleanup-disk-space tool |
| Stuck in queue | Import failed silently | Check logs, manual import |

