# Beads CLI Reference (bd)

Comprehensive reference for the [Beads](https://github.com/steveyegge/beads) distributed issue tracker CLI.

## Overview

Beads is a distributed issue tracker designed for AI agents with:
- **Hash-based IDs** - Collision-resistant identifiers (e.g., `home-server-xxl`)
- **Git-backed sync** - Auto-syncs via hooks, works across machines
- **Dependency tracking** - 4 types: blocks, related, parent-child, discovered-from
- **JSONL source of truth** - `.beads/issues.jsonl` with SQLite cache

## Installation

```bash
# macOS (Homebrew)
brew tap steveyegge/beads
brew install beads

# Verify
bd --version
```

## Database Location

```
.beads/
├── issues.jsonl      # Source of truth (committed to git)
├── beads.db          # SQLite cache (gitignored)
├── config.yaml       # Configuration
├── metadata.json     # Schema version
└── .gitignore        # Ignores local files
```

## Core Commands

### Finding Work

```bash
# Find ready work (no blockers) - PRIMARY COMMAND
bd ready

# With filters
bd ready --priority 0           # Critical only
bd ready --priority 1           # High priority
bd ready --json                 # JSON output for programmatic use

# View all tasks
bd list
bd list --status open           # Open tasks
bd list --status in_progress    # In-progress
bd list --status closed         # Closed

# Filter by label
bd list --label trading-bot
bd list --label infrastructure,monitoring   # Multiple (AND)

# View blocked tasks
bd blocked

# Search by text
bd search "websocket"
bd search "refactor"
```

### Viewing Tasks

```bash
# Show task details
bd show <id>
bd show home-server-xxl

# JSON output
bd show <id> --json
```

### Creating Tasks

```bash
# Basic syntax
bd create "Task title" [options]

# Options
-t, --type TYPE        # task, bug, feature, epic, chore (default: task)
-p, --priority NUM     # 0=critical, 1=high, 2=medium, 3=low (default: 2)
-l, --labels LABELS    # Comma-separated labels
-d, --description DESC # Detailed description

# Examples
bd create "Fix authentication bug" -t bug -p 0 -l "auth,urgent"
bd create "Implement dark mode" -t feature -p 1 -l "ui,enhancement"
bd create "Refactor metrics system" -t epic -p 1 -l "refactor,trading-bot" \
  -d "Consolidate 8 metrics files into 3"
```

### Updating Tasks

```bash
# Change status
bd update <id> --status in_progress
bd update <id> --status open

# Change priority
bd update <id> --priority 0

# Add/change labels
bd update <id> --labels "new-label,another"

# Change title
bd update <id> --title "New title"
```

### Closing Tasks

```bash
# Close with reason
bd close <id> --reason "Implemented in PR #123"

# Close without reason
bd close <id>

# Batch close
bd close <id1> <id2> <id3>
```

### Dependency Management

```bash
# Add dependency (B blocks A - can't start A until B is done)
bd dep add <blocked-id> <blocker-id> --type blocks

# Dependency types
--type blocks          # Hard blocker
--type related         # Soft connection
--type parent-child    # Hierarchical
--type discovered-from # Found during other work

# View dependency tree
bd dep tree <id>

# Check for cycles (IMPORTANT - cycles break the graph!)
bd dep cycles

# Remove dependency
bd dep remove <child-id> <parent-id>
```

### Git Synchronization

```bash
# Manual sync (usually auto via hooks)
bd sync

# Check database health
bd doctor

# View database info
bd info

# View statistics
bd stats
```

## Task Types

| Type | Use Case |
|------|----------|
| `task` | General work item |
| `bug` | Something broken that needs fixing |
| `feature` | New functionality |
| `epic` | Large multi-task initiative |
| `chore` | Maintenance, cleanup, non-feature work |

## Priority Levels

| Priority | Meaning | When to Use |
|----------|---------|-------------|
| 0 | Critical | Production down, security issues, blockers |
| 1 | High | Important work, should be done soon |
| 2 | Medium | Normal priority (default) |
| 3+ | Low | Backlog, nice-to-have |

## Status Values

| Status | Meaning |
|--------|---------|
| `open` | Not started, available for claiming |
| `in_progress` | Currently being worked on |
| `closed` | Completed |

## JSON Output

All commands support `--json` for programmatic access:

```bash
# Get first ready task ID
bd ready --json | jq -r '.[0].id'

# Get all high-priority tasks
bd list --json | jq '.[] | select(.priority <= 1)'

# Get tasks by label
bd list --json | jq '.[] | select(.labels | contains(["trading-bot"]))'

# Check if task is blocked
bd show <id> --json | jq '.blocked_by'

# Get task count by status
bd list --json | jq 'group_by(.status) | map({status: .[0].status, count: length})'
```

## Common Workflows

### Session Start

```bash
git pull origin main
bd ready                        # Find unblocked work
bd list --status in_progress    # Check in-progress
bd blocked                      # Review blocked items
```

### Claim → Work → Complete

```bash
# 1. Claim
bd update <id> --status in_progress
git add .beads/ && git commit -m "claim: <id> - Description" && git push

# 2. Work (on feature branch)
git checkout -b feature/<id>-description
# ... do work ...

# 3. Complete
bd close <id> --reason "Implemented in PR #X"
git add .beads/ && git commit -m "close: <id>"
```

### Discover Work During Task

```bash
# Found new issue while working on another
bd create "Found issue during X" -t bug -p 1 -l "discovered"
bd dep add <new-id> <current-id> --type discovered-from
```

### Breaking Down an Epic

```bash
# Create epic
bd create "Implement authentication system" -t epic -p 1

# Create child tasks
bd create "Design auth schema" -t task -p 1
bd create "Implement JWT tokens" -t task -p 1
bd create "Add login endpoint" -t task -p 1

# Link as parent-child
bd dep add <child1-id> <epic-id> --type parent-child
bd dep add <child2-id> <epic-id> --type parent-child
bd dep add <child3-id> <epic-id> --type parent-child

# Add sequential dependencies
bd dep add <jwt-id> <schema-id> --type blocks
bd dep add <login-id> <jwt-id> --type blocks
```

## Labels Convention

| Category | Labels |
|----------|--------|
| Project | `trading-bot`, `infrastructure`, `media`, `agents` |
| Area | `refactor`, `cleanup`, `testing`, `docs`, `monitoring` |
| Component | `websocket`, `traefik`, `zfs`, `network`, `ui` |
| Urgency | `urgent`, `blocking`, `tech-debt` |

## Server Restrictions

**⚠️ Beads is LOCAL-ONLY - Not installed on the server**

The beads tooling (`bd` CLI, daemon, beads-ui) is intentionally **not installed** on the home server. This is by design:

- **Why**: A beads daemon running on the server caused sync conflicts. It modified `issues.jsonl` with stale data from its internal database, preventing `git pull` from working.
- **Git hooks disabled**: The server's `.git/hooks/` (post-merge, post-checkout, pre-commit, pre-push) are no-ops to prevent any beads operations.
- **Data still syncs**: The `.beads/issues.jsonl` file is git-tracked and syncs to the server via normal `git pull`.

**Correct Workflow:**
```bash
# LOCAL machine only:
bd create "New task" -p 1
bd update <id> --status in_progress
bd close <id>

# Sync to server:
git add .beads/ && git commit -m "beads: update" && git push

# Server just pulls (no bd commands):
ssh server "cd ~/server && git pull"
```

**Never on the server:**
- Don't install `bd` CLI
- Don't run `bd daemon`
- Don't install beads-ui
- Don't run any `bd` commands

## Troubleshooting

### Sync Issues

```bash
# Check database health
bd doctor

# Force rebuild cache
rm .beads/beads.db
bd list  # Rebuilds cache
```

### Dependency Cycles

```bash
# Check for cycles
bd dep cycles

# If cycles found, remove one dependency to break the cycle
bd dep remove <id1> <id2>
```

### Git Hook Issues

```bash
# Reinstall hooks
bd init --force
```

## Quick Reference

| Action | Command |
|--------|---------|
| Find work | `bd ready` |
| View all | `bd list` |
| View details | `bd show <id>` |
| Create task | `bd create "title" -t task -p 1 -l "labels"` |
| Claim task | `bd update <id> --status in_progress` |
| Complete task | `bd close <id> --reason "note"` |
| Add blocker | `bd dep add <child> <parent> --type blocks` |
| View deps | `bd dep tree <id>` |
| Check cycles | `bd dep cycles` |
| Check health | `bd doctor` |
| Sync | `bd sync` |
| Stats | `bd stats` |

## See Also

- [beads-viewer.md](beads-viewer.md) - bv reference (AI graph sidecar)
- [beads-task-management tool](../tools/beads-task-management/SKILL.md) - Workflow guide
- [task-manager-agent](../personas/task-manager-agent.md) - Task coordination persona
- [Beads GitHub](https://github.com/steveyegge/beads) - Official repository
