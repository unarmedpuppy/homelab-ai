#!/bin/bash
# Backup ZFS pool to Backblaze B2
# Usage: ./backup-to-b2.sh [--dry-run]

set -e

# Configuration
BUCKET="b2:jenquist-cloud"
SOURCE="/jenquist-cloud/archive"
LOG_DIR="$HOME/server/logs/backups"
LOG_FILE="$LOG_DIR/backup-$(date +%Y%m%d-%H%M%S).log"

# Create log directory
mkdir -p "$LOG_DIR"

# Check if dry run
DRY_RUN=""
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN="--dry-run"
    echo "=== DRY RUN MODE ===" | tee -a "$LOG_FILE"
fi

echo "Starting backup at $(date)" | tee -a "$LOG_FILE"
echo "Source: $SOURCE" | tee -a "$LOG_FILE"
echo "Destination: $BUCKET" | tee -a "$LOG_FILE"
echo "---" | tee -a "$LOG_FILE"

# Run rclone sync
# --transfers 4: Number of parallel transfers
# --checkers 8: Number of parallel checkers
# --progress: Show progress
# --log-file: Log to file
# --log-level INFO: Log level
rclone sync "$SOURCE" "$BUCKET/archive" \
    $DRY_RUN \
    --transfers 4 \
    --checkers 8 \
    --progress \
    --log-file "$LOG_FILE" \
    --log-level INFO \
    --stats 1m \
    --stats-one-line

RESULT=$?

echo "---" | tee -a "$LOG_FILE"
echo "Backup completed at $(date) with exit code $RESULT" | tee -a "$LOG_FILE"

# Keep only last 30 log files
ls -t "$LOG_DIR"/backup-*.log 2>/dev/null | tail -n +31 | xargs -r rm

exit $RESULT
