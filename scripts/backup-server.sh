#!/bin/bash

# Comprehensive Home Server Backup Script
# This script backs up:
# - All Docker volumes
# - All docker-compose.yml files and configurations
# - System configurations (/etc)
# - User home directory configurations
# - Cron jobs
# - Mount point information
# - System package lists

set -euo pipefail

# Configuration
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_USER="${SERVER_USER:-unarmedpuppy}"
SERVER_HOST="${SERVER_HOST:-192.168.86.47}"
SERVER_PORT="${SERVER_PORT:-4242}"

# Backup destination - can be overridden via environment variable
BACKUP_DEST="${BACKUP_DEST:-/mnt/server-cloud/backups}"
BACKUP_BASE_DIR="${BACKUP_DEST}/server-backup-${BACKUP_DATE}"

# Logging
LOG_FILE="${BACKUP_BASE_DIR}/backup.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Function to run commands on remote server
run_remote() {
    ssh -p "$SERVER_PORT" "${SERVER_USER}@${SERVER_HOST}" "$@"
}

# Function to copy files from remote server
copy_from_remote() {
    scp -P "$SERVER_PORT" -r "${SERVER_USER}@${SERVER_HOST}:$1" "$2"
}

# Check if running locally or remotely
# If we can't connect via SSH, assume we're on the server
if ssh -p "$SERVER_PORT" -o ConnectTimeout=5 -o BatchMode=yes "${SERVER_USER}@${SERVER_HOST}" "echo test" >/dev/null 2>&1 || [ -f "/etc/debian_version" ]; then
    if [ -f "/etc/debian_version" ]; then
        # Running on the server itself
        IS_REMOTE=false
        SERVER_HOME="$HOME"
    else
        # Can SSH, running from local machine
        IS_REMOTE=true
        SERVER_HOME="/home/${SERVER_USER}"
    fi
else
    # Can't SSH but not on server - assume local mode
    IS_REMOTE=false
    SERVER_HOME="$HOME"
fi

# Create backup directory structure
if [ "$IS_REMOTE" = true ]; then
    # Create backup directory on server first
    run_remote "mkdir -p ${BACKUP_BASE_DIR}/{docker-volumes,docker-configs,system-configs,home-configs,cron-jobs,logs,mount-info,package-lists}"
else
    mkdir -p "${BACKUP_BASE_DIR}"/{docker-volumes,docker-configs,system-configs,home-configs,cron-jobs,logs,mount-info,package-lists}
fi

log "Starting comprehensive backup of home server..."
log "Backup destination: ${BACKUP_BASE_DIR}"

# 1. Backup all Docker volumes
log "Backing up Docker volumes..."
if [ "$IS_REMOTE" = true ]; then
    # Get list of volumes from remote
    VOLUMES=$(run_remote "docker volume ls -q")
    
    for volume in $VOLUMES; do
        log "  Backing up volume: $volume"
        
        # Create a temporary container to backup the volume
        # Sanitize volume name for filename (replace / with _)
        run_remote "docker run --rm -v ${volume}:/data -v ${BACKUP_BASE_DIR}/docker-volumes:/backup alpine sh -c 'cd /data && tar czf /backup/\$(echo ${volume} | tr / _).tar.gz .'" || warning "Failed to backup volume: $volume"
    done
else
    VOLUMES=$(docker volume ls -q)
    
    for volume in $VOLUMES; do
        log "  Backing up volume: $volume"
        # Sanitize volume name for filename (replace / with _)
        safe_name=$(echo "$volume" | tr '/' '_')
        docker run --rm \
            -v "${volume}:/data" \
            -v "${BACKUP_BASE_DIR}/docker-volumes:/backup" \
            alpine sh -c "cd /data && tar czf /backup/${safe_name}.tar.gz ." || warning "Failed to backup volume: $volume"
    done
fi

log "Docker volumes backed up: $(echo $VOLUMES | wc -w) volumes"

# 2. Backup all docker-compose.yml files and app configurations
log "Backing up Docker Compose configurations..."
if [ "$IS_REMOTE" = true ]; then
    run_remote "tar czf ${BACKUP_BASE_DIR}/docker-configs/docker-compose-configs.tar.gz -C ${SERVER_HOME}/server/apps ." || warning "Failed to backup docker-compose configs"
    
    # Also backup traefik config
    run_remote "if [ -d ${SERVER_HOME}/server/apps/traefik ]; then tar czf ${BACKUP_BASE_DIR}/docker-configs/traefik-config.tar.gz -C ${SERVER_HOME}/server/apps/traefik .; fi" || warning "Failed to backup traefik config"
else
    tar czf "${BACKUP_BASE_DIR}/docker-configs/docker-compose-configs.tar.gz" -C "${SERVER_HOME}/server/apps" . || warning "Failed to backup docker-compose configs"
    
    if [ -d "${SERVER_HOME}/server/apps/traefik" ]; then
        tar czf "${BACKUP_BASE_DIR}/docker-configs/traefik-config.tar.gz" -C "${SERVER_HOME}/server/apps/traefik" . || warning "Failed to backup traefik config"
    fi
fi

# 3. Backup system configurations
log "Backing up system configurations (/etc)..."
if [ "$IS_REMOTE" = true ]; then
    # Backup /etc excluding some large/unnecessary directories
    run_remote "sudo tar czf ${BACKUP_BASE_DIR}/system-configs/etc-backup.tar.gz \
        --exclude=/etc/ssl/certs \
        --exclude=/etc/ld.so.cache \
        --exclude=/etc/systemd/system/multi-user.target.wants \
        -C / etc" || warning "Failed to backup /etc"
else
    sudo tar czf "${BACKUP_BASE_DIR}/system-configs/etc-backup.tar.gz" \
        --exclude=/etc/ssl/certs \
        --exclude=/etc/ld.so.cache \
        --exclude=/etc/systemd/system/multi-user.target.wants \
        -C / etc || warning "Failed to backup /etc"
fi

# 4. Backup home directory configurations
log "Backing up home directory configurations..."
if [ "$IS_REMOTE" = true ]; then
    run_remote "tar czf ${BACKUP_BASE_DIR}/home-configs/home-config.tar.gz \
        -C ${SERVER_HOME} \
        .bashrc .bash_history .profile .ssh .gitconfig \
        .config .local .vimrc .zshrc 2>/dev/null || true" || warning "Failed to backup home configs"
else
    tar czf "${BACKUP_BASE_DIR}/home-configs/home-config.tar.gz" \
        -C "${SERVER_HOME}" \
        .bashrc .bash_history .profile .ssh .gitconfig \
        .config .local .vimrc .zshrc 2>/dev/null || true || warning "Failed to backup home configs"
fi

# 5. Backup cron jobs
log "Backing up cron jobs..."
if [ "$IS_REMOTE" = true ]; then
    run_remote "crontab -l > ${BACKUP_BASE_DIR}/cron-jobs/user-crontab.txt 2>/dev/null || echo '# No user crontab' > ${BACKUP_BASE_DIR}/cron-jobs/user-crontab.txt"
    run_remote "sudo crontab -l > ${BACKUP_BASE_DIR}/cron-jobs/root-crontab.txt 2>/dev/null || echo '# No root crontab' > ${BACKUP_BASE_DIR}/cron-jobs/root-crontab.txt"
    
    # Also backup system cron directories
    run_remote "sudo tar czf ${BACKUP_BASE_DIR}/cron-jobs/system-cron.tar.gz -C / etc/cron.d etc/cron.daily etc/cron.hourly etc/cron.monthly etc/cron.weekly 2>/dev/null || true"
else
    crontab -l > "${BACKUP_BASE_DIR}/cron-jobs/user-crontab.txt" 2>/dev/null || echo "# No user crontab" > "${BACKUP_BASE_DIR}/cron-jobs/user-crontab.txt"
    sudo crontab -l > "${BACKUP_BASE_DIR}/cron-jobs/root-crontab.txt" 2>/dev/null || echo "# No root crontab" > "${BACKUP_BASE_DIR}/cron-jobs/root-crontab.txt"
    
    sudo tar czf "${BACKUP_BASE_DIR}/cron-jobs/system-cron.tar.gz" -C / etc/cron.d etc/cron.daily etc/cron.hourly etc/cron.monthly etc/cron.weekly 2>/dev/null || true
fi

# 6. Backup mount point information
log "Backing up mount point information..."
if [ "$IS_REMOTE" = true ]; then
    run_remote "df -h > ${BACKUP_BASE_DIR}/mount-info/df-output.txt"
    run_remote "mount > ${BACKUP_BASE_DIR}/mount-info/mount-output.txt"
    run_remote "cat /etc/fstab > ${BACKUP_BASE_DIR}/mount-info/fstab.txt"
    run_remote "sudo blkid > ${BACKUP_BASE_DIR}/mount-info/blkid.txt"
    run_remote "lsblk > ${BACKUP_BASE_DIR}/mount-info/lsblk.txt"
    
    # Backup ZFS configuration if exists
    run_remote "sudo zpool list > ${BACKUP_BASE_DIR}/mount-info/zpool-list.txt 2>/dev/null || true"
    run_remote "sudo zfs list > ${BACKUP_BASE_DIR}/mount-info/zfs-list.txt 2>/dev/null || true"
else
    df -h > "${BACKUP_BASE_DIR}/mount-info/df-output.txt"
    mount > "${BACKUP_BASE_DIR}/mount-info/mount-output.txt"
    cat /etc/fstab > "${BACKUP_BASE_DIR}/mount-info/fstab.txt"
    sudo blkid > "${BACKUP_BASE_DIR}/mount-info/blkid.txt"
    lsblk > "${BACKUP_BASE_DIR}/mount-info/lsblk.txt"
    
    sudo zpool list > "${BACKUP_BASE_DIR}/mount-info/zpool-list.txt" 2>/dev/null || true
    sudo zfs list > "${BACKUP_BASE_DIR}/mount-info/zfs-list.txt" 2>/dev/null || true
fi

# 7. Backup package lists
log "Backing up package lists..."
if [ "$IS_REMOTE" = true ]; then
    run_remote "dpkg --get-selections > ${BACKUP_BASE_DIR}/package-lists/dpkg-selections.txt"
    run_remote "apt list --installed > ${BACKUP_BASE_DIR}/package-lists/apt-installed.txt 2>/dev/null || true"
    run_remote "snap list > ${BACKUP_BASE_DIR}/package-lists/snap-list.txt 2>/dev/null || true"
else
    dpkg --get-selections > "${BACKUP_BASE_DIR}/package-lists/dpkg-selections.txt"
    apt list --installed > "${BACKUP_BASE_DIR}/package-lists/apt-installed.txt" 2>/dev/null || true
    snap list > "${BACKUP_BASE_DIR}/package-lists/snap-list.txt" 2>/dev/null || true
fi

# 8. Backup Docker system information
log "Backing up Docker system information..."
if [ "$IS_REMOTE" = true ]; then
    run_remote "docker ps -a > ${BACKUP_BASE_DIR}/docker-configs/docker-containers.txt"
    run_remote "docker images > ${BACKUP_BASE_DIR}/docker-configs/docker-images.txt"
    run_remote "docker network ls > ${BACKUP_BASE_DIR}/docker-configs/docker-networks.txt"
    run_remote "docker volume ls > ${BACKUP_BASE_DIR}/docker-configs/docker-volumes-list.txt"
else
    docker ps -a > "${BACKUP_BASE_DIR}/docker-configs/docker-containers.txt"
    docker images > "${BACKUP_BASE_DIR}/docker-configs/docker-images.txt"
    docker network ls > "${BACKUP_BASE_DIR}/docker-configs/docker-networks.txt"
    docker volume ls > "${BACKUP_BASE_DIR}/docker-configs/docker-volumes-list.txt"
fi

# 9. Create backup manifest
log "Creating backup manifest..."
MANIFEST_FILE="${BACKUP_BASE_DIR}/backup-manifest.txt"
if [ "$IS_REMOTE" = true ]; then
    run_remote "cat > ${MANIFEST_FILE} <<EOF
Backup Date: ${BACKUP_DATE}
Server Host: ${SERVER_HOST}
Backup Type: Comprehensive Server Backup

Contents:
- Docker Volumes: $(echo $VOLUMES | wc -w) volumes
- Docker Configs: All docker-compose.yml files and app configs
- System Configs: /etc directory
- Home Configs: User home directory dotfiles
- Cron Jobs: User and root crontabs, system cron directories
- Mount Info: fstab, mount points, disk information
- Package Lists: Installed packages list
- Docker Info: Container, image, network, and volume lists

Backup Location: ${BACKUP_BASE_DIR}
EOF"
else
    cat > "${MANIFEST_FILE}" <<EOF
Backup Date: ${BACKUP_DATE}
Server Host: $(hostname)
Backup Type: Comprehensive Server Backup

Contents:
- Docker Volumes: $(echo $VOLUMES | wc -w) volumes
- Docker Configs: All docker-compose.yml files and app configs
- System Configs: /etc directory
- Home Configs: User home directory dotfiles
- Cron Jobs: User and root crontabs, system cron directories
- Mount Info: fstab, mount points, disk information
- Package Lists: Installed packages list
- Docker Info: Container, image, network, and volume lists

Backup Location: ${BACKUP_BASE_DIR}
EOF
fi

# 10. Calculate backup size
log "Calculating backup size..."
if [ "$IS_REMOTE" = true ]; then
    BACKUP_SIZE=$(run_remote "du -sh ${BACKUP_BASE_DIR} | cut -f1")
else
    BACKUP_SIZE=$(du -sh "${BACKUP_BASE_DIR}" | cut -f1)
fi

log "Backup completed successfully!"
log "Backup size: ${BACKUP_SIZE}"
log "Backup location: ${BACKUP_BASE_DIR}"
log "Log file: ${LOG_FILE}"

# Create symlink to latest backup
if [ "$IS_REMOTE" = true ]; then
    run_remote "ln -sfn server-backup-${BACKUP_DATE} ${BACKUP_DEST}/latest"
else
    ln -sfn "server-backup-${BACKUP_DATE}" "${BACKUP_DEST}/latest"
fi

# If running remotely, optionally copy to local machine
if [ "$IS_REMOTE" = true ] && [ "${COPY_TO_LOCAL:-false}" = "true" ]; then
    LOCAL_BACKUP_DIR="${SCRIPT_DIR}/../backups/server-backup-${BACKUP_DATE}"
    log "Copying backup to local machine: ${LOCAL_BACKUP_DIR}"
    mkdir -p "$(dirname "${LOCAL_BACKUP_DIR}")"
    copy_from_remote "${BACKUP_BASE_DIR}" "${LOCAL_BACKUP_DIR}"
fi

log "Backup process completed at $(date)"

