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
#   WORKSPACE_DIR - Base workspace directory (auto-detected: /workspace in container, or parent of script)
#   BEADS_DIR     - Directory containing .beads/ (default: $WORKSPACE_DIR/home-server)
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
BEADS_DIR="${BEADS_DIR:-$WORKSPACE_DIR/home-server}"
# Store runtime files in script directory (works both in container and locally)
STATUS_FILE="${STATUS_FILE:-$SCRIPT_DIR/.ralph-wiggum-status.json}"
CONTROL_FILE="${CONTROL_FILE:-$SCRIPT_DIR/.ralph-wiggum-control}"
LOG_FILE="${LOG_FILE:-$SCRIPT_DIR/.ralph-wiggum.log}"
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
TYPE_FILTER="task"  # Default to task to skip epics
SORT_ORDER="oldest"  # Default to oldest for logical ordering
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
        -t|--type)
            TYPE_FILTER="$2"
            shift 2
            ;;
        -s|--sort)
            SORT_ORDER="$2"
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
            echo "  -t, --type TYPE        Filter by type: task, bug, feature, epic (default: task)"
            echo "  -s, --sort ORDER       Sort order: oldest, priority, hybrid (default: oldest)"
            echo "  -m, --max NUM          Maximum number of tasks to process (0=unlimited)"
            echo "  -n, --dry-run          Show tasks without executing"
            echo "  -v, --verbose          Verbose output"
            echo "  -h, --help             Show this help"
            echo ""
            echo "Environment:"
            echo "  WORKSPACE_DIR Base workspace directory (auto-detected)"
            echo "  BEADS_DIR     Directory with .beads/ (default: \$WORKSPACE_DIR/home-server)"
            echo "  STATUS_FILE   JSON status file (default: script directory)"
            echo "  CONTROL_FILE  Control file for stop commands (default: script directory)"
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

# Extract repo from labels (looks for repo:* pattern)
# Returns the repo directory path or empty string if not found
get_repo_from_labels() {
    local labels="$1"

    # Look for repo:* pattern in labels
    local repo
    repo=$(echo "$labels" | tr ',' '\n' | grep -E '^repo:' | head -1 | sed 's/^repo://')

    if [ -n "$repo" ]; then
        echo "$WORKSPACE_DIR/$repo"
    else
        echo ""
    fi
}

# Use Claude to intelligently determine working directory
# Returns repo path or empty string if unable to determine
determine_working_dir_with_llm() {
    local task_json="$1"

    local title
    local description
    local labels
    title=$(echo "$task_json" | jq -r '.title // ""')
    description=$(echo "$task_json" | jq -r '.description // ""')
    labels=$(echo "$task_json" | jq -r '.labels // [] | join(", ")')

    # List available repos
    local available_repos
    available_repos=$(ls -d "$WORKSPACE_DIR"/*/ 2>/dev/null | xargs -I{} basename {} | tr '\n' ', ' | sed 's/,$//')

    local prompt
    prompt=$(cat << EOF
You need to determine which repository this task should be worked on in.

Task Title: $title
Task Description: $description
Task Labels: $labels

Available repositories in the workspace:
$available_repos

Based on the task information, respond with ONLY the repository name (e.g., "polyjuiced" or "home-server").
If you cannot determine the correct repository, respond with "UNKNOWN".
Do not include any other text or explanation.
EOF
)

    local result
    result=$(claude -p "$prompt" 2>/dev/null | tr -d '[:space:]' | head -1)

    # Validate the result is an actual repo
    if [ -n "$result" ] && [ "$result" != "UNKNOWN" ] && [ -d "$WORKSPACE_DIR/$result" ]; then
        echo "$WORKSPACE_DIR/$result"
    else
        echo ""
    fi
}

# Get working directory for a task
# Priority: 1) repo:* label, 2) LLM determination, 3) fail
get_working_dir() {
    local task_json="$1"
    local labels
    labels=$(echo "$task_json" | jq -r '.labels // [] | join(",")')

    # First try to get repo from labels
    local repo_dir
    repo_dir=$(get_repo_from_labels "$labels")

    if [ -n "$repo_dir" ]; then
        echo "$repo_dir"
        return 0
    fi

    # No repo label found, try LLM determination
    log_warn "No repo:* label found, using LLM to determine working directory..."
    repo_dir=$(determine_working_dir_with_llm "$task_json")

    if [ -n "$repo_dir" ]; then
        log_info "LLM determined working directory: $repo_dir"
        echo "$repo_dir"
        return 0
    fi

    # Could not determine, return empty to signal failure
    echo ""
    return 1
}

# Pull all git repos in workspace to ensure we have latest code
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
                # Try to handle dirty working tree
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

    # Note: --type is not supported by bd ready, filter client-side
    if [ -n "$SORT_ORDER" ]; then
        cmd="$cmd --sort $SORT_ORDER"
    fi

    # Use high limit to get accurate count (bd ready defaults to 10)
    cmd="$cmd --limit 1000"

    local jq_filter='length'
    if [ -n "$TYPE_FILTER" ]; then
        jq_filter="[.[] | select(.issue_type == \"$TYPE_FILTER\")] | length"
    fi

    count=$(cd "$BEADS_DIR" && eval "$cmd" 2>/dev/null | jq "$jq_filter" 2>/dev/null || echo "0")
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

    # Note: --type is not supported by bd ready, filter client-side
    if [ -n "$SORT_ORDER" ]; then
        cmd="$cmd --sort $SORT_ORDER"
    fi

    if $VERBOSE; then
        log_info "Running: $cmd (in $BEADS_DIR)"
    fi

    # Run query from beads directory and get first task
    local result
    result=$(cd "$BEADS_DIR" && eval "$cmd" 2>/dev/null || echo "[]")

    # Apply type filter client-side and return first task as JSON
    local jq_filter='.[0] // empty'
    if [ -n "$TYPE_FILTER" ]; then
        jq_filter="[.[] | select(.issue_type == \"$TYPE_FILTER\")] | .[0] // empty"
    fi
    echo "$result" | jq -r "$jq_filter"
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
    task_type=$(echo "$task_json" | jq -r '.issue_type // "task"')
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

# Build review prompt for fresh-eyes verification of completed work
build_review_prompt() {
    local task_json="$1"
    local working_dir="$2"

    local title
    local description
    local task_type
    local labels

    title=$(echo "$task_json" | jq -r '.title // "Unknown task"')
    description=$(echo "$task_json" | jq -r '.description // ""')
    task_type=$(echo "$task_json" | jq -r '.issue_type // "task"')
    labels=$(echo "$task_json" | jq -r '.labels // [] | join(", ")')

    cat << EOF
You are reviewing a recently completed task with fresh eyes.

## Task That Was Completed
- **Title**: $title
- **Type**: $task_type
- **Labels**: $labels
- **Working Directory**: $working_dir

## Task Description
$description

## Your Review Mission

You are performing a final review of this completed work. Your job is to:

1. **Read Context Documents First**:
   - Read AGENTS.md in the working directory for project context
   - Look for any plan documents in agents/plans/ related to this task or feature
   - Check agents/reference/ for relevant architectural documents
   - If this task references a parent epic or plan, find and read it

2. **Review Recent Changes**:
   - Run \`git log --oneline -10\` to see recent commits
   - Run \`git diff HEAD~3..HEAD\` to examine what was changed (adjust range as needed)
   - Examine the actual code changes made

3. **Verify Architectural Fit**:
   - Does the implementation align with the project's architecture documented in AGENTS.md?
   - Does it follow the patterns and conventions of the codebase?
   - Are there any plans in agents/plans/ that this task relates to? Does the implementation fit the plan?
   - If part of a larger feature, does it integrate properly with existing or planned components?

4. **Check Completeness**:
   - Does the implementation fully address the task requirements?
   - Are there any edge cases or scenarios not handled?
   - Were tests added or updated if applicable?
   - Is the code properly committed and pushed?

5. **Identify Issues**:
   - If you find problems, list them clearly
   - If minor issues exist that don't block completion, note them but don't block
   - If major issues exist that mean the task isn't actually done, clearly state "REVIEW_FAILED"

## Output Format

End your review with EXACTLY one of these lines:
- \`REVIEW_PASSED\` - The implementation is solid and fits the architecture
- \`REVIEW_PASSED_WITH_NOTES: <brief notes>\` - Minor issues noted but acceptable
- \`REVIEW_FAILED: <reason>\` - Major issues found, task should not be marked complete

Be thorough but practical. Minor style issues don't warrant failing a review.
Focus on whether the work actually accomplishes the task and fits the project's direction.
EOF
}

# Run fresh-eyes review on completed task
run_review() {
    local task_json="$1"
    local working_dir="$2"
    local task_id="$3"

    log_info "Running fresh-eyes review for task: $task_id"

    if $DRY_RUN; then
        log_info "[DRY RUN] Would run review for task"
        return 0
    fi

    # Build review prompt
    local review_prompt
    review_prompt=$(build_review_prompt "$task_json" "$working_dir")

    # Create temp file for prompt
    local prompt_file
    prompt_file=$(mktemp)
    echo "$review_prompt" > "$prompt_file"

    # Change to working directory
    cd "$working_dir"

    # Run claude for review and capture output
    local review_output
    local exit_code=0
    review_output=$(claude -p "$(cat "$prompt_file")" 2>&1) || exit_code=$?

    # Clean up
    rm -f "$prompt_file"

    if [ $exit_code -ne 0 ]; then
        log_warn "Review claude invocation failed with exit code $exit_code"
        log_warn "Treating as passed to avoid blocking (review is advisory)"
        return 0
    fi

    # Log review output for debugging
    if $VERBOSE; then
        log_info "Review output: $review_output"
    fi

    # Check for REVIEW_FAILED in output
    if echo "$review_output" | grep -q "REVIEW_FAILED"; then
        local failure_reason
        failure_reason=$(echo "$review_output" | grep -o "REVIEW_FAILED:.*" | head -1)
        log_error "Review failed: $failure_reason"
        return 1
    fi

    # Check for passes
    if echo "$review_output" | grep -q "REVIEW_PASSED_WITH_NOTES"; then
        local notes
        notes=$(echo "$review_output" | grep -o "REVIEW_PASSED_WITH_NOTES:.*" | head -1)
        log_success "Review passed with notes: $notes"
        return 0
    fi

    if echo "$review_output" | grep -q "REVIEW_PASSED"; then
        log_success "Review passed"
        return 0
    fi

    # Default to passed if no explicit result (be lenient)
    log_warn "Review completed without explicit result, treating as passed"
    return 0
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

# Check if a task's parent epic has all children completed, and close it if so
check_and_close_parent_epic() {
    local task_id="$1"

    if $DRY_RUN; then
        return 0
    fi

    # Get task's parent (if any)
    local task_json
    task_json=$(run_bd show "$task_id" --json 2>/dev/null) || return 0

    local parent_id
    parent_id=$(echo "$task_json" | jq -r '.[0].parent // empty')

    if [ -z "$parent_id" ]; then
        return 0  # No parent
    fi

    # Check if parent is an epic
    local parent_json
    parent_json=$(run_bd show "$parent_id" --json 2>/dev/null) || return 0

    local parent_type
    parent_type=$(echo "$parent_json" | jq -r '.[0].issue_type // empty')

    if [ "$parent_type" != "epic" ]; then
        return 0  # Parent is not an epic
    fi

    local parent_status
    parent_status=$(echo "$parent_json" | jq -r '.[0].status // empty')

    if [ "$parent_status" != "open" ] && [ "$parent_status" != "in_progress" ]; then
        return 0  # Parent already closed
    fi

    # Get all children of the parent epic
    local children
    children=$(echo "$parent_json" | jq -r '.[0].children // []')

    if [ "$children" = "[]" ] || [ -z "$children" ]; then
        return 0  # No children
    fi

    # Check if all children are closed
    local all_closed=true
    for child_id in $(echo "$children" | jq -r '.[]'); do
        local child_json
        child_json=$(run_bd show "$child_id" --json 2>/dev/null) || continue

        local child_status
        child_status=$(echo "$child_json" | jq -r '.[0].status // "open"')

        if [ "$child_status" != "closed" ]; then
            all_closed=false
            break
        fi
    done

    if $all_closed; then
        local parent_title
        parent_title=$(echo "$parent_json" | jq -r '.[0].title // "Unknown"')

        log_info "All children of epic '$parent_id' are complete. Auto-closing epic."
        run_bd close "$parent_id" --reason "All children completed by Ralph Wiggum"

        # Commit the epic closure
        (
            cd "$BEADS_DIR"
            if [ -d ".beads" ]; then
                git add .beads/
                git commit -m "close epic: $parent_id - All children completed" || true
            fi
        )

        log_success "Auto-closed epic: $parent_id - $parent_title"

        # Recursively check if this epic's parent should also be closed
        check_and_close_parent_epic "$parent_id"
    fi
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

    # Check if parent epic should be auto-closed
    check_and_close_parent_epic "$task_id"

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
    log_info "Type filter: ${TYPE_FILTER:-<none>}"
    log_info "Sort order: ${SORT_ORDER:-hybrid}"
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

    # Pull all repos to ensure we're working with latest code
    pull_all_repos

    # Count initial tasks
    REMAINING_TASKS=$(count_ready_tasks)
    log_info "Found $REMAINING_TASKS ready tasks with label '$LABEL_FILTER'"

    if [ "$REMAINING_TASKS" -eq 0 ]; then
        log_info "No tasks to process. Exiting."
        write_status "completed" "No tasks found with label '$LABEL_FILTER'"
        exit 0
    fi

    write_status "running" "Processing tasks"

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
        log_info "Task $task_num ($REMAINING_TASKS remaining): $CURRENT_TASK_ID"
        log_info "Title: $CURRENT_TASK_TITLE"
        log_info "Labels: $task_labels"
        log_info "=========================================="

        # Determine working directory from repo:* label or LLM
        local working_dir
        working_dir=$(get_working_dir "$task_json")

        # If no working directory could be determined, fail loudly and exit
        if [ -z "$working_dir" ]; then
            log_error "FATAL: Could not determine working directory for task $CURRENT_TASK_ID"
            log_error "Task has no repo:* label and LLM could not determine the correct repository."
            log_error "Please add a repo:* label to this task (e.g., repo:polyjuiced, repo:home-server)"
            fail_task "$CURRENT_TASK_ID" "Could not determine working directory - missing repo:* label"
            write_status "failed" "Could not determine working directory for $CURRENT_TASK_ID"
            exit 1
        fi

        log_info "Working directory: $working_dir"

        # Update status
        write_status "running" "Working on task $task_num ($REMAINING_TASKS remaining)"

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

            # Run fresh-eyes review before marking complete
            write_status "running" "Reviewing task $task_num with fresh eyes"
            if run_review "$task_json" "$working_dir" "$CURRENT_TASK_ID"; then
                complete_task "$CURRENT_TASK_ID" "Completed by Ralph Wiggum autonomous loop"
                ((TASKS_COMPLETED++))
                consecutive_failures=0
            else
                log_error "Fresh-eyes review failed for task $CURRENT_TASK_ID"
                fail_task "$CURRENT_TASK_ID" "Review failed - implementation may not fit architecture/plan"
                ((TASKS_FAILED++))
                ((consecutive_failures++))
            fi
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

        # Re-count remaining tasks (completing tasks may unblock new ones)
        REMAINING_TASKS=$(count_ready_tasks)

        # Update status
        write_status "running" "Completed $TASKS_COMPLETED tasks, $REMAINING_TASKS remaining"

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
