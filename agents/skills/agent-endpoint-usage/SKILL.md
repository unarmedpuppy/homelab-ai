---
name: agent-endpoint-usage
description: Use the Local AI Router agent endpoint to run autonomous tasks via skill discovery
when_to_use: When you need to run autonomous agent tasks via the Local AI API
---

# Agent Endpoint Usage

The Local AI Router provides an agent endpoint that accomplishes tasks by discovering and following skills - the same skills that human operators use.

## Architecture: Skill-Based Agent

Instead of hardcoded tools, the agent **discovers capabilities on-demand** from `agents/skills/`. This means:

- **No context pollution** - Skills are loaded only when needed
- **Same knowledge base** - Agent uses the same skills as humans
- **Discoverable** - Agent can find relevant skills for any task
- **Maintainable** - Update skills once, used everywhere

## Quick Reference

| Property | Value |
|----------|-------|
| **Endpoint** | `POST /agent/run` |
| **Tools List** | `GET /agent/tools` |
| **Base URL** | `https://local-ai-api.server.unarmedpuppy.com` |

## How It Works

### Agent Workflow

1. **Receive task** from user
2. **Discover skills** - `list_skills()` or `search_skills(query)`
3. **Read skill** - `read_skill(name)` to get instructions
4. **Follow instructions** - Use `run_shell` to execute commands from skill
5. **Complete task** - `task_complete(answer)`

### Example Flow

Task: "Restart the homepage container"

```
Agent: search_skills("docker restart")
-> Found: docker-container-management

Agent: read_skill("docker-container-management")
-> Gets full instructions with exact commands

Agent: run_shell("bash scripts/connect-server.sh 'docker restart homepage'")
-> Container restarted

Agent: task_complete("Homepage container restarted successfully")
```

## Core Tools (Always Available)

### Skill Discovery

| Tool | Description |
|------|-------------|
| `list_skills` | List all available skills with descriptions |
| `search_skills` | Search skills by keyword |
| `read_skill` | Read full skill instructions |

### Execution

| Tool | Description |
|------|-------------|
| `run_shell` | Execute shell commands |
| `read_file` | Read file contents |
| `write_file` | Create/overwrite files |
| `edit_file` | Make precise edits |
| `list_directory` | List directory contents |
| `search_files` | Find files by pattern |

### Git

| Tool | Description |
|------|-------------|
| `git_status` | Working tree status |
| `git_diff` | Show changes |
| `git_log` | Commit history |
| `git_add` | Stage files |
| `git_commit` | Create commit |
| `git_push` | Push to remote |
| `git_pull` | Pull from remote |

### Completion

| Tool | Description |
|------|-------------|
| `task_complete` | Signal task is done |

## Available Skills

The agent can discover any skill in `agents/skills/`. Key categories:

### Deployment & Operations
- `standard-deployment` - Deploy code to server
- `connect-server` - SSH to server
- `docker-container-management` - Container operations

### Infrastructure
- `check-service-health` - Health monitoring
- `troubleshoot-container-failure` - Debug containers
- `configure-traefik-labels` - Reverse proxy setup

### Backups
- `backup-server` - Run backups
- `restore-server` - Restore from backup
- `manage-b2-backup` - Cloud backup management

### Utilities
- `http-api-requests` - Make HTTP requests with curl
- `cleanup-disk-space` - Free disk space
- `git-server-sync` - Sync git repos

Run `list_skills()` for the complete list.

## Basic Usage

### Run an Agent Task

```bash
curl -X POST https://local-ai-api.server.unarmedpuppy.com/agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Check the status of all Docker containers on the server",
    "working_directory": "/tmp",
    "model": "auto",
    "max_steps": 20
  }'
```

### List Available Tools

```bash
curl https://local-ai-api.server.unarmedpuppy.com/agent/tools | jq '.tools | length'
```

## Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `task` | string | Yes | - | The task description |
| `working_directory` | string | No | `/tmp` | Working directory for file operations |
| `model` | string | No | `auto` | Model to use |
| `max_steps` | integer | No | 50 | Maximum agent steps |

## Response Format

```json
{
  "success": true,
  "final_answer": "All containers are running. Found 15 active containers.",
  "steps": [...],
  "total_steps": 4,
  "terminated_reason": "completed"
}
```

## Example Tasks

### Server Operations

```bash
# Check container status
curl -X POST https://local-ai-api.server.unarmedpuppy.com/agent/run \
  -H "Content-Type: application/json" \
  -d '{"task": "List all running containers and show any that are unhealthy"}'

# Restart a service
curl -X POST https://local-ai-api.server.unarmedpuppy.com/agent/run \
  -H "Content-Type: application/json" \
  -d '{"task": "Restart the homepage container using the appropriate skill"}'

# Check service health
curl -X POST https://local-ai-api.server.unarmedpuppy.com/agent/run \
  -H "Content-Type: application/json" \
  -d '{"task": "Run a health check on all services"}'
```

### Deployment

```bash
# Deploy changes
curl -X POST https://local-ai-api.server.unarmedpuppy.com/agent/run \
  -H "Content-Type: application/json" \
  -d '{"task": "Deploy the latest changes to the homepage app"}'
```

### Debugging

```bash
# Debug a failing container
curl -X POST https://local-ai-api.server.unarmedpuppy.com/agent/run \
  -H "Content-Type: application/json" \
  -d '{"task": "The frigate container keeps restarting. Diagnose the issue."}'
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_MAX_STEPS` | 50 | Maximum steps per run |
| `AGENT_MAX_RETRIES` | 3 | Retries for malformed responses |
| `AGENT_SKILLS_DIR` | `/app/agents/skills` | Skills directory path |
| `AGENT_ALLOWED_PATHS` | `/tmp,/home` | Paths agent can access |
| `AGENT_SHELL_TIMEOUT` | 30 | Shell command timeout |

### Docker Volume Mount

Skills are mounted into the container:

```yaml
volumes:
  - ../../agents/skills:/app/agents/skills:ro
```

## Adding New Skills

To add capabilities the agent can use:

1. Create skill directory: `mkdir agents/skills/my-skill`
2. Create SKILL.md with YAML frontmatter:
   ```yaml
   ---
   name: my-skill
   description: What this skill does
   when_to_use: When to use this skill
   script: scripts/my-script.sh  # optional
   ---
   ```
3. Document the workflow with exact commands
4. Deploy - skill is immediately available to agent

## Troubleshooting

### "No skills found"
- Check that skills directory is mounted correctly
- Verify `AGENT_SKILLS_DIR` environment variable

### Agent can't find relevant skill
- Use `search_skills` with different keywords
- Check skill frontmatter has good `description` and `when_to_use`

### Commands from skill fail
- Skills contain commands for server execution
- May need to use `connect-server` skill for SSH wrapper

## Related

- [Local AI Router README](../../apps/local-ai-router/README.md)
- [Skills Directory](../../agents/skills/)
- [connect-server skill](../connect-server/SKILL.md)
- [docker-container-management skill](../docker-container-management/SKILL.md)
