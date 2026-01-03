#!/bin/bash
# Switch local git remotes from GitHub to Gitea
# Usage: ./switch-to-gitea.sh [repo-path]
# If no path given, operates on current directory

set -e

GITEA_HOST="gitea.server.unarmedpuppy.com"
GITEA_SSH_PORT="2223"
GITEA_USER="unarmedpuppy"

# Check SSH config
check_ssh_config() {
    if ! grep -q "Host $GITEA_HOST" ~/.ssh/config 2>/dev/null; then
        echo "WARNING: SSH config for Gitea not found. Add this to ~/.ssh/config:"
        echo ""
        echo "Host $GITEA_HOST"
        echo "    HostName $GITEA_HOST"
        echo "    Port $GITEA_SSH_PORT"
        echo "    User git"
        echo "    IdentityFile ~/.ssh/id_ed25519"
        echo ""
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Switch remote for a single repo
switch_repo() {
    local repo_path="$1"
    
    if [ ! -d "$repo_path/.git" ]; then
        echo "Not a git repository: $repo_path"
        return 1
    fi
    
    cd "$repo_path"
    local repo_name=$(basename "$repo_path")
    
    # Get current remote
    local current_remote=$(git remote get-url origin 2>/dev/null || echo "none")
    
    if [[ "$current_remote" == *"$GITEA_HOST"* ]]; then
        echo "[$repo_name] Already pointing to Gitea"
        return 0
    fi
    
    # Check if github remote exists, rename if so
    if git remote get-url github &>/dev/null; then
        echo "[$repo_name] 'github' remote already exists"
    elif [[ "$current_remote" == *"github.com"* ]]; then
        echo "[$repo_name] Renaming 'origin' to 'github'"
        git remote rename origin github
    fi
    
    # Set origin to Gitea
    local gitea_url="ssh://git@$GITEA_HOST:$GITEA_SSH_PORT/$GITEA_USER/$repo_name.git"
    
    if git remote get-url origin &>/dev/null; then
        echo "[$repo_name] Updating origin to: $gitea_url"
        git remote set-url origin "$gitea_url"
    else
        echo "[$repo_name] Adding origin: $gitea_url"
        git remote add origin "$gitea_url"
    fi
    
    # Verify
    echo "[$repo_name] Remotes:"
    git remote -v
    echo ""
}

# Main
check_ssh_config

if [ -n "$1" ]; then
    switch_repo "$1"
else
    switch_repo "$(pwd)"
fi

echo "Done! Test with: git fetch origin"
