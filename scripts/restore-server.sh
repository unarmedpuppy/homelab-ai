#!/bin/bash

# Home Server Restore Script
# This script restores from backups created by backup-server.sh

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_USER="${SERVER_USER:-unarmedpuppy}"
SERVER_HOST="${SERVER_HOST:-192.168.86.47}"
SERVER_PORT="${SERVER_PORT:-4242}"

# Restore source - can be overridden
RESTORE_SOURCE="${RESTORE_SOURCE:-/mnt/server-cloud/backups/latest}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to run commands on remote server
run_remote() {
    ssh -p "$SERVER_PORT" "${SERVER_USER}@${SERVER_HOST}" "$@"
}

# Function to copy files to remote server
copy_to_remote() {
    scp -P "$SERVER_PORT" -r "$1" "${SERVER_USER}@${SERVER_HOST}:$2"
}

# Check if running locally or remotely
if ssh -p "$SERVER_PORT" -o ConnectTimeout=5 -o BatchMode=yes "${SERVER_USER}@${SERVER_HOST}" "echo test" >/dev/null 2>&1; then
    IS_REMOTE=true
    SERVER_HOME="/home/${SERVER_USER}"
else
    if [ -f "/etc/debian_version" ]; then
        IS_REMOTE=false
        SERVER_HOME="$HOME"
    else
        error "Cannot connect to server. Please check SSH configuration."
    fi
fi

# Verify backup source exists
if [ "$IS_REMOTE" = true ]; then
    if ! run_remote "[ -d ${RESTORE_SOURCE} ]"; then
        error "Backup source not found: ${RESTORE_SOURCE}"
    fi
else
    if [ ! -d "$RESTORE_SOURCE" ]; then
        error "Backup source not found: ${RESTORE_SOURCE}"
    fi
fi

log "Starting restore from: ${RESTORE_SOURCE}"
warning "This will overwrite existing data. Are you sure? (yes/no)"
read -r CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    log "Restore cancelled."
    exit 0
fi

# Menu for selective restore
cat <<EOF

What would you like to restore?

1. Docker Volumes (all)
2. Docker Configurations
3. System Configurations (/etc)
4. Home Directory Configs
5. Cron Jobs
6. Everything (full restore)

Enter selection (1-6):
EOF
read -r SELECTION

restore_docker_volumes() {
    log "Restoring Docker volumes..."
    if [ "$IS_REMOTE" = true ]; then
        VOLUME_FILES=$(run_remote "ls ${RESTORE_SOURCE}/docker-volumes/*.tar.gz 2>/dev/null || true")
    else
        VOLUME_FILES=$(ls "${RESTORE_SOURCE}"/docker-volumes/*.tar.gz 2>/dev/null || true)
    fi
    
    if [ -z "$VOLUME_FILES" ]; then
        warning "No volume backups found"
        return
    fi
    
    for vol_file in $VOLUME_FILES; do
        # Extract volume name from filename
        vol_name=$(basename "$vol_file" .tar.gz)
        log "  Restoring volume: $vol_name"
        
        if [ "$IS_REMOTE" = true ]; then
            run_remote "docker volume create $vol_name || true"
            run_remote "docker run --rm -v ${vol_name}:/data -v ${RESTORE_SOURCE}/docker-volumes:/backup alpine sh -c 'cd /data && tar xzf /backup/$(basename $vol_file)'"
        else
            docker volume create "$vol_name" || true
            docker run --rm \
                -v "${vol_name}:/data" \
                -v "${RESTORE_SOURCE}/docker-volumes:/backup" \
                alpine sh -c "cd /data && tar xzf /backup/$(basename "$vol_file")"
        fi
    done
    log "Docker volumes restored"
}

restore_docker_configs() {
    log "Restoring Docker configurations..."
    if [ "$IS_REMOTE" = true ]; then
        run_remote "cd ${SERVER_HOME}/server/apps && tar xzf ${RESTORE_SOURCE}/docker-configs/docker-compose-configs.tar.gz"
        if run_remote "[ -f ${RESTORE_SOURCE}/docker-configs/traefik-config.tar.gz ]"; then
            run_remote "cd ${SERVER_HOME}/server/apps/traefik && tar xzf ${RESTORE_SOURCE}/docker-configs/traefik-config.tar.gz"
        fi
    else
        cd "${SERVER_HOME}/server/apps" && tar xzf "${RESTORE_SOURCE}/docker-configs/docker-compose-configs.tar.gz"
        if [ -f "${RESTORE_SOURCE}/docker-configs/traefik-config.tar.gz" ]; then
            cd "${SERVER_HOME}/server/apps/traefik" && tar xzf "${RESTORE_SOURCE}/docker-configs/traefik-config.tar.gz"
        fi
    fi
    log "Docker configurations restored"
}

restore_system_configs() {
    log "Restoring system configurations..."
    warning "Restoring /etc will require sudo and may affect system configuration."
    log "Backing up current /etc first..."
    
    if [ "$IS_REMOTE" = true ]; then
        run_remote "sudo cp -r /etc /etc.backup.\$(date +%Y%m%d_%H%M%S)"
        run_remote "cd / && sudo tar xzf ${RESTORE_SOURCE}/system-configs/etc-backup.tar.gz"
    else
        sudo cp -r /etc "/etc.backup.$(date +%Y%m%d_%H%M%S)"
        cd / && sudo tar xzf "${RESTORE_SOURCE}/system-configs/etc-backup.tar.gz"
    fi
    
    log "System configurations restored. You may need to reboot for changes to take effect."
}

restore_home_configs() {
    log "Restoring home directory configurations..."
    if [ "$IS_REMOTE" = true ]; then
        run_remote "cd ${SERVER_HOME} && tar xzf ${RESTORE_SOURCE}/home-configs/home-config.tar.gz"
    else
        cd "$SERVER_HOME" && tar xzf "${RESTORE_SOURCE}/home-configs/home-config.tar.gz"
    fi
    log "Home directory configurations restored"
}

restore_cron_jobs() {
    log "Restoring cron jobs..."
    if [ "$IS_REMOTE" = true ]; then
        if run_remote "[ -f ${RESTORE_SOURCE}/cron-jobs/user-crontab.txt ]"; then
            run_remote "crontab ${RESTORE_SOURCE}/cron-jobs/user-crontab.txt"
        fi
        if run_remote "[ -f ${RESTORE_SOURCE}/cron-jobs/root-crontab.txt ]"; then
            run_remote "sudo crontab ${RESTORE_SOURCE}/cron-jobs/root-crontab.txt"
        fi
        if run_remote "[ -f ${RESTORE_SOURCE}/cron-jobs/system-cron.tar.gz ]"; then
            run_remote "cd / && sudo tar xzf ${RESTORE_SOURCE}/cron-jobs/system-cron.tar.gz"
        fi
    else
        if [ -f "${RESTORE_SOURCE}/cron-jobs/user-crontab.txt" ]; then
            crontab "${RESTORE_SOURCE}/cron-jobs/user-crontab.txt"
        fi
        if [ -f "${RESTORE_SOURCE}/cron-jobs/root-crontab.txt" ]; then
            sudo crontab "${RESTORE_SOURCE}/cron-jobs/root-crontab.txt"
        fi
        if [ -f "${RESTORE_SOURCE}/cron-jobs/system-cron.tar.gz" ]; then
            cd / && sudo tar xzf "${RESTORE_SOURCE}/cron-jobs/system-cron.tar.gz"
        fi
    fi
    log "Cron jobs restored"
}

case "$SELECTION" in
    1)
        restore_docker_volumes
        ;;
    2)
        restore_docker_configs
        ;;
    3)
        restore_system_configs
        ;;
    4)
        restore_home_configs
        ;;
    5)
        restore_cron_jobs
        ;;
    6)
        log "Performing full restore..."
        restore_docker_volumes
        restore_docker_configs
        restore_home_configs
        restore_cron_jobs
        warning "System configs (/etc) restored separately. Run option 3 if needed."
        ;;
    *)
        error "Invalid selection"
        ;;
esac

log "Restore completed!"
log "If you restored Docker volumes, you may want to restart containers:"
log "  cd ~/server/scripts && ./docker-restart.sh"

