#!/bin/bash
# Install Harbor Auto-Deployer as a systemd service
#
# Usage:
#   ./install-harbor-deployer.sh          # Install and start
#   ./install-harbor-deployer.sh uninstall # Remove service
#
# Prerequisites:
#   - Python 3.8+
#   - docker Python package: pip3 install docker
#   - User must be in docker group

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="harbor-deployer"
SERVICE_FILE="${SCRIPT_DIR}/${SERVICE_NAME}.service"
SYSTEMD_DIR="/etc/systemd/system"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

check_prerequisites() {
    log "Checking prerequisites..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed"
    fi
    log "  Python 3: $(python3 --version)"

    # Check docker Python package
    if ! python3 -c "import docker" &> /dev/null; then
        warning "docker Python package not installed"
        log "  Installing: pip3 install docker"
        pip3 install docker
    fi
    log "  docker package: OK"

    # Check docker socket
    if [ ! -S /var/run/docker.sock ]; then
        error "Docker socket not found at /var/run/docker.sock"
    fi
    log "  Docker socket: OK"

    # Check user is in docker group
    if ! groups | grep -q docker; then
        warning "Current user may not be in docker group"
    fi
}

install_service() {
    log "Installing ${SERVICE_NAME} service..."

    # Check service file exists
    if [ ! -f "${SERVICE_FILE}" ]; then
        error "Service file not found: ${SERVICE_FILE}"
    fi

    # Create logs directory
    mkdir -p /home/unarmedpuppy/server/logs
    log "  Created logs directory"

    # Copy service file
    sudo cp "${SERVICE_FILE}" "${SYSTEMD_DIR}/${SERVICE_NAME}.service"
    log "  Copied service file to ${SYSTEMD_DIR}"

    # Reload systemd
    sudo systemctl daemon-reload
    log "  Reloaded systemd"

    # Enable service
    sudo systemctl enable "${SERVICE_NAME}"
    log "  Enabled ${SERVICE_NAME} service"

    # Start service
    sudo systemctl start "${SERVICE_NAME}"
    log "  Started ${SERVICE_NAME} service"

    # Check status
    if sudo systemctl is-active --quiet "${SERVICE_NAME}"; then
        log "Service is running!"
        echo ""
        log "Useful commands:"
        echo "  sudo systemctl status ${SERVICE_NAME}    # Check status"
        echo "  sudo journalctl -u ${SERVICE_NAME} -f    # View logs"
        echo "  tail -f ~/server/logs/harbor-deployer.log  # View app logs"
    else
        error "Service failed to start. Check: sudo journalctl -u ${SERVICE_NAME}"
    fi
}

uninstall_service() {
    log "Uninstalling ${SERVICE_NAME} service..."

    # Stop service
    if sudo systemctl is-active --quiet "${SERVICE_NAME}"; then
        sudo systemctl stop "${SERVICE_NAME}"
        log "  Stopped service"
    fi

    # Disable service
    if sudo systemctl is-enabled --quiet "${SERVICE_NAME}" 2>/dev/null; then
        sudo systemctl disable "${SERVICE_NAME}"
        log "  Disabled service"
    fi

    # Remove service file
    if [ -f "${SYSTEMD_DIR}/${SERVICE_NAME}.service" ]; then
        sudo rm "${SYSTEMD_DIR}/${SERVICE_NAME}.service"
        log "  Removed service file"
    fi

    # Reload systemd
    sudo systemctl daemon-reload
    log "  Reloaded systemd"

    log "Service uninstalled"
}

# Main
case "${1:-install}" in
    install)
        check_prerequisites
        install_service
        ;;
    uninstall)
        uninstall_service
        ;;
    *)
        echo "Usage: $0 {install|uninstall}"
        exit 1
        ;;
esac
