#!/bin/bash
# Script to import n8n workflows via API

set -e

# Configuration
N8N_URL="${N8N_URL:-https://n8n.server.unarmedpuppy.com}"
N8N_API_KEY="${N8N_API_KEY:-}"
WORKFLOWS_DIR="${WORKFLOWS_DIR:-./workflows}"

# Load API key from .env.local if it exists
if [ -f .env.local ]; then
    export $(grep N8N_API_KEY .env.local | xargs)
fi

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Importing n8n workflows...${NC}"
echo "n8n URL: $N8N_URL"
echo ""

# Function to import a workflow
import_workflow() {
    local workflow_file=$1
    local workflow_name=$(basename "$workflow_file" .json)
    
    echo -e "${YELLOW}Importing: $workflow_name${NC}"
    
    # Read workflow JSON and extract only the fields that n8n API accepts
    # Nodes must only have: name, type, typeVersion, position, parameters (no id, no credentials)
    workflow_json=$(cat "$workflow_file" | jq '{
        name: .name,
        nodes: (.nodes | map({
            name: .name,
            type: .type,
            typeVersion: .typeVersion,
            position: .position,
            parameters: .parameters
        })),
        connections: .connections,
        settings: (.settings // {})
    }')
    
    # Import workflow via API
    if [ -z "$N8N_API_KEY" ]; then
        echo -e "${RED}Error: N8N_API_KEY not set${NC}"
        return 1
    fi
    
    response=$(curl -s -w "\n%{http_code}" -X POST \
        "$N8N_URL/api/v1/workflows" \
        -H "X-N8N-API-KEY: $N8N_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$workflow_json")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 201 ]; then
        workflow_id=$(echo "$body" | jq -r '.id // empty')
        if [ -n "$workflow_id" ]; then
            echo -e "${GREEN}✓ Successfully imported: $workflow_name (ID: $workflow_id)${NC}"
            return 0
        else
            echo -e "${GREEN}✓ Successfully imported: $workflow_name${NC}"
            return 0
        fi
    else
        echo -e "${RED}✗ Failed to import: $workflow_name${NC}"
        echo "HTTP Code: $http_code"
        echo "Response: $body"
        return 1
    fi
}

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is required but not installed.${NC}"
    echo "Install with: sudo apt-get install jq"
    exit 1
fi

# Check if curl is installed
if ! command -v curl &> /dev/null; then
    echo -e "${RED}Error: curl is required but not installed.${NC}"
    exit 1
fi

# Test n8n connection
echo "Testing n8n connection..."
if [ -z "$N8N_API_KEY" ]; then
    echo -e "${RED}Error: N8N_API_KEY not set${NC}"
    echo "Please set N8N_API_KEY environment variable or add it to .env.local"
    exit 1
fi

if curl -s -f -H "X-N8N-API-KEY: $N8N_API_KEY" "$N8N_URL/api/v1/workflows" > /dev/null; then
    echo -e "${GREEN}✓ Connected to n8n${NC}"
    echo ""
else
    echo -e "${RED}✗ Failed to connect to n8n${NC}"
    echo "Please check:"
    echo "  - n8n URL: $N8N_URL"
    echo "  - API Key: (check .env.local file)"
    exit 1
fi

# Import all workflow files
success_count=0
fail_count=0

for workflow_file in "$WORKFLOWS_DIR"/*.json; do
    if [ -f "$workflow_file" ]; then
        if import_workflow "$workflow_file"; then
            ((success_count++))
        else
            ((fail_count++))
        fi
        echo ""
    fi
done

# Summary
echo "========================================="
echo -e "${GREEN}Successfully imported: $success_count${NC}"
if [ $fail_count -gt 0 ]; then
    echo -e "${RED}Failed to import: $fail_count${NC}"
fi
echo "========================================="

if [ $fail_count -gt 0 ]; then
    exit 1
fi

