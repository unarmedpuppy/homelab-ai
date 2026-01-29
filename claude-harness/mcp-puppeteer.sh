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

MCP_DIR="${HOME}/.claude"
MCP_CONFIG="${MCP_DIR}/mcp.json"

PUPPETEER_CONFIG='{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
      "env": {
        "PUPPETEER_EXECUTABLE_PATH": "/usr/bin/chromium"
      }
    }
  }
}'

enable_puppeteer() {
    mkdir -p "$MCP_DIR"

    if [ -f "$MCP_CONFIG" ]; then
        # Check if puppeteer is already configured
        if jq -e '.mcpServers.puppeteer' "$MCP_CONFIG" > /dev/null 2>&1; then
            echo "Puppeteer MCP is already enabled"
            return 0
        fi

        # Merge with existing config
        local existing=$(cat "$MCP_CONFIG")
        echo "$existing" | jq --argjson puppeteer "$PUPPETEER_CONFIG" \
            '.mcpServers.puppeteer = $puppeteer.mcpServers.puppeteer' > "$MCP_CONFIG"
        echo "Puppeteer MCP enabled (merged with existing config)"
    else
        # Create new config
        echo "$PUPPETEER_CONFIG" | jq '.' > "$MCP_CONFIG"
        echo "Puppeteer MCP enabled (new config created)"
    fi

    echo ""
    echo "Restart your Claude session for changes to take effect."
    echo "Tools available: puppeteer_navigate, puppeteer_screenshot, puppeteer_click, etc."
}

disable_puppeteer() {
    if [ ! -f "$MCP_CONFIG" ]; then
        echo "No MCP config found - Puppeteer MCP is not enabled"
        return 0
    fi

    if ! jq -e '.mcpServers.puppeteer' "$MCP_CONFIG" > /dev/null 2>&1; then
        echo "Puppeteer MCP is not enabled"
        return 0
    fi

    # Remove puppeteer from config
    local updated=$(jq 'del(.mcpServers.puppeteer)' "$MCP_CONFIG")

    # Check if mcpServers is now empty
    if echo "$updated" | jq -e '.mcpServers | length == 0' > /dev/null 2>&1; then
        rm "$MCP_CONFIG"
        echo "Puppeteer MCP disabled (config file removed - was only entry)"
    else
        echo "$updated" > "$MCP_CONFIG"
        echo "Puppeteer MCP disabled"
    fi

    echo ""
    echo "Restart your Claude session for changes to take effect."
}

status_puppeteer() {
    if [ ! -f "$MCP_CONFIG" ]; then
        echo "Status: DISABLED (no MCP config)"
        return 0
    fi

    if jq -e '.mcpServers.puppeteer' "$MCP_CONFIG" > /dev/null 2>&1; then
        echo "Status: ENABLED"
        echo ""
        echo "Current config:"
        jq '.mcpServers.puppeteer' "$MCP_CONFIG"
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
