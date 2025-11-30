# Transfer Spotify Playlists to Plex

This guide covers multiple methods to transfer your Spotify playlists to Plex.

## Overview

**The Challenge**: Spotify playlists are just metadata - you need to:
1. Get the track list from Spotify
2. Download the actual audio files
3. Organize them in Plex's music library
4. Create a playlist in Plex

## Method 1: Using SpotifyDL + Manual Plex Playlist (Easiest)

### Step 1: Export Spotify Playlist

**Option A: Using Spotify Web Player**
1. Open your playlist in Spotify (web or desktop)
2. Copy the playlist URL (e.g., `https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M`)
3. Or use the SpotifyDL web UI at: http://192.168.86.47:8800

**Option B: Export via Spotify API (for automation)**
- See `export_spotify_playlist.py` script below

### Step 2: Download Tracks with SpotifyDL

**Via Web UI:**
1. Open http://192.168.86.47:8800
2. Paste playlist URL or individual track URLs
3. Click download
4. Files will be saved to `apps/spotifydl/data/`

**Via Command Line:**
```bash
# Download entire playlist
docker exec -it spotdl spotdl download "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"

# Download single track
docker exec -it spotdl spotdl download "https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT"
```

### Step 3: Move Files to Plex Music Library

Your Plex music library is at: `/jenquist-cloud/archive` (mounted as `/data` in container)

**Organize by Artist/Album:**
```bash
# From spotifydl data directory
cd apps/spotifydl/data

# Move to Plex music library
# Plex expects: /data/Music/Artist/Album/Track.mp3
# SpotifyDL saves as: Artist - Title.mp3

# You may need to organize manually or use a script
# See organize_for_plex.py below
```

### Step 4: Create Playlist in Plex

**Manual Method:**
1. Open Plex: https://plex.server.unarmedpuppy.com
2. Go to **Music** library
3. Select tracks
4. Click **Add to Playlist** → **New Playlist**
5. Name it (e.g., "My Spotify Playlist")

**Automated Method:**
- See `create_plex_playlist.py` script below

## Method 2: Using Soundiiz (Third-Party Service)

**Pros**: Easiest, handles matching automatically
**Cons**: Requires subscription, tracks must already exist in Plex

1. Sign up at https://soundiiz.com/
2. Connect Spotify account
3. Connect Plex account (requires Plex token)
4. Select playlist → Transfer
5. Soundiiz matches tracks from your Plex library

**Note**: This only works if tracks already exist in your Plex library. It doesn't download new tracks.

## Method 3: Full Automation Script

See `transfer_spotify_to_plex.py` for a complete automated solution.

## File Organization

Plex expects music organized as:
```
/data/Music/
  Artist Name/
    Album Name/
      Track Number - Track Title.mp3
```

SpotifyDL saves as:
```
Artist - Title.mp3
```

**Solution**: Use a music tagger/organizer like:
- **beets** (automated tagging and organization)
- **MusicBrainz Picard** (manual tagging)
- Custom script (see `organize_for_plex.py`)

## Getting Your Plex Token

To use Plex API scripts, you need a token:

1. Open Plex: https://plex.server.unarmedpuppy.com
2. Go to **Settings** → **Network**
3. Or use: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/

## Troubleshooting

**Downloads failing?**
- Check SpotifyDL logs: `docker logs spotdl`
- Verify YouTube Music access (SpotifyDL uses YT Music as source)
- Check disk space: `df -h`

**Plex not finding tracks?**
- Ensure files are in the correct library path
- Check file permissions
- Trigger library scan in Plex: **Settings** → **Library** → **Scan Library Files**

**Playlist not showing?**
- Plex playlists are user-specific
- Ensure you're logged in as the correct user
- Check playlist is set to "Shared" if needed

