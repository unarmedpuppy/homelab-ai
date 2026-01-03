#!/bin/bash
set -euo pipefail

GITEA_URL="https://gitea.server.unarmedpuppy.com"
GITEA_API="${GITEA_URL}/api/v1"

source "$(dirname "$0")/../apps/gitea/.env"

if [[ -z "${GITHUB_USERNAME:-}" ]] || [[ -z "${GITHUB_PAT:-}" ]]; then
    echo "Error: GITHUB_USERNAME and GITHUB_PAT must be set in apps/gitea/.env"
    exit 1
fi

GITEA_TOKEN="${GITEA_API_TOKEN:-}"
if [[ -z "$GITEA_TOKEN" ]]; then
    echo "Error: GITEA_API_TOKEN not set. Create one at ${GITEA_URL}/user/settings/applications"
    echo "Add it to apps/gitea/.env as GITEA_API_TOKEN=your_token"
    exit 1
fi

REPOS=(
    "agent-gateway"
    "agents"
    "agents-mono"
    "beads-viewer"
    "budget"
    "chatterbox-tts-service"
    "home-server"
    "homelab-ai"
    "maptapdat"
    "media-downs-dockerized"
    "opencode-terminal"
    "pokedex"
    "polyjuiced"
    "shared-agent-skills"
    "smart-home-3d"
    "tcg-scraper"
    "trading-bot"
    "trading-journal"
    "workflow-agents"
)

create_mirror() {
    local repo_name="$1"
    local github_url="https://github.com/${GITHUB_USERNAME}/${repo_name}.git"
    
    echo "Creating mirror for ${repo_name}..."
    
    response=$(curl -s -w "\n%{http_code}" -X POST "${GITEA_API}/repos/migrate" \
        -H "Authorization: token ${GITEA_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{
            \"clone_addr\": \"${github_url}\",
            \"uid\": 1,
            \"repo_name\": \"${repo_name}\",
            \"mirror\": true,
            \"private\": false,
            \"auth_username\": \"${GITHUB_USERNAME}\",
            \"auth_password\": \"${GITHUB_PAT}\",
            \"mirror_interval\": \"8h\"
        }")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [[ "$http_code" == "201" ]]; then
        echo "  ✓ Created mirror for ${repo_name}"
    elif [[ "$http_code" == "409" ]]; then
        echo "  - ${repo_name} already exists, skipping"
    else
        echo "  ✗ Failed to create mirror for ${repo_name}: ${body}"
    fi
}

echo "Setting up Gitea mirrors from GitHub"
echo "====================================="
echo "GitHub User: ${GITHUB_USERNAME}"
echo "Gitea URL: ${GITEA_URL}"
echo "Repos to mirror: ${#REPOS[@]}"
echo ""

for repo in "${REPOS[@]}"; do
    create_mirror "$repo"
done

echo ""
echo "Done! Visit ${GITEA_URL} to verify mirrors."
echo ""
echo "To add more repos later, use: agents/skills/add-gitea-mirror"
