#!/bin/bash
set -euo pipefail

APPUSER="${APPUSER:-appuser}"
CLAUDE_VOLUME_DIR="/home/$APPUSER/.claude"
CLAUDE_CONFIG="/home/$APPUSER/.claude.json"
CLAUDE_CONFIG_IN_VOLUME="$CLAUDE_VOLUME_DIR/.claude.json"
SSH_DIR="/home/$APPUSER/.ssh"
WORKSPACE_DIR="/workspace"

fix_volume_permissions() {
    chown -R "$APPUSER:$APPUSER" "$CLAUDE_VOLUME_DIR" 2>/dev/null || true
    chown -R "$APPUSER:$APPUSER" "$SSH_DIR" 2>/dev/null || true
    chown -R "$APPUSER:$APPUSER" "$WORKSPACE_DIR" 2>/dev/null || true
    chmod 700 "$SSH_DIR" 2>/dev/null || true
}

setup_ssh_key() {
    if [ ! -f "$SSH_DIR/id_ed25519" ]; then
        echo "Generating SSH key for deployments..."
        gosu "$APPUSER" ssh-keygen -t ed25519 -f "$SSH_DIR/id_ed25519" -N "" -C "claude-harness@container"
        echo ""
        echo "SSH public key (add to claude-deploy@server authorized_keys):"
        cat "$SSH_DIR/id_ed25519.pub"
        echo ""
    fi
}

setup_claude_symlink() {
    if [ -f "$CLAUDE_CONFIG_IN_VOLUME" ] && [ ! -L "$CLAUDE_CONFIG" ]; then
        gosu "$APPUSER" ln -sf "$CLAUDE_CONFIG_IN_VOLUME" "$CLAUDE_CONFIG"
        echo "Symlinked $CLAUDE_CONFIG -> $CLAUDE_CONFIG_IN_VOLUME"
    fi
}

wait_for_auth() {
    echo "=============================================="
    echo "ERROR: Claude CLI not authenticated"
    echo "=============================================="
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
}

fix_volume_permissions
setup_ssh_key
setup_claude_symlink

if [ ! -f "$CLAUDE_CONFIG" ] && [ ! -f "$CLAUDE_CONFIG_IN_VOLUME" ]; then
    wait_for_auth
fi

if [ ! -s "$CLAUDE_CONFIG" ] && [ ! -s "$CLAUDE_CONFIG_IN_VOLUME" ]; then
    echo "ERROR: Token file exists but is empty"
    echo "Re-authenticate: docker exec -it claude-harness claude"
    tail -f /dev/null
fi

echo "OAuth tokens found. Starting Claude Harness..."
exec gosu "$APPUSER" uvicorn main:app --host 0.0.0.0 --port 8013
