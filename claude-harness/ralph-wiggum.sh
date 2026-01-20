#!/bin/bash
# Ralph Wiggum - Autonomous Task Loop for Claude Harness
#
# "Me fail English? That's unpossible!"
#
# This script runs inside the claude-harness container and:
# 1. Parses tasks.md for ready tasks (filtered by label/priority)
# 2. Claims each task (updates status to IN_PROGRESS)
# 3. Runs Claude with the task as a prompt
# 4. Marks tasks complete or failed (updates status in tasks.md)
# 5. Loops until no more ready tasks or stop requested
#
# Works directly with tasks.md - no external API required.
#
# Usage:
#   ./ralph-wiggum.sh --label mercury         # Process mercury-labeled tasks
#   ./ralph-wiggum.sh --label trading-bot     # Only trading-bot tasks
#   ./ralph-wiggum.sh --priority 0            # Only critical priority
#   ./ralph-wiggum.sh --dry-run               # Show what would run
#   ./ralph-wiggum.sh --max 5                 # Max 5 tasks then stop
#
# Environment variables:
#   WORKSPACE_DIR - Base workspace directory (auto-detected: /workspace in container, or parent of script)
#   TASKS_FILE    - Path to tasks.md (default: $WORKSPACE_DIR/home-server/tasks.md)
#   STATUS_FILE   - JSON status file path (default: script directory)
#   CONTROL_FILE  - Control commands file (default: script directory)

set -uo pipefail

# Determine script directory for relative path resolution
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Auto-detect workspace: use /workspace if it exists (container), otherwise derive from script location
# Script is at: <workspace>/homelab-ai/claude-harness/ralph-wiggum.sh
if [ -d "/workspace" ]; then
    DEFAULT_WORKSPACE="/workspace"
else
    # Go up two levels: claude-harness -> homelab-ai -> workspace
    DEFAULT_WORKSPACE="$(cd "$SCRIPT_DIR/../.." && pwd)"
fi

# Configuration from environment or defaults
WORKSPACE_DIR="${WORKSPACE_DIR:-$DEFAULT_WORKSPACE}"
TASKS_FILE="${TASKS_FILE:-$WORKSPACE_DIR/home-server/tasks.md}"
# Store runtime files in script directory (works both in container and locally)
STATUS_FILE="${STATUS_FILE:-$SCRIPT_DIR/.ralph-wiggum-status.json}"
CONTROL_FILE="${CONTROL_FILE:-$SCRIPT_DIR/.ralph-wiggum-control}"
LOG_FILE="${LOG_FILE:-$SCRIPT_DIR/.ralph-wiggum.log}"
MAX_RETRIES=3
RETRY_DELAY=10

# Metrics endpoint for observability
METRICS_ENDPOINT="${METRICS_ENDPOINT:-http://llm-router:8013/metrics/harness}"

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
            echo "  WORKSPACE_DIR   Base workspace directory (auto-detected)"
            echo "  TASKS_FILE      Path to tasks.md (default: \$WORKSPACE_DIR/home-server/tasks.md)"
            echo "  STATUS_FILE     JSON status file (default: script directory)"
            echo "  CONTROL_FILE    Control file for stop commands (default: script directory)"
            echo ""
            echo "Examples:"
            echo "  ./ralph-wiggum.sh --label mercury"
            echo "  ./ralph-wiggum.sh --label multi-ralph --priority 1 --max 3"
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
REMAINING_TASKS=0
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

# Emit metrics to LLM router for observability
emit_metric() {
    local event_type="$1"
    local task_id="${2:-}"
    local duration_ms="${3:-0}"
    local success="${4:-true}"
    local error_msg="${5:-}"

    # Don't emit metrics in dry run mode
    if $DRY_RUN; then
        return 0
    fi

    # Build JSON payload
    local payload
    payload=$(cat << EOF
{
    "source": "ralph",
    "event": "$event_type",
    "label": "$LABEL_FILTER",
    "task_id": "$task_id",
    "task_title": "$CURRENT_TASK_TITLE",
    "duration_ms": $duration_ms,
    "success": $success,
    "error": $([ -n "$error_msg" ] && echo "\"$error_msg\"" || echo "null"),
    "completed_tasks": $TASKS_COMPLETED,
    "failed_tasks": $TASKS_FAILED,
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
)

    # Post to metrics endpoint (fire and forget, don't fail on errors)
    curl -sf -X POST "$METRICS_ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "$payload" \
        --max-time 5 \
        2>/dev/null || true
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
  "remaining_tasks": $REMAINING_TASKS,
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

# Parse tasks.md and extract tasks as JSON
# Returns array of task objects matching filters
parse_tasks() {
    local status_filter="${1:-OPEN}"
    local label_filter="${2:-}"
    local priority_filter="${3:-}"

    if [ ! -f "$TASKS_FILE" ]; then
        echo "[]"
        return
    fi

    # Use awk to parse the markdown task format
    awk -v status="$status_filter" -v label="$label_filter" -v priority="$priority_filter" '
    BEGIN {
        in_task = 0
        task_count = 0
        printf "["
    }

    # Match task header: ### [STATUS] Title {#task-id}
    /^### \[/ {
        # Close previous task if any
        if (in_task && match_found) {
            if (task_count > 0) printf ","
            printf "{\"id\":\"%s\",\"title\":\"%s\",\"status\":\"%s\",\"priority\":%d,\"repo\":\"%s\",\"labels\":\"%s\",\"description\":\"%s\"}",
                task_id, task_title, task_status, task_priority, task_repo, task_labels, task_desc
            task_count++
        }

        # Parse new task header
        in_task = 1
        match_found = 0
        task_desc = ""
        task_priority = 2
        task_repo = ""
        task_labels = ""

        # Extract status
        match($0, /\[([A-Z_]+)\]/, arr)
        task_status = arr[1]

        # Extract title (between ] and {#)
        gsub(/^### \[[A-Z_]+\] /, "")
        gsub(/ \{#.*$/, "")
        task_title = $0
        # Escape quotes in title
        gsub(/"/, "\\\"", task_title)

        # Extract task ID
        match($0, /\{#([^}]+)\}/, arr)
        task_id = arr[1]

        # Check status filter
        if (task_status == status) {
            match_found = 1
        }
        next
    }

    # Parse metadata table row
    in_task && /^\| P[0-3] / {
        # Extract priority, repo, labels from table row
        split($0, parts, "|")
        if (length(parts) >= 4) {
            gsub(/^[ \t]+|[ \t]+$/, "", parts[2])  # priority
            gsub(/^[ \t]+|[ \t]+$/, "", parts[3])  # repo
            gsub(/^[ \t]+|[ \t]+$/, "", parts[4])  # labels

            # Parse priority (P0, P1, P2, P3)
            if (match(parts[2], /P([0-3])/, arr)) {
                task_priority = arr[1]
            }
            task_repo = parts[3]
            task_labels = parts[4]

            # Apply label filter
            if (label != "" && match_found) {
                if (index(task_labels, label) == 0) {
                    match_found = 0
                }
            }

            # Apply priority filter
            if (priority != "" && match_found) {
                if (task_priority != priority) {
                    match_found = 0
                }
            }
        }
        next
    }

    # Collect description lines (skip table headers and separators)
    in_task && !/^\|/ && !/^---/ && !/^#### / && !/^```/ {
        if (task_desc != "") task_desc = task_desc "\\n"
        line = $0
        gsub(/"/, "\\\"", line)
        task_desc = task_desc line
    }

    END {
        # Output last task if matches
        if (in_task && match_found) {
            if (task_count > 0) printf ","
            printf "{\"id\":\"%s\",\"title\":\"%s\",\"status\":\"%s\",\"priority\":%d,\"repo\":\"%s\",\"labels\":\"%s\",\"description\":\"%s\"}",
                task_id, task_title, task_status, task_priority, task_repo, task_labels, task_desc
        }
        printf "]"
    }
    ' "$TASKS_FILE"
}

# Count ready tasks
count_ready_tasks() {
    local tasks
    tasks=$(parse_tasks "OPEN" "$LABEL_FILTER" "$PRIORITY_FILTER")
    echo "$tasks" | jq 'length' 2>/dev/null || echo "0"
}

# Get the next ready task
get_next_task() {
    local tasks
    tasks=$(parse_tasks "OPEN" "$LABEL_FILTER" "$PRIORITY_FILTER")
    echo "$tasks" | jq -r '.[0] // empty' 2>/dev/null
}

# Update task status in tasks.md
update_task_status() {
    local task_id="$1"
    local new_status="$2"

    if $DRY_RUN; then
        log_info "[DRY RUN] Would update task $task_id to status $new_status"
        return 0
    fi

    # Use sed to update the task status
    # Match: ### [OLD_STATUS] Title {#task-id}
    # Replace with: ### [NEW_STATUS] Title {#task-id}
    sed -i "s/^### \[[A-Z_]*\] \(.*{#${task_id}}\)$/### [${new_status}] \1/" "$TASKS_FILE"

    if [ $? -eq 0 ]; then
        log_info "Updated task $task_id to $new_status"
        return 0
    else
        log_error "Failed to update task $task_id"
        return 1
    fi
}

# Commit and push tasks.md changes
sync_tasks() {
    if $DRY_RUN; then
        log_info "[DRY RUN] Would commit and push tasks.md"
        return 0
    fi

    local tasks_dir
    tasks_dir=$(dirname "$TASKS_FILE")

    (
        cd "$tasks_dir" || return 1

        # Check if there are changes
        if git diff --quiet tasks.md 2>/dev/null; then
            log_info "No changes to tasks.md"
            return 0
        fi

        git add tasks.md
        git commit -m "Ralph Wiggum: Update task statuses

Completed: $TASKS_COMPLETED, Failed: $TASKS_FAILED
Label: $LABEL_FILTER"

        if git push origin HEAD 2>&1; then
            log_success "Synced tasks.md to remote"
        else
            log_warn "Could not push tasks.md - may need manual push"
        fi
    )
}

# Get working directory from task repo field
get_working_dir() {
    local task_json="$1"
    local repo
    repo=$(echo "$task_json" | jq -r '.repo // ""')

    if [ -n "$repo" ] && [ -d "$WORKSPACE_DIR/$repo" ]; then
        echo "$WORKSPACE_DIR/$repo"
        return 0
    fi

    # Fallback: try to extract from labels
    local labels
    labels=$(echo "$task_json" | jq -r '.labels // ""')

    # Look for repo:* pattern in labels
    local repo_from_label
    repo_from_label=$(echo "$labels" | tr ',' '\n' | grep -E '^repo:' | head -1 | sed 's/^repo://')

    if [ -n "$repo_from_label" ] && [ -d "$WORKSPACE_DIR/$repo_from_label" ]; then
        echo "$WORKSPACE_DIR/$repo_from_label"
        return 0
    fi

    # Could not determine
    echo ""
    return 1
}

# Pull all git repos in workspace
pull_all_repos() {
    log_info "Pulling all repos in workspace..."
    local failed_repos=""

    for dir in "$WORKSPACE_DIR"/*/; do
        if [ -d "$dir/.git" ]; then
            local repo_name
            repo_name=$(basename "$dir")

            if (cd "$dir" && git fetch origin --prune 2>/dev/null && git pull --rebase 2>/dev/null); then
                if $VERBOSE; then
                    log_info "  Pulled: $repo_name"
                fi
            else
                if (cd "$dir" && git stash 2>/dev/null && git pull --rebase 2>/dev/null && git stash pop 2>/dev/null); then
                    log_warn "  Pulled with stash: $repo_name"
                else
                    log_warn "  Failed to pull: $repo_name (may have conflicts)"
                    failed_repos="$failed_repos $repo_name"
                fi
            fi
        fi
    done

    if [ -n "$failed_repos" ]; then
        log_warn "Some repos failed to pull:$failed_repos"
    else
        log_success "All repos pulled successfully"
    fi
}

# Claim a task
claim_task() {
    local task_id="$1"
    local task_title="$2"

    log_info "Claiming task: $task_id - $task_title"
    update_task_status "$task_id" "IN_PROGRESS"
}

# Complete a task
complete_task() {
    local task_id="$1"
    log_success "Completing task: $task_id"
    update_task_status "$task_id" "CLOSED"
}

# Mark task as failed (return to OPEN with note)
fail_task() {
    local task_id="$1"
    local reason="$2"

    log_error "Task failed: $task_id - $reason"
    update_task_status "$task_id" "OPEN"
    log_warn "Task $task_id returned to OPEN status. Manual review needed."
}

# Build prompt from task
build_prompt() {
    local task_json="$1"
    local working_dir="$2"

    local title description priority labels repo

    title=$(echo "$task_json" | jq -r '.title // "Unknown task"')
    description=$(echo "$task_json" | jq -r '.description // ""' | sed 's/\\n/\n/g')
    priority=$(echo "$task_json" | jq -r '.priority // 2')
    labels=$(echo "$task_json" | jq -r '.labels // ""')
    repo=$(echo "$task_json" | jq -r '.repo // ""')

    cat << EOF
You are working on the following task from the task tracker.

## Task Details
- **Title**: $title
- **Priority**: $priority (0=critical, 1=high, 2=medium, 3=low)
- **Labels**: $labels
- **Repo**: $repo
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
- Commit and push all changes before completing

Work autonomously to complete this task. If you encounter blockers that cannot be resolved, note them in your summary.

Begin working on this task now.
EOF
}

# Build review prompt
build_review_prompt() {
    local task_json="$1"
    local working_dir="$2"

    local title description labels

    title=$(echo "$task_json" | jq -r '.title // "Unknown task"')
    description=$(echo "$task_json" | jq -r '.description // ""' | sed 's/\\n/\n/g')
    labels=$(echo "$task_json" | jq -r '.labels // ""')

    cat << EOF
You are reviewing a recently completed task with fresh eyes.

## Task That Was Completed
- **Title**: $title
- **Labels**: $labels
- **Working Directory**: $working_dir

## Task Description
$description

## Your Review Mission

1. **Read Context Documents First**: Read AGENTS.md in the working directory
2. **Review Recent Changes**: Run \`git log --oneline -10\` and \`git diff HEAD~3..HEAD\`
3. **Verify Completeness**: Does the implementation fully address the task?
4. **Check Quality**: Are there any issues with the implementation?

## Output Format

End your review with EXACTLY one of these lines:
- \`REVIEW_PASSED\` - The implementation is solid
- \`REVIEW_PASSED_WITH_NOTES: <brief notes>\` - Minor issues noted but acceptable
- \`REVIEW_FAILED: <reason>\` - Major issues found
EOF
}

# Run fresh-eyes review
run_review() {
    local task_json="$1"
    local working_dir="$2"
    local task_id="$3"

    log_info "Running fresh-eyes review for task: $task_id"

    if $DRY_RUN; then
        log_info "[DRY RUN] Would run review for task"
        return 0
    fi

    local review_prompt
    review_prompt=$(build_review_prompt "$task_json" "$working_dir")

    cd "$working_dir"

    local review_output exit_code=0
    review_output=$(claude -p "$review_prompt" 2>&1) || exit_code=$?

    if [ $exit_code -ne 0 ]; then
        log_warn "Review claude invocation failed, treating as passed"
        return 0
    fi

    if echo "$review_output" | grep -q "REVIEW_FAILED"; then
        local failure_reason
        failure_reason=$(echo "$review_output" | grep -o "REVIEW_FAILED:.*" | head -1)
        log_error "Review failed: $failure_reason"
        return 1
    fi

    if echo "$review_output" | grep -q "REVIEW_PASSED"; then
        log_success "Review passed"
        return 0
    fi

    log_warn "Review completed without explicit result, treating as passed"
    return 0
}

# Commit changes from working directory
commit_changes() {
    local working_dir="$1"
    local task_id="$2"
    local task_title="$3"

    log_info "Committing changes from: $working_dir"

    if $DRY_RUN; then
        log_info "[DRY RUN] Would commit and push changes"
        return 0
    fi

    (
        cd "$working_dir" || return 1

        if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
            log_info "No changes to commit in $working_dir"
            return 0
        fi

        git add -A
        local commit_msg="Ralph - $task_id: $task_title"
        if git commit -m "$commit_msg"; then
            log_success "Committed changes: $commit_msg"
        else
            log_warn "Nothing to commit or commit failed"
            return 0
        fi

        if git push origin HEAD 2>&1; then
            log_success "Pushed changes to origin"
        else
            log_warn "Could not push changes"
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
        return 0
    fi

    local prompt_file
    prompt_file=$(mktemp)
    echo "$prompt" > "$prompt_file"

    cd "$working_dir"
    git fetch origin --prune 2>/dev/null || true
    git pull origin main 2>/dev/null || git pull 2>/dev/null || true

    local exit_code=0
    if claude -p "$(cat "$prompt_file")" 2>&1; then
        exit_code=0
    else
        exit_code=$?
    fi

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
    log_info "Tasks file: $TASKS_FILE"
    log_info ""

    # Verify tasks.md exists
    if [ ! -f "$TASKS_FILE" ]; then
        log_error "Tasks file not found: $TASKS_FILE"
        write_status "failed" "Tasks file not found"
        exit 1
    fi
    log_info "Tasks file exists"

    # Pull all repos
    pull_all_repos

    # Count initial tasks
    REMAINING_TASKS=$(count_ready_tasks)
    log_info "Found $REMAINING_TASKS ready tasks with label '$LABEL_FILTER'"

    emit_metric "session_started" "" 0 true

    if [ "$REMAINING_TASKS" -eq 0 ]; then
        log_info "No tasks to process. Exiting."
        write_status "completed" "No tasks found with label '$LABEL_FILTER'"
        exit 0
    fi

    write_status "running" "Processing tasks"

    local consecutive_failures=0

    while true; do
        if check_stop_requested; then
            log_info "Stop requested. Finishing up."
            write_status "stopping" "Stop requested"
            break
        fi

        if [ "$MAX_TASKS" -gt 0 ] && [ "$TASKS_COMPLETED" -ge "$MAX_TASKS" ]; then
            log_info "Reached maximum tasks ($MAX_TASKS). Stopping."
            break
        fi

        local task_json
        task_json=$(get_next_task)

        if [ -z "$task_json" ]; then
            log_info "No more ready tasks. Ralph Wiggum is done!"
            break
        fi

        CURRENT_TASK_ID=$(echo "$task_json" | jq -r '.id')
        CURRENT_TASK_TITLE=$(echo "$task_json" | jq -r '.title')
        local task_labels
        task_labels=$(echo "$task_json" | jq -r '.labels // ""')

        local task_num=$((TASKS_COMPLETED + TASKS_FAILED + 1))
        log_info "=========================================="
        log_info "Task $task_num ($REMAINING_TASKS remaining): $CURRENT_TASK_ID"
        log_info "Title: $CURRENT_TASK_TITLE"
        log_info "Labels: $task_labels"
        log_info "=========================================="

        local working_dir
        working_dir=$(get_working_dir "$task_json")

        if [ -z "$working_dir" ]; then
            log_error "FATAL: Could not determine working directory for task $CURRENT_TASK_ID"
            log_error "Please add a 'repo' field to this task"
            fail_task "$CURRENT_TASK_ID" "Could not determine working directory"
            write_status "failed" "Could not determine working directory for $CURRENT_TASK_ID"
            exit 1
        fi

        log_info "Working directory: $working_dir"
        write_status "running" "Working on task $task_num ($REMAINING_TASKS remaining)"

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

        claim_task "$CURRENT_TASK_ID" "$CURRENT_TASK_TITLE"

        local task_start_time
        task_start_time=$(date +%s%3N)

        emit_metric "task_started" "$CURRENT_TASK_ID" 0 true

        local prompt
        prompt=$(build_prompt "$task_json" "$working_dir")

        if run_claude "$prompt" "$working_dir" "$CURRENT_TASK_ID"; then
            commit_changes "$working_dir" "$CURRENT_TASK_ID" "$CURRENT_TASK_TITLE"

            write_status "running" "Reviewing task $task_num with fresh eyes"
            if run_review "$task_json" "$working_dir" "$CURRENT_TASK_ID"; then
                complete_task "$CURRENT_TASK_ID"
                ((TASKS_COMPLETED++))
                consecutive_failures=0

                local task_end_time task_duration_ms
                task_end_time=$(date +%s%3N)
                task_duration_ms=$((task_end_time - task_start_time))
                emit_metric "task_completed" "$CURRENT_TASK_ID" "$task_duration_ms" true
            else
                log_error "Fresh-eyes review failed for task $CURRENT_TASK_ID"
                fail_task "$CURRENT_TASK_ID" "Review failed"
                ((TASKS_FAILED++))
                ((consecutive_failures++))

                local task_end_time task_duration_ms
                task_end_time=$(date +%s%3N)
                task_duration_ms=$((task_end_time - task_start_time))
                emit_metric "task_failed" "$CURRENT_TASK_ID" "$task_duration_ms" false "Review failed"
            fi
        else
            fail_task "$CURRENT_TASK_ID" "Claude execution failed"
            ((TASKS_FAILED++))
            ((consecutive_failures++))

            local task_end_time task_duration_ms
            task_end_time=$(date +%s%3N)
            task_duration_ms=$((task_end_time - task_start_time))
            emit_metric "task_failed" "$CURRENT_TASK_ID" "$task_duration_ms" false "Claude execution failed"

            if [ "$consecutive_failures" -ge "$MAX_RETRIES" ]; then
                log_error "Too many consecutive failures ($consecutive_failures). Stopping."
                break
            fi

            log_info "Waiting ${RETRY_DELAY}s before next task..."
            sleep "$RETRY_DELAY"
        fi

        REMAINING_TASKS=$(count_ready_tasks)
        write_status "running" "Completed $TASKS_COMPLETED tasks, $REMAINING_TASKS remaining"

        CURRENT_TASK_ID=""
        CURRENT_TASK_TITLE=""

        if ! $DRY_RUN; then
            sleep 2
        fi
    done

    log_info "=========================================="
    log_info "Ralph Wiggum Complete"
    log_info "Tasks completed: $TASKS_COMPLETED"
    log_info "Tasks failed: $TASKS_FAILED"
    log_info "=========================================="

    emit_metric "session_completed" "" 0 true

    # Sync tasks.md to remote
    if ! $DRY_RUN; then
        log_info "Final tasks sync..."
        sync_tasks
    fi
}

# Run main
main
