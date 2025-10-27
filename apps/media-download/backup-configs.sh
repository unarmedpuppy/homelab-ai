#!/bin/bash
# Backup all configuration files
# Usage: ./backup-configs.sh

set -e

BACKUP_DIR="../backups/media-download"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="media-download-backup-${TIMESTAMP}.tar.gz"

echo "💾 Creating backup..."
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Create compressed backup of all config directories
tar -czf "${BACKUP_DIR}/${BACKUP_FILE}" \
    nzbhydra2/config/ \
    jackett/config/ \
    nzbget/config/ \
    qbittorrent/config/ \
    sonarr/config/ \
    radarr/config/ \
    lidarr/config/ \
    bazarr/config/ \
    wireguard/config/

echo "✅ Backup created: ${BACKUP_DIR}/${BACKUP_FILE}"
echo ""
echo "📊 Backup size: $(du -h "${BACKUP_DIR}/${BACKUP_FILE}" | cut -f1)"
echo ""
echo "📝 To restore:"
echo "   tar -xzf ${BACKUP_DIR}/${BACKUP_FILE}"
echo ""
echo "🗑️  To list existing backups:"
echo "   ls -lh ${BACKUP_DIR}/"
echo ""

