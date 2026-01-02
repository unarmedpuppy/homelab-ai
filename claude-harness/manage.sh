#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="claude-harness"
SERVICE_FILE="$SCRIPT_DIR/claude-harness.service"
SYSTEMD_PATH="/etc/systemd/system/$SERVICE_NAME.service"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This command requires sudo"
        exit 1
    fi
}

check_claude_cli() {
    if ! command -v claude &> /dev/null; then
        log_error "Claude CLI not installed"
        echo ""
        echo "Install with: npm install -g @anthropic-ai/claude-code"
        echo "Then authenticate: claude"
        return 1
    fi
    return 0
}

check_python_deps() {
    if ! python3 -c "import fastapi, uvicorn, pydantic" &> /dev/null; then
        log_warn "Python dependencies missing"
        echo "Installing: fastapi uvicorn pydantic"
        pip3 install --user fastapi uvicorn pydantic
    fi
}

cmd_install() {
    check_root
    
    log_info "Checking prerequisites..."
    
    if ! check_claude_cli; then
        exit 1
    fi
    
    check_python_deps
    
    log_info "Installing systemd service..."
    cp "$SERVICE_FILE" "$SYSTEMD_PATH"
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    systemctl start "$SERVICE_NAME"
    
    log_info "Service installed and started"
    echo ""
    systemctl status "$SERVICE_NAME" --no-pager || true
}

cmd_update() {
    check_root
    
    log_info "Updating service..."
    cp "$SERVICE_FILE" "$SYSTEMD_PATH"
    systemctl daemon-reload
    systemctl restart "$SERVICE_NAME"
    
    log_info "Service updated and restarted"
    systemctl status "$SERVICE_NAME" --no-pager || true
}

cmd_status() {
    echo "=== Service Status ==="
    systemctl status "$SERVICE_NAME" --no-pager || true
    echo ""
    echo "=== Health Check ==="
    curl -s http://localhost:8013/health 2>/dev/null || echo "Service not responding"
}

cmd_logs() {
    local lines="${1:-100}"
    journalctl -u "$SERVICE_NAME" -n "$lines" --no-pager
}

cmd_follow() {
    journalctl -u "$SERVICE_NAME" -f
}

cmd_restart() {
    check_root
    systemctl restart "$SERVICE_NAME"
    log_info "Service restarted"
}

cmd_stop() {
    check_root
    systemctl stop "$SERVICE_NAME"
    log_info "Service stopped"
}

cmd_uninstall() {
    check_root
    
    log_info "Stopping and removing service..."
    systemctl stop "$SERVICE_NAME" || true
    systemctl disable "$SERVICE_NAME" || true
    rm -f "$SYSTEMD_PATH"
    systemctl daemon-reload
    
    log_info "Service uninstalled"
}

cmd_test() {
    log_info "Testing Claude Harness..."
    
    echo "1. Health check:"
    curl -s http://localhost:8013/health | python3 -m json.tool 2>/dev/null || echo "Failed"
    
    echo ""
    echo "2. Test completion (this may take a moment):"
    curl -s -X POST http://localhost:8013/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d '{"messages":[{"role":"user","content":"Say hello in exactly 3 words"}]}' \
        | python3 -m json.tool 2>/dev/null || echo "Failed"
}

cmd_help() {
    cat << EOF
Claude Harness Management Script

Usage: $0 <command> [args]

Commands:
  install     Install and start the systemd service (requires sudo)
  update      Update service file and restart (requires sudo)
  status      Show service status and health
  logs [n]    Show last n log lines (default: 100)
  follow      Follow logs in real-time
  restart     Restart the service (requires sudo)
  stop        Stop the service (requires sudo)
  uninstall   Remove the service (requires sudo)
  test        Run health check and test completion
  help        Show this help message

Prerequisites:
  - Claude CLI: npm install -g @anthropic-ai/claude-code
  - Authenticate: claude (follow OAuth flow)
  - Python deps: pip3 install fastapi uvicorn pydantic

Examples:
  sudo $0 install    # First-time setup
  sudo $0 update     # After git pull
  $0 status          # Check if running
  $0 logs 50         # Last 50 log lines
  $0 test            # Verify it works
EOF
}

case "${1:-help}" in
    install)   cmd_install ;;
    update)    cmd_update ;;
    status)    cmd_status ;;
    logs)      cmd_logs "${2:-100}" ;;
    follow)    cmd_follow ;;
    restart)   cmd_restart ;;
    stop)      cmd_stop ;;
    uninstall) cmd_uninstall ;;
    test)      cmd_test ;;
    help|*)    cmd_help ;;
esac
