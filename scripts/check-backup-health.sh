#!/bin/bash

# Backup Health Check Script
# Checks if backups are running successfully and alerts on failures

set -euo pipefail

BACKUP_BASE="/mnt/server-cloud/backups"
MAX_AGE_HOURS=25  # Alert if backup is older than this

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

error() {
    echo "[ERROR] $1" >&2
    exit 1
}

warning() {
    echo "[WARNING] $1" >&2
}

# Check daily backup
if [ -d "${BACKUP_BASE}/daily/latest" ]; then
    BACKUP_AGE=$(( ($(date +%s) - $(stat -c %Y "${BACKUP_BASE}/daily/latest")) / 3600 ))
    
    if [ $BACKUP_AGE -gt $MAX_AGE_HOURS ]; then
        error "Daily backup is ${BACKUP_AGE} hours old (threshold: ${MAX_AGE_HOURS} hours)"
    else
        log "Daily backup is healthy (${BACKUP_AGE} hours old)"
    fi
else
    error "Daily backup directory not found: ${BACKUP_BASE}/daily/latest"
fi

# Check if backup is empty
if [ ! -d "${BACKUP_BASE}/daily/latest/docker-volumes" ] || [ -z "$(ls -A "${BACKUP_BASE}/daily/latest/docker-volumes" 2>/dev/null)" ]; then
    error "Daily backup appears to be empty"
fi

# Check disk space on backup drive
DISK_USAGE=$(df -h "${BACKUP_BASE}" | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    warning "Backup drive is ${DISK_USAGE}% full. Consider cleaning up old backups."
elif [ "$DISK_USAGE" -gt 95 ]; then
    error "Backup drive is ${DISK_USAGE}% full. Immediate action required!"
fi

log "Backup health check passed"

