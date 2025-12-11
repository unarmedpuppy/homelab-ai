# Agents

Agent system for the home server. This directory contains all agent-related documentation, skills, and workflows.

## Structure

```
agents/
├── README.md                # This file - directory index
├── skills/                  # Workflow guides (SKILL.md files)
│   ├── standard-deployment/
│   ├── deploy-new-service/
│   └── ...
├── plans/                   # Implementation plans and task management
│   ├── local/              # Local scratch plans (gitignored)
│   ├── tasks.md            # Task management documentation
│   ├── archive/            # Completed task phases
│   └── templates/          # Task templates
├── personas/                # Agent personalities
│   └── server-agent.md     # Server management specialist
└── reference/               # Deep documentation
    ├── docker.md           # Docker patterns
    ├── deployment.md       # Deployment workflows
    └── plan_act.md         # Workflow documentation
```

## Quick Reference

| Directory | Purpose | Committed |
|-----------|---------|-----------|
| `skills/` | Reusable workflow guides with YAML frontmatter | ✅ |
| `plans/` | Shared implementation plans | ✅ |
| `plans/local/` | Local scratch work (session notes) | ❌ |
| `personas/` | Specialized agent personalities | ✅ |
| `reference/` | Deep-dive documentation by topic | ✅ |

## Task Management

Tasks are managed using [Beads](https://github.com/steveyegge/beads), a distributed issue tracker for AI agents.

**Quick Commands:**
```bash
bd ready                 # Find work (no blockers)
bd list                  # View all tasks
bd create "title" -p 1   # Create task
bd close <id>            # Complete task
```

See `agents/plans/tasks.md` for full documentation.

## Skills

Workflow guides with YAML frontmatter for agent discovery.

**Available Skills:**
- `standard-deployment` - Deploy code changes to server
- `deploy-new-service` - Set up a new Docker service
- `troubleshoot-container-failure` - Debug container issues
- `troubleshoot-stuck-downloads` - Fix Sonarr/Radarr queue issues
- `system-health-check` - Comprehensive system status
- `cleanup-disk-space` - Free up disk space
- `edit-wiki-content` - Programmatically edit Wiki.js pages
- `beads-task-management` - Task management with Beads

Each skill has a `SKILL.md` with YAML frontmatter describing when to use it.

## Personas

Specialized agent personalities for domain expertise.

**Available Personas:**
- `server-agent.md` - Server management and deployment specialist
- `infrastructure-agent.md` - Network infrastructure, security, DNS, and firewall specialist
- `app-implementation-agent.md` - Research and implement new applications with Traefik, homepage, and deployment
- `media-download-agent.md` - Media download stack (Sonarr, Radarr, VPN) specialist
- `task-manager-agent.md` - Task coordination and management with Beads
- `critical-thinking-agent.md` - Hyper-objective logic engine for decision-making

Personas provide focused expertise for specific domains. Reference them when working on related tasks.

## Plans

Implementation planning separated into shared and local:

- **`plans/`** - Committed plans for multi-session features, architectural decisions
- **`plans/local/`** - Gitignored scratch work, session notes, exploratory analysis

See `agents/plans/README.md` for plan format and workflow.

## Reference Documentation

Deep-dive documentation split by topic:

- `docker.md` - Docker Compose patterns and best practices
- `deployment.md` - Deployment workflows and server details
- `plan_act.md` - Plan → Act → Test workflow documentation

## Usage

1. **Session start**: Check `bd ready` for pending tasks
2. **Before work**: Check `skills/` for existing solutions
3. **During work**: Use `skills/` for common workflows, reference `personas/` for expertise
4. **Session end**: Update tasks, create skills for solutions

## Entry Point

For agents, start with `AGENTS.md` at the project root. This file provides the universal entrypoint for all AI assistants.
