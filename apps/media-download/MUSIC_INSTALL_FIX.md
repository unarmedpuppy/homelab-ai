# Fixing mutagen Installation on macOS

## The Problem

On macOS with Homebrew Python, you may see this error:
```
error: externally-managed-environment
```

This happens because macOS protects the system Python installation.

## Solution

Install mutagen with the `--break-system-packages` flag:

```bash
pip3 install --user --break-system-packages mutagen
```

## Quick Fix

Run the helper script:
```bash
cd apps/media-download
./install_mutagen.sh
```

Or install manually:
```bash
pip3 install --user --break-system-packages mutagen
```

## Verify Installation

After installing, verify it works:
```bash
python3 -c "import mutagen; print('mutagen works!')"
```

## If Installation Still Fails

### Option 1: Use Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install mutagen
# Then run scripts with: python3 organize_music_for_plex.py ...
```

### Option 2: Use pipx
```bash
brew install pipx
pipx install mutagen
```

### Option 3: Install on Server Instead
If local installation is problematic, transfer files to server first and organize there:
```bash
# Transfer files
scp -P 4242 -r /path/to/playlists unarmedpuppy@192.168.86.47:~/playlists

# Organize on server
cd apps/media-download
./organize_on_server.sh ~/playlists
```

## After Installation

Once mutagen is installed, you can run:
```bash
cd apps/media-download
./organize_and_transfer_music.sh /path/to/your/playlist/folders
```

