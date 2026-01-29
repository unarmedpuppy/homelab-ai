#!/bin/bash
# Toggle Puppeteer MCP on/off for Claude Code
#
# Usage:
#   mcp-puppeteer enable   - Enable Puppeteer MCP
#   mcp-puppeteer disable  - Disable Puppeteer MCP
#   mcp-puppeteer status   - Check if enabled
#
# After enabling, restart your Claude session for changes to take effect.

set -euo pipefail

enable_puppeteer() {
    # Check if already configured
    if claude mcp list 2>/dev/null | grep -q "^puppeteer:"; then
        echo "Puppeteer MCP is already enabled"
        claude mcp list 2>/dev/null | grep "^puppeteer:"
        return 0
    fi

    # Add via CLI (writes to correct config location)
    if claude mcp add puppeteer -e "PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium" -- npx -y @modelcontextprotocol/server-puppeteer 2>&1; then
        echo ""
        echo "Puppeteer MCP enabled."
        echo "Restart your Claude session for changes to take effect."
        echo "Tools available: puppeteer_navigate, puppeteer_screenshot, puppeteer_click, etc."
    else
        echo "Failed to add Puppeteer MCP server"
        return 1
    fi
}

disable_puppeteer() {
    # Check if configured
    if ! claude mcp list 2>/dev/null | grep -q "^puppeteer:"; then
        echo "Puppeteer MCP is not enabled"
        return 0
    fi

    # Remove via CLI
    if claude mcp remove puppeteer 2>&1; then
        echo ""
        echo "Puppeteer MCP disabled."
        echo "Restart your Claude session for changes to take effect."
    else
        echo "Failed to remove Puppeteer MCP server"
        return 1
    fi
}

status_puppeteer() {
    if claude mcp list 2>/dev/null | grep -q "^puppeteer:"; then
        echo "Status: ENABLED"
        echo ""
        claude mcp list 2>/dev/null | grep "^puppeteer:"
    else
        echo "Status: DISABLED"
    fi
}

case "${1:-status}" in
    enable|on)
        enable_puppeteer
        ;;
    disable|off)
        disable_puppeteer
        ;;
    status)
        status_puppeteer
        ;;
    *)
        echo "Usage: mcp-puppeteer [enable|disable|status]"
        echo ""
        echo "Commands:"
        echo "  enable   - Enable Puppeteer MCP for browser automation"
        echo "  disable  - Disable Puppeteer MCP"
        echo "  status   - Check current status"
        exit 1
        ;;
esac
