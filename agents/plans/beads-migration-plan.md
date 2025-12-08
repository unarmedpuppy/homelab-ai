# Beads Migration Plan

**Status**: Draft
**Created**: 2025-12-07
**Priority**: P1
**Project**: agents

## Overview

Migrate from the current markdown-based task system (`agents/tasks/tasks.md`) to [Beads](https://github.com/steveyegge/beads), a distributed issue tracker designed for AI agents with multi-session memory and git-backed synchronization.

## Current State Analysis

### What We Have Now

```
agents/tasks/
├── tasks.md         # Main task list (28KB, 26 active tasks)
├── registry.md      # Duplicate/older task registry
├── README.md        # Usage documentation
├── archive/         # Empty archive directory
└── templates/       # Task templates
```

**Current Workflow:**
1. Edit `tasks.md` directly (markdown tables)
2. Git-based claiming protocol (change status in table)
3. Manual status updates (`[AVAILABLE]` → `[CLAIMED by @id]` → `[COMPLETE]`)
4. Feature branch per task
5. No dependency tracking beyond documentation
6. No "ready work" detection - agents must scan entire list

**Pain Points:**
- Manual parsing of markdown tables
- No structured dependency management
- Merge conflicts on concurrent task updates
- Status legend duplicated in multiple places
- Registry.md and tasks.md drift out of sync
- No programmatic query interface for agents
- No memory decay / compaction for old tasks

### What Beads Provides

| Feature | Current System | Beads |
|---------|---------------|-------|
| Storage | Markdown tables | SQLite cache + git-synced JSONL |
| IDs | Sequential (T1, T2...) | Hash-based (`bd-a1b2`) - no conflicts |
| Dependencies | Manual documentation | 4 types: blocks, related, parent-child, discovered-from |
| Ready work | Manual scanning | `bd ready --json` auto-detection |
| Agent interface | Parse markdown | `--json` output on all commands |
| Multi-agent sync | Git pull + 1-min commit | 5-second auto-export + git hooks |
| Memory decay | Manual archive | Automatic compaction over time |
| Status tracking | Text in table | Structured states with transitions |

## Implementation Plan

### Phase 1: Installation & Setup (Local)

**Objective**: Install Beads and initialize in the home-server repo

**Steps:**

1. **Install Beads CLI**
   ```bash
   # Option A: Quick install (recommended)
   curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash

   # Option B: npm
   npm install -g @beads/bd

   # Option C: Homebrew
   brew tap steveyegge/beads && brew install bd
   ```

2. **Initialize Beads in repo**
   ```bash
   cd /Users/joshuajenquist/repos/personal/home-server
   bd init
   ```

   This creates:
   ```
   .beads/
   ├── beads.jsonl      # Source of truth (committed to git)
   ├── beads.db         # Local SQLite cache (gitignored)
   ├── deletions.jsonl  # Deletion manifest
   ├── config.yaml      # Configuration
   └── metadata.json    # Schema version
   ```

3. **Configure git hooks** (optional but recommended)
   - Accept the git hook installation prompt during `bd init`
   - Enables immediate sync on git operations

4. **Verify setup**
   ```bash
   bd doctor
   bd info
   ```

### Phase 2: Data Migration

**Objective**: Import all existing tasks from `tasks.md` into Beads

**Migration Script**: Create `scripts/migrate-tasks-to-beads.sh`

```bash
#!/bin/bash
# Migrate existing tasks.md to Beads format

# Priority mapping: P0=0, P1=1, P2=2
# Type mapping: All as "task" initially

# Example migration commands for each task:
# bd create "Consolidate metrics system (8 files → 3)" \
#   -t task -p 0 -l "trading-bot,refactor" \
#   -d "Reduce metrics system from 8 files to 3 for better code quality. Biggest code quality win. See IMPLEMENTATION_ROADMAP.md"
```

**Manual Migration Steps** (for 26 tasks):

1. **Create tasks by priority group:**

   **P0 Tasks:**
   ```bash
   bd create "Consolidate metrics system (8 files → 3)" -t task -p 0 -l "trading-bot,refactor"
   bd create "WebSocket data producer integration" -t task -p 0 -l "trading-bot,websocket"
   bd create "IBKR integration testing" -t task -p 0 -l "trading-bot,integration"
   bd create "Strategy-to-execution pipeline" -t task -p 0 -l "trading-bot,core"
   bd create "Migrate ZFS from RAID-Z1 to RAID-Z2" -t epic -p 0 -l "infrastructure,storage"
   bd create "Setup new 6-drive RAID-Z2 pool" -t epic -p 0 -l "infrastructure,storage"
   ```

   **P1 Tasks:**
   ```bash
   bd create "Remove backward compat duplication in strategy.py" -t task -p 1 -l "trading-bot,cleanup"
   bd create "Standardize error handling" -t task -p 1 -l "trading-bot,quality"
   bd create "UI WebSocket integration" -t task -p 1 -l "trading-bot,ui"
   bd create "WebSocket testing" -t task -p 1 -l "trading-bot,testing"
   bd create "Sentiment provider base class" -t task -p 1 -l "trading-bot,refactor"
   bd create "Standardize Traefik config" -t epic -p 1 -l "infrastructure,traefik"
   bd create "Setup SMART monitoring on server" -t task -p 1 -l "infrastructure,monitoring"
   bd create "Test drive health check script" -t task -p 1 -l "infrastructure,monitoring"
   bd create "Review current drive health status" -t task -p 1 -l "infrastructure,monitoring"
   bd create "Purchase ASUS routers" -t task -p 1 -l "infrastructure,network"
   bd create "Set up ASUS routers with AdGuard DNS" -t task -p 1 -l "infrastructure,network"
   ```

   **P2 Tasks:**
   ```bash
   bd create "Standardize import patterns" -t task -p 2 -l "trading-bot,cleanup"
   bd create "Add missing type hints" -t task -p 2 -l "trading-bot,typing"
   bd create "Media-Download Directory Cleanup" -t task -p 2 -l "media,cleanup"
   bd create "Configure automated drive health monitoring/alerts" -t task -p 2 -l "infrastructure,monitoring"
   bd create "Update infrastructure docs after router migration" -t task -p 2 -l "infrastructure,docs"
   ```

2. **Add dependencies:**
   ```bash
   # T7 (UI WebSocket) depends on T6 (WebSocket producers)
   bd dep add <t7-id> <t6-id> --type blocks

   # T8 (WebSocket testing) depends on T6 and T7
   bd dep add <t8-id> <t6-id> --type blocks
   bd dep add <t8-id> <t7-id> --type blocks

   # T25 (Router setup) depends on T24 (Purchase routers)
   bd dep add <t25-id> <t24-id> --type blocks

   # T26 (Docs update) depends on T25 (Router setup)
   bd dep add <t26-id> <t25-id> --type blocks

   # Drive monitoring chain
   bd dep add <t19-id> <t18-id> --type blocks  # Test depends on setup
   bd dep add <t20-id> <t18-id> --type blocks  # Alerts depends on setup
   bd dep add <t20-id> <t19-id> --type blocks  # Alerts depends on test
   bd dep add <t21-id> <t18-id> --type blocks  # Review depends on setup

   # ZFS tasks depend on drive health review
   bd dep add <t22-id> <t18-id> --type blocks
   bd dep add <t22-id> <t19-id> --type blocks
   bd dep add <t22-id> <t21-id> --type blocks
   ```

3. **Mark completed tasks:**
   ```bash
   # Homepage cleanup tasks (T13-T16 marked [COMPLETE])
   bd close <t13-id> --reason "Icons updated to si-* format"
   bd close <t14-id> --reason "Media icons updated"
   bd close <t15-id> --reason "Productivity category consolidated"
   bd close <t16-id> --reason "Social/News and Gaming icons fixed"
   ```

4. **Mark blocked tasks:**
   ```bash
   bd update <t25-id> --status blocked  # Router setup blocked by purchase
   bd update <t26-id> --status blocked  # Docs update blocked by router setup
   ```

### Phase 3: Documentation Updates

**Objective**: Update all documentation to reference Beads

**Files to Update:**

1. **`AGENTS.md`** - Update task management section:
   ```markdown
   ## Task Management

   Tasks are managed using [Beads](https://github.com/steveyegge/beads), a distributed issue tracker.

   ### Quick Commands

   ```bash
   # Find ready work (no blockers)
   bd ready --json

   # View all tasks
   bd list

   # Create new task
   bd create "Task description" -t task -p 1 -l "project,area"

   # Claim task (start work)
   bd update <id> --status in_progress

   # Complete task
   bd close <id> --reason "Completion note"

   # View dependencies
   bd dep tree <id>
   ```

   ### Task Claiming Protocol

   ```bash
   # 1. Pull latest
   git pull origin main

   # 2. Find ready work
   bd ready

   # 3. Claim task
   bd update <task-id> --status in_progress

   # 4. Commit claim
   git add .beads/
   git commit -m "claim: <task-id> - Description"
   git push origin main

   # 5. Create feature branch
   git checkout -b feature/<task-id>-description
   ```
   ```

2. **`agents/tasks/README.md`** - Update or replace:
   ```markdown
   # Task Coordination

   Task tracking using [Beads](https://github.com/steveyegge/beads).

   ## Files

   - **`.beads/`** - Beads database (at repo root)
   - **`tasks.md`** - DEPRECATED (see migration notes)

   ## Common Operations

   | Action | Command |
   |--------|---------|
   | Find ready work | `bd ready` |
   | View all tasks | `bd list` |
   | View task details | `bd show <id>` |
   | Create task | `bd create "title" -t task -p <priority>` |
   | Update status | `bd update <id> --status <status>` |
   | Add dependency | `bd dep add <child> <parent>` |
   | Close task | `bd close <id> --reason "note"` |

   ## For AI Agents

   Always use `--json` flag for programmatic access:

   ```bash
   bd ready --json | jq '.issues[0].id'
   bd show <id> --json
   ```
   ```

3. **`agents/personas/server-agent.md`** - Add Beads section:
   ```markdown
   ### Task Discovery

   Use Beads for task management:

   ```bash
   # Find work without blockers
   bd ready --json

   # Filter by label
   bd list --label infrastructure --json

   # Check dependencies
   bd dep tree <id>
   ```
   ```

4. **Create new tool** - `agents/tools/beads-task-management/SKILL.md`:
   ```yaml
   ---
   name: beads-task-management
   description: Manage tasks with Beads distributed issue tracker
   when_to_use: Creating, updating, querying tasks; finding ready work; managing dependencies
   ---

   # Beads Task Management

   Use Beads CLI for all task operations.

   ## Finding Work

   ```bash
   # Ready work (no blockers)
   bd ready

   # Filter by label
   bd list --label trading-bot
   bd list --label infrastructure

   # Filter by priority
   bd ready --priority 0  # P0 only
   ```

   ## Creating Tasks

   ```bash
   bd create "Task title" \
     -t task \         # type: task|bug|feature|epic|chore
     -p 1 \            # priority: 0-4 (0 highest)
     -l "project,area" # labels
   ```

   ## Managing Dependencies

   ```bash
   # Task B blocked by Task A
   bd dep add <b-id> <a-id> --type blocks

   # View dependency tree
   bd dep tree <id>

   # Find cycles
   bd dep cycles
   ```

   ## Workflow

   ```bash
   # 1. Find work
   bd ready --json

   # 2. Claim task
   bd update <id> --status in_progress
   git add .beads/ && git commit -m "claim: <id>"
   git push

   # 3. Create branch
   git checkout -b feature/<id>-description

   # 4. Work on task...

   # 5. Complete
   bd close <id> --reason "Implemented in PR #X"
   git add .beads/ && git commit -m "close: <id>"
   ```
   ```

### Phase 4: Archive Old System

**Objective**: Archive but preserve the old task system

**Steps:**

1. **Archive old tasks.md:**
   ```bash
   mkdir -p agents/tasks/archive
   mv agents/tasks/tasks.md agents/tasks/archive/tasks-pre-beads.md
   mv agents/tasks/registry.md agents/tasks/archive/registry-pre-beads.md
   ```

2. **Add migration note to archive:**
   ```markdown
   # Archive Note

   These files were migrated to Beads on 2025-12-07.

   To view current tasks, use:
   - `bd list` - All tasks
   - `bd ready` - Ready work

   These files are kept for historical reference only.
   ```

3. **Keep tasks directory for README:**
   ```
   agents/tasks/
   ├── README.md          # Updated with Beads instructions
   ├── archive/
   │   ├── tasks-pre-beads.md
   │   └── registry-pre-beads.md
   └── templates/         # May still be useful for epic templates
   ```

### Phase 5: Verification & Testing

**Objective**: Verify migration is complete and working

**Verification Checklist:**

- [ ] `bd doctor` reports healthy
- [ ] `bd list` shows all migrated tasks
- [ ] `bd ready` returns unblocked tasks
- [ ] Dependency graph is correct (`bd dep tree` for key tasks)
- [ ] Git sync works (commit, push, pull on another machine)
- [ ] `--json` output is parseable
- [ ] Blocked tasks show in `bd blocked`
- [ ] Labels filter correctly (`bd list --label trading-bot`)
- [ ] Priority filter works (`bd list --priority 0`)

**Test Workflow:**

```bash
# 1. Create test task
bd create "Test Beads integration" -t task -p 2 -l "test"

# 2. Find it in ready work
bd ready | grep -i test

# 3. Claim it
bd update <id> --status in_progress

# 4. Add a blocker
bd create "Blocking task" -t task -p 2
bd dep add <test-id> <blocking-id> --type blocks

# 5. Verify test task no longer in ready
bd ready | grep -i test  # Should not appear

# 6. Close blocker
bd close <blocking-id> --reason "Test complete"

# 7. Verify test task is ready again
bd ready | grep -i test  # Should appear

# 8. Close test task
bd close <test-id> --reason "Migration verified"
```

## Migration Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| 1 | 15 min | Install Beads, initialize repo |
| 2 | 30-60 min | Migrate 26 tasks with dependencies |
| 3 | 20 min | Update documentation |
| 4 | 5 min | Archive old system |
| 5 | 15 min | Verification testing |

**Total: ~1.5-2 hours**

## Rollback Plan

If issues are encountered:

1. Old `tasks.md` is archived in `agents/tasks/archive/`
2. Beads `.beads/` directory can be removed
3. Restore archive files to original location
4. Git history preserves all states

## Post-Migration Benefits

1. **For Agents:**
   - `bd ready --json` instantly finds unblocked work
   - Structured dependency management
   - No markdown parsing required
   - Hash-based IDs prevent conflicts

2. **For Multi-Agent Coordination:**
   - 5-second auto-sync reduces conflicts
   - Git hooks enable immediate propagation
   - Collision-resistant IDs work across concurrent workers

3. **For Long-Term Maintenance:**
   - Memory decay automatically compacts old tasks
   - Full audit trail in git
   - Structured export/import for backups

## Files Created/Modified Summary

**Created:**
- `.beads/` directory (at repo root)
- `agents/tools/beads-task-management/SKILL.md`
- `agents/personas/task-manager-agent.md`
- `scripts/migrate-tasks-to-beads.sh`

**Modified:**
- `AGENTS.md` - Task management section, tool table, persona table
- `agents/tasks/README.md` - Updated for Beads
- `agents/personas/server-agent.md` - Add Beads reference
- Other agent personas - Add task discovery sections

**Archived:**
- `agents/tasks/tasks.md` → `agents/tasks/archive/tasks-pre-beads.md`
- `agents/tasks/registry.md` → `agents/tasks/archive/registry-pre-beads.md`

## Implementation Tasks

Detailed claimable tasks are defined in `agents/tasks/tasks.md`:

| Task | Description |
|------|-------------|
| T27 | Install Beads CLI |
| T28 | Initialize Beads in repository |
| T29 | Migrate P0 tasks to Beads |
| T30 | Migrate P1 tasks to Beads |
| T31 | Migrate P2 tasks to Beads |
| T32 | Add task dependencies in Beads |
| T33 | Mark completed tasks in Beads |
| T34 | Create beads-task-management tool |
| T35 | Create task-manager-agent persona |
| T36 | Update AGENTS.md for Beads workflow |
| T37 | Update existing agent personas for Beads |
| T38 | Update agents/tasks/README.md for Beads |
| T39 | Archive old task system and verify migration |

**Dependency chain:**
```
T27 → T28 → T29, T30, T31 (parallel)
                  ↓
            T32, T33 (parallel)
                  ↓
                T34
                  ↓
         T35, T36, T37, T38 (parallel)
                  ↓
                T39
```

## Labels Schema

Recommended label taxonomy:

| Category | Labels |
|----------|--------|
| Project | `trading-bot`, `media-download`, `infrastructure`, `agents` |
| Area | `refactor`, `cleanup`, `testing`, `docs`, `monitoring`, `security` |
| Component | `websocket`, `ui`, `traefik`, `zfs`, `network` |
| Urgency | `urgent`, `blocked`, `waiting` |

## Priority Mapping

| Old | Beads | Description |
|-----|-------|-------------|
| P0 | 0 | Critical / Must do immediately |
| P1 | 1 | High / Should do soon |
| P2 | 2 | Medium / Can wait |
| - | 3 | Low |
| - | 4 | Backlog |

---

**Next Steps:**
1. Review this plan
2. Approve for implementation
3. Execute phases 1-5
4. Verify migration complete
