# Music Organization Guide for Plex

## Overview

You have music files organized by playlist folders, but Plex needs them organized as:
```
Music/
  Artist Name/
    Album Name/
      Track Number - Track Title.mp3
```

This guide covers multiple methods to organize your music and import it into Plex.

## Your Setup

- **Plex Music Library**: `/jenquist-cloud/archive/entertainment-media/Music`
- **Lidarr Music Library**: `/jenquist-cloud/archive/entertainment-media/Music` (same location)
- **Current Files**: Organized by playlist folders (e.g., `Playlist1/Song1.mp3`)

## Method 1: Automated Script (Recommended)

### Using `organize_music_for_plex.py`

This script automatically:
1. Scans playlist folders
2. Extracts metadata from audio files
3. Organizes into Artist/Album/Track structure
4. Copies/moves to Plex library
5. Generates playlist mappings

**Step 1: Install dependencies**
```bash
# On your local machine
pip3 install mutagen

# Or on server
bash scripts/connect-server.sh "pip3 install mutagen"
```

**Step 2: Run in dry-run mode first**
```bash
cd apps/media-download

# Dry run (shows what would happen without making changes)
python3 organize_music_for_plex.py \
  --source /path/to/your/playlist/folders \
  --target /jenquist-cloud/archive/entertainment-media/Music
```

**Step 3: Review the output**
- Check that artist/album/track names are correct
- Verify target paths look right

**Step 4: Execute for real**
```bash
# Copy files (keeps originals)
python3 organize_music_for_plex.py \
  --source /path/to/your/playlist/folders \
  --target /jenquist-cloud/archive/entertainment-media/Music \
  --execute

# Or move files (removes from source)
python3 organize_music_for_plex.py \
  --source /path/to/your/playlist/folders \
  --target /jenquist-cloud/archive/entertainment-media/Music \
  --execute \
  --move
```

**Step 5: Transfer to server (if running locally)**
```bash
# Copy organized files to server
scp -P 4242 -r /path/to/organized/Music/* unarmedpuppy@192.168.86.47:/jenquist-cloud/archive/entertainment-media/Music/
```

## Method 2: Using beets (Best for Large Collections)

**beets** is a powerful music library organizer that:
- Automatically tags files using MusicBrainz
- Organizes into your preferred structure
- Handles duplicates and missing metadata
- Can import directly to Plex library

### Installation

**Option A: Docker (Recommended)**
```yaml
# Add to docker-compose.yml
beets:
  image: linuxserver/beets:latest
  container_name: media-download-beets
  environment:
    - PUID=1000
    - PGID=1000
    - TZ=America/Chicago
  volumes:
    - ./beets/config:/config
    - /jenquist-cloud/archive/entertainment-media/Music:/music
    - /path/to/your/playlist/folders:/import
  restart: unless-stopped
```

**Option B: Local Installation**
```bash
pip3 install beets
```

### Configuration

Create `beets/config/config.yaml`:
```yaml
directory: /music
library: /config/musiclibrary.db

paths:
  default: $artist/$album%aunique{}/$track $title
  singleton: $artist/Non-Album/$title
  comp: Compilations/$album%aunique{}/$track $title

import:
  copy: yes
  move: no
  write: yes
  incremental: yes
  quiet: no
  timid: yes
  log: /config/beets.log

plugins: fetchart embedart
```

### Usage

**Import from playlist folders:**
```bash
# Docker
docker exec -it media-download-beets beet import /import/PlaylistName

# Local
beet import /path/to/playlist/folder
```

**beets will:**
1. Match each file to MusicBrainz database
2. Download correct metadata
3. Organize into Artist/Album structure
4. Copy to your music library
5. Ask for confirmation on uncertain matches

## Method 3: Using MusicBrainz Picard (Manual Control)

**MusicBrainz Picard** is a GUI application for tagging music files.

### Installation

**Download**: https://picard.musicbrainz.org/downloads/

### Usage

1. **Open Picard**
2. **Add files**: Drag playlist folders into Picard
3. **Cluster**: Click "Cluster" to group files by album
4. **Lookup**: Click "Lookup" to match against MusicBrainz
5. **Review**: Check matches, fix any errors
6. **Save**: Click "Save" to write tags and organize files

**Configure organization:**
- Options → File Naming
- Set pattern: `$if($albumartist,$albumartist,Unknown Artist)/$if($album,$album,Unknown Album)/$if($tracknumber,$tracknumber - ,)$title`

## Method 4: Using Lidarr (For Future Downloads)

Lidarr can organize existing files, but it's primarily designed for automated downloads.

**To use Lidarr for organization:**
1. Open Lidarr: http://192.168.86.47:8686
2. Go to **Settings** → **Media Management**
3. Set root folder to: `/music`
4. Use **Import** → **Manual Import** to import existing files
5. Lidarr will organize them automatically

**Note**: Lidarr works best when files have good metadata already.

## Importing to Plex

### After Organization

1. **Trigger Library Scan**
   - Open Plex: https://plex.server.unarmedpuppy.com
   - Go to **Settings** → **Library**
   - Click **Scan Library Files** for Music library

2. **Verify Files Appear**
   - Check that artists/albums show up correctly
   - Verify track numbers and titles

### Creating Playlists in Plex

**Option 1: Manual (Easiest)**
1. Open Plex Music library
2. Browse to tracks
3. Select multiple tracks (Ctrl/Cmd + Click)
4. Click **Add to Playlist** → **New Playlist**
5. Name it (e.g., "My Spotify Playlist")

**Option 2: Using Playlist Files**
1. Create `.m3u` playlist file:
   ```
   #EXTM3U
   #EXTINF:123,Artist - Title
   /jenquist-cloud/archive/entertainment-media/Music/Artist/Album/Track.mp3
   ```
2. Place in Plex playlists directory (if configured)
3. Or import via Plex web UI

**Option 3: Using Plex API**
- See `create_plex_playlist.py` script (if available)
- Requires Plex token

## Troubleshooting

### Files Not Showing in Plex

1. **Check file permissions**
   ```bash
   # On server
   sudo chown -R 1000:1000 /jenquist-cloud/archive/entertainment-media/Music
   sudo chmod -R 755 /jenquist-cloud/archive/entertainment-media/Music
   ```

2. **Verify directory structure**
   - Must be: `Artist/Album/Track.mp3`
   - Not: `Artist - Track.mp3` (missing album folder)

3. **Check file formats**
   - Plex supports: MP3, FLAC, M4A, AAC, OGG, WMA
   - Ensure files aren't corrupted

4. **Trigger manual scan**
   - Plex → Settings → Library → Scan Library Files

### Metadata Issues

**Missing or incorrect metadata:**
- Use beets or MusicBrainz Picard to fix tags
- Re-run organization script after fixing

**Files in "Unknown Artist" or "Unknown Album":**
- Metadata extraction failed
- Manually tag files or use beets/Picard

### Duplicate Files

**If you see duplicates:**
- Check if files were copied instead of moved
- Remove source files after verifying organization
- Use Plex's duplicate detection: Settings → Library → Show Duplicates

## Best Practices

1. **Always do a dry run first**
   - Review what will happen before making changes

2. **Keep backups**
   - Copy files before moving/organizing
   - Or use `--copy` mode first, verify, then delete originals

3. **Fix metadata before organizing**
   - Better metadata = better organization
   - Use beets or Picard for accurate tagging

4. **Organize in batches**
   - Process one playlist at a time
   - Verify results before continuing

5. **Use consistent structure**
   - Stick to: `Artist/Album/Track.mp3`
   - Plex and Lidarr both expect this format

## Quick Reference

**Your paths:**
- Plex library: `/jenquist-cloud/archive/entertainment-media/Music`
- Lidarr library: `/jenquist-cloud/archive/entertainment-media/Music`
- Plex container path: `/data/Music` (inside container)

**Expected structure:**
```
Music/
  Artist Name/
    Album Name/
      01 - Track Title.mp3
      02 - Another Track.mp3
```

**Script usage:**
```bash
# Dry run
python3 organize_music_for_plex.py --source /playlists --target /music

# Execute (copy)
python3 organize_music_for_plex.py --source /playlists --target /music --execute

# Execute (move)
python3 organize_music_for_plex.py --source /playlists --target /music --execute --move
```

