# Claude Harness - Agent Instructions

You are running inside the **claude-harness** container, the primary development environment for all homelab projects.

## Environment

- **Container**: `claude-harness` (Docker)
- **Workspace**: `/workspace` (all repos cloned here)
- **Task Tracking**: `/workspace/home-server/tasks.md` (markdown-based task file)
- **Server Access**: SSH to `claude-deploy@host.docker.internal:4242`

## Workspace Structure

```
/workspace/
├── AGENTS.md              ← Cross-repo agent instructions (read this!)
├── home-server/           ← Server infrastructure
│   └── tasks.md           ← Task tracking (edit directly or use API)
├── homelab-ai/            ← AI services
├── pokedex/               ← Pokemon app
├── polyjuiced/            ← Trading bot
├── agent-gateway/         ← Agent gateway
└── [other repos]/
```

**Always read `/workspace/AGENTS.md` first** for cross-repo context.

## Task Management (tasks.md)

Tasks are tracked in `/workspace/home-server/tasks.md`. Edit the file directly and commit changes.

## Ralph Wiggum - Autonomous Task Loop

Ralph Wiggum processes tasks automatically. Start via API:

```bash
# Start processing tasks with a label
curl -X POST http://localhost:8013/v1/ralph/start \
  -H "Content-Type: application/json" \
  -d '{"label": "multi-ralph"}'

# Check progress
curl http://localhost:8013/v1/ralph/status

# Stop gracefully
curl -X POST http://localhost:8013/v1/ralph/stop
```

See `agents/reference/ralph-wiggum.md` for full documentation.

## Critical Rules

### Docker Commands Require `sudo`

The `claude-deploy` user is **NOT in the docker group** for security:

```bash
# CORRECT
ssh -p 4242 claude-deploy@host.docker.internal 'sudo docker ps'

# WRONG (will fail)
ssh -p 4242 claude-deploy@host.docker.internal 'docker ps'
```

### Allowed Docker Operations (via SSH)

| Command | Allowed |
|---------|---------|
| `sudo docker ps/logs/inspect/images/stats` | Yes |
| `sudo docker start/stop/restart` | Yes |
| `sudo docker compose up/down` | Yes (in /home/unarmedpuppy/server/apps/ only) |
| `sudo docker rm/rmi/volume rm/system prune` | **NO - BLOCKED** |

## Git Workflow

All repos are cloned to `/workspace`. Work directly here:

```bash
cd /workspace/home-server
git pull
# Make changes...
git add . && git commit -m "message" && git push
```

## Deployment

- **Code changes**: Push tag → CI builds → Harbor Deployer auto-deploys
- **Config changes**: Push to home-server → Gitea Actions deploys

No SSH deployment needed - it's fully automated.

## Access Methods

This container supports multiple access methods:

| Port | Service | Use Case |
|------|---------|----------|
| 8013 | Claude API | OpenAI-compatible API |
| 22 | SSH | Terminal access |
| 8443 | code-server | VS Code in browser |

## Puppeteer MCP (Browser Automation)

Puppeteer MCP provides browser automation tools (screenshots, clicking, navigation). It's installed but **disabled by default** to save resources.

### Enable/Disable

```bash
# Check status
mcp-puppeteer status

# Enable (then restart Claude session)
mcp-puppeteer enable

# Disable
mcp-puppeteer disable
```

### Available Tools (when enabled)

| Tool | Description |
|------|-------------|
| `puppeteer_navigate` | Navigate to a URL |
| `puppeteer_screenshot` | Take a screenshot |
| `puppeteer_click` | Click an element |
| `puppeteer_fill` | Fill a form field |
| `puppeteer_evaluate` | Run JavaScript in page |

### Use Case

Enable this when you need to:
- Visually inspect a deployed web app
- Take screenshots of UI issues
- Test user interactions
- Debug frontend rendering

## Boundaries

### Always Do
- Read `/workspace/AGENTS.md` for cross-repo context
- Track tasks in `/workspace/home-server/tasks.md` or via Tasks API
- Use `sudo` for docker commands via SSH
- Commit and push changes before ending sessions

### Never Do
- Run docker commands without sudo (will fail)
- Try to delete containers/images/volumes (blocked)
- Work outside `/workspace` for repo changes
- Forget to push changes
