#!/bin/bash
set -euo pipefail

APPUSER="${APPUSER:-appuser}"
CLAUDE_VOLUME_DIR="/home/$APPUSER/.claude"
CLAUDE_CONFIG="/home/$APPUSER/.claude.json"
CLAUDE_CONFIG_IN_VOLUME="$CLAUDE_VOLUME_DIR/.claude.json"
SSH_DIR="/home/$APPUSER/.ssh"
WORKSPACE_DIR="/workspace"

update_claude_cli() {
    # IMPORTANT: Must use npm update, NOT the native installer (curl | bash)
    # Native installer puts binary at ~/.local/bin/claude which breaks yolo wrapper
    # npm keeps it at /usr/bin/claude where yolo wrapper expects it
    echo "Checking for Claude CLI updates..."
    local current_version=$(claude --version 2>/dev/null | head -1 || echo "unknown")
    echo "Current Claude CLI version: $current_version"

    # Update Claude CLI to latest version via npm
    if npm update -g @anthropic-ai/claude-code 2>&1; then
        local new_version=$(claude --version 2>/dev/null | head -1 || echo "unknown")
        if [ "$current_version" != "$new_version" ]; then
            echo "Claude CLI updated: $current_version -> $new_version"
        else
            echo "Claude CLI already at latest version: $new_version"
        fi
    else
        echo "Warning: Failed to update Claude CLI, continuing with current version"
    fi
}

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
    # Use internal Docker network address to avoid Traefik auth header issues
    if [ -n "${GITEA_TOKEN:-}" ]; then
        echo "http://oauth2:${GITEA_TOKEN}@gitea:3000" >> "$creds_file"
        echo "Git configured with Gitea token authentication (internal: gitea:3000)"
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

setup_ssh_host_keys() {
    # Persist SSH host keys across container recreations
    local host_keys_volume="/etc/ssh/host_keys"

    if [ -d "$host_keys_volume" ]; then
        # Check if volume has existing keys
        if ls "$host_keys_volume"/ssh_host_*_key 1>/dev/null 2>&1; then
            echo "Restoring SSH host keys from volume..."
            cp "$host_keys_volume"/ssh_host_* /etc/ssh/
            chmod 600 /etc/ssh/ssh_host_*_key
            chmod 644 /etc/ssh/ssh_host_*_key.pub
        else
            # Generate new keys and save to volume
            echo "Generating SSH host keys..."
            ssh-keygen -A
            echo "Persisting SSH host keys to volume..."
            cp /etc/ssh/ssh_host_* "$host_keys_volume/"
        fi
    else
        # No volume mounted, just generate keys normally
        ssh-keygen -A
    fi
}

start_sshd() {
    echo "Starting SSH server..."
    /usr/sbin/sshd
}

setup_workspace() {
    (
        cd "$WORKSPACE_DIR"

        # All repos to clone - format: "org/repo"
        # Most are under homelab/, but some are under unarmedpuppy/
        REPOS=(
            "homelab/home-server"
            "homelab/homelab-ai"
            "homelab/tasks"
            "homelab/pokedex"
            "homelab/polyjuiced"
            "homelab/agent-gateway"
            "homelab/maptapdat"
            "homelab/trading-bot"
            "homelab/trading-journal"
            "homelab/shua-ledger"
            "homelab/bird"
            "homelab/n8n-automations"
            "homelab/smart-home-3d"
            "unarmedpuppy/workflows"
        )

        for org_repo in "${REPOS[@]}"; do
            local org="${org_repo%/*}"
            local repo="${org_repo#*/}"
            local gitea_url="http://gitea:3000/${org}/${repo}.git"

            if [ ! -d "$repo" ]; then
                echo "Cloning $repo from Gitea ($org)..."
                # Use internal Docker network address (gitea:3000) to avoid Traefik auth issues
                if [ -n "${GITEA_TOKEN:-}" ]; then
                    gosu "$APPUSER" git clone "$gitea_url" || {
                        echo "Warning: Failed to clone $repo from Gitea"
                    }
                else
                    echo "Warning: GITEA_TOKEN not set, cannot clone $repo"
                fi
            else
                # Repo exists - ensure remote is internal Gitea, not GitHub or external Gitea
                local current_remote=$(git -C "$repo" remote get-url origin 2>/dev/null || true)
                if [[ "$current_remote" == *"github.com"* ]] || [[ "$current_remote" == *"gitea.server.unarmedpuppy.com"* ]]; then
                    echo "Fixing $repo remote -> internal Gitea ($org)"
                    gosu "$APPUSER" git -C "$repo" remote set-url origin "$gitea_url"
                fi
                # Pull latest on startup (fast-forward only to avoid conflicts)
                echo "Pulling latest for $repo..."
                gosu "$APPUSER" git -C "$repo" pull --ff-only 2>/dev/null || {
                    echo "Warning: Could not fast-forward $repo, fetching instead"
                    gosu "$APPUSER" git -C "$repo" fetch origin --prune 2>/dev/null || true
                }
            fi
        done

        # Create workspace-level CLAUDE.md that references home-server/WORKSPACE-AGENTS.md
        # Claude Code reads CLAUDE.md automatically, which then loads the full context
        if [ ! -e "CLAUDE.md" ]; then
            if [ -f "home-server/WORKSPACE-AGENTS.md" ]; then
                echo "Creating workspace CLAUDE.md -> @home-server/WORKSPACE-AGENTS.md..."
                echo "@home-server/WORKSPACE-AGENTS.md" > CLAUDE.md
                chown "$APPUSER:$APPUSER" CLAUDE.md
            else
                echo "Warning: home-server/WORKSPACE-AGENTS.md not found, creating minimal CLAUDE.md"
                cat > CLAUDE.md << 'CLAUDE_EOF'
# Homelab Workspace

See `home-server/WORKSPACE-AGENTS.md` for full cross-repo documentation.

## Quick Reference

- **Tasks**: `./home-server/tasks.md`
- **Server config**: `./home-server/`
CLAUDE_EOF
                chown "$APPUSER:$APPUSER" CLAUDE.md
            fi
        fi
    )
}


setup_shared_skills() {
    # Aggregate skills from ALL repos into /workspace/.claude/skills/
    # This replaces the npm shared-agent-skills package approach
    local skills_target="$WORKSPACE_DIR/.claude/skills"

    # Create skills directory
    gosu "$APPUSER" mkdir -p "$skills_target"

    # Remove old symlinks (handles renamed/removed skills)
    find "$skills_target" -type l -delete 2>/dev/null || true

    # Scan ALL repos for skills and aggregate them
    local count=0
    local collisions=0
    for repo in "$WORKSPACE_DIR"/*/; do
        local repo_name=$(basename "$repo")

        # Check both patterns: agents/skills/ (preferred) and .claude/skills/
        for skills_dir in "$repo"agents/skills "$repo".claude/skills; do
            [ -d "$skills_dir" ] || continue

            # Pattern 1: agents/skills/skill-name/SKILL.md
            for skill_file in "$skills_dir"/*/SKILL.md; do
                [ -f "$skill_file" ] || continue

                local name=$(basename "$(dirname "$skill_file")")

                # Check for collision
                if [ -L "$skills_target/${name}.md" ]; then
                    echo "WARN: Skill collision '$name' from $repo_name (skipping)"
                    collisions=$((collisions + 1))
                    continue
                fi

                gosu "$APPUSER" ln -sf "$skill_file" "$skills_target/${name}.md"
                count=$((count + 1))
            done

            # Pattern 2: .claude/skills/skill-name.md (direct files, not symlinks)
            for skill_file in "$skills_dir"/*.md; do
                [ -f "$skill_file" ] || continue
                # Skip if it's a symlink (avoid double-counting)
                [ -L "$skill_file" ] && continue
                # Skip README
                [[ "$(basename "$skill_file")" == "README.md" ]] && continue

                local name=$(basename "$skill_file" .md)

                if [ -L "$skills_target/${name}.md" ]; then
                    echo "WARN: Skill collision '$name' from $repo_name (skipping)"
                    collisions=$((collisions + 1))
                    continue
                fi

                gosu "$APPUSER" ln -sf "$skill_file" "$skills_target/${name}.md"
                count=$((count + 1))
            done
        done
    done

    echo "Linked $count skills from all repos to $skills_target"
    [ $collisions -gt 0 ] && echo "WARN: $collisions skill collisions detected"

    # Create CLAUDE.md at workspace root if missing
    if [ ! -f "$WORKSPACE_DIR/CLAUDE.md" ]; then
        if [ -f "$WORKSPACE_DIR/AGENTS.md" ]; then
            gosu "$APPUSER" cp "$WORKSPACE_DIR/AGENTS.md" "$WORKSPACE_DIR/CLAUDE.md"
            echo "Created CLAUDE.md from AGENTS.md"
        elif [ -f "$WORKSPACE_DIR/home-server/AGENTS.md" ]; then
            gosu "$APPUSER" cp "$WORKSPACE_DIR/home-server/AGENTS.md" "$WORKSPACE_DIR/CLAUDE.md"
            echo "Created CLAUDE.md from home-server/AGENTS.md"
        fi
    fi
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

update_claude_cli
fix_volume_permissions
setup_ssh_key
setup_claude_symlink
setup_git_config
setup_gpg_signing
setup_claude_yolo
setup_ssh_host_keys
start_sshd
setup_workspace
setup_shared_skills
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
