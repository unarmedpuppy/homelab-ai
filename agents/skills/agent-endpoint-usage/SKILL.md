---
name: agent-endpoint-usage
description: Use the Local AI Router agent endpoint to run autonomous tasks
when_to_use: When you need to run autonomous agent tasks via the Local AI API
---

# Agent Endpoint Usage

The Local AI Router provides an agent endpoint that can autonomously execute tasks using a set of registered tools. The agent runs in a host-controlled loop where the model emits one action per turn.

## Quick Reference

| Property | Value |
|----------|-------|
| **Endpoint** | `POST /agent/run` |
| **Tools List** | `GET /agent/tools` |
| **Base URL** | `https://local-ai-api.server.unarmedpuppy.com` |

## Basic Usage

### Run an Agent Task

```bash
curl -X POST https://local-ai-api.server.unarmedpuppy.com/agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "List all Python files in the current directory",
    "working_directory": "/tmp",
    "model": "auto",
    "max_steps": 20
  }'
```

### List Available Tools

```bash
curl https://local-ai-api.server.unarmedpuppy.com/agent/tools | jq '.tools | length'
```

## Available Tools (27 total)

### File Tools (5)

| Tool | Description |
|------|-------------|
| `read_file` | Read contents of a file |
| `write_file` | Create or overwrite a file |
| `edit_file` | Make precise edits using string replacement |
| `list_directory` | List contents of a directory |
| `search_files` | Find files by pattern or content |

### Shell Tools (2)

| Tool | Description |
|------|-------------|
| `run_shell` | Execute a shell command |
| `task_complete` | Signal that the task is done |

### Git Tools (9)

| Tool | Description |
|------|-------------|
| `git_status` | Show working tree status |
| `git_diff` | Show changes between commits/working tree |
| `git_log` | Show commit logs |
| `git_add` | Add files to staging area |
| `git_commit` | Create a commit |
| `git_branch` | List or create branches |
| `git_checkout` | Switch branches or restore files |
| `git_pull` | Fetch and merge from remote |
| `git_push` | Push commits to remote |

### SSH Tools (2)

| Tool | Description |
|------|-------------|
| `ssh_command` | Execute command on remote server via SSH |
| `ssh_file_exists` | Check if file/directory exists on remote server |

**SSH Configuration:**
- Default user: `unarmedpuppy`
- Default port: `4242`
- Allowed hosts: `server`, `192.168.86.47` (configurable via `AGENT_SSH_HOSTS`)

### Docker Tools (6)

| Tool | Description |
|------|-------------|
| `docker_ps` | List containers (optionally all) |
| `docker_logs` | Get container logs |
| `docker_restart` | Restart a container |
| `docker_compose_up` | Start services with docker-compose |
| `docker_inspect` | Get detailed container info |
| `docker_stats` | Get resource usage statistics |

### HTTP Tools (3)

| Tool | Description |
|------|-------------|
| `http_get` | Make GET request to API/URL |
| `http_post` | Make POST request (webhooks, APIs) |
| `http_head` | Check if URL exists (HEAD request) |

**HTTP Configuration:**
- Default timeout: 30 seconds
- Max response size: 100KB
- Internal network access: Enabled by default

## Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `task` | string | Yes | - | The task description for the agent |
| `working_directory` | string | No | `/tmp` | Working directory for file operations |
| `model` | string | No | `auto` | Model to use (auto, small, big, etc.) |
| `max_steps` | integer | No | 50 | Maximum number of agent steps |

## Response Format

```json
{
  "status": "complete",
  "result": "Task completed successfully. Created hello.py with hello world code.",
  "steps_taken": 3,
  "model_used": "qwen2.5:14b",
  "duration_seconds": 12.5
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_MAX_STEPS` | 50 | Maximum steps per agent run |
| `AGENT_MAX_RETRIES` | 3 | Retries for malformed responses |
| `AGENT_ALLOWED_PATHS` | `/tmp,/home` | Comma-separated allowed paths |
| `AGENT_SHELL_TIMEOUT` | 30 | Shell command timeout (seconds) |
| `AGENT_SSH_HOSTS` | `server,192.168.86.47` | Allowed SSH hosts |
| `AGENT_SSH_USER` | `unarmedpuppy` | Default SSH user |
| `AGENT_SSH_PORT` | `4242` | Default SSH port |
| `AGENT_HTTP_TIMEOUT` | 30 | HTTP request timeout |
| `AGENT_HTTP_ALLOW_INTERNAL` | `true` | Allow internal network URLs |

## Security

The agent has built-in security measures:

### Command Blocklist
Dangerous commands are blocked:
- `rm -rf /`, filesystem formatters
- Fork bombs, chmod 777 on root
- Piping curl/wget to shell

### Path Validation
File operations are sandboxed to:
- Working directory
- `/tmp` and `/home`
- Additional paths via `AGENT_EXTRA_PATHS`

### SSH Host Allowlist
SSH only connects to pre-approved hosts in `AGENT_SSH_HOSTS`.

## Examples

### Deploy a Service

```bash
curl -X POST https://local-ai-api.server.unarmedpuppy.com/agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "SSH to the server and restart the homepage container",
    "max_steps": 10
  }'
```

### Check Container Health

```bash
curl -X POST https://local-ai-api.server.unarmedpuppy.com/agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "List all running containers and show the logs of any that are unhealthy",
    "max_steps": 15
  }'
```

### Make API Requests

```bash
curl -X POST https://local-ai-api.server.unarmedpuppy.com/agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Check if the GitHub API is responding and show the rate limit status",
    "max_steps": 5
  }'
```

### Create and Commit Code

```bash
curl -X POST https://local-ai-api.server.unarmedpuppy.com/agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "In /tmp/test-repo, create a Python script that fetches weather data, then commit it",
    "working_directory": "/tmp/test-repo",
    "max_steps": 20
  }'
```

## Troubleshooting

### "Host not in SSH allowlist"
Add the host to `AGENT_SSH_HOSTS` environment variable in the router's docker-compose.yml.

### "Path not in allowed directories"
The path is outside the sandbox. Add it to `AGENT_ALLOWED_PATHS` or `AGENT_EXTRA_PATHS`.

### "Command blocked"
The command matches a dangerous pattern. Review the command and use safer alternatives.

### Tool not found
Check `GET /agent/tools` to see available tools. Some tools may not be registered if their module failed to import.

## Related

- [Local AI Router README](../../apps/local-ai-router/README.md)
- [test-local-ai-router skill](../test-local-ai-router/SKILL.md)
