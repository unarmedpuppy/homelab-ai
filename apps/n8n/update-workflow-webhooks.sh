#!/bin/bash
# Script to update webhook URLs in n8n workflows via API

set -e

# Configuration
N8N_URL="${N8N_URL:-https://n8n.server.unarmedpuppy.com}"
N8N_API_KEY="${N8N_API_KEY:-}"
WEBHOOK_URL="${WEBHOOK_URL:-http://ai-agent-webhook:8100/webhook/ai-agent}"

# Load API key from .env.local if it exists
if [ -f .env.local ]; then
    export $(grep N8N_API_KEY .env.local | xargs)
fi

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ -z "$N8N_API_KEY" ]; then
    echo -e "${RED}Error: N8N_API_KEY not set${NC}"
    exit 1
fi

echo -e "${YELLOW}Updating webhook URLs in n8n workflows...${NC}"
echo "Webhook URL: $WEBHOOK_URL"
echo ""

# Get all workflows
workflows=$(curl -s -X GET "$N8N_URL/api/v1/workflows" \
    -H "X-N8N-API-KEY: $N8N_API_KEY" | jq -r '.data[] | select(.name | contains("Monitor")) | "\(.id)|\(.name)"')

if [ -z "$workflows" ]; then
    echo -e "${RED}No workflows found${NC}"
    exit 1
fi

# Update each workflow
while IFS='|' read -r workflow_id workflow_name; do
    echo -e "${YELLOW}Updating: $workflow_name (ID: $workflow_id)${NC}"
    
    # Get workflow details
    workflow=$(curl -s -X GET "$N8N_URL/api/v1/workflows/$workflow_id" \
        -H "X-N8N-API-KEY: $N8N_API_KEY")
    
    # Update webhook URL in nodes
    updated_workflow=$(echo "$workflow" | jq --arg url "$WEBHOOK_URL" '
        .nodes = (.nodes | map(
            if .name == "Call AI Agent Webhook" then
                .parameters.url = $url
            else
                .
            end
        ))
    ')
    
    # Update workflow via API
    response=$(curl -s -w "\n%{http_code}" -X PUT \
        "$N8N_URL/api/v1/workflows/$workflow_id" \
        -H "X-N8N-API-KEY: $N8N_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$updated_workflow")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✓ Updated: $workflow_name${NC}"
    else
        echo -e "${RED}✗ Failed to update: $workflow_name (HTTP $http_code)${NC}"
        echo "$body" | head -3
    fi
    echo ""
    
done <<< "$workflows"

echo -e "${GREEN}Done!${NC}"
echo ""
echo "Note: You still need to:"
echo "  1. Configure Docker Socket credential in n8n UI"
echo "  2. Configure AI Agent Webhook Auth credential in n8n UI"
echo "  3. Assign credentials to workflow nodes"
echo "  4. Activate workflows"

