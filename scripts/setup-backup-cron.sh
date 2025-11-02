#!/bin/bash

# Setup Backup Cron Jobs
# This script sets up automated backup cron jobs based on the backup strategy

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_USER="${SERVER_USER:-unarmedpuppy}"
SERVER_HOST="${SERVER_HOST:-192.168.86.47}"
SERVER_PORT="${SERVER_PORT:-4242}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running on server
if [ -f "/etc/debian_version" ]; then
    IS_REMOTE=false
    BACKUP_SCRIPT="${SCRIPT_DIR}/backup-server.sh"
    CLEANUP_SCRIPT="${SCRIPT_DIR}/cleanup-old-backups.sh"
else
    IS_REMOTE=true
    BACKUP_SCRIPT="~/server/scripts/backup-server.sh"
    CLEANUP_SCRIPT="~/server/scripts/cleanup-old-backups.sh"
fi

log "Setting up backup cron jobs..."

if [ "$IS_REMOTE" = true ]; then
    log "Installing cron jobs on remote server..."
    ssh -p "$SERVER_PORT" "${SERVER_USER}@${SERVER_HOST}" "bash -s" <<'EOF'
# Create cron jobs
CRON_JOBS=(
    "# Daily backup at 2 AM"
    "0 2 * * * BACKUP_DEST=/mnt/server-cloud/backups/daily ~/server/scripts/backup-server.sh >> /var/log/server-backup-daily.log 2>&1"
    ""
    "# Weekly backup on Sunday at 1 AM"
    "0 1 * * 0 BACKUP_DEST=/mnt/server-cloud/backups/weekly ~/server/scripts/backup-server.sh >> /var/log/server-backup-weekly.log 2>&1"
    ""
    "# Monthly backup on 1st at midnight"
    "0 0 1 * * BACKUP_DEST=/mnt/server-cloud/backups/monthly ~/server/scripts/backup-server.sh >> /var/log/server-backup-monthly.log 2>&1"
    ""
    "# Cleanup old backups (runs after daily backup)"
    "30 2 * * * ~/server/scripts/cleanup-old-backups.sh >> /var/log/backup-cleanup.log 2>&1"
    ""
    "# Backup health check"
    "0 3 * * * ~/server/scripts/check-backup-health.sh >> /var/log/backup-health.log 2>&1"
)

# Add to root crontab
(crontab -l 2>/dev/null; printf '%s\n' "${CRON_JOBS[@]}") | sudo crontab -

echo "Cron jobs installed successfully"
EOF
else
    # Running on server directly
    log "Installing cron jobs on local server..."
    
    CRON_JOBS=(
        "# Daily backup at 2 AM"
        "0 2 * * * BACKUP_DEST=/mnt/server-cloud/backups/daily ${BACKUP_SCRIPT} >> /var/log/server-backup-daily.log 2>&1"
        ""
        "# Weekly backup on Sunday at 1 AM"
        "0 1 * * 0 BACKUP_DEST=/mnt/server-cloud/backups/weekly ${BACKUP_SCRIPT} >> /var/log/server-backup-weekly.log 2>&1"
        ""
        "# Monthly backup on 1st at midnight"
        "0 0 1 * * BACKUP_DEST=/mnt/server-cloud/backups/monthly ${BACKUP_SCRIPT} >> /var/log/server-backup-monthly.log 2>&1"
        ""
        "# Cleanup old backups (runs after daily backup)"
        "30 2 * * * ${CLEANUP_SCRIPT} >> /var/log/backup-cleanup.log 2>&1"
        ""
        "# Backup health check"
        "0 3 * * * ${SCRIPT_DIR}/check-backup-health.sh >> /var/log/backup-health.log 2>&1"
    )
    
    # Add to root crontab
    (sudo crontab -l 2>/dev/null; printf '%s\n' "${CRON_JOBS[@]}") | sudo crontab -
    
    log "Cron jobs installed successfully"
fi

log "Backup cron jobs have been set up!"
log ""
log "Scheduled backups:"
log "  - Daily: 2:00 AM (kept for 7 days)"
log "  - Weekly: Sunday 1:00 AM (kept for 4 weeks)"
log "  - Monthly: 1st of month at midnight (kept for 6 months)"
log ""
log "You can view cron jobs with: sudo crontab -l"
log "You can test backup manually with: ${BACKUP_SCRIPT}"

