#!/bin/bash
set -e

GITEA_TOKEN="bae92395084591de4d32e8deefe780e9b4123ba1"
GITEA_URL="https://gitea.server.unarmedpuppy.com/api/v1"

if [ -z "$HARBOR_USERNAME" ] || [ -z "$HARBOR_PASSWORD" ]; then
    echo "Usage: HARBOR_USERNAME=xxx HARBOR_PASSWORD=xxx ./add-harbor-secrets.sh"
    echo ""
    echo "Get values from: home-server/apps/harbor/.env"
    exit 1
fi

REPOS="maptapdat homelab-ai beads-viewer smart-home-3d opencode-terminal trading-bot trading-journal pokedex"

for repo in $REPOS; do
    echo "Adding secrets to $repo..."
    
    curl -s -X PUT "$GITEA_URL/repos/unarmedpuppy/$repo/actions/secrets/HARBOR_USERNAME" \
        -H "Authorization: token $GITEA_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"data\": \"$HARBOR_USERNAME\"}" > /dev/null
    
    curl -s -X PUT "$GITEA_URL/repos/unarmedpuppy/$repo/actions/secrets/HARBOR_PASSWORD" \
        -H "Authorization: token $GITEA_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"data\": \"$HARBOR_PASSWORD\"}" > /dev/null
    
    echo "  Done"
done

echo ""
echo "All repos configured with Harbor secrets."
