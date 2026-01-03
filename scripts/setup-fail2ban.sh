#!/bin/bash

# Setup fail2ban Script
# Installs and configures fail2ban for SSH protection

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    error "This script must be run as root or with sudo"
fi

log "Setting up fail2ban for SSH protection..."

# Step 1: Install fail2ban
if ! command -v fail2ban-server &> /dev/null; then
    log "Installing fail2ban..."
    apt update
    apt install -y fail2ban
    log "✓ fail2ban installed"
else
    info "fail2ban already installed"
fi

# Step 2: Create jail.local configuration
log "Creating fail2ban configuration..."
JAIL_FILE="/etc/fail2ban/jail.local"

if [ -f "$JAIL_FILE" ]; then
    warning "jail.local already exists. Backing up..."
    cp "$JAIL_FILE" "${JAIL_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
fi

cat > "$JAIL_FILE" << 'EOF'
[DEFAULT]
# Ban time: 1 hour
bantime = 3600

# Time window: 10 minutes
findtime = 600

# Max retries: 5 attempts
maxretry = 5

# Email notifications (optional - uncomment and configure)
# destemail = your-email@example.com
# sendername = Fail2Ban
# action = %(action_mwl)s

[sshd]
enabled = true
# SSH port (change if different)
port = 4242
filter = sshd
# Use systemd journal (Debian 12+ doesn't use auth.log)
backend = systemd
maxretry = 3
bantime = 86400  # 24 hours for SSH
findtime = 600   # 10 minutes
EOF

log "✓ Configuration created"

# Step 3: Verify SSH port
SSH_PORT=$(grep -E "^Port" /etc/ssh/sshd_config 2>/dev/null | awk '{print $2}' || echo "4242")
if [ "$SSH_PORT" != "4242" ]; then
    warning "SSH port in config is $SSH_PORT, but jail.local uses 4242"
    read -p "Update jail.local to use port $SSH_PORT? (y/n): " -r UPDATE_PORT
    if [ "$UPDATE_PORT" = "y" ] || [ "$UPDATE_PORT" = "Y" ]; then
        sed -i "s/port = 4242/port = $SSH_PORT/" "$JAIL_FILE"
        log "✓ Updated port to $SSH_PORT"
    fi
fi

# Step 4: Test configuration
log "Testing fail2ban configuration..."
if fail2ban-client -t; then
    log "✓ Configuration is valid"
else
    error "Configuration test failed. Please check /etc/fail2ban/jail.local"
fi

# Step 5: Enable and start fail2ban
log "Enabling fail2ban service..."
systemctl enable fail2ban
systemctl restart fail2ban

# Step 6: Verify status
sleep 2
if systemctl is-active --quiet fail2ban; then
    log "✓ fail2ban is running"
else
    error "fail2ban failed to start. Check logs: journalctl -u fail2ban"
fi

# Step 7: Show status
echo ""
log "fail2ban status:"
fail2ban-client status
echo ""
fail2ban-client status sshd 2>/dev/null || info "SSH jail not active yet (will activate on first ban)"

# Step 8: Show useful commands
echo ""
info "Useful commands:"
echo "  Check status:     sudo fail2ban-client status"
echo "  Check SSH jail:   sudo fail2ban-client status sshd"
echo "  Unban IP:         sudo fail2ban-client set sshd unbanip <IP>"
echo "  Ban IP manually:  sudo fail2ban-client set sshd banip <IP>"
echo "  View logs:        sudo tail -f /var/log/fail2ban.log"
echo ""

log "✓ fail2ban setup complete!"


