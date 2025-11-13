#!/bin/bash
# Query Task Registry Helper Script
#
# Provides command-line access to task registry queries.
# For programmatic access, use MCP tools instead.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REGISTRY_PATH="$PROJECT_ROOT/agents/tasks/registry.md"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Query the task registry.

Options:
    -s, --status STATUS       Filter by status (pending, claimed, in_progress, blocked, review, completed, cancelled)
    -a, --assignee AGENT_ID   Filter by assignee
    -p, --project PROJECT     Filter by project
    -r, --priority PRIORITY    Filter by priority (low, medium, high)
    -t, --task-id TASK_ID     Get specific task by ID
    -c, --count               Show only count
    -h, --help                Show this help message

Examples:
    $0 --status pending
    $0 --assignee agent-001
    $0 --project home-server
    $0 --status in_progress --priority high
    $0 --task-id T1.1
    $0 --count

Note: For programmatic access, use MCP tools (query_tasks, get_task).
EOF
}

# Parse arguments
STATUS=""
ASSIGNEE=""
PROJECT=""
PRIORITY=""
TASK_ID=""
COUNT_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--status)
            STATUS="$2"
            shift 2
            ;;
        -a|--assignee)
            ASSIGNEE="$2"
            shift 2
            ;;
        -p|--project)
            PROJECT="$2"
            shift 2
            ;;
        -r|--priority)
            PRIORITY="$2"
            shift 2
            ;;
        -t|--task-id)
            TASK_ID="$2"
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

# Check if registry exists
if [[ ! -f "$REGISTRY_PATH" ]]; then
    echo -e "${RED}Error: Task registry not found at $REGISTRY_PATH${NC}" >&2
    exit 1
fi

# Parse registry markdown
parse_tasks() {
    local in_table=false
    local count=0
    
    while IFS= read -r line; do
        # Start of table
        if [[ "$line" =~ \|\ *Task\ ID\ *\| ]]; then
            in_table=true
            continue
        fi
        
        # Skip separator line
        if [[ "$in_table" == true && "$line" =~ ^\|\ *--- ]]; then
            continue
        fi
        
        # End of table
        if [[ "$in_table" == true && ! "$line" =~ ^\|\ * ]]; then
            break
        fi
        
        # Parse task row
        if [[ "$in_table" == true && "$line" =~ ^\|\ * ]]; then
            # Remove leading/trailing | and split
            line="${line#|}"
            line="${line%|}"
            IFS='|' read -ra FIELDS <<< "$line"
            
            # Trim whitespace from each field
            for i in "${!FIELDS[@]}"; do
                FIELDS[$i]=$(echo "${FIELDS[$i]}" | xargs)
            done
            
            # Skip empty rows
            if [[ "${FIELDS[0]}" == "-" || -z "${FIELDS[0]}" ]]; then
                continue
            fi
            
            # Extract fields
            local task_id="${FIELDS[0]}"
            local title="${FIELDS[1]}"
            local description="${FIELDS[2]}"
            local status="${FIELDS[3]}"
            local assignee="${FIELDS[4]}"
            local priority="${FIELDS[5]}"
            local dependencies="${FIELDS[6]}"
            local project="${FIELDS[7]}"
            local created="${FIELDS[8]}"
            local updated="${FIELDS[9]}"
            
            # Apply filters
            if [[ -n "$TASK_ID" && "$task_id" != "$TASK_ID" ]]; then
                continue
            fi
            if [[ -n "$STATUS" && "$status" != "$STATUS" ]]; then
                continue
            fi
            if [[ -n "$ASSIGNEE" && "$assignee" != "$ASSIGNEE" ]]; then
                continue
            fi
            if [[ -n "$PROJECT" && "$project" != "$PROJECT" ]]; then
                continue
            fi
            if [[ -n "$PRIORITY" && "$priority" != "$PRIORITY" ]]; then
                continue
            fi
            
            # Output task
            if [[ "$COUNT_ONLY" == true ]]; then
                ((count++))
            else
                echo "Task ID: $task_id"
                echo "  Title: $title"
                echo "  Description: $description"
                echo "  Status: $status"
                echo "  Assignee: $assignee"
                echo "  Priority: $priority"
                echo "  Dependencies: $dependencies"
                echo "  Project: $project"
                echo "  Created: $created"
                echo "  Updated: $updated"
                echo ""
            fi
        fi
    done < "$REGISTRY_PATH"
    
    if [[ "$COUNT_ONLY" == true ]]; then
        echo "$count"
    fi
}

# Execute query
if [[ -n "$TASK_ID" ]]; then
    # Single task lookup
    result=$(parse_tasks)
    if [[ -z "$result" ]]; then
        echo -e "${RED}Task $TASK_ID not found${NC}" >&2
        exit 1
    else
        echo "$result"
    fi
else
    # Multiple tasks
    parse_tasks
fi

