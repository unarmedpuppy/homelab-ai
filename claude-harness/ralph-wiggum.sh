#!/bin/bash
# Ralph Wiggum - Autonomous Task Loop for Claude Harness
#
# "Me fail English? That's unpossible!"
#
# This script runs inside the claude-harness container and:
# 1. Queries beads for ready tasks (filtered by label/priority)
# 2. Claims each task
# 3. Runs Claude with the task as a prompt
# 4. Marks tasks complete or failed
# 5. Loops until no more ready tasks or stop requested
#
# Usage:
#   ./ralph-wiggum.sh --label mercury         # Process mercury-labeled tasks
#   ./ralph-wiggum.sh --label trading-bot     # Only trading-bot tasks
#   ./ralph-wiggum.sh --priority 0            # Only critical priority
#   ./ralph-wiggum.sh --dry-run               # Show what would run
#   ./ralph-wiggum.sh --max 5                 # Max 5 tasks then stop
#
# Environment variables:
#   BEADS_DIR     - Directory containing .beads/ (default: /workspace/home-server)
#   STATUS_FILE   - JSON status file path (default: /workspace/.ralph-wiggum-status.json)
#   CONTROL_FILE  - Control commands file (default: /workspace/.ralph-wiggum-control)

set -uo pipefail

# Configuration from environment or defaults
WORKSPACE_DIR="${WORKSPACE_DIR:-/workspace}"
BEADS_DIR="${BEADS_DIR:-/workspace/home-server}"
STATUS_FILE="${STATUS_FILE:-/workspace/.ralph-wiggum-status.json}"
CONTROL_FILE="${CONTROL_FILE:-/workspace/.ralph-wiggum-control}"
LOG_FILE="${LOG_FILE:-/workspace/.ralph-wiggum.log}"
MAX_RETRIES=3
RETRY_DELAY=10

# Colors for output (disabled in non-terminal)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

# Parse arguments
LABEL_FILTER=""
PRIORITY_FILTER=""
DRY_RUN=false
MAX_TASKS=0  # 0 = unlimited
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -l|--label)
            LABEL_FILTER="$2"
            shift 2
            ;;
        -p|--priority)
            PRIORITY_FILTER="$2"
            shift 2
            ;;
        -n|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -m|--max)
            MAX_TASKS="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            echo "Ralph Wiggum - Autonomous Task Loop for Claude Harness"
            echo ""
            echo "Usage: ./ralph-wiggum.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -l, --label LABEL      Filter tasks by label (REQUIRED)"
            echo "  -p, --priority NUM     Filter by priority (0=critical, 1=high, 2=medium, 3=low)"
            echo "  -m, --max NUM          Maximum number of tasks to process (0=unlimited)"
            echo "  -n, --dry-run          Show tasks without executing"
            echo "  -v, --verbose          Verbose output"
            echo "  -h, --help             Show this help"
            echo ""
            echo "Environment:"
            echo "  BEADS_DIR     Directory with .beads/ (default: /workspace/home-server)"
            echo "  STATUS_FILE   JSON status file (default: /workspace/.ralph-wiggum-status.json)"
            echo "  CONTROL_FILE  Control file for stop commands"
            echo ""
            echo "Examples:"
            echo "  ./ralph-wiggum.sh --label mercury"
            echo "  ./ralph-wiggum.sh --label trading-bot --priority 1 --max 3"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate required label
if [ -z "$LABEL_FILTER" ]; then
    echo "ERROR: --label is required"
    echo "Usage: ./ralph-wiggum.sh --label <label>"
    exit 1
fi

# State tracking
TASKS_COMPLETED=0
TASKS_FAILED=0
TOTAL_TASKS=0
CURRENT_TASK_ID=""
CURRENT_TASK_TITLE=""
STARTED_AT=""

# Logging functions
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "$msg"
    echo "$msg" >> "$LOG_FILE"
}

log_info() {
    log "${BLUE}INFO${NC}: $1"
}

log_success() {
    log "${GREEN}SUCCESS${NC}: $1"
}

log_warn() {
    log "${YELLOW}WARN${NC}: $1"
}

log_error() {
    log "${RED}ERROR${NC}: $1"
}

# Write status to JSON file for API consumption
write_status() {
    local status="$1"
    local message="${2:-}"

    cat > "$STATUS_FILE" << EOF
{
  "running": $([ "$status" = "running" ] && echo "true" || echo "false"),
  "status": "$status",
  "label": "$LABEL_FILTER",
  "total_tasks": $TOTAL_TASKS,
  "completed_tasks": $TASKS_COMPLETED,
  "failed_tasks": $TASKS_FAILED,
  "current_task": $([ -n "$CURRENT_TASK_ID" ] && echo "\"$CURRENT_TASK_ID\"" || echo "null"),
  "current_task_title": $([ -n "$CURRENT_TASK_TITLE" ] && echo "\"$CURRENT_TASK_TITLE\"" || echo "null"),
  "started_at": $([ -n "$STARTED_AT" ] && echo "\"$STARTED_AT\"" || echo "null"),
  "last_update": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "message": $([ -n "$message" ] && echo "\"$message\"" || echo "null")
}
EOF
}

# Check for stop request
check_stop_requested() {
    if [ -f "$CONTROL_FILE" ]; then
        local cmd
        cmd=$(cat "$CONTROL_FILE" 2>/dev/null || echo "")
        if [ "$cmd" = "stop" ]; then
            log_warn "Stop requested via control file"
            return 0
        fi
    fi
    return 1
}

# Map labels to working directories
get_working_dir() {
    local labels="$1"

    # Check for specific repo labels
    case "$labels" in
        *trading-bot*|*polyjuiced*)
            echo "$WORKSPACE_DIR/polyjuiced"
            ;;
        *home-server*|*infrastructure*)
            echo "$WORKSPACE_DIR/home-server"
            ;;
        *homelab-ai*|*ai-services*|*claude-harness*)
            echo "$WORKSPACE_DIR/homelab-ai"
            ;;
        *pokedex*)
            echo "$WORKSPACE_DIR/pokedex"
            ;;
        *agent-gateway*)
            echo "$WORKSPACE_DIR/agent-gateway"
            ;;
        *beads-viewer*)
            echo "$WORKSPACE_DIR/beads-viewer"
            ;;
        *maptapdat*)
            echo "$WORKSPACE_DIR/maptapdat"
            ;;
        *trading-journal*)
            echo "$WORKSPACE_DIR/trading-journal"
            ;;
        *shua-ledger*)
            echo "$WORKSPACE_DIR/shua-ledger"
            ;;
        *bird*)
            echo "$WORKSPACE_DIR/bird"
            ;;
        *mercury*)
            # Mercury is a project - need to determine which repo
            # Default to workspace root for cross-repo work
            echo "$WORKSPACE_DIR"
            ;;
        *)
            # Default to workspace root
            echo "$WORKSPACE_DIR"
            ;;
    esac
}

# Run bd command from beads directory
run_bd() {
    (cd "$BEADS_DIR" && bd "$@")
}

# Count ready tasks
count_ready_tasks() {
    local count
    local cmd="bd ready --json"

    if [ -n "$LABEL_FILTER" ]; then
        cmd="$cmd --label $LABEL_FILTER"
    fi

    if [ -n "$PRIORITY_FILTER" ]; then
        cmd="$cmd --priority $PRIORITY_FILTER"
    fi

    count=$(cd "$BEADS_DIR" && eval "$cmd" 2>/dev/null | jq 'length' 2>/dev/null || echo "0")
    echo "$count"
}

# Get the next ready task
get_next_task() {
    local cmd="bd ready --json"

    if [ -n "$LABEL_FILTER" ]; then
        cmd="$cmd --label $LABEL_FILTER"
    fi

    if [ -n "$PRIORITY_FILTER" ]; then
        cmd="$cmd --priority $PRIORITY_FILTER"
    fi

    if $VERBOSE; then
        log_info "Running: $cmd (in $BEADS_DIR)"
    fi

    # Run query from beads directory and get first task
    local result
    result=$(cd "$BEADS_DIR" && eval "$cmd" 2>/dev/null || echo "[]")

    # Return first task as JSON
    echo "$result" | jq -r '.[0] // empty'
}

# Build prompt from task
build_prompt() {
    local task_json="$1"
    local working_dir="$2"

    local title
    local description
    local task_type
    local priority
    local labels

    title=$(echo "$task_json" | jq -r '.title // "Unknown task"')
    description=$(echo "$task_json" | jq -r '.description // ""')
    task_type=$(echo "$task_json" | jq -r '.type // "task"')
    priority=$(echo "$task_json" | jq -r '.priority // 2')
    labels=$(echo "$task_json" | jq -r '.labels // [] | join(", ")')

    # Build comprehensive prompt
    cat << EOF
You are working on the following task from the beads issue tracker.

## Task Details
- **Title**: $title
- **Type**: $task_type
- **Priority**: $priority (0=critical, 1=high, 2=medium, 3=low)
- **Labels**: $labels
- **Working Directory**: $working_dir

## Description
$description

## Instructions

1. Read any relevant AGENTS.md files in the working directory for context
2. Analyze what needs to be done for this task
3. Implement the solution:
   - Make necessary code changes
   - Run tests if applicable
   - Commit changes with descriptive messages
4. Push changes to git when complete
5. Provide a summary of what was accomplished

**Important**:
- Work in the directory: $working_dir
- The beads database is in /workspace/home-server/.beads/ (do not modify it directly)
- Commit and push all changes before completing

Work autonomously to complete this task. If you encounter blockers that cannot be resolved, note them in your summary.

Begin working on this task now.
EOF
}

# Claim a task
claim_task() {
    local task_id="$1"
    local task_title="$2"

    log_info "Claiming task: $task_id - $task_title"

    if $DRY_RUN; then
        log_info "[DRY RUN] Would run: bd update $task_id --status in_progress"
        return 0
    fi

    run_bd update "$task_id" --status in_progress

    # Commit the claim from beads directory
    (
        cd "$BEADS_DIR"
        if [ -d ".beads" ]; then
            git add .beads/
            git commit -m "claim: $task_id - $task_title" || true
            git push origin main || log_warn "Could not push claim commit"
        fi
    )
}

# Complete a task
complete_task() {
    local task_id="$1"
    local reason="$2"

    log_success "Completing task: $task_id"

    if $DRY_RUN; then
        log_info "[DRY RUN] Would run: bd close $task_id --reason '$reason'"
        return 0
    fi

    run_bd close "$task_id" --reason "$reason"

    # Commit the completion from beads directory
    (
        cd "$BEADS_DIR"
        if [ -d ".beads" ]; then
            git add .beads/
            git commit -m "close: $task_id - Completed by Ralph Wiggum" || true
            git push origin main || log_warn "Could not push completion commit"
        fi
    )
}

# Mark task as blocked/failed
fail_task() {
    local task_id="$1"
    local reason="$2"

    log_error "Task failed: $task_id - $reason"

    if $DRY_RUN; then
        log_info "[DRY RUN] Would update task with failure note"
        return 0
    fi

    # Return task to open status
    run_bd update "$task_id" --status open || true

    log_warn "Task $task_id returned to open status. Manual review needed."
}

# Commit and push code changes from working directory
commit_changes() {
    local working_dir="$1"
    local task_id="$2"
    local task_title="$3"

    log_info "Committing changes from: $working_dir"

    if $DRY_RUN; then
        log_info "[DRY RUN] Would commit and push changes from $working_dir"
        return 0
    fi

    (
        cd "$working_dir" || return 1

        # Check if there are any changes to commit
        if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
            log_info "No changes to commit in $working_dir"
            return 0
        fi

        # Stage all changes
        git add -A

        # Commit with Ralph prefix
        local commit_msg="Ralph - $task_id: $task_title"
        if git commit -m "$commit_msg"; then
            log_success "Committed changes: $commit_msg"
        else
            log_warn "Nothing to commit or commit failed"
            return 0
        fi

        # Push to origin
        if git push origin HEAD 2>&1; then
            log_success "Pushed changes to origin"
        else
            log_warn "Could not push changes - may need manual push"
        fi
    )
}

# Run Claude on a task
run_claude() {
    local prompt="$1"
    local working_dir="$2"
    local task_id="$3"

    log_info "Running Claude in: $working_dir"

    if $DRY_RUN; then
        log_info "[DRY RUN] Would run claude with prompt (${#prompt} chars)"
        echo "--- DRY RUN: Task would execute here ---"
        return 0
    fi

    # Create temp file for prompt
    local prompt_file
    prompt_file=$(mktemp)
    echo "$prompt" > "$prompt_file"

    # Change to working directory and pull latest
    cd "$working_dir"
    git fetch origin --prune 2>/dev/null || true
    git pull origin main 2>/dev/null || git pull 2>/dev/null || true

    # Run claude (uses the YOLO wrapper with --dangerously-skip-permissions)
    local exit_code=0
    if claude -p "$(cat "$prompt_file")" 2>&1; then
        exit_code=0
    else
        exit_code=$?
    fi

    # Clean up
    rm -f "$prompt_file"

    if [ $exit_code -eq 0 ]; then
        log_success "Claude completed successfully"
        return 0
    else
        log_error "Claude failed with exit code $exit_code"
        return $exit_code
    fi
}

# Cleanup on exit
cleanup() {
    write_status "completed" "Ralph Wiggum finished. Completed: $TASKS_COMPLETED, Failed: $TASKS_FAILED"
    rm -f "$CONTROL_FILE" 2>/dev/null || true
}
trap cleanup EXIT

# Main loop
main() {
    STARTED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    log_info "=========================================="
    log_info "Ralph Wiggum Starting"
    log_info "=========================================="
    log_info "Label filter: $LABEL_FILTER"
    log_info "Priority filter: ${PRIORITY_FILTER:-<none>}"
    log_info "Max tasks: ${MAX_TASKS:-unlimited}"
    log_info "Dry run: $DRY_RUN"
    log_info "Beads directory: $BEADS_DIR"
    log_info ""

    # Verify beads is available
    if ! command -v bd &> /dev/null; then
        log_error "Beads CLI (bd) not found. Cannot continue."
        write_status "failed" "Beads CLI not found"
        exit 1
    fi

    # Verify beads directory exists
    if [ ! -d "$BEADS_DIR/.beads" ]; then
        log_error "Beads database not found at $BEADS_DIR/.beads"
        write_status "failed" "Beads database not found"
        exit 1
    fi

    # Sync beads at start
    log_info "Syncing beads..."
    (cd "$BEADS_DIR" && bd sync 2>/dev/null) || log_warn "Beads sync failed, continuing anyway"

    # Count initial tasks
    TOTAL_TASKS=$(count_ready_tasks)
    log_info "Found $TOTAL_TASKS ready tasks with label '$LABEL_FILTER'"

    if [ "$TOTAL_TASKS" -eq 0 ]; then
        log_info "No tasks to process. Exiting."
        write_status "completed" "No tasks found with label '$LABEL_FILTER'"
        exit 0
    fi

    write_status "running" "Processing $TOTAL_TASKS tasks"

    local consecutive_failures=0

    while true; do
        # Check for stop request
        if check_stop_requested; then
            log_info "Stop requested. Finishing up."
            write_status "stopping" "Stop requested"
            break
        fi

        # Check if we've hit max tasks
        if [ "$MAX_TASKS" -gt 0 ] && [ "$TASKS_COMPLETED" -ge "$MAX_TASKS" ]; then
            log_info "Reached maximum tasks ($MAX_TASKS). Stopping."
            break
        fi

        # Get next task
        local task_json
        task_json=$(get_next_task)

        if [ -z "$task_json" ]; then
            log_info "No more ready tasks. Ralph Wiggum is done!"
            break
        fi

        # Extract task details
        CURRENT_TASK_ID=$(echo "$task_json" | jq -r '.id')
        CURRENT_TASK_TITLE=$(echo "$task_json" | jq -r '.title')
        local task_labels
        task_labels=$(echo "$task_json" | jq -r '.labels // [] | join(",")')

        local task_num=$((TASKS_COMPLETED + TASKS_FAILED + 1))
        log_info "=========================================="
        log_info "Task $task_num of $TOTAL_TASKS: $CURRENT_TASK_ID"
        log_info "Title: $CURRENT_TASK_TITLE"
        log_info "Labels: $task_labels"
        log_info "=========================================="

        # Determine working directory
        local working_dir
        working_dir=$(get_working_dir "$task_labels")
        log_info "Working directory: $working_dir"

        # Update status
        write_status "running" "Working on task $task_num of $TOTAL_TASKS"

        # Verify working directory exists
        if [ ! -d "$working_dir" ]; then
            log_error "Working directory does not exist: $working_dir"
            fail_task "$CURRENT_TASK_ID" "Working directory not found"
            ((TASKS_FAILED++))
            ((consecutive_failures++))

            if [ "$consecutive_failures" -ge "$MAX_RETRIES" ]; then
                log_error "Too many consecutive failures. Stopping."
                break
            fi
            continue
        fi

        # Claim the task
        claim_task "$CURRENT_TASK_ID" "$CURRENT_TASK_TITLE"

        # Build prompt
        local prompt
        prompt=$(build_prompt "$task_json" "$working_dir")

        if $VERBOSE; then
            log_info "Prompt length: ${#prompt} chars"
        fi

        # Run Claude
        if run_claude "$prompt" "$working_dir" "$CURRENT_TASK_ID"; then
            # Commit and push any code changes Claude made
            commit_changes "$working_dir" "$CURRENT_TASK_ID" "$CURRENT_TASK_TITLE"

            complete_task "$CURRENT_TASK_ID" "Completed by Ralph Wiggum autonomous loop"
            ((TASKS_COMPLETED++))
            consecutive_failures=0
        else
            fail_task "$CURRENT_TASK_ID" "Claude execution failed"
            ((TASKS_FAILED++))
            ((consecutive_failures++))

            if [ "$consecutive_failures" -ge "$MAX_RETRIES" ]; then
                log_error "Too many consecutive failures ($consecutive_failures). Stopping."
                break
            fi

            # Wait before retrying
            log_info "Waiting ${RETRY_DELAY}s before next task..."
            sleep "$RETRY_DELAY"
        fi

        # Update status
        write_status "running" "Completed $TASKS_COMPLETED of $TOTAL_TASKS tasks"

        # Clear current task
        CURRENT_TASK_ID=""
        CURRENT_TASK_TITLE=""

        # Small delay between tasks
        if ! $DRY_RUN; then
            sleep 2
        fi
    done

    log_info "=========================================="
    log_info "Ralph Wiggum Complete"
    log_info "Tasks completed: $TASKS_COMPLETED"
    log_info "Tasks failed: $TASKS_FAILED"
    log_info "=========================================="

    # Final sync
    if ! $DRY_RUN; then
        log_info "Final beads sync..."
        (cd "$BEADS_DIR" && bd sync 2>/dev/null) || true
        (cd "$BEADS_DIR" && git push origin main 2>/dev/null) || true
    fi
}

# Run main
main
