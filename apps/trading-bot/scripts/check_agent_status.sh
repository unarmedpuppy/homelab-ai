#!/bin/bash
# Check Agent Status Script
# Run this script to check for agent updates and review pending work

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STATUS_DIR="$PROJECT_ROOT/docs/agent_status"
REVIEW_DIR="$PROJECT_ROOT/docs/reviews/pending"
TODO_FILE="$PROJECT_ROOT/docs/PROJECT_TODO.md"

echo "========================================="
echo "Agent Status Check"
echo "========================================="
echo ""

# Check for agent status files
if [ -d "$STATUS_DIR" ] && [ "$(ls -A $STATUS_DIR/*.md 2>/dev/null)" ]; then
    echo "📋 Active Agent Status Files:"
    echo ""
    for file in "$STATUS_DIR"/*.md; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            mod_time=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$file" 2>/dev/null || stat -c "%y" "$file" 2>/dev/null | cut -d'.' -f1)
            echo "  - $filename (Last updated: $mod_time)"
        fi
    done
else
    echo "📋 No agent status files found"
fi

echo ""

# Check for pending reviews
if [ -d "$REVIEW_DIR" ] && [ "$(ls -A $REVIEW_DIR/*.md 2>/dev/null)" ]; then
    echo "🔍 Pending Reviews:"
    echo ""
    for file in "$REVIEW_DIR"/*.md; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            mod_time=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$file" 2>/dev/null || stat -c "%y" "$file" 2>/dev/null | cut -d'.' -f1)
            echo "  - $filename (Last updated: $mod_time)"
        fi
    done
else
    echo "🔍 No pending reviews"
fi

echo ""

# Check PROJECT_TODO.md for active tasks
if [ -f "$TODO_FILE" ]; then
    echo "📊 Active Tasks in PROJECT_TODO.md:"
    echo ""
    # Extract active tasks from the table
    awk '/### Active Tasks/,/### Recently Completed/' "$TODO_FILE" | \
        grep -E '\|.*In Progress|🔄' | head -10
    
    echo ""
    echo "📊 Tasks Ready for Review:"
    echo ""
    awk '/### Active Tasks/,/### Recently Completed/' "$TODO_FILE" | \
        grep -E '\|.*Review|🔍' | head -10
fi

echo ""
echo "========================================="
echo "Next Steps:"
echo "========================================="
echo ""
echo "1. Review the status files above"
echo "2. Ask the coordinator: 'Check agent status and review pending work'"
echo "3. Or manually review files in: $STATUS_DIR"
echo ""

