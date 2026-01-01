#!/bin/bash
# Bird Bookmark Processor Cron Wrapper
# Fetches X/Twitter bookmarks and likes, stores in database
# Recommended: Every 6 hours
# Cron: 0 */6 * * * ~/server/scripts/bird-cron.sh

set -e

# Configuration
SCRIPT_DIR="$(dirname "$0")"
BIRD_APP_DIR="${HOME}/server/apps/bird"
LOG_DIR="${HOME}/server/logs"
LOG_FILE="${LOG_DIR}/bird.log"
LOCK_FILE="/tmp/bird-processor.lock"

# Ensure log directory exists
mkdir -p "${LOG_DIR}"

# Prevent concurrent runs
if [ -f "${LOCK_FILE}" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Bird processor already running, skipping" >> "${LOG_FILE}"
    exit 0
fi
trap "rm -f ${LOCK_FILE}" EXIT
touch "${LOCK_FILE}"

# Run processor
echo "" >> "${LOG_FILE}"
echo "========================================" >> "${LOG_FILE}"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting scheduled bird processing" >> "${LOG_FILE}"
echo "========================================" >> "${LOG_FILE}"

cd "${BIRD_APP_DIR}"
docker compose run --rm bird python process_bookmarks.py >> "${LOG_FILE}" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Bird processing completed" >> "${LOG_FILE}"
