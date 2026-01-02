#!/bin/bash
set -euo pipefail

# Claude Code Harness - Container Entrypoint
#
# Checks for OAuth authentication before starting the service.
# If not authenticated, provides instructions for one-time auth.

CLAUDE_CONFIG="$HOME/.claude.json"

# Check if Claude CLI is authenticated
if [ ! -f "$CLAUDE_CONFIG" ]; then
    echo "=============================================="
    echo "ERROR: Claude CLI not authenticated"
    echo "=============================================="
    echo ""
    echo "OAuth tokens not found at $CLAUDE_CONFIG"
    echo ""
    echo "To authenticate (one-time setup):"
    echo ""
    echo "  1. Run: docker exec -it claude-harness claude"
    echo "  2. Open the URL shown in your browser"
    echo "  3. Log in with your Claude Max account"
    echo "  4. Tokens will be saved to the Docker volume"
    echo "  5. Restart the container: docker restart claude-harness"
    echo ""
    echo "=============================================="
    
    # Keep container running so user can exec into it
    echo "Container staying alive for authentication..."
    echo "Run: docker exec -it claude-harness claude"
    
    # Sleep forever so container doesn't exit
    tail -f /dev/null
fi

# Verify token file has content
if [ ! -s "$CLAUDE_CONFIG" ]; then
    echo "ERROR: $CLAUDE_CONFIG exists but is empty"
    echo "Re-authenticate: docker exec -it claude-harness claude"
    tail -f /dev/null
fi

echo "OAuth tokens found. Starting Claude Harness..."

# Start the FastAPI service
exec uvicorn main:app --host 0.0.0.0 --port 8013
