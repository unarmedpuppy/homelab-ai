# Home Server - Agent Instructions

**Read this file first.** This is your entry point for understanding and contributing to the project.

## ⚠️ Critical Requirements

**Before doing anything:**
1. **🔍 CHECK TOOLS FIRST**: Always check `agents/tools/` before solving problems or looking up commands
2. **📝 CREATE TOOLS**: If you solve a problem, create a tool in `agents/tools/` for future use

See [Tool Lookup Protocol](#-tool-lookup-protocol) for details.

## Project Summary

This is a home server codebase with Docker-based services for media management, trading automation, and various self-hosted applications. The system uses Docker Compose for orchestration and includes automated deployment workflows.

**Tech Stack**: Docker, Docker Compose, Python, Bash, SQLite (memory system)

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
│   ├── memory/              # SQLite memory for decisions
│   ├── tasks/               # Task tracking
│   ├── tools/               # Workflow guides
│   └── personas/            # Agent personalities
└── docs/                    # Documentation
```

**Key Directories**:
- `apps/` - Docker applications (trading-bot, media-download, etc.)
- `agents/tasks/tasks.md` - **Task list across sessions**
- `agents/tools/` - Reusable workflow guides
- `scripts/` - Automation and deployment scripts

## Code Style

- Follow existing patterns in each application directory
- Use Docker Compose for all services
- Document changes in appropriate README files

See `agents/reference/` for detailed patterns and workflows.

## Boundaries

### Always Do
- **🔍 CHECK TOOLS FIRST**: Before solving any problem or looking up commands, **MUST** check `agents/tools/` for existing solutions
- Check `agents/tasks/tasks.md` at session start for pending/in-progress tasks
- Use tools from `agents/tools/` for common workflows
- **📝 CREATE TOOLS**: If you solve a problem with commands or create a script, **MUST** create a tool in `agents/tools/` for future use
- Update task status when claiming/completing work
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

**ALWAYS check `agents/tools/` first** before:
- Looking up commands
- Searching for solutions
- Writing new scripts
- Troubleshooting issues
- Performing any operation

**How to check tools:**
1. List available tools: `ls agents/tools/` or browse `agents/tools/` directory
2. Read tool descriptions in YAML frontmatter (in `SKILL.md` files)
3. Search for relevant keywords in tool names/descriptions
4. Read the tool's `SKILL.md` file for complete instructions

**Example workflow:**
```bash
# Need to deploy code? Check tools first:
ls agents/tools/ | grep -i deploy
# Found: standard-deployment/
cat agents/tools/standard-deployment/SKILL.md

# Need to troubleshoot? Check tools first:
ls agents/tools/ | grep -i troubleshoot
# Found: troubleshoot-container-failure/, troubleshoot-stuck-downloads/
```

### After Solving a Problem

**MUST create a tool** if you:
- Solved a problem with a set of commands
- Created a script to solve a problem
- Found a reusable workflow
- Discovered a pattern that might be needed again

**Tool creation process:**
1. Create directory: `mkdir -p agents/tools/tool-name`
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

Store plans in `agents/plans/` (shared) or `agents/plans-local/` (local only):

- **`agents/plans/`** - Committed plans for multi-session features, architectural decisions, implementation strategies
- **`agents/plans-local/`** - Gitignored scratch work, session notes, exploratory analysis

**Reference Documentation** (not plans):
- **`agents/reference/`** - Persistent reference guides, how-to documentation, architectural references
- **`docs/`** - Project-level documentation (security audits, etc.)

**⚠️ IMPORTANT**: 
- **Plans and strategies** → `agents/plans/` or `agents/plans-local/`
- **Reference guides and how-tos** → `agents/reference/`
- **Do NOT** create planning/strategy docs in `docs/` - use `agents/plans/` instead

See `agents/reference/plan_act.md` for plan templates and workflow details.

### Task Claiming (Multi-Agent)

See `agents/tasks/tasks.md` for available work. Protocol:

```bash
# 1. Pull latest
git pull origin main

# 2. Claim task (edit agents/tasks/tasks.md)
# Change [AVAILABLE] → [CLAIMED by @your-id]

# 3. Commit and push within 1 minute
git add agents/tasks/tasks.md
git commit -m "claim: Task X - Description"
git push origin main

# 4. Create feature branch
git checkout -b feature/task-x-description

# 5. When feature is complete, submit PR
# Push feature branch and create pull request to main
git push origin feature/task-x-description
# Then create PR via GitHub CLI or web interface
```


## Tool Documentation

**⚠️ READ THIS FIRST**: Before solving any problem, **MUST** check `agents/tools/` for existing solutions. See [Tool Lookup Protocol](#-tool-lookup-protocol) above.

Agent-discoverable tool guides are in `agents/tools/`. Each tool has a `SKILL.md` file with YAML frontmatter for discovery. Tools reference scripts in `scripts/` directory when applicable.

### Deployment & Git
| Tool | Purpose | Script |
|------|---------|--------|
| [standard-deployment](agents/tools/standard-deployment/) | Deploy code changes to server | `scripts/deploy-to-server.sh` |
| [connect-server](agents/tools/connect-server/) | Execute commands on server | `scripts/connect-server.sh` |
| [git-server-sync](agents/tools/git-server-sync/) | Sync git between local and server | `scripts/git-server-sync.sh` |

### Security
| Tool | Purpose | Script |
|------|---------|--------|
| [security-audit](agents/tools/security-audit/) | Comprehensive security audit | `scripts/security-audit.sh` |
| [validate-secrets](agents/tools/validate-secrets/) | Validate secrets configuration | `scripts/validate-secrets.sh` |
| [fix-hardcoded-credentials](agents/tools/fix-hardcoded-credentials/) | Fix hardcoded credentials | `scripts/fix-hardcoded-credentials.sh` |

### Monitoring & Health
| Tool | Purpose | Script |
|------|---------|--------|
| [check-service-health](agents/tools/check-service-health/) | Health check for all services | `scripts/check-service-health.sh` |
| [system-health-check](agents/tools/system-health-check/) | Comprehensive system status | - |
| [verify-dns-setup](agents/tools/verify-dns-setup/) | Verify DNS configuration | `scripts/verify-dns-setup.sh` |

### Backup & Restore
| Tool | Purpose | Script |
|------|---------|--------|
| [backup-server](agents/tools/backup-server/) | Comprehensive server backup | `scripts/backup-server.sh` |
| [restore-server](agents/tools/restore-server/) | Restore from backups | `scripts/restore-server.sh` |
| [check-backup-health](agents/tools/check-backup-health/) | Validate backup integrity | `scripts/check-backup-health.sh` |

### Troubleshooting
| Tool | Purpose | Script |
|------|---------|--------|
| [troubleshoot-container-failure](agents/tools/troubleshoot-container-failure/) | Debug container issues | - |
| [troubleshoot-stuck-downloads](agents/tools/troubleshoot-stuck-downloads/) | Fix Sonarr/Radarr issues | - |
| [cleanup-disk-space](agents/tools/cleanup-disk-space/) | Free disk space | - |

### Drive Health & Storage
| Tool | Purpose | Script |
|------|---------|--------|
| [monitor-drive-health](agents/tools/monitor-drive-health/) | Monitor drive health with SMART status | `scripts/check-drive-health.sh` |

### Utilities
| Tool | Purpose | Script |
|------|---------|--------|
| [deploy-new-service](agents/tools/deploy-new-service/) | Set up new Docker service | - |
| [configure-traefik-labels](agents/tools/configure-traefik-labels/) | Configure Traefik reverse proxy labels for apps | - |
| [update-homepage-groups](agents/tools/update-homepage-groups/) | Update homepage organization | `scripts/update-homepage-groups.py` |
| [edit-wiki-content](agents/tools/edit-wiki-content/) | Edit Wiki.js pages via API | `apps/wiki/edit-wiki.py` |

## Agent Personas

Specialized agent personalities are available in `agents/personas/`:

| Persona | Purpose |
|---------|---------|
| [server-agent](agents/personas/server-agent.md) | Server management and deployment specialist |
| [critical-thinking-agent](agents/personas/critical-thinking-agent.md) | Hyper-objective logic engine for strengthening thinking and decision-making |

For server-specific tasks, reference the server-agent persona.
For critical analysis, decision review, or challenging assumptions, reference the critical-thinking-agent persona.

## Deep-Dive Documentation

| Document | Purpose |
|----------|---------|
| `agents/tasks/tasks.md` | Task list, claiming protocol, status |
| `agents/reference/docker.md` | Docker patterns and best practices |
| `agents/reference/deployment.md` | Deployment workflows |
| `agents/reference/plan_act.md` | Planning and workflow documentation |
| `agents/reference/storage/` | Storage and ZFS reference guides |
| `agents/plans/` | Implementation plans and strategies |
| `agents/tools/` | Tool-specific guides |

---

**Keep it simple. Run commands directly. Use tasks + memory for continuity.**

