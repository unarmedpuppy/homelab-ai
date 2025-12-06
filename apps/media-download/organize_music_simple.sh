#!/bin/bash
# Simple script to organize music files for Plex
# This is a basic version that uses existing metadata

set -e

SOURCE_DIR="${1:-./playlists}"
TARGET_DIR="${2:-/jenquist-cloud/archive/entertainment-media/Music}"
DRY_RUN="${3:-true}"

echo "============================================================"
echo "Simple Music Organization for Plex"
echo "============================================================"
echo "Source: $SOURCE_DIR"
echo "Target: $TARGET_DIR"
echo "Mode: $([ "$DRY_RUN" = "true" ] && echo "DRY RUN" || echo "LIVE")"
echo "============================================================"

# Check if mutagen is available (for metadata extraction)
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found"
    exit 1
fi

# Check if mutagen is installed
if ! python3 -c "import mutagen" 2>/dev/null; then
    echo "Installing mutagen..."
    pip3 install --user mutagen
fi

# Run the Python organizer
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/organize_music_for_plex.py" \
    --source "$SOURCE_DIR" \
    --target "$TARGET_DIR" \
    $([ "$DRY_RUN" = "true" ] && echo "" || echo "--execute")

echo ""
echo "Done! Next steps:"
echo "1. Review the organized files"
echo "2. If satisfied, run again with DRY_RUN=false to actually move files"
echo "3. Trigger Plex library scan"
echo "4. Create playlists in Plex (manually or using create_plex_playlist.py)"

