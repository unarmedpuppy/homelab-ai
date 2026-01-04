#!/bin/bash
# Docker Maintenance Script
# Runs weekly to clean up unused Docker resources
# Add to crontab: 0 5 * * 1 ~/server/scripts/docker-maintenance.sh >> ~/server/logs/docker-maintenance.log 2>&1

set -e

LOG_DIR="${HOME}/server/logs"
mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "=== Starting Docker Maintenance ==="

# Show current disk usage
log "Docker disk usage before cleanup:"
docker system df

# Remove stopped containers (orphans from deleted apps, crashed containers, etc.)
log "Removing stopped containers..."
docker container prune -f

# Remove unused images (not referenced by any container)
log "Removing unused images..."
docker image prune -a -f

# Remove unused networks
log "Removing unused networks..."
docker network prune -f

# Note: NOT pruning volumes by default - too risky for data loss
# Uncomment the following line only if you're sure:
# docker volume prune -f

# Remove build cache
log "Removing build cache..."
docker builder prune -f

# Show disk usage after cleanup
log "Docker disk usage after cleanup:"
docker system df

log "=== Docker Maintenance Complete ==="
