# Claude Code Harness

> **⚠️ DEPRECATED**: This component has been superseded by **agent-harness** (`/workspace/agent-harness/`).
>
> Agent-harness provides:
> - Profile-based configuration (ralph, avery, gilfoyle, jobin)
> - Enhanced memory system with hooks
> - Multi-platform support (Docker, macOS, Linux native)
>
> **Migration**: Use `home-server/apps/agent-harness/docker-compose.yml` for deployment.
> See `/workspace/agent-harness/AGENTS.md` for documentation.

---

*The documentation below is kept for historical reference.*

OpenAI-compatible API wrapper for Claude Code CLI, enabling the Local AI Router to use Claude models via your Claude Max subscription.

## Quick Start Checklist

**First-time installation on server:**

```bash
# 1. SSH to server
ssh -p 4242 unarmedpuppy@192.168.86.47

# 2. Install Claude Code CLI
npm install -g @anthropic-ai/claude-code

# 3. Authenticate (one-time OAuth flow)
claude
# Opens browser URL - log in with Claude Max account
# Tokens stored in ~/.claude.json

# 4. Verify CLI works headless
claude -p "Say hello"

# 5. Pull latest code
cd ~/server && git pull

# 6. Install service
cd apps/claude-harness
sudo ./manage.sh install

# 7. Test it works
./manage.sh test
```

**After code updates:**

```bash
cd ~/server && git pull
cd apps/claude-harness
sudo ./manage.sh update
```

## Management Script

All service management is done via `manage.sh`:

| Command | Description |
|---------|-------------|
| `sudo ./manage.sh install` | First-time setup (installs systemd service) |
| `sudo ./manage.sh update` | Update service after git pull |
| `./manage.sh status` | Show service status and health |
| `./manage.sh logs [n]` | Show last n log lines (default: 100) |
| `./manage.sh follow` | Follow logs in real-time |
| `sudo ./manage.sh restart` | Restart the service |
| `sudo ./manage.sh stop` | Stop the service |
| `sudo ./manage.sh uninstall` | Remove the service |
| `./manage.sh test` | Run health check and test completion |

### What `sudo ./manage.sh install` Does

Step-by-step breakdown of the install command:

| Step | Command | What it does |
|------|---------|--------------|
| 1 | `check_root` | Verifies you ran with sudo |
| 2 | `check_claude_cli` | Verifies `claude` command is installed |
| 3 | `check_python_deps` | Installs fastapi/uvicorn/pydantic if missing |
| 4 | `cp SERVICE_FILE SYSTEMD_PATH` | Copies `claude-harness.service` to `/etc/systemd/system/` |
| 5 | `systemctl daemon-reload` | Tells systemd to re-read service files |
| 6 | `systemctl enable` | Enables auto-start on boot |
| 7 | `systemctl start` | Starts the FastAPI service immediately |
| 8 | `systemctl status` | Shows if it started successfully |

**Files modified:**

| Location | Action |
|----------|--------|
| `/etc/systemd/system/claude-harness.service` | Created (systemd service definition) |
| `~/.local/lib/python*/...` | Maybe (Python packages if missing) |
| Systemd state | Modified (service enabled and started) |

**Safe to run?** Yes. The script:
- Only touches its own service file
- Doesn't modify system configs, PATH, or bashrc
- Can be fully reversed with `sudo ./manage.sh uninstall`

### Script Safety Features

The script uses `set -euo pipefail`:
- `set -e` → Exit immediately if any command fails
- `set -u` → Error on undefined variables (catches typos)
- `set -o pipefail` → Pipeline fails if any command in it fails

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         HOME SERVER                              │
│                                                                  │
│  ┌──────────────┐      ┌─────────────────┐      ┌─────────────┐ │
│  │ Local AI     │      │ Claude Harness  │      │ Claude Code │ │
│  │ Router       │─────▶│ (FastAPI:8013)  │─────▶│ CLI         │ │
│  │ (Docker)     │      │ (systemd)       │      │ (headless)  │ │
│  └──────────────┘      └─────────────────┘      └─────────────┘ │
│         │                                              │         │
│   host.docker.internal:8013                    ~/.claude.json   │
│                                                (OAuth tokens)   │
└─────────────────────────────────────────────────────────────────┘
```

**Why not Docker?**
- Claude Code stores OAuth tokens in `~/.claude.json`
- Tokens are tied to the user session that ran `claude` interactively
- Running in Docker would require mounting credentials and managing token refresh
- Systemd service is simpler and works reliably

## Detailed Setup Instructions

### Prerequisites

- Node.js 18+ on server
- Python 3.11+ with pip
- Claude Max subscription (or Claude Pro)

### Step 1: Install Claude Code CLI

```bash
ssh -p 4242 unarmedpuppy@192.168.86.47

# Option A: npm (if Node.js installed)
npm install -g @anthropic-ai/claude-code

# Option B: Official installer
curl -fsSL https://claude.ai/install.sh | bash

# Verify
claude --version
```

### Step 2: Authenticate (One-Time)

```bash
# On server
claude

# Claude displays a URL like:
#   Please open this URL: https://claude.ai/oauth/...
#
# Open that URL in any browser
# Log in with your Claude Max account
# Tokens are stored in ~/.claude.json
```

### Step 3: Verify Headless Mode

```bash
claude -p "Say hello in exactly 5 words"
# Should output response without prompts
```

### Step 4: Install Service

```bash
cd ~/server/apps/claude-harness
sudo ./manage.sh install
```

### Step 5: Verify

```bash
./manage.sh status
./manage.sh test
```

## Endpoints

### Synchronous (OpenAI-compatible)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check (shows job counts, timeouts) |
| `/v1/models` | GET | List available models |
| `/v1/chat/completions` | POST | Chat completions (30 min timeout) |

### Async Job Queue (Fire-and-Forget)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/jobs` | POST | Create async job, returns immediately |
| `/v1/jobs` | GET | List all jobs (filter by status) |
| `/v1/jobs/{job_id}` | GET | Get job status and result |
| `/v1/jobs/{job_id}` | DELETE | Delete completed/failed job |

## Configuration

Timeouts are configurable via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAUDE_SYNC_TIMEOUT` | 1800 (30 min) | Timeout for `/v1/chat/completions` |
| `CLAUDE_ASYNC_TIMEOUT` | 7200 (2 hr) | Timeout for `/v1/jobs` async tasks |

## Usage Examples

### Synchronous Chat Completion

```bash
# Direct to harness (for testing)
curl -X POST http://localhost:8013/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello!"}]}'

# Via router (production use)
curl -X POST http://localhost:8012/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"claude-sonnet","messages":[{"role":"user","content":"Hello!"}]}'
```

### Async Job Queue (Fire-and-Forget)

For long-running autonomous tasks (CI/CD, n8n workflows, etc.):

**1. Create a Job**

```bash
curl -X POST http://claude-harness.server.unarmedpuppy.com/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Update the README in trading-bot, commit the changes, push to git, and create release tag v1.2.3",
    "working_directory": "/workspace/trading-bot",
    "system_prompt": "Complete all work autonomously. Commit with descriptive messages. Push to git. Create and push version tags when releasing."
  }'
```

**Response (immediate):**

```json
{
  "job_id": "job-abc123def456",
  "status": "pending",
  "message": "Job created and queued for execution",
  "poll_url": "/v1/jobs/job-abc123def456"
}
```

**2. Poll for Status**

```bash
curl http://claude-harness.server.unarmedpuppy.com/v1/jobs/job-abc123def456
```

**Response:**

```json
{
  "id": "job-abc123def456",
  "status": "completed",
  "prompt": "Update the README in trading-bot...",
  "model": "claude-sonnet-4-20250514",
  "created_at": "2025-01-13T20:00:00",
  "started_at": "2025-01-13T20:00:01",
  "completed_at": "2025-01-13T20:05:30",
  "result": "I've updated the README with the new API documentation...",
  "duration_seconds": 329.5
}
```

**3. List Jobs**

```bash
# All jobs
curl http://claude-harness.server.unarmedpuppy.com/v1/jobs

# Filter by status
curl "http://claude-harness.server.unarmedpuppy.com/v1/jobs?status=running"
curl "http://claude-harness.server.unarmedpuppy.com/v1/jobs?status=completed"
```

**4. Delete Completed Job**

```bash
curl -X DELETE http://claude-harness.server.unarmedpuppy.com/v1/jobs/job-abc123def456
```

### Job Request Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `prompt` | Yes | - | The task for Claude to execute |
| `model` | No | `claude-sonnet-4-20250514` | Model to use |
| `working_directory` | No | `/workspace` | Working directory (must be under `/workspace`) |
| `system_prompt` | No | - | System prompt prepended to the task |

### Job Statuses

| Status | Description |
|--------|-------------|
| `pending` | Job created, waiting to start |
| `running` | Claude is working on the task |
| `completed` | Task finished successfully |
| `failed` | Task failed with an error |
| `timeout` | Task exceeded the 2-hour timeout |

## n8n Integration

### Fire-and-Forget Workflow

Use an HTTP Request node in n8n to trigger autonomous Claude tasks:

**HTTP Request Node Settings:**
- **Method:** POST
- **URL:** `http://claude-harness.server.unarmedpuppy.com/v1/jobs`
- **Body Content Type:** JSON
- **Body:**

```json
{
  "prompt": "{{ $json.task_description }}",
  "working_directory": "/workspace/{{ $json.repo_name }}",
  "system_prompt": "You are an autonomous development agent. Complete all work, commit changes with descriptive messages, push to git. If releasing, create a semver tag and push it."
}
```

### Poll for Completion (Optional)

Add a second workflow or use n8n's Wait node + HTTP Request to poll:

1. **Wait Node:** 30 seconds
2. **HTTP Request:** GET `/v1/jobs/{{ $json.job_id }}`
3. **IF Node:** Check if `status == "completed"` or `status == "failed"`
4. **Loop back** to Wait if still `running`

### Example: Auto-Release on PR Merge

```
Webhook (PR merged) → HTTP Request (create job) → Respond "Job queued"
                              ↓
                    Claude: pulls latest, runs tests,
                    bumps version, commits, tags, pushes
```

## Router Configuration

Already configured in `apps/local-ai-router/config/providers.yaml`:

```yaml
- id: claude-harness
  name: "Claude Harness (Claude Max)"
  endpoint: "http://host.docker.internal:8013"
  enabled: true
```

After installing the harness, restart the router to connect:

```bash
cd ~/server/apps/local-ai-router
docker compose restart
```

## Troubleshooting

### Claude CLI not found

```bash
which claude
# If not found, add to PATH:
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Authentication expired

```bash
# Re-authenticate
claude
# Follow OAuth flow again
sudo ./manage.sh restart
```

### Service won't start

```bash
./manage.sh logs 50
# Check for:
# - Missing Python dependencies
# - Claude CLI not in PATH for systemd
# - Permission issues on ~/.claude.json
```

### Router can't reach harness

```bash
# Test from router container
docker exec -it local-ai-router curl http://host.docker.internal:8013/health

# If that fails, check:
# 1. Harness is running: ./manage.sh status
# 2. Port 8013 is open: sudo ufw allow 8013/tcp
# 3. Docker can reach host: check docker-compose.yml has extra_hosts
```

## Ralph Wiggum - Autonomous Task Loop

Ralph Wiggum is an autonomous task loop that works through tasks from `tasks.md`. It can be started via **curl API** or directly in the container.

**Key features:**
- Start/stop/monitor via HTTP API (curl)
- Progress tracking (e.g., "3 of 60 tasks completed")
- Tasks tracked in `/workspace/home-server/tasks.md`
- Work happens in sibling repo directories (e.g., `/workspace/polyjuiced`)
- Parses tasks.md directly - no external API required

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/ralph/start` | POST | Start Ralph Wiggum with label filter |
| `/v1/ralph/status` | GET | Get current progress and status |
| `/v1/ralph/stop` | POST | Request graceful stop |
| `/v1/ralph/logs` | GET | Get recent log lines |

### Start via curl

```bash
# Start processing tasks with label "mercury"
curl -X POST http://claude-harness.server.unarmedpuppy.com/v1/ralph/start \
  -H "Content-Type: application/json" \
  -d '{"label": "mercury"}'

# With optional filters
curl -X POST http://claude-harness.server.unarmedpuppy.com/v1/ralph/start \
  -H "Content-Type: application/json" \
  -d '{
    "label": "trading-bot",
    "priority": 1,
    "max_tasks": 5,
    "dry_run": false
  }'
```

**Response:**
```json
{
  "message": "Ralph Wiggum starting with label 'mercury'",
  "status_url": "/v1/ralph/status",
  "stop_url": "/v1/ralph/stop"
}
```

### Check Progress

```bash
curl http://claude-harness.server.unarmedpuppy.com/v1/ralph/status
```

**Response:**
```json
{
  "running": true,
  "status": "running",
  "label": "mercury",
  "total_tasks": 60,
  "completed_tasks": 3,
  "failed_tasks": 0,
  "current_task": "home-server-abc123",
  "current_task_title": "Add retry logic to API client",
  "started_at": "2025-01-17T20:30:00Z",
  "last_update": "2025-01-17T20:35:00Z",
  "message": "Working on task 4 of 60"
}
```

### Stop Gracefully

```bash
curl -X POST http://claude-harness.server.unarmedpuppy.com/v1/ralph/stop
```

Ralph will finish the current task then exit.

### View Logs

```bash
curl "http://claude-harness.server.unarmedpuppy.com/v1/ralph/logs?lines=50"
```

### Direct Shell Usage (Alternative)

```bash
# SSH or exec into the container
docker exec -it claude-harness bash

# Run directly (label is required)
./ralph-wiggum.sh --label mercury
./ralph-wiggum.sh --label trading-bot --priority 1 --max 3
./ralph-wiggum.sh --label infra --dry-run
```

### API Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `label` | **Yes** | - | Label to filter tasks |
| `priority` | No | all | Filter by priority (0-3) |
| `max_tasks` | No | 0 (unlimited) | Stop after N tasks |
| `dry_run` | No | false | Preview without executing |

### Task Location

- **Tasks file**: `/workspace/home-server/tasks.md`
- **Work directories**: `/workspace/<repo>/` (sibling directories)

Tasks are parsed from tasks.md and Claude is executed in the appropriate repo directory based on task labels.

### Label to Repo Mapping

| Label | Working Directory |
|-------|-------------------|
| `trading-bot`, `polyjuiced` | `/workspace/polyjuiced` |
| `home-server`, `infrastructure` | `/workspace/home-server` |
| `homelab-ai`, `ai-services` | `/workspace/homelab-ai` |
| `pokedex` | `/workspace/pokedex` |
| `mercury` | `/workspace` (cross-repo) |
| (others) | `/workspace` (root) |

### Example Workflow

```bash
# 1. Create tasks in tasks.md (edit the markdown file directly)
# Add task to home-server/tasks.md following the task format

# 2. Commit and push
git add tasks.md && git commit -m "add mercury tasks" && git push

# 3. Start Ralph Wiggum via API
curl -X POST http://claude-harness.server.unarmedpuppy.com/v1/ralph/start \
  -H "Content-Type: application/json" \
  -d '{"label": "mercury"}'

# 3. Monitor progress
watch -n 10 'curl -s http://claude-harness.server.unarmedpuppy.com/v1/ralph/status | jq'

# 4. Stop early if needed
curl -X POST http://claude-harness.server.unarmedpuppy.com/v1/ralph/stop
```

### Status Values

| Status | Description |
|--------|-------------|
| `idle` | Not running |
| `running` | Processing tasks |
| `stopping` | Stop requested, finishing current task |
| `completed` | All tasks done or stopped |
| `failed` | Error occurred |

### Logs

Logs are written to `/workspace/.ralph-wiggum.log` inside the container. Access via API or directly:

```bash
# Via API
curl "http://claude-harness.server.unarmedpuppy.com/v1/ralph/logs?lines=100"

# Via shell
docker exec claude-harness tail -f /workspace/.ralph-wiggum.log
```

## Limitations

1. **No true streaming**: Claude CLI outputs complete response, then chunked to client
2. **Sequential execution**: One Claude task at a time (CLI limitation). Jobs queue up.
3. **In-memory job store**: Jobs are lost on service restart. Use for fire-and-forget, not critical workflows.
4. **Rate limits**: Claude Max subscription limits apply
5. **Token expiry**: Re-authenticate if OAuth tokens expire (~30 days)

## Workspace Setup (Docker Version)

The Docker version of claude-harness includes automatic workspace configuration on startup:

### Skills Aggregation

Skills are automatically discovered and symlinked from all repos in `/workspace`:

```
/workspace/.claude/skills/           # Aggregated skills
├── deploy-new-service.md → ../home-server/agents/skills/.../SKILL.md
├── create-daily-digest.md → ../bird/agents/skills/.../SKILL.md
├── check-positions.md → ../trading-bot/agents/skills/.../SKILL.md
└── ...
```

**How it works:**
- On startup, scans all `/workspace/*/` repos
- Looks for skills in `agents/skills/*/SKILL.md` or `.claude/skills/*.md`
- Creates symlinks in `/workspace/.claude/skills/`
- Warns on name collisions (first repo alphabetically wins)

**Adding skills to your repo:**
```
your-repo/
└── agents/skills/
    └── your-skill-name/
        └── SKILL.md
```

### Task Management

Tasks are tracked in `/workspace/home-server/tasks.md`. Edit the file directly to create or update tasks:

```bash
# View tasks
cat /workspace/home-server/tasks.md | grep -E '^\### \[' | head -20

# Find open tasks
grep -E '^\### \[OPEN\]' /workspace/home-server/tasks.md

# Find tasks by label
grep -B2 'polyjuiced' /workspace/home-server/tasks.md | grep '^\###'
```

**Committing task changes:**
```bash
cd /workspace/home-server
git add tasks.md && git commit -m "task: description"
git push
```

## Files

```
claude-harness/                      # Docker version (homelab-ai)
├── Dockerfile                 # Container definition
├── main.py                    # FastAPI service
├── ralph-wiggum.sh            # Autonomous task loop script
├── entrypoint.sh              # Startup script (skills, repos)
├── requirements.txt           # Python dependencies
├── claude-harness.service     # Systemd unit file
├── manage.sh                  # Management script
├── CLAUDE.md                  # Agent instructions
├── .claude/skills/            # Container-specific skills
└── README.md                  # This file
```

## See Also

- [Claude Code Harness Plan](../../agents/plans/claude-code-harness.md)
- [Local AI Router](../local-ai-router/README.md)
- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code/overview)
