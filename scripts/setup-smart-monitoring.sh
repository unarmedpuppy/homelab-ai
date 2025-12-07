#!/bin/bash

# Setup SMART Monitoring
# Installs smartmontools and configures automated drive health monitoring

set -euo pipefail

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

log "Setting up SMART monitoring..."

# 1. Install smartmontools
log "Installing smartmontools..."
if ! command -v smartctl &> /dev/null; then
    sudo apt update
    sudo apt install smartmontools -y
    log "smartmontools installed"
else
    log "smartmontools already installed"
fi

# 2. Enable SMART on all drives
log "Enabling SMART on all drives..."
for disk in /dev/sd[a-z] /dev/nvme[0-9]n[0-9]; do
    if [ -b "$disk" ]; then
        if sudo smartctl -i "$disk" &>/dev/null; then
            sudo smartctl -s on "$disk" 2>/dev/null && log "  Enabled SMART on $disk" || warning "  Could not enable SMART on $disk"
        fi
    fi
done

# 3. Make health check script executable
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "${SCRIPT_DIR}/check-drive-health.sh" ]; then
    chmod +x "${SCRIPT_DIR}/check-drive-health.sh"
    log "Made check-drive-health.sh executable"
else
    warning "check-drive-health.sh not found"
fi

# 4. Setup daily cron job
log "Setting up daily cron job..."
CRON_CMD="0 3 * * * ${SCRIPT_DIR}/check-drive-health.sh >> /var/log/drive-health.log 2>&1"

# Check if cron job already exists
if sudo crontab -l 2>/dev/null | grep -q "check-drive-health.sh"; then
    warning "Cron job already exists"
else
    (sudo crontab -l 2>/dev/null; echo "$CRON_CMD") | sudo crontab -
    log "Added daily cron job (runs at 3 AM)"
fi

# 5. Test the script
log "Testing drive health check..."
if bash "${SCRIPT_DIR}/check-drive-health.sh" > /dev/null 2>&1; then
    log "Drive health check test passed"
else
    warning "Drive health check test had issues (this may be normal if drives have warnings)"
fi

log ""
log "SMART monitoring setup complete!"
log ""
log "Next steps:"
log "1. Run manual check: bash ${SCRIPT_DIR}/check-drive-health.sh"
log "2. View logs: tail -f /var/log/drive-health.log"
log "3. Check cron: sudo crontab -l"
log ""
log "To setup email alerts, edit: ${SCRIPT_DIR}/drive-health-alert.sh"

