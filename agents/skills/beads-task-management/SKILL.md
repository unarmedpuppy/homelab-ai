---
name: beads-task-management
description: Manage tasks with Beads distributed issue tracker
when_to_use: Creating, updating, querying tasks; finding ready work; managing dependencies
---

# Beads Task Management

Manage tasks using [Beads](https://github.com/steveyegge/beads), a distributed issue tracker for AI agents with git-backed synchronization.

## ⚠️ Important: Local-Only

**Beads runs LOCALLY only, not on the server.**

- The `bd` CLI is **not installed** on the home server
- Run all `bd` commands locally, then sync via git push
- The server receives updates via `git pull` only
- See `agents/reference/beads.md#server-restrictions` for details

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

### Why bv vs. Raw Beads?

Using Beads directly gives an agent **data**. Using `bv --robot-*` gives an agent **intelligence**.

| Capability | Raw Beads (JSONL) | bv Robot Mode |
|------------|-------------------|---------------|
| Query | "List all issues." | "List the top 5 bottlenecks blocking the release." |
| Context Cost | High (Linear with issue count) | Low (Fixed summary struct) |
| Graph Logic | Agent must infer/compute | Pre-computed (PageRank/Brandes) |
| Safety | Agent might miss a cycle | Cycles explicitly flagged |

### Agent Usage Patterns

Agents typically use `bv` in three phases:

1. **Triage & Orientation**: Before starting a session, run `bv --robot-insights`. You receive a lightweight JSON summary of the project's structural health. You immediately know:
   - "I should not work on Task C yet because it depends on Task B, which is a Bottleneck."
   - "The graph has a cycle (A→B→A); I must fix this structural error before adding new features."

2. **Impact Analysis**: When asked to "refactor the login module," check the PageRank and Impact Scores of the relevant tasks. If scores are high, this is a high-risk change with many downstream dependents—run more comprehensive tests.

3. **Execution Planning**: Instead of guessing the order of operations, use `bv --robot-plan` to generate a strictly linearized plan with parallel execution tracks.

### Using bv as an AI sidecar

[bv](https://github.com/Dicklesworthstone/beads_viewer) is a fast terminal UI for Beads projects. It renders lists/details and precomputes dependency metrics (PageRank, critical path, cycles, etc.) so you instantly see blockers and execution order. For agents, it's a graph sidecar: instead of parsing JSONL or risking hallucinated traversal, call the robot flags to get deterministic, dependency-aware outputs.

**⚠️ IMPORTANT: As an agent, you MUST ONLY use `bv` with the robot flags, otherwise you'll get stuck in the interactive TUI that's intended for human usage only!**

```bash
# Show all AI-facing commands
bv --robot-help

# Get graph metrics (PageRank, betweenness, critical path, cycles)
bv --robot-insights

# Get execution plan with parallel tracks and unblocks
bv --robot-plan

# Get priority recommendations with reasoning
bv --robot-priority

# List available recipes (filters)
bv --robot-recipes

# Show changes since a commit or date
bv --robot-diff --diff-since <commit|date>
```

Use these commands instead of hand-rolling graph logic; `bv` already computes the hard parts so agents can act safely and quickly.

### bv --robot-insights Schema

The output is strictly typed and easily parseable:

```json
{
  "bottlenecks": [{ "id": "CORE-123", "value": 0.45 }],
  "keystones": [{ "id": "API-001", "value": 12.0 }],
  "influencers": [{ "id": "AUTH-007", "value": 0.82 }],
  "hubs": [{ "id": "EPIC-100", "value": 0.67 }],
  "authorities": [{ "id": "UTIL-050", "value": 0.91 }],
  "cycles": [["TASK-A", "TASK-B", "TASK-A"]],
  "clusterDensity": 0.045,
  "stats": { "pageRank": {}, "betweenness": {}, "topologicalOrder": [] }
}
```

| Field | Metric | What It Contains |
|-------|--------|------------------|
| `bottlenecks` | Betweenness | Top nodes bridging graph clusters |
| `keystones` | Critical Path | Top nodes on longest dependency chains |
| `influencers` | Eigenvector | Top nodes connected to important neighbors |
| `hubs` | HITS Hub | Top dependency aggregators (Epics) |
| `authorities` | HITS Authority | Top prerequisite providers (Utilities) |
| `cycles` | Cycle Detection | All circular dependency paths (fix these first!) |
| `clusterDensity` | Density | Overall graph interconnectedness |
| `stats` | All Metrics | Full raw data for custom analysis |

### JSON output from bd

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

### bv Robot Commands (AI-only)

| Action | Command |
|--------|---------|
| Help | `bv --robot-help` |
| Execution plan | `bv --robot-plan` |
| Graph insights | `bv --robot-insights` |
| Priority recs | `bv --robot-priority` |
| Available recipes | `bv --robot-recipes` |
| Diff since | `bv --robot-diff --diff-since <ref>` |

See `agents/personas/task-manager-agent.md` for complete task coordination guidance.
