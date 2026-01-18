# Claude Harness - Agent Instructions

You are running inside the **claude-harness** container, the primary development environment for all homelab projects.

## Environment

- **Container**: `claude-harness` (Docker)
- **Workspace**: `/workspace` (all repos cloned here)
- **Task Database**: `/workspace/home-server/.beads/` (beads lives in home-server repo)
- **Server Access**: SSH to `claude-deploy@host.docker.internal:4242`

## Workspace Structure

```
/workspace/
├── AGENTS.md              ← Cross-repo agent instructions (read this!)
├── home-server/           ← Server infrastructure
│   └── .beads/            ← Task database (run bd from here!)
├── homelab-ai/            ← AI services
├── pokedex/               ← Pokemon app
├── polyjuiced/            ← Trading bot
├── agent-gateway/         ← Agent gateway
└── [other repos]/
```

**Always read `/workspace/AGENTS.md` first** for cross-repo context.

## Task Management (Beads)

**Important**: Run `bd` commands from `/workspace/home-server/` where `.beads/` lives:

```bash
cd /workspace/home-server
bd ready              # Find unblocked work
bd list               # View all tasks
bd create "title" -p 1  # Create task
bd close <id>         # Complete task
```

## Ralph Wiggum - Autonomous Task Loop

Ralph Wiggum processes beads tasks automatically. Start via API:

```bash
# Start processing tasks with a label
curl -X POST http://localhost:8013/v1/ralph/start \
  -H "Content-Type: application/json" \
  -d '{"label": "mercury"}'

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

## Boundaries

### Always Do
- Read `/workspace/AGENTS.md` for cross-repo context
- Use `bd` commands for task tracking
- Use `sudo` for docker commands via SSH
- Commit and push changes before ending sessions

### Never Do
- Run docker commands without sudo (will fail)
- Try to delete containers/images/volumes (blocked)
- Work outside `/workspace` for repo changes
- Forget to push changes
