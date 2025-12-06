# Quick Start: Organize Music for Plex

## Your Situation

You have music files organized by playlist folders:
```
playlists/
  My Playlist 1/
    Song1.mp3
    Song2.mp3
  My Playlist 2/
    Song3.mp3
```

You need them organized for Plex:
```
Music/
  Artist Name/
    Album Name/
      01 - Track Title.mp3
```

## Fastest Method: Automated Script with Transfer

**Recommended**: Use the all-in-one script that organizes and transfers:

```bash
cd apps/media-download
chmod +x organize_and_transfer_music.sh
./organize_and_transfer_music.sh /path/to/your/playlist/folders
```

This script will:
1. Organize files locally (with preview)
2. Ask for confirmation
3. Transfer organized files to server
4. Set correct permissions
5. Clean up temp files

**That's it!** Then just scan your Plex library.

---

## Alternative: Manual Organization

### Step 1: Install Dependencies

**On your local machine:**
```bash
pip3 install mutagen
```

**Or on the server:**
```bash
bash scripts/connect-server.sh "pip3 install mutagen"
```

### Step 2: Run Dry Run

**If files are on your local machine:**
```bash
cd apps/media-download
python3 organize_music_for_plex.py \
  --source /path/to/your/playlist/folders \
  --target /tmp/organized_music
```

**If files are on the server:**
```bash
bash scripts/connect-server.sh "cd ~/server/apps/media-download && python3 organize_music_for_plex.py --source /path/to/playlists --target /jenquist-cloud/archive/entertainment-media/Music"
```

### Step 3: Review Output

Check that:
- Artist names look correct
- Album names are right
- Track numbers are present
- File paths make sense

### Step 4: Execute (Copy Mode)

**Copy files (keeps originals):**
```bash
python3 organize_music_for_plex.py \
  --source /path/to/your/playlist/folders \
  --target /jenquist-cloud/archive/entertainment-media/Music \
  --execute
```

### Step 5: Transfer to Server (if needed)

If you organized locally and didn't use the automated script:
```bash
# Copy to server
rsync -avz -e "ssh -p 4242" \
  /tmp/organized_music/ \
  unarmedpuppy@192.168.86.47:/jenquist-cloud/archive/entertainment-media/Music/

# Set permissions
ssh -p 4242 unarmedpuppy@192.168.86.47 \
  "sudo chown -R 1000:1000 /jenquist-cloud/archive/entertainment-media/Music"
```

**Or use the automated script** (see top of this guide) which handles transfer automatically.

### Step 6: Scan Plex Library

1. Open Plex: https://plex.server.unarmedpuppy.com
2. Go to **Settings** → **Library**
3. Click **Scan Library Files** for Music library
4. Wait for scan to complete

### Step 7: Create Playlists

**Option A: Manual (Easiest)**
1. Open Plex Music library
2. Browse to tracks
3. Select tracks (Ctrl/Cmd + Click)
4. Click **Add to Playlist** → **New Playlist**
5. Name it

**Option B: Automated**
```bash
# First, get your Plex token from:
# https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/

export PLEX_TOKEN="your-token-here"
python3 create_plex_playlist.py \
  --mappings playlist_mappings.json \
  --plex-token "$PLEX_TOKEN"
```

## Alternative: Use beets (Best for Large Collections)

If you have many files or want better metadata matching:

1. **Add beets to docker-compose.yml** (see MUSIC_ORGANIZATION_GUIDE.md)
2. **Configure beets** (create config.yaml)
3. **Import playlists:**
   ```bash
   docker exec -it media-download-beets beet import /import/PlaylistName
   ```

beets will:
- Match files to MusicBrainz database
- Download correct metadata
- Organize automatically
- Handle duplicates

## Troubleshooting

### "No metadata found"
- Files may not have embedded tags
- Script will try to parse filename (e.g., "Artist - Title.mp3")
- Use beets or MusicBrainz Picard for better tagging

### "Files not showing in Plex"
- Check file permissions: `sudo chown -R 1000:1000 /jenquist-cloud/archive/entertainment-media/Music`
- Verify structure: Must be `Artist/Album/Track.mp3`
- Trigger manual scan in Plex

### "Playlist not created"
- Tracks must be in Plex library first
- Check that file paths match Plex's internal paths
- May need to manually create playlist if automated method fails

## File Locations

- **Plex Music Library**: `/jenquist-cloud/archive/entertainment-media/Music`
- **Lidarr Music Library**: Same location
- **Scripts**: `apps/media-download/`

## Need More Help?

See `MUSIC_ORGANIZATION_GUIDE.md` for:
- Detailed explanations
- Alternative methods (beets, MusicBrainz Picard, Lidarr)
- Advanced configuration
- Troubleshooting guide

