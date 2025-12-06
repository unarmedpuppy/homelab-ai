#!/bin/bash
# Organize music files and transfer to server
# This script handles both local organization and server transfer

set -e

# Configuration
SOURCE_DIR="${1:-./playlists}"
TARGET_DIR="${2:-/jenquist-cloud/archive/entertainment-media/Music}"
SERVER_USER="unarmedpuppy"
SERVER_HOST="192.168.86.47"
SERVER_PORT="4242"
SERVER_PATH="~/server/apps/media-download"
LOCAL_TEMP_DIR="${TMPDIR:-/tmp}/organized_music_$$"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "============================================================"
echo "Music Organization & Transfer to Server"
echo "============================================================"
echo "Source: $SOURCE_DIR"
echo "Target: $TARGET_DIR (on server)"
echo "Temp directory: $LOCAL_TEMP_DIR"
echo "============================================================"
echo ""

# Check if source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "✗ Source directory not found: $SOURCE_DIR"
    echo "Usage: $0 <source_dir> [target_dir]"
    exit 1
fi

# Check if python3 and mutagen are available
if ! command -v python3 &> /dev/null; then
    echo "✗ python3 not found. Please install Python 3."
    exit 1
fi

echo "[1/4] Installing dependencies (if needed)..."
# Check if mutagen is available
if ! python3 -c "import mutagen" 2>/dev/null; then
    echo "  Installing mutagen..."
    # On macOS with Homebrew Python, need --break-system-packages flag
    # Try with --break-system-packages first (required for externally-managed environments)
    if pip3 install --user --break-system-packages mutagen 2>&1 | grep -qE "(Successfully installed|Requirement already satisfied)"; then
        echo "  ✓ Installed mutagen to user directory"
    # Fallback: try without the flag
    elif pip3 install --user mutagen 2>&1 | grep -qE "(Successfully installed|Requirement already satisfied)"; then
        echo "  ✓ Installed mutagen to user directory"
    else
        echo "  ✗ Could not install mutagen automatically"
        echo ""
        echo "  Please install manually:"
        echo "    pip3 install --user --break-system-packages mutagen"
        echo ""
        echo "  Or run: ./install_mutagen.sh"
        echo ""
        echo "  Then run this script again."
        exit 1
    fi
    
    # Verify installation
    if ! python3 -c "import mutagen" 2>/dev/null; then
        echo "  ⚠ Installation completed but mutagen still not importable"
        echo "  This may be a PATH issue. Trying to continue..."
    fi
fi
echo -e "${GREEN}✓ Dependencies ready${NC}"

echo ""
echo "[2/4] Organizing files locally (dry run first)..."
echo "  Note: Files will be organized to a TEMP directory first, then transferred to server"
echo "  Temp directory: $LOCAL_TEMP_DIR"
echo "  Final destination: $TARGET_DIR (on server)"
echo ""
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Verify mutagen is available
if ! python3 -c "import mutagen" 2>/dev/null; then
    echo "  ✗ mutagen still not available after installation attempt"
    echo "  Please install manually:"
    echo "    pip3 install --user --break-system-packages mutagen"
    echo "  Or run: cd $SCRIPT_DIR && ./install_mutagen.sh"
    exit 1
fi

# Run dry run and show output
python3 "$SCRIPT_DIR/organize_music_for_plex.py" \
    --source "$SOURCE_DIR" \
    --target "$LOCAL_TEMP_DIR" \
    2>&1 | tee /tmp/organize_dryrun.log

DRY_RUN_EXIT_CODE=${PIPESTATUS[0]}
if [ $DRY_RUN_EXIT_CODE -ne 0 ]; then
    echo ""
    echo "  ⚠ Dry run had issues. Check output above or /tmp/organize_dryrun.log"
    echo "  Continuing anyway..."
fi

echo ""
echo "  ℹ The paths shown above are TEMPORARY (local temp directory)"
echo "  After you confirm, files will be transferred to: $TARGET_DIR"

echo ""
read -p "Review the dry run output above. Continue with actual organization? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "[3/4] Organizing files (copying to temp directory)..."
echo "  Organizing to: $LOCAL_TEMP_DIR"
echo "  (These will be transferred to server in next step)"
mkdir -p "$LOCAL_TEMP_DIR"
python3 "$SCRIPT_DIR/organize_music_for_plex.py" \
    --source "$SOURCE_DIR" \
    --target "$LOCAL_TEMP_DIR" \
    --execute

if [ $? -ne 0 ]; then
    echo "✗ Organization failed"
    exit 1
fi

ORGANIZED_COUNT=$(find "$LOCAL_TEMP_DIR" -type f \( -name "*.mp3" -o -name "*.flac" -o -name "*.m4a" \) | wc -l | tr -d ' ')
echo -e "${GREEN}✓ Organized $ORGANIZED_COUNT files to temp directory${NC}"

echo ""
echo "[4/4] Transferring organized files to server..."
echo "  From: $LOCAL_TEMP_DIR (local temp)"
echo "  To:   $TARGET_DIR (on server)"
echo "  This may take a while depending on file sizes..."

# Create target directory on server if it doesn't exist
ssh -p "$SERVER_PORT" "$SERVER_USER@$SERVER_HOST" "mkdir -p '$TARGET_DIR'"

# Transfer files
echo "  Starting transfer..."
rsync -avz --progress -e "ssh -p $SERVER_PORT" \
    "$LOCAL_TEMP_DIR/" \
    "$SERVER_USER@$SERVER_HOST:$TARGET_DIR/"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Transfer complete${NC}"
    
    # Set permissions on server
    echo "  Setting permissions on server..."
    ssh -p "$SERVER_PORT" "$SERVER_USER@$SERVER_HOST" \
        "sudo chown -R 1000:1000 '$TARGET_DIR' && sudo chmod -R 755 '$TARGET_DIR'"
    
    echo ""
    echo "============================================================"
    echo "✓ Complete!"
    echo "============================================================"
    echo "Files transferred to: $TARGET_DIR"
    echo ""
    echo "Next steps:"
    echo "1. Open Plex: https://plex.server.unarmedpuppy.com"
    echo "2. Go to Settings → Library"
    echo "3. Click 'Scan Library Files' for Music library"
    echo "4. Wait for scan to complete"
    echo "5. Create playlists manually or run:"
    echo "   python3 create_plex_playlist.py --mappings playlist_mappings.json"
    echo ""
    echo "Cleaning up temp directory..."
    rm -rf "$LOCAL_TEMP_DIR"
    echo -e "${GREEN}✓ Done!${NC}"
else
    echo "✗ Transfer failed"
    echo "Files are still in: $LOCAL_TEMP_DIR"
    exit 1
fi

