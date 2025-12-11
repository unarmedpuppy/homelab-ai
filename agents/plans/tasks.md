# Task Management

Task tracking using [Beads](https://github.com/steveyegge/beads), a distributed issue tracker for AI agents.

## Quick Start

```bash
# Find ready work (no blockers)
bd ready

# View all tasks
bd list

# View task details
bd show <id>
```

## Task Database

Tasks are stored in `.beads/` at the repository root (not in this directory). The database:
- Uses hash-based IDs (e.g., `home-server-xxl`) for collision-free multi-agent work
- Syncs automatically via git hooks
- Supports dependency tracking with `bd dep` commands

## Workflow

### Session Start
```bash
git pull origin main
bd ready                        # Unblocked work
bd list --status in_progress    # In-progress tasks
bd blocked                      # Blocked tasks
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
```

### Create Tasks
```bash
bd create "Task title" -t task -p 1 -l "project,area" -d "Description"
# Types: task, bug, feature, epic, chore
# Priority: 0 (critical), 1 (high), 2 (medium), 3 (low)
```

### Manage Dependencies
```bash
bd dep add <blocked-id> <blocker-id> --type blocks
bd dep tree <id>
bd dep cycles
```

## Documentation

- **Complete guide**: `agents/skills/beads-task-management/SKILL.md`
- **Task coordination persona**: `agents/personas/task-manager-agent.md`
- **Beads CLI help**: `bd --help`

## Archive

Legacy task files from the markdown-based system are in `archive/`:
- `archive/tasks.md` - Original markdown task list
- `archive/registry.md` - Original task ID registry
