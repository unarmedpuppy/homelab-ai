# Cobalt - YouTube Audio Downloader

Self-hosted [Cobalt](https://github.com/imputnet/cobalt) instance for downloading audio from YouTube. Intended as a fallback for tracks that SoulSync/Soulseek can't find.

## Architecture

```
┌─────────────────┐     ┌──────────────────────┐
│  SoulSync       │     │  Cobalt API          │
│  (wishlist DB)  │────▶│  localhost:9000      │
└─────────────────┘     └──────────┬───────────┘
                                   │
                        ┌──────────▼───────────┐
                        │  yt-session-generator │
                        │  (YouTube auth tokens)│
                        └──────────────────────┘
```

## Components

### Cobalt API
- **Container**: `cobalt`
- **Image**: `harbor.server.unarmedpuppy.com/ghcr/imputnet/cobalt:11`
- **Port**: 9000
- **URL**: https://cobalt.server.unarmedpuppy.com/

### YouTube Session Generator
- **Container**: `yt-session-generator`
- **Image**: `harbor.server.unarmedpuppy.com/ghcr/imputnet/yt-session-generator:webserver`
- **Purpose**: Generates poToken & visitor_data for YouTube authentication
- **Status**: ⚠️ Currently failing to generate tokens (see Known Issues)

## Usage

### Test Cobalt API directly

```bash
# Check API status
curl http://localhost:9000/

# Download audio from YouTube
curl -X POST http://localhost:9000/ \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID", "downloadMode": "audio", "audioFormat": "mp3"}'
```

### Download SoulSync Wishlist Tracks

```bash
# Dry run - see what would be downloaded
python3 ~/server/apps/media-download/cobalt/download_wishlist.py --dry-run --limit 10

# Download with limit
python3 ~/server/apps/media-download/cobalt/download_wishlist.py --limit 20

# Download all (keeps wishlist entries for failed tracks)
python3 ~/server/apps/media-download/cobalt/download_wishlist.py --keep-wishlist
```

**Script options:**
- `--limit N`: Only process N tracks
- `--dry-run`: Don't download, just show what would happen
- `--keep-wishlist`: Don't remove tracks from wishlist after successful download

**Output:**
- Downloaded files go to: `/jenquist-cloud/archive/entertainment-media/Music/{Artist}/{Title}.mp3`
- Failed downloads logged to: `~/server/apps/media-download/cobalt/failed_downloads.json`

## Known Issues

### 1. YouTube Login Required (~80% of videos)

Most YouTube music videos require authentication. You'll see:
```json
{"status":"error","error":{"code":"error.api.youtube.login"}}
```

**Why**: YouTube requires proof-of-origin tokens for most content. The yt-session-generator should provide these but is currently failing.

**Workarounds**:
- Some videos work without auth (try different search results)
- Fix yt-session-generator (see below)
- Use cookies (temporary, they expire quickly)

### 2. yt-session-generator Failing

The session generator logs show:
```
[WARNING] update failed: timeout waiting for outgoing API request
```

**Potential fixes to try**:
1. Restart container: `docker restart yt-session-generator`
2. Check if it needs `--no-sandbox` for Chromium
3. Network/DNS issues from container

### 3. YouTube Music URLs vs Regular YouTube

YouTube Music URLs (`music.youtube.com`) often fail even when regular YouTube URLs work. The script converts to regular YouTube URLs automatically.

## Files

| File | Purpose |
|------|---------|
| `download_wishlist.py` | Main script to download SoulSync wishlist |
| `failed_downloads.json` | Log of tracks that failed to download |
| `README.md` | This file |

## Dependencies

Installed on host:
- `ytmusicapi` - For searching YouTube Music catalog
- `yt-dlp` - At `~/.local/bin/yt-dlp` (not used by Cobalt, available for debugging)

## Related Services

| Service | Purpose | Status |
|---------|---------|--------|
| SoulSync | Music discovery from Spotify | ✅ Running |
| slskd | Soulseek P2P downloads | ✅ Running |
| spotdl | Alternative YouTube downloader | ⚠️ Same auth issues |

## Maintenance

### Restart Cobalt
```bash
cd ~/server/apps/media-download
docker compose restart cobalt yt-session-generator
```

### View logs
```bash
docker logs cobalt --tail 50
docker logs yt-session-generator --tail 50
```

### Check wishlist count
```bash
docker exec soulsync python3 -c "
import sqlite3
conn = sqlite3.connect('/app/database/music_library.db')
print(conn.execute('SELECT COUNT(*) FROM wishlist_tracks').fetchone()[0])
"
```

## Future Improvements

1. **Fix yt-session-generator** - Debug why token generation is timing out
2. **Cookie automation** - Script to refresh YouTube cookies periodically
3. **Hybrid approach** - Try Cobalt first, fall back to Soulseek retry
4. **Rate limiting** - Add delays to avoid YouTube blocks

---

*Created: 2026-01-04*
*Last Updated: 2026-01-04*
