#!/bin/bash

# Cleanup Old Backups Script
# Removes old backups based on retention policy

set -euo pipefail

BACKUP_BASE="/mnt/server-cloud/backups"

# Retention periods (in days)
DAILY_RETENTION=7
WEEKLY_RETENTION=28
MONTHLY_RETENTION=180

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Cleanup daily backups
if [ -d "${BACKUP_BASE}/daily" ]; then
    log "Cleaning up daily backups older than ${DAILY_RETENTION} days..."
    find "${BACKUP_BASE}/daily" -maxdepth 1 -type d -name "server-backup-*" -mtime +${DAILY_RETENTION} -exec rm -rf {} \;
fi

# Cleanup weekly backups
if [ -d "${BACKUP_BASE}/weekly" ]; then
    log "Cleaning up weekly backups older than ${WEEKLY_RETENTION} days..."
    find "${BACKUP_BASE}/weekly" -maxdepth 1 -type d -name "server-backup-*" -mtime +${WEEKLY_RETENTION} -exec rm -rf {} \;
fi

# Cleanup monthly backups
if [ -d "${BACKUP_BASE}/monthly" ]; then
    log "Cleaning up monthly backups older than ${MONTHLY_RETENTION} days..."
    find "${BACKUP_BASE}/monthly" -maxdepth 1 -type d -name "server-backup-*" -mtime +${MONTHLY_RETENTION} -exec rm -rf {} \;
fi

log "Backup cleanup completed"

