# Agents

Agent system for the home server. This directory contains all agent-related documentation, tools, and workflows.

## Structure

```
agents/
├── README.md                # This file - directory index
├── tasks/                   # Task management
│   ├── tasks.md            # Active task tracking
│   ├── archive/             # Completed task phases
│   └── templates/          # Task templates
├── tools/                   # Workflow guides (formerly skills)
│   ├── standard-deployment/
│   ├── deploy-new-service/
│   └── ...
├── personas/                # Agent personalities
│   └── server-agent.md     # Server management specialist
├── plans/                   # Shared implementation plans (committed)
├── plans-local/             # Local scratch plans (gitignored)
└── reference/               # Deep documentation
    ├── docker.md           # Docker patterns
    ├── deployment.md        # Deployment workflows
    └── plan_act.md         # Workflow documentation
```

## Quick Reference

| Directory | Purpose | Committed |
|-----------|---------|-----------|
| `tasks/` | Task tracking with claiming protocol | ✅ |
| `tools/` | Reusable workflow guides with YAML frontmatter | ✅ |
| `personas/` | Specialized agent personalities | ✅ |
| `plans/` | Shared implementation plans | ✅ |
| `plans-local/` | Local scratch work (session notes) | ❌ |
| `reference/` | Deep-dive documentation by topic | ✅ |

## Tasks

Task tracking with multi-agent claiming protocol. See `agents/tasks/tasks.md` for active tasks.

**Task Claiming Protocol:**
1. Pull latest: `git pull origin main`
2. Edit `agents/tasks/tasks.md`: Change `[AVAILABLE]` → `[CLAIMED by @your-id]`
3. Commit and push within 1 minute
4. Create feature branch

See `agents/tasks/README.md` for full documentation.

## Tools

Workflow guides (formerly "skills") with YAML frontmatter for agent discovery.

**Available Tools:**
- `standard-deployment` - Deploy code changes to server
- `deploy-new-service` - Set up a new Docker service
- `troubleshoot-container-failure` - Debug container issues
- `troubleshoot-stuck-downloads` - Fix Sonarr/Radarr queue issues
- `system-health-check` - Comprehensive system status
- `cleanup-disk-space` - Free up disk space
- `edit-wiki-content` - Programmatically edit Wiki.js pages

Each tool has a `README.md` with YAML frontmatter describing when to use it.

## Personas

Specialized agent personalities for domain expertise.

**Available Personas:**
- `server-agent.md` - Server management and deployment specialist

Personas provide focused expertise for specific domains. Reference them when working on related tasks.

## Plans

Implementation planning separated into shared and local:

- **`plans/`** - Committed plans for multi-session features, architectural decisions
- **`plans-local/`** - Gitignored scratch work, session notes, exploratory analysis

See `agents/plans/README.md` for plan format and workflow.

## Reference Documentation

Deep-dive documentation split by topic:

- `docker.md` - Docker Compose patterns and best practices
- `deployment.md` - Deployment workflows and server details
- `plan_act.md` - Plan → Act → Test workflow documentation

## Usage

1. **Session start**: Check `tasks/tasks.md` for pending/in-progress tasks
2. **Before work**: Check `tools/` for existing solutions
3. **During work**: Use `tools/` for common workflows, reference `personas/` for expertise
4. **Session end**: Update tasks, create tools for solutions

## Entry Point

For agents, start with `AGENTS.md` at the project root. This file provides the universal entrypoint for all AI assistants.
