---
name: beads-task-management
description: Manage tasks with Beads distributed issue tracker
when_to_use: Creating, updating, querying tasks; finding ready work; managing dependencies
---

# Beads Task Management

Manage tasks using [Beads](https://github.com/steveyegge/beads), a distributed issue tracker for AI agents with git-backed synchronization.

## Overview

Beads provides:
- **Hash-based IDs** - No merge conflicts (`home-server-xxl` instead of `T1`)
- **Dependency tracking** - 4 types: blocks, related, parent-child, discovered-from
- **Ready work detection** - `bd ready` finds unblocked tasks
- **Git synchronization** - Auto-syncs via hooks, works across machines
- **JSON output** - `--json` flag for programmatic access

## Finding Work

```bash
# Find ready work (no blockers)
bd ready

# For programmatic use
bd ready --json

# Filter by priority (0 = critical)
bd ready --priority 0

# Filter by label
bd list --label trading-bot
bd list --label infrastructure

# View all tasks
bd list

# View blocked tasks
bd blocked
```

## Creating Tasks

```bash
# Standard task
bd create "Task title" -t task -p 1 -l "project,area" -d "Description"

# Types: task, bug, feature, epic, chore
# Priority: 0 (critical), 1 (high), 2 (medium), 3 (low)

# Examples
bd create "Fix authentication bug" -t bug -p 0 -l "auth,urgent"
bd create "Implement dark mode" -t feature -p 1 -l "ui,enhancement"
bd create "Refactor metrics system" -t epic -p 1 -l "refactor,trading-bot"
```

## Claiming Tasks

```bash
# 1. Find ready work
bd ready

# 2. Claim task
bd update <id> --status in_progress

# 3. Commit claim to git
git add .beads/
git commit -m "claim: <id> - Description"
git push origin main

# 4. Create feature branch
git checkout -b feature/<id>-description
```

## Managing Dependencies

```bash
# Add blocker (B blocks A - can't start A until B is done)
bd dep add <blocked-id> <blocker-id> --type blocks

# Other dependency types
bd dep add <id1> <id2> --type related        # Soft connection
bd dep add <id1> <id2> --type parent-child   # Hierarchical
bd dep add <id1> <id2> --type discovered-from # Found during other work

# View dependency tree
bd dep tree <id>

# Check for cycles
bd dep cycles

# Remove dependency
bd dep remove <child-id> <parent-id>
```

## Completing Tasks

```bash
# Close with reason
bd close <id> --reason "Implemented in PR #123"

# Commit closure
git add .beads/
git commit -m "close: <id> - Completion note"
git push

# Batch close
bd close <id1> <id2> <id3>
```

## Querying Tasks

```bash
# View task details
bd show <id>
bd show <id> --json

# Filter by status
bd list --status open
bd list --status in_progress
bd list --status closed

# Filter by priority
bd list --priority 0    # Critical only
bd list --priority 1    # High priority

# Filter by label
bd list --label trading-bot
bd list --label infrastructure,monitoring   # Multiple labels (AND)

# Search by text
bd search "websocket"
```

## Git Synchronization

Beads auto-syncs with git via hooks:

```bash
# Manual sync (usually not needed)
bd sync

# Check database health
bd doctor

# View database info
bd info
```

## For AI Agents

Always use `--json` for programmatic access:

```bash
# Get first ready task ID
bd ready --json | jq -r '.[0].id'

# Get all trading-bot tasks
bd list --json | jq '.[] | select(.labels | contains(["trading-bot"]))'

# Check if task is blocked
bd show <id> --json | jq '.blocked_by'
```

## Labels

| Category | Labels |
|----------|--------|
| Project | `trading-bot`, `infrastructure`, `media`, `agents` |
| Area | `refactor`, `cleanup`, `testing`, `docs`, `monitoring` |
| Component | `websocket`, `traefik`, `zfs`, `network`, `ui` |

## Priority Levels

| Priority | Meaning | Action |
|----------|---------|--------|
| 0 | Critical | Work immediately |
| 1 | High | Work soon |
| 2 | Medium | Schedule appropriately |
| 3+ | Low | Backlog |

## Common Workflows

### Session Start
```bash
git pull origin main
bd ready
bd list --status in_progress
```

### Claim → Work → Complete
```bash
# Claim
bd update <id> --status in_progress
git add .beads/ && git commit -m "claim: <id>" && git push

# Work (on feature branch)
git checkout -b feature/<id>-description
# ... do work ...

# Complete
bd close <id> --reason "Implemented"
git add .beads/ && git commit -m "close: <id>"
# Create PR
```

### Discover Work During Task
```bash
# Found new issue while working on another
bd create "Found issue during X" -t bug -p 1
bd dep add <new-id> <current-id> --type discovered-from
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
| Check health | `bd doctor` |
| Sync | `bd sync` |

See `agents/personas/task-manager-agent.md` for complete task coordination guidance.
