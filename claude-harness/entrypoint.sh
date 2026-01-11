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
    
    # Copy user's authorized_keys for inbound SSH if mounted
    if [ -f "/etc/ssh/user_authorized_keys" ]; then
        cp /etc/ssh/user_authorized_keys "$SSH_DIR/authorized_keys"
        chown "$APPUSER:$APPUSER" "$SSH_DIR/authorized_keys"
        chmod 600 "$SSH_DIR/authorized_keys"
        echo "Copied authorized_keys for SSH access"
    fi
}

setup_claude_symlink() {
    if [ -f "$CLAUDE_CONFIG_IN_VOLUME" ] && [ ! -L "$CLAUDE_CONFIG" ]; then
        gosu "$APPUSER" ln -sf "$CLAUDE_CONFIG_IN_VOLUME" "$CLAUDE_CONFIG"
        echo "Symlinked $CLAUDE_CONFIG -> $CLAUDE_CONFIG_IN_VOLUME"
    fi
}

setup_git_config() {
    if [ -n "${GIT_AUTHOR_NAME:-}" ]; then
        gosu "$APPUSER" git config --global user.name "$GIT_AUTHOR_NAME"
    fi
    if [ -n "${GIT_AUTHOR_EMAIL:-}" ]; then
        gosu "$APPUSER" git config --global user.email "$GIT_AUTHOR_EMAIL"
    fi

    # Set up credential helper
    gosu "$APPUSER" git config --global credential.helper store
    local creds_file="/home/$APPUSER/.git-credentials"
    > "$creds_file"  # Clear/create file

    # Gitea credentials (primary - for all homelab repos)
    if [ -n "${GITEA_TOKEN:-}" ]; then
        echo "https://oauth2:${GITEA_TOKEN}@gitea.server.unarmedpuppy.com" >> "$creds_file"
        echo "Git configured with Gitea token authentication"
    fi

    # GitHub credentials (secondary - for external dependencies)
    if [ -n "${GITHUB_TOKEN:-}" ]; then
        echo "https://x-access-token:${GITHUB_TOKEN}@github.com" >> "$creds_file"
        echo "Git configured with GitHub token authentication"
    fi

    chown "$APPUSER:$APPUSER" "$creds_file"
    chmod 600 "$creds_file"
}

setup_gpg_signing() {
    local gpg_key_file="/etc/gpg-key.asc"
    local gpg_dir="/home/$APPUSER/.gnupg"
    
    if [ -f "$gpg_key_file" ] && [ -n "${GPG_KEY_ID:-}" ]; then
        mkdir -p "$gpg_dir"
        chmod 700 "$gpg_dir"
        chown "$APPUSER:$APPUSER" "$gpg_dir"
        
        gosu "$APPUSER" gpg --batch --import "$gpg_key_file" 2>/dev/null || true
        
        gosu "$APPUSER" git config --global user.signingkey "$GPG_KEY_ID"
        gosu "$APPUSER" git config --global commit.gpgsign true
        gosu "$APPUSER" git config --global gpg.program gpg
        
        echo "GPG signing configured with key $GPG_KEY_ID"
    fi
}

setup_claude_yolo() {
    cat > /usr/local/bin/claude-yolo << 'EOF'
#!/bin/bash
case "$1" in
    --version|--help|-h|-v)
        exec /usr/bin/claude.orig "$@"
        ;;
    *)
        exec /usr/bin/claude.orig --dangerously-skip-permissions "$@"
        ;;
esac
EOF
    chmod +x /usr/local/bin/claude-yolo
    
    if [ ! -f /usr/bin/claude.orig ]; then
        mv /usr/bin/claude /usr/bin/claude.orig
        ln -s /usr/local/bin/claude-yolo /usr/bin/claude
    fi
    
    local bashrc="/home/$APPUSER/.bashrc"
    if ! grep -q "cd /workspace" "$bashrc" 2>/dev/null; then
        echo "cd /workspace" >> "$bashrc"
        chown "$APPUSER:$APPUSER" "$bashrc"
    fi
}

start_sshd() {
    echo "Starting SSH server..."
    /usr/sbin/sshd
}

setup_workspace() {
    (
        cd "$WORKSPACE_DIR"

        # All homelab repos to clone
        # Using Gitea (local) as primary, GitHub as fallback
        HOMELAB_REPOS=(
            "home-server"
            "homelab-ai"
            "pokedex"
            "polyjuiced"
            "agent-gateway"
            "beads-viewer"
            "maptapdat"
            "trading-bot"
            "trading-journal"
            "workflows"
            "shua-ledger"
        )

        for repo in "${HOMELAB_REPOS[@]}"; do
            if [ ! -d "$repo" ]; then
                echo "Cloning $repo from Gitea..."
                # Use Gitea exclusively for homelab repos (not GitHub)
                if [ -n "${GITEA_TOKEN:-}" ]; then
                    gosu "$APPUSER" git clone "https://gitea.server.unarmedpuppy.com/homelab/${repo}.git" || {
                        echo "Warning: Failed to clone $repo from Gitea"
                    }
                else
                    echo "Warning: GITEA_TOKEN not set, cannot clone $repo"
                fi
            else
                # Repo exists - ensure remote is Gitea, not GitHub
                local current_remote=$(git -C "$repo" remote get-url origin 2>/dev/null || true)
                if [[ "$current_remote" == *"github.com"* ]]; then
                    echo "Fixing $repo remote: GitHub -> Gitea"
                    gosu "$APPUSER" git -C "$repo" remote set-url origin "https://gitea.server.unarmedpuppy.com/homelab/${repo}.git"
                fi
            fi
        done

        # Create workspace-level AGENTS.md if it doesn't exist
        if [ ! -f "AGENTS.md" ]; then
            echo "Creating workspace AGENTS.md..."
            cat > AGENTS.md << 'AGENTS_EOF'
# Homelab Workspace - Agent Instructions

This is the unified development workspace for all homelab projects.

## Workspace Structure

- `/workspace/` - Root workspace (you are here)
- `/workspace/.beads/` - Unified task database
- `/workspace/<repo>/` - Individual project repos

## Task Management

All tasks tracked in /workspace/.beads/:
```bash
bd ready              # Find unblocked work
bd list               # View all tasks
bd create "title" -p 1  # Create task
bd close <id>         # Complete task
```

## Deployment

- **Code changes**: Push tag → CI builds → Harbor Deployer auto-deploys
- **Config changes**: Push to home-server → Gitea Actions deploys

## Per-Repo Context

Each repo has its own AGENTS.md with specific instructions:
- `home-server/AGENTS.md` - Server infrastructure, Docker apps
- `homelab-ai/AGENTS.md` - AI services (router, dashboard, etc.)

## Quick Commands

```bash
# SSH to server (if needed for debugging)
ssh -p 4242 claude-deploy@host.docker.internal 'sudo docker ps'

# Check all repo status
for d in */; do [ -d "$d/.git" ] && echo "=== $d ===" && git -C "$d" status -s; done

# Pull all repos
for d in */; do [ -d "$d/.git" ] && git -C "$d" pull; done

# Push all repos with changes
for d in */; do [ -d "$d/.git" ] && git -C "$d" diff --quiet || (cd "$d" && git push); done
```

## Access Methods

| Device | Method | Command |
|--------|--------|---------|
| Laptop/PC | SSH | `ssh appuser@server:22` (container SSH port) |
| Laptop/PC | VS Code | Remote-SSH extension |
| Phone | Web terminal | ttyd at terminal.server.unarmedpuppy.com |
| Any | code-server | (if installed) |

## Boundaries

### Always Do
- Use `bd` commands for task tracking
- Commit after logical units of work
- Pull before starting work

### Never Do
- Work in multiple environments simultaneously (pick one)
- Forget to push changes
- Ignore failing tests
AGENTS_EOF
            chown "$APPUSER:$APPUSER" AGENTS.md
        fi
    )
}

setup_beads() {
    (
        cd "$WORKSPACE_DIR"

        # Initialize beads if not already done and bd command exists
        if [ ! -d ".beads" ] && command -v bd &> /dev/null; then
            echo "Initializing beads in workspace..."
            gosu "$APPUSER" bd init --prefix "workspace-" || true
        fi

        # Start beads daemon if available
        if command -v bd &> /dev/null; then
            echo "Starting beads daemon..."
            gosu "$APPUSER" bd daemon start &> /dev/null &
        fi
    )
}

start_code_server() {
    if command -v code-server &> /dev/null; then
        echo "Starting code-server on port 8443..."
        # Create code-server config
        mkdir -p "/home/$APPUSER/.config/code-server"
        cat > "/home/$APPUSER/.config/code-server/config.yaml" << EOF
bind-addr: 0.0.0.0:8443
auth: none
cert: false
EOF
        chown -R "$APPUSER:$APPUSER" "/home/$APPUSER/.config"

        # Start code-server in background
        gosu "$APPUSER" code-server --user-data-dir "/home/$APPUSER/.code-server" "$WORKSPACE_DIR" &
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
setup_git_config
setup_gpg_signing
setup_claude_yolo
start_sshd
setup_workspace
setup_beads
start_code_server

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
