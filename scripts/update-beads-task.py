#!/usr/bin/env python3
"""
Script to update Beads task status.
Usage: python scripts/update-beads-task.py <task-id> <status> [reason]
"""

import json
import sys
from datetime import datetime
from pathlib import Path

if len(sys.argv) < 3:
    print("Usage: python scripts/update-beads-task.py <task-id> <status> [reason]")
    sys.exit(1)

task_id = sys.argv[1]
new_status = sys.argv[2]
reason = sys.argv[3] if len(sys.argv) > 3 else None

repo_root = Path(__file__).parent.parent
beads_file = repo_root / ".beads" / "issues.jsonl"

# Read all issues
issues = []
with open(beads_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            issues.append(json.loads(line))

# Find and update the task
updated = False
for issue in issues:
    if issue['id'] == task_id:
        issue['status'] = new_status
        issue['updated_at'] = datetime.now().isoformat()
        if new_status == 'closed' and reason:
            issue['closed_at'] = datetime.now().isoformat()
            if 'description' in issue:
                issue['description'] += f"\n\n**Closed**: {reason}"
        updated = True
        print(f"Updated {task_id}: {issue['title']} -> {new_status}")
        break

if not updated:
    print(f"Error: Task {task_id} not found")
    sys.exit(1)

# Write back
with open(beads_file, 'w', encoding='utf-8') as f:
    for issue in issues:
        f.write(json.dumps(issue) + '\n')

print("Done!")

