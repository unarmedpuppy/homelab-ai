#!/bin/bash
set -euo pipefail

# Claude Code Harness - Container Entrypoint
#
# Checks for OAuth authentication before starting the service.
# If not authenticated, provides instructions for one-time auth.
#
# Volume mount: /home/appuser/.claude (directory)
# Claude CLI expects: /home/appuser/.claude.json (file)
# Solution: Symlink the file from the volume directory

CLAUDE_VOLUME_DIR="$HOME/.claude"
CLAUDE_CONFIG="$HOME/.claude.json"
CLAUDE_CONFIG_IN_VOLUME="$CLAUDE_VOLUME_DIR/.claude.json"

# Create symlink if volume has the token file but symlink doesn't exist
if [ -f "$CLAUDE_CONFIG_IN_VOLUME" ] && [ ! -L "$CLAUDE_CONFIG" ]; then
    ln -sf "$CLAUDE_CONFIG_IN_VOLUME" "$CLAUDE_CONFIG"
    echo "Symlinked $CLAUDE_CONFIG -> $CLAUDE_CONFIG_IN_VOLUME"
fi

# Check if Claude CLI is authenticated
if [ ! -f "$CLAUDE_CONFIG" ] && [ ! -f "$CLAUDE_CONFIG_IN_VOLUME" ]; then
    echo "=============================================="
    echo "ERROR: Claude CLI not authenticated"
    echo "=============================================="
    echo ""
    echo "OAuth tokens not found."
    echo ""
    echo "To authenticate (one-time setup):"
    echo ""
    echo "  1. Run: docker exec -it claude-harness claude"
    echo "  2. Open the URL shown in your browser"
    echo "  3. Log in with your Claude Max account"
    echo "  4. After auth completes, copy the token to the volume:"
    echo "     docker exec claude-harness cp ~/.claude.json ~/.claude/.claude.json"
    echo "  5. Restart the container: docker restart claude-harness"
    echo ""
    echo "=============================================="
    
    echo "Container staying alive for authentication..."
    
    tail -f /dev/null
fi

# Verify token file has content
if [ ! -s "$CLAUDE_CONFIG" ] && [ ! -s "$CLAUDE_CONFIG_IN_VOLUME" ]; then
    echo "ERROR: Token file exists but is empty"
    echo "Re-authenticate: docker exec -it claude-harness claude"
    tail -f /dev/null
fi

if [ -f "$CLAUDE_CONFIG_IN_VOLUME" ] && [ ! -L "$CLAUDE_CONFIG" ]; then
    ln -sf "$CLAUDE_CONFIG_IN_VOLUME" "$CLAUDE_CONFIG"
fi

echo "OAuth tokens found. Starting Claude Harness..."

# Start the FastAPI service
exec uvicorn main:app --host 0.0.0.0 --port 8013
