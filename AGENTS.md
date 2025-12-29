# Home Server - Agent Instructions

**Read this file first.** This is your entry point for understanding and contributing to the project.

## ⚠️ Critical Requirements

**Before doing anything:**
1. **🔍 CHECK TOOLS FIRST**: Always check `agents/skills/` before solving problems or looking up commands
2. **📝 CREATE TOOLS**: If you solve a problem, create a tool in `agents/skills/` for future use
3. **📋 USE BEADS FOR TASKS**: All task management **MUST** use Beads (`bd` commands) - never create manual task lists

**Quick Reference:**
```bash
bd ready                 # Find work (no blockers)
bd list                  # View all tasks
bd create "title" -p 1   # Create task
bd close <id>            # Complete task

# bv (AI sidecar) - ONLY use --robot-* flags!
bv --robot-plan          # Execution plan with parallel tracks
bv --robot-insights      # Graph metrics (PageRank, critical path)
bv --robot-priority      # Priority recommendations
```

See [Task Management with Beads](#task-management-with-beads) and [Tool Lookup Protocol](#-tool-lookup-protocol) for details.

## Project Summary

This is a home server codebase with Docker-based services for media management, trading automation, and various self-hosted applications. The system uses Docker Compose for orchestration and includes automated deployment workflows.

**Tech Stack**: Docker, Docker Compose, Python, Bash, SQLite (memory system)

## Docker Images - Harbor Registry

**All Docker images MUST be pulled through Harbor registry** for offline capability and to avoid rate limits.

```bash
# ❌ WRONG - Direct pulls
image: postgres:17-alpine
image: ghcr.io/gethomepage/homepage:latest
image: lscr.io/linuxserver/sonarr:latest

# ✅ CORRECT - Through Harbor proxy cache
image: harbor.server.unarmedpuppy.com/docker-hub/library/postgres:17-alpine
image: harbor.server.unarmedpuppy.com/ghcr/gethomepage/homepage:latest
image: harbor.server.unarmedpuppy.com/lscr/linuxserver/sonarr:latest
```

**Registry Mapping:**
| Original | Harbor Path |
|----------|-------------|
| `postgres:tag` | `harbor.server.unarmedpuppy.com/docker-hub/library/postgres:tag` |
| `user/image:tag` | `harbor.server.unarmedpuppy.com/docker-hub/user/image:tag` |
| `ghcr.io/org/image:tag` | `harbor.server.unarmedpuppy.com/ghcr/org/image:tag` |
| `lscr.io/linuxserver/app:tag` | `harbor.server.unarmedpuppy.com/lscr/linuxserver/app:tag` |

**Custom Images:** Push to `harbor.server.unarmedpuppy.com/library/`

See `apps/harbor/README.md` for complete Harbor documentation.

## Quick Commands

```bash
# Docker operations
docker ps                                    # List containers
docker logs <container> --tail 100           # View logs
docker compose -f apps/X/docker-compose.yml restart  # Restart service

# Check resources
df -h                    # Disk space
free -h                  # Memory (Linux)
docker system df         # Docker disk usage

# Git workflow
git add . && git commit -m "message" && git push
```

## Architecture Overview

```
home-server/
├── apps/                    # Docker Compose applications
│   ├── trading-bot/         # Trading bot
│   ├── media-download/      # Media management stack
│   ├── traefik/             # Reverse proxy
│   └── [other apps]/
├── scripts/                 # Automation scripts
├── agents/                  # Agent system
│   ├── skills/              # Workflow guides (SKILL.md files)
│   ├── plans/               # Plans and task management
│   ├── personas/            # Agent personalities
│   └── reference/           # Reference documentation
└── docs/                    # Documentation
```

**Key Directories**:
- `apps/` - Docker applications (trading-bot, media-download, etc.)
- `.beads/` - **Task database (Beads distributed issue tracker)**
- `agents/skills/` - Reusable workflow guides
- `scripts/` - Automation and deployment scripts

## Code Style

- Follow existing patterns in each application directory
- Use Docker Compose for all services
- Document changes in appropriate README files

See `agents/reference/` for detailed patterns and workflows.

## Boundaries

### Always Do
- **🔍 CHECK TOOLS FIRST**: Before solving any problem or looking up commands, **MUST** check `agents/skills/` for existing solutions
- Check for tasks at session start: `bd ready` (unblocked work) and `bd list --status in_progress` (in-progress tasks)
- Use tools from `agents/skills/` for common workflows
- **📝 CREATE TOOLS**: If you solve a problem with commands or create a script, **MUST** create a tool in `agents/skills/` for future use
- Update task status when claiming/completing work (`bd update <id> --status in_progress`, `bd close <id>`)
- Commit after each logical unit of work
- **🔄 SUBMIT PR WHEN COMPLETE**: When a feature is complete, **MUST** submit a pull request from the feature branch back to main

### Ask First
- Architectural changes affecting multiple services
- Adding new Docker services or major dependencies
- Changing deployment workflows
- Modifying security configurations

### Never Do
- Commit secrets or credentials (use `.env` files, gitignored)
- **🚨 NEVER MAKE CHANGES DIRECTLY ON THE SERVER** - This is absolutely forbidden without explicit user approval
  - **ONLY** make changes locally in the git repository
  - Commit and push to git
  - SSH to server and `git pull` to deploy changes
  - This is the ONLY way to get changes to the server
  - No exceptions - even "quick fixes" must go through git
- Skip task status updates
- Delete files without understanding dependencies
- Make unrelated changes in a single commit

## 🔍 Tool Lookup Protocol

**⚠️ CRITICAL: This is a MUST-DO requirement**

### Before Solving Any Problem

**ALWAYS check `agents/skills/` first** before:
- Looking up commands
- Searching for solutions
- Writing new scripts
- Troubleshooting issues
- Performing any operation

**How to check tools:**
1. List available tools: `ls agents/skills/` or browse `agents/skills/` directory
2. Read tool descriptions in YAML frontmatter (in `SKILL.md` files)
3. Search for relevant keywords in tool names/descriptions
4. Read the tool's `SKILL.md` file for complete instructions

**Example workflow:**
```bash
# Need to deploy code? Check tools first:
ls agents/skills/ | grep -i deploy
# Found: standard-deployment/
cat agents/skills/standard-deployment/SKILL.md

# Need to troubleshoot? Check tools first:
ls agents/skills/ | grep -i troubleshoot
# Found: troubleshoot-container-failure/, troubleshoot-stuck-downloads/
```

### After Solving a Problem

**MUST create a tool** if you:
- Solved a problem with a set of commands
- Created a script to solve a problem
- Found a reusable workflow
- Discovered a pattern that might be needed again

**Tool creation process:**
1. Create directory: `mkdir -p agents/skills/tool-name`
2. Create `SKILL.md` with YAML frontmatter:
   ```yaml
   ---
   name: tool-name
   description: Brief description
   when_to_use: When to use this tool
   script: scripts/script-name.sh  # if applicable
   ---
   ```
3. Document the solution, usage, and examples
4. Reference the tool in this file's tool table (if appropriate)

**Why this matters:**
- Prevents duplicate work
- Builds institutional knowledge
- Makes solutions discoverable
- Enables consistency across sessions

## Workflow

### Plan → Act → Test

1. **Plan**: Understand requirements, explore code, **check tools first**
2. **Act**: Implement incrementally, commit often, follow code style, **create tools for solutions**
3. **Test**: Verify services start correctly, check logs, update docs

### Planning Documentation

Store plans in `agents/plans/` (shared) or `agents/plans/local/` (local only):

- **`agents/plans/`** - Committed plans for multi-session features, architectural decisions, implementation strategies
- **`agents/plans/local/`** - Gitignored scratch work, session notes, exploratory analysis

**Reference Documentation** (not plans):
- **`agents/reference/`** - Persistent reference guides, how-to documentation, architectural references
- **`docs/`** - Project-level documentation (security audits, etc.)

**⚠️ IMPORTANT**: 
- **Plans and strategies** → `agents/plans/` or `agents/plans/local/`
- **Reference guides and how-tos** → `agents/reference/`
- **Do NOT** create planning/strategy docs in `docs/` - use `agents/plans/` instead

See `agents/reference/plan_act.md` for plan templates and workflow details.

### Task Management with Beads

Tasks are managed using [Beads](https://github.com/steveyegge/beads), a distributed issue tracker with git-backed synchronization. See `agents/skills/beads-task-management/SKILL.md` for complete documentation.

**Session Start:**
```bash
# 1. Pull latest
git pull origin main

# 2. Find ready work (no blockers)
bd ready

# 3. Check in-progress tasks
bd list --status in_progress

# 4. Review blocked tasks
bd blocked
```

**Claiming and Working:**
```bash
# 1. Claim task
bd update <id> --status in_progress

# 2. Commit claim and push
git add .beads/ && git commit -m "claim: <id> - Description" && git push

# 3. Create feature branch
git checkout -b feature/<id>-description

# 4. Work on task...

# 5. Complete task
bd close <id> --reason "Implemented in PR #X"
git add .beads/ && git commit -m "close: <id>"

# 6. Submit PR when complete
git push origin feature/<id>-description
# Then create PR via GitHub CLI or web interface
```

**Creating Tasks:**
```bash
bd create "Task title" -t task -p 1 -l "project,area" -d "Description"
# Types: task, bug, feature, epic, chore
# Priority: 0 (critical), 1 (high), 2 (medium), 3 (low)
```

**Managing Dependencies:**
```bash
bd dep add <blocked-id> <blocker-id> --type blocks
bd dep tree <id>
```


## Tool Documentation

**⚠️ READ THIS FIRST**: Before solving any problem, **MUST** check `agents/skills/` for existing solutions. See [Tool Lookup Protocol](#-tool-lookup-protocol) above.

Agent-discoverable tool guides are in `agents/skills/`. Each tool has a `SKILL.md` file with YAML frontmatter for discovery. Tools reference scripts in `scripts/` directory when applicable.

### Deployment & Git
| Tool | Purpose | Script |
|------|---------|--------|
| [standard-deployment](agents/skills/standard-deployment/) | Deploy code changes to server | `scripts/deploy-to-server.sh` |
| [deploy-polymarket-bot](agents/skills/deploy-polymarket-bot/) | Safe polymarket-bot deployment (checks for active trades) | `agents/skills/deploy-polymarket-bot/deploy.sh` |
| [connect-server](agents/skills/connect-server/) | Execute commands on server | `scripts/connect-server.sh` |
| [git-server-sync](agents/skills/git-server-sync/) | Sync git between local and server | `scripts/git-server-sync.sh` |

### Security
| Tool | Purpose | Script |
|------|---------|--------|
| [security-audit](agents/skills/security-audit/) | Comprehensive security audit | `scripts/security-audit.sh` |
| [validate-secrets](agents/skills/validate-secrets/) | Validate secrets configuration | `scripts/validate-secrets.sh` |
| [fix-hardcoded-credentials](agents/skills/fix-hardcoded-credentials/) | Fix hardcoded credentials | `scripts/fix-hardcoded-credentials.sh` |

### Monitoring & Health
| Tool | Purpose | Script |
|------|---------|--------|
| [check-service-health](agents/skills/check-service-health/) | Health check for all services | `scripts/check-service-health.sh` |
| [system-health-check](agents/skills/system-health-check/) | Comprehensive system status | - |
| [verify-dns-setup](agents/skills/verify-dns-setup/) | Verify DNS configuration | `scripts/verify-dns-setup.sh` |

### Backup & Restore
| Tool | Purpose | Script |
|------|---------|--------|
| [backup-server](agents/skills/backup-server/) | Comprehensive server backup | `scripts/backup-server.sh` |
| [restore-server](agents/skills/restore-server/) | Restore from backups | `scripts/restore-server.sh` |
| [check-backup-health](agents/skills/check-backup-health/) | Validate backup integrity | `scripts/check-backup-health.sh` |
| [manage-b2-backup](agents/skills/manage-b2-backup/) | Manage B2 cloud backups (status, prioritize, monitor) | `scripts/backup-to-b2.sh` |
| [enable-rsnapshot](agents/skills/enable-rsnapshot/) | Enable/configure rsnapshot local backups | - |

### Troubleshooting
| Tool | Purpose | Script |
|------|---------|--------|
| [troubleshoot-container-failure](agents/skills/troubleshoot-container-failure/) | Debug container issues | - |
| [troubleshoot-stuck-downloads](agents/skills/troubleshoot-stuck-downloads/) | Fix Sonarr/Radarr issues | - |
| [cleanup-disk-space](agents/skills/cleanup-disk-space/) | Free disk space | - |
| [troubleshoot-disk-full](agents/skills/troubleshoot-disk-full/) | Diagnose/fix disk full issues (AdGuard, Docker, logs) | - |

### Drive Health & Storage
| Tool | Purpose | Script |
|------|---------|--------|
| [monitor-drive-health](agents/skills/monitor-drive-health/) | Monitor drive health with SMART status | `scripts/check-drive-health.sh` |
| [zfs-pool-recovery](agents/skills/zfs-pool-recovery/) | Recover ZFS pool from failures, import issues | - |

### Task Management
| Tool | Purpose | Script |
|------|---------|--------|
| [beads-task-management](agents/skills/beads-task-management/) | Manage tasks with Beads distributed issue tracker | - |

### Utilities
| Tool | Purpose | Script |
|------|---------|--------|
| [deploy-new-service](agents/skills/deploy-new-service/) | Set up new Docker service | - |
| [configure-traefik-labels](agents/skills/configure-traefik-labels/) | Configure Traefik reverse proxy labels for apps | - |
| [update-homepage-groups](agents/skills/update-homepage-groups/) | Update homepage organization | `scripts/update-homepage-groups.py` |
| [edit-wiki-content](agents/skills/edit-wiki-content/) | Edit Wiki.js pages via API | `apps/wiki/edit-wiki.py` |
| [post-to-mattermost](agents/skills/post-to-mattermost/) | Post messages to Mattermost via gateway | - |
| [test-local-ai-router](agents/skills/test-local-ai-router/) | Test Local AI Router with memory and metrics tracking | - |

## Agent Personas

Specialized agent personalities are available in `agents/personas/`:

| Persona | Purpose |
|---------|---------|
| [task-manager-agent](agents/personas/task-manager-agent.md) | Task coordination and management with Beads |
| [server-agent](agents/personas/server-agent.md) | Server management and deployment specialist |
| [backup-agent](agents/personas/backup-agent.md) | Backup configuration and B2 storage management |
| [critical-thinking-agent](agents/personas/critical-thinking-agent.md) | Hyper-objective logic engine for strengthening thinking and decision-making |

For task coordination and finding work, reference the task-manager-agent persona.
For server-specific tasks, reference the server-agent persona.
For backup configuration and B2 management, reference the backup-agent persona.
For critical analysis, decision review, or challenging assumptions, reference the critical-thinking-agent persona.

## Deep-Dive Documentation

| Document | Purpose |
|----------|---------|
| `.beads/` | Task database (use `bd` commands to query) |
| `agents/reference/beads.md` | **Beads CLI reference (bd)** - comprehensive command guide |
| `agents/reference/beads-viewer.md` | **Beads Viewer reference (bv)** - AI graph sidecar |
| `agents/skills/beads-task-management/` | Beads workflow guide |
| `agents/reference/docker.md` | Docker patterns and best practices |
| `agents/reference/deployment.md` | Deployment workflows |
| `agents/reference/homepage-labels.md` | Homepage dashboard labels (groups, icons, hrefs) |
| `agents/reference/plan_act.md` | Planning and workflow documentation |
| `agents/reference/storage/` | Storage and ZFS reference guides |
| `agents/reference/backups.md` | **Backup systems** - B2, rsnapshot, disaster recovery |
| `agents/reference/local-ai-router.md` | **Local AI Router** - Quick reference for memory/metrics systems |
| `agents/plans/` | Implementation plans and strategies |
| `agents/skills/` | Tool-specific guides |

---

**Keep it simple. Run commands directly. Use `bd ready` + memory for continuity.**


## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
