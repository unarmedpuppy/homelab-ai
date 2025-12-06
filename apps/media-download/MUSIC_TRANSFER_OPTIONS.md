# Music Transfer Options

## Overview

You have two main approaches for getting your music files organized and onto the server:

1. **Organize locally, then transfer** (Recommended)
2. **Transfer first, then organize on server**

## Option 1: Organize Locally, Then Transfer (Recommended)

**Best for**: When you want to preview organization before transferring

### Automated Script

Use the `organize_and_transfer_music.sh` script:

```bash
cd apps/media-download
chmod +x organize_and_transfer_music.sh

# Run the script
./organize_and_transfer_music.sh /path/to/your/playlist/folders
```

**What it does:**
1. Organizes files locally into temp directory
2. Shows you a preview (dry run)
3. Asks for confirmation
4. Organizes files
5. Transfers organized files to server via rsync
6. Sets correct permissions on server
7. Cleans up temp files

**Pros:**
- Preview before transferring
- Faster (organize locally, then one transfer)
- Cleaner (only organized files on server)
- Can review before committing

**Cons:**
- Requires local Python/mutagen
- Uses local disk space temporarily

### Manual Steps

If you prefer manual control:

```bash
# 1. Organize locally
cd apps/media-download
python3 organize_music_for_plex.py \
  --source /path/to/playlist/folders \
  --target /tmp/organized_music \
  --execute

# 2. Review organized files
ls -R /tmp/organized_music

# 3. Transfer to server
rsync -avz -e "ssh -p 4242" \
  /tmp/organized_music/ \
  unarmedpuppy@192.168.86.47:/jenquist-cloud/archive/entertainment-media/Music/

# 4. Set permissions
ssh -p 4242 unarmedpuppy@192.168.86.47 \
  "sudo chown -R 1000:1000 /jenquist-cloud/archive/entertainment-media/Music && \
   sudo chmod -R 755 /jenquist-cloud/archive/entertainment-media/Music"

# 5. Clean up
rm -rf /tmp/organized_music
```

## Option 2: Transfer First, Then Organize on Server

**Best for**: When you want to keep everything on the server

### Automated Script

Use the `organize_on_server.sh` script:

```bash
cd apps/media-download
chmod +x organize_on_server.sh

# First, transfer unorganized files
scp -P 4242 -r /path/to/playlist/folders \
  unarmedpuppy@192.168.86.47:~/playlists

# Then organize on server
./organize_on_server.sh ~/playlists
```

**What it does:**
1. Checks that files exist on server
2. Installs dependencies on server
3. Runs dry run
4. Asks for confirmation
5. Organizes files directly on server

**Pros:**
- Everything stays on server
- No local disk space needed
- Can organize multiple times

**Cons:**
- Slower (transfer unorganized files first)
- Less preview capability
- Requires server to have Python/mutagen

### Manual Steps

```bash
# 1. Transfer unorganized files to server
scp -P 4242 -r /path/to/playlist/folders \
  unarmedpuppy@192.168.86.47:~/playlists

# 2. Organize on server
bash scripts/connect-server.sh \
  "cd ~/server/apps/media-download && \
   python3 organize_music_for_plex.py \
   --source ~/playlists \
   --target /jenquist-cloud/archive/entertainment-media/Music \
   --execute"

# 3. Set permissions
bash scripts/connect-server.sh \
  "sudo chown -R 1000:1000 /jenquist-cloud/archive/entertainment-media/Music && \
   sudo chmod -R 755 /jenquist-cloud/archive/entertainment-media/Music"
```

## Comparison

| Method | Speed | Preview | Disk Space | Complexity |
|--------|-------|---------|------------|------------|
| **Organize & Transfer** | Fast | Yes | Local temp | Easy |
| **Transfer & Organize** | Slower | Limited | Server only | Medium |

## Recommendation

**Use Option 1 (Organize & Transfer)** because:
- You can preview the organization before committing
- Faster overall (one organized transfer vs. unorganized + organize)
- Cleaner result (only organized files on server)
- Easier to troubleshoot locally

## Quick Start (Recommended)

```bash
cd apps/media-download
chmod +x organize_and_transfer_music.sh
./organize_and_transfer_music.sh /path/to/your/playlist/folders
```

That's it! The script handles everything.

## After Transfer

Regardless of which method you use:

1. **Scan Plex Library**
   - Open Plex: https://plex.server.unarmedpuppy.com
   - Settings → Library → Scan Library Files

2. **Create Playlists**
   - Manual: Select tracks in Plex → Add to Playlist
   - Automated: Use `create_plex_playlist.py` (if playlist_mappings.json was created)

## Troubleshooting

### "Permission denied" during transfer
```bash
# Set permissions on server
ssh -p 4242 unarmedpuppy@192.168.86.47 \
  "sudo chown -R 1000:1000 /jenquist-cloud/archive/entertainment-media/Music"
```

### "Connection refused" or SSH issues
- Check server is accessible: `ping 192.168.86.47`
- Verify SSH port: `ssh -p 4242 unarmedpuppy@192.168.86.47 "echo 'Connected'"`

### Files not showing in Plex
- Check file permissions (see above)
- Verify directory structure: `Artist/Album/Track.mp3`
- Trigger manual scan in Plex

### Large file transfers taking too long
- Use `rsync` with progress: `rsync -avz --progress -e "ssh -p 4242" ...`
- Or transfer in batches by playlist folder

