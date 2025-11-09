#!/bin/bash
# Script to import n8n workflows via API

set -e

# Configuration
N8N_URL="${N8N_URL:-https://n8n.server.unarmedpuppy.com}"
N8N_USER="${N8N_USER:-admin}"
N8N_PASSWORD="${N8N_PASSWORD:-changeme123}"
WORKFLOWS_DIR="${WORKFLOWS_DIR:-./workflows}"

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
    
    # Read workflow JSON and remove fields that shouldn't be sent
    workflow_json=$(cat "$workflow_file" | jq 'del(.id, .updatedAt, .versionId)')
    
    # Import workflow via API
    response=$(curl -s -w "\n%{http_code}" -X POST \
        "$N8N_URL/api/v1/workflows" \
        -u "$N8N_USER:$N8N_PASSWORD" \
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
if curl -s -f -u "$N8N_USER:$N8N_PASSWORD" "$N8N_URL/api/v1/workflows" > /dev/null; then
    echo -e "${GREEN}✓ Connected to n8n${NC}"
    echo ""
else
    echo -e "${RED}✗ Failed to connect to n8n${NC}"
    echo "Please check:"
    echo "  - n8n URL: $N8N_URL"
    echo "  - Username: $N8N_USER"
    echo "  - Password: (check .env file)"
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

