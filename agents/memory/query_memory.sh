#!/bin/bash
#
# Memory Query Helper Script
# Fallback tool for querying agent memory when MCP tools are not available
#
# Usage:
#   ./query_memory.sh [command] [options]
#
# Commands:
#   decisions [--project PROJECT] [--limit N] [--search TEXT]
#   patterns [--severity low|medium|high] [--limit N] [--search TEXT]
#   search QUERY [--limit N]
#   recent [--limit N]
#   context [--task TASK]
#
# Examples:
#   ./query_memory.sh decisions --project home-server --limit 5
#   ./query_memory.sh patterns --severity high
#   ./query_memory.sh search "PostgreSQL database"
#   ./query_memory.sh recent --limit 10
#

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_PATH="${SCRIPT_DIR}/memory.db"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "Error: Memory database not found at $DB_PATH" >&2
    exit 1
fi

# Check if sqlite3 is available
if ! command -v sqlite3 &> /dev/null; then
    echo "Error: sqlite3 command not found. Please install sqlite3." >&2
    exit 1
fi

# Helper function to run SQLite query
run_query() {
    local query="$1"
    sqlite3 -header -column "$DB_PATH" "$query"
}

# Query decisions
query_decisions() {
    local project=""
    local limit=10
    local search=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --project)
                project="$2"
                shift 2
                ;;
            --limit)
                limit="$2"
                shift 2
                ;;
            --search)
                search="$2"
                shift 2
                ;;
            *)
                echo "Unknown option: $1" >&2
                exit 1
                ;;
        esac
    done
    
    local where_clauses=()
    
    if [ -n "$project" ]; then
        where_clauses+=("project='$project'")
    fi
    
    if [ -n "$search" ]; then
        where_clauses+=("(content LIKE '%$search%' OR rationale LIKE '%$search%')")
    fi
    
    local where=""
    if [ ${#where_clauses[@]} -gt 0 ]; then
        where="WHERE "
        local first=1
        for clause in "${where_clauses[@]}"; do
            if [ $first -eq 1 ]; then
                where="$where$clause"
                first=0
            else
                where="$where AND $clause"
            fi
        done
    fi
    
    run_query "SELECT id, content, rationale, project, task, importance, created_at FROM decisions $where ORDER BY created_at DESC LIMIT $limit;"
}

# Query patterns
query_patterns() {
    local severity=""
    local limit=10
    local search=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --severity)
                severity="$2"
                shift 2
                ;;
            --limit)
                limit="$2"
                shift 2
                ;;
            --search)
                search="$2"
                shift 2
                ;;
            *)
                echo "Unknown option: $1" >&2
                exit 1
                ;;
        esac
    done
    
    local where_clauses=()
    
    if [ -n "$severity" ]; then
        where_clauses+=("severity='$severity'")
    fi
    
    if [ -n "$search" ]; then
        where_clauses+=("(name LIKE '%$search%' OR description LIKE '%$search%' OR solution LIKE '%$search%')")
    fi
    
    local where=""
    if [ ${#where_clauses[@]} -gt 0 ]; then
        where="WHERE "
        local first=1
        for clause in "${where_clauses[@]}"; do
            if [ $first -eq 1 ]; then
                where="$where$clause"
                first=0
            else
                where="$where AND $clause"
            fi
        done
    fi
    
    run_query "SELECT id, name, description, solution, severity, frequency, created_at FROM patterns $where ORDER BY frequency DESC, created_at DESC LIMIT $limit;"
}

# Full-text search
search_memory() {
    local query="$1"
    local limit=20
    
    if [ -z "$query" ]; then
        echo "Error: Search query required" >&2
        exit 1
    fi
    
    while [[ $# -gt 1 ]]; do
        case $2 in
            --limit)
                limit="$3"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done
    
    echo "=== Decisions ==="
    run_query "SELECT id, content, project, created_at FROM decisions WHERE content LIKE '%$query%' OR rationale LIKE '%$query%' ORDER BY created_at DESC LIMIT $limit;"
    
    echo ""
    echo "=== Patterns ==="
    run_query "SELECT id, name, description, severity FROM patterns WHERE name LIKE '%$query%' OR description LIKE '%$query%' OR solution LIKE '%$query%' ORDER BY frequency DESC LIMIT $limit;"
}

# Get recent decisions
get_recent() {
    local limit=5
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --limit)
                limit="$2"
                shift 2
                ;;
            *)
                echo "Unknown option: $1" >&2
                exit 1
                ;;
        esac
    done
    
    run_query "SELECT id, content, project, task, importance, created_at FROM decisions ORDER BY created_at DESC LIMIT $limit;"
}

# Get context by task
get_context() {
    local task=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --task)
                task="$2"
                shift 2
                ;;
            *)
                echo "Unknown option: $1" >&2
                exit 1
                ;;
        esac
    done
    
    if [ -z "$task" ]; then
        echo "Error: --task required" >&2
        exit 1
    fi
    
    run_query "SELECT id, agent_id, task, current_work, status, notes, created_at, updated_at FROM context WHERE task LIKE '%$task%' ORDER BY updated_at DESC;"
}

# Main command handler
case "${1:-}" in
    decisions)
        shift
        query_decisions "$@"
        ;;
    patterns)
        shift
        query_patterns "$@"
        ;;
    search)
        shift
        search_memory "$@"
        ;;
    recent)
        shift
        get_recent "$@"
        ;;
    context)
        shift
        get_context "$@"
        ;;
    help|--help|-h)
        cat << EOF
Memory Query Helper Script
Fallback tool for querying agent memory when MCP tools are not available

Usage:
  $0 [command] [options]

Commands:
  decisions [--project PROJECT] [--limit N] [--search TEXT]
    Query decisions from memory
    
  patterns [--severity low|medium|high] [--limit N] [--search TEXT]
    Query patterns from memory
    
  search QUERY [--limit N]
    Full-text search across decisions and patterns
    
  recent [--limit N]
    Get recent decisions
    
  context --task TASK
    Get context for a specific task

Examples:
  $0 decisions --project home-server --limit 5
  $0 patterns --severity high
  $0 search "PostgreSQL database"
  $0 recent --limit 10
  $0 context --task T1.3

Database: $DB_PATH
EOF
        exit 0
        ;;
    "")
        echo "Error: Command required. Use '$0 help' for usage." >&2
        exit 1
        ;;
    *)
        echo "Error: Unknown command '$1'. Use '$0 help' for usage." >&2
        exit 1
        ;;
esac

