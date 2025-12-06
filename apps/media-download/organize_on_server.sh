#!/bin/bash
# Organize music files directly on the server
# Use this if you've already transferred unorganized files to the server

set -e

# Configuration
SOURCE_DIR="${1:-~/playlists}"
TARGET_DIR="${2:-/jenquist-cloud/archive/entertainment-media/Music}"
SERVER_USER="unarmedpuppy"
SERVER_HOST="192.168.86.47"
SERVER_PORT="4242"
SERVER_SCRIPT_PATH="~/server/apps/media-download"

echo "============================================================"
echo "Organize Music on Server"
echo "============================================================"
echo "Source: $SOURCE_DIR (on server)"
echo "Target: $TARGET_DIR (on server)"
echo "============================================================"
echo ""

# Check if source directory exists on server
if ! ssh -p "$SERVER_PORT" "$SERVER_USER@$SERVER_HOST" "[ -d '$SOURCE_DIR' ]"; then
    echo "✗ Source directory not found on server: $SOURCE_DIR"
    echo ""
    echo "First, transfer your playlist folders to the server:"
    echo "  scp -P $SERVER_PORT -r /path/to/playlists $SERVER_USER@$SERVER_HOST:~/"
    exit 1
fi

echo "[1/3] Installing dependencies on server..."
ssh -p "$SERVER_PORT" "$SERVER_USER@$SERVER_HOST" \
    "pip3 install --user mutagen 2>&1 || sudo pip3 install mutagen"

echo ""
echo "[2/3] Running dry run on server..."
ssh -p "$SERVER_PORT" "$SERVER_USER@$SERVER_HOST" \
    "cd $SERVER_SCRIPT_PATH && python3 organize_music_for_plex.py --source '$SOURCE_DIR' --target '$TARGET_DIR'" \
    | head -100

echo ""
read -p "Review the dry run output above. Continue with actual organization? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "[3/3] Organizing files on server..."
ssh -p "$SERVER_PORT" "$SERVER_USER@$SERVER_HOST" \
    "cd $SERVER_SCRIPT_PATH && python3 organize_music_for_plex.py --source '$SOURCE_DIR' --target '$TARGET_DIR' --execute --copy"

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "✓ Complete!"
    echo "============================================================"
    echo "Files organized in: $TARGET_DIR"
    echo ""
    echo "Next steps:"
    echo "1. Open Plex: https://plex.server.unarmedpuppy.com"
    echo "2. Go to Settings → Library"
    echo "3. Click 'Scan Library Files' for Music library"
    echo "4. Wait for scan to complete"
    echo "5. Create playlists manually or run:"
    echo "   bash scripts/connect-server.sh 'cd ~/server/apps/media-download && python3 create_plex_playlist.py --mappings playlist_mappings.json'"
else
    echo "✗ Organization failed"
    exit 1
fi

