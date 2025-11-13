#!/bin/bash
# Query Messages Helper Script
#
# Provides command-line access to message queries.
# For programmatic access, use MCP tools instead.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
INDEX_PATH="$PROJECT_ROOT/agents/communication/messages/index.json"
MESSAGES_DIR="$PROJECT_ROOT/agents/communication/messages"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Query agent messages.

Options:
    -a, --agent-id AGENT_ID   Filter by agent ID (to or from)
    -s, --status STATUS       Filter by status (pending, acknowledged, in_progress, resolved, escalated)
    -t, --type TYPE           Filter by type (request, response, notification, escalation)
    -r, --priority PRIORITY    Filter by priority (low, medium, high, urgent)
    -m, --message-id MSG_ID   Get specific message by ID
    -c, --count               Show only count
    -h, --help                Show this help message

Examples:
    $0 --agent-id agent-001 --status pending
    $0 --type request --priority high
    $0 --message-id MSG-2025-01-13-001
    $0 --count

Note: For programmatic access, use MCP tools (get_agent_messages, query_messages).
EOF
}

# Parse arguments
AGENT_ID=""
STATUS=""
TYPE=""
PRIORITY=""
MESSAGE_ID=""
COUNT_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--agent-id)
            AGENT_ID="$2"
            shift 2
            ;;
        -s|--status)
            STATUS="$2"
            shift 2
            ;;
        -t|--type)
            TYPE="$2"
            shift 2
            ;;
        -r|--priority)
            PRIORITY="$2"
            shift 2
            ;;
        -m|--message-id)
            MESSAGE_ID="$2"
            shift 2
            ;;
        -c|--count)
            COUNT_ONLY=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option: $1${NC}" >&2
            usage
            exit 1
            ;;
    esac
done

# Check if index exists
if [[ ! -f "$INDEX_PATH" ]]; then
    echo -e "${YELLOW}Warning: Message index not found. No messages yet.${NC}" >&2
    exit 0
fi

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is required but not installed. Install with: brew install jq${NC}" >&2
    exit 1
fi

# Query messages
query_messages() {
    local count=0
    
    # Read index
    local messages
    messages=$(jq -r '.messages[]' "$INDEX_PATH" 2>/dev/null || echo "[]")
    
    # If specific message ID requested
    if [[ -n "$MESSAGE_ID" ]]; then
        local message
        message=$(jq -r ".messages[] | select(.message_id == \"$MESSAGE_ID\")" "$INDEX_PATH" 2>/dev/null)
        
        if [[ -z "$message" || "$message" == "null" ]]; then
            echo -e "${RED}Message $MESSAGE_ID not found${NC}" >&2
            exit 1
        fi
        
        # Get message file path
        local file_path
        file_path=$(echo "$message" | jq -r '.file')
        file_path="$PROJECT_ROOT/$file_path"
        
        if [[ -f "$file_path" ]]; then
            if [[ "$COUNT_ONLY" == true ]]; then
                echo "1"
            else
                cat "$file_path"
            fi
        else
            echo -e "${RED}Message file not found: $file_path${NC}" >&2
            exit 1
        fi
        return
    fi
    
    # Filter messages
    while IFS= read -r message; do
        # Skip empty
        if [[ -z "$message" || "$message" == "null" ]]; then
            continue
        fi
        
        # Extract fields
        local from_agent
        local to_agent
        local msg_status
        local msg_type
        local msg_priority
        local message_id
        
        from_agent=$(echo "$message" | jq -r '.from_agent // ""')
        to_agent=$(echo "$message" | jq -r '.to_agent // ""')
        msg_status=$(echo "$message" | jq -r '.status // ""')
        msg_type=$(echo "$message" | jq -r '.type // ""')
        msg_priority=$(echo "$message" | jq -r '.priority // ""')
        message_id=$(echo "$message" | jq -r '.message_id // ""')
        
        # Apply filters
        if [[ -n "$AGENT_ID" ]]; then
            if [[ "$from_agent" != "$AGENT_ID" && "$to_agent" != "$AGENT_ID" && "$to_agent" != "all" ]]; then
                continue
            fi
        fi
        if [[ -n "$STATUS" && "$msg_status" != "$STATUS" ]]; then
            continue
        fi
        if [[ -n "$TYPE" && "$msg_type" != "$TYPE" ]]; then
            continue
        fi
        if [[ -n "$PRIORITY" && "$msg_priority" != "$PRIORITY" ]]; then
            continue
        fi
        
        # Output message
        if [[ "$COUNT_ONLY" == true ]]; then
            ((count++))
        else
            local file_path
            file_path=$(echo "$message" | jq -r '.file')
            file_path="$PROJECT_ROOT/$file_path"
            
            if [[ -f "$file_path" ]]; then
                echo "=== Message: $message_id ==="
                cat "$file_path"
                echo ""
            fi
        fi
    done < <(jq -c '.messages[]' "$INDEX_PATH" 2>/dev/null || echo "")
    
    if [[ "$COUNT_ONLY" == true ]]; then
        echo "$count"
    fi
}

# Execute query
query_messages

