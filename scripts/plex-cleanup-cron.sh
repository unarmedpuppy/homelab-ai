#!/bin/bash
# Plex Cleanup Cron Wrapper
# Runs plex-cleanup.py with proper environment and logging
# Scheduled: Daily at 3 AM CST

set -e

# Configuration
SCRIPT_DIR="$(dirname "$0")"
CLEANUP_SCRIPT="${SCRIPT_DIR}/plex-cleanup.py"
LOG_DIR="${HOME}/server/logs"
LOG_FILE="${LOG_DIR}/plex-cleanup.log"
LOCK_FILE="/tmp/plex-cleanup.lock"

# Plex credentials (sourced from bashrc or set here)
export PLEX_URL="${PLEX_URL:-http://localhost:32400}"
export PLEX_TOKEN="${PLEX_TOKEN:-KFm75bzkfZB1cWCRifK7}"

# Sonarr connection (uses default localhost:8989, reads API key from config)
export SONARR_URL="${SONARR_URL:-http://localhost:8989}"

# Ensure log directory exists
mkdir -p "${LOG_DIR}"

# Prevent concurrent runs
if [ -f "${LOCK_FILE}" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cleanup already running, skipping" >> "${LOG_FILE}"
    exit 0
fi
trap "rm -f ${LOCK_FILE}" EXIT
touch "${LOCK_FILE}"

# Run cleanup
echo "" >> "${LOG_FILE}"
echo "========================================" >> "${LOG_FILE}"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting scheduled cleanup" >> "${LOG_FILE}"
echo "========================================" >> "${LOG_FILE}"

python3 "${CLEANUP_SCRIPT}" --run >> "${LOG_FILE}" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cleanup completed" >> "${LOG_FILE}"
