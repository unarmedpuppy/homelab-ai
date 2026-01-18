# Ralph Wiggum - Autonomous Task Loop

Ralph Wiggum is an autonomous task loop that processes beads tasks through the Claude Harness. Named after the Simpsons character, it cheerfully works through tasks one by one.

## Overview

- **Location**: Runs inside the `claude-harness` container
- **Control**: HTTP API (curl) or direct shell
- **Task Source**: Beads database at `/workspace/home-server/.beads/`
- **Work Location**: Sibling repo directories (e.g., `/workspace/polyjuiced`)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/ralph/start` | POST | Start with label filter (required) |
| `/v1/ralph/status` | GET | Get progress (X of Y tasks) |
| `/v1/ralph/stop` | POST | Graceful stop after current task |
| `/v1/ralph/logs` | GET | Recent log lines |

## Quick Start

### Start Processing Tasks

```bash
# Start with a label filter (required)
curl -X POST http://claude-harness.server.unarmedpuppy.com/v1/ralph/start \
  -H "Content-Type: application/json" \
  -d '{"label": "mercury"}'

# With all options
curl -X POST http://claude-harness.server.unarmedpuppy.com/v1/ralph/start \
  -H "Content-Type: application/json" \
  -d '{
    "label": "trading-bot",
    "priority": 1,
    "max_tasks": 5,
    "dry_run": false
  }'
```

### Monitor Progress

```bash
curl http://claude-harness.server.unarmedpuppy.com/v1/ralph/status
```

Response:
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
  "message": "Working on task 4 of 60"
}
```

### Stop Gracefully

```bash
curl -X POST http://claude-harness.server.unarmedpuppy.com/v1/ralph/stop
```

### View Logs

```bash
curl "http://claude-harness.server.unarmedpuppy.com/v1/ralph/logs?lines=100"
```

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `label` | **Yes** | - | Beads label to filter tasks |
| `priority` | No | all | Filter by priority (0=critical, 1=high, 2=medium, 3=low) |
| `max_tasks` | No | 0 | Maximum tasks (0=unlimited) |
| `dry_run` | No | false | Preview without executing |

## How It Works

1. **Query**: Runs `bd ready --json --label <label>` from `/workspace/home-server/`
2. **Claim**: Marks task as `in_progress` in beads
3. **Execute**: Runs Claude CLI in the target repo directory
4. **Complete**: Marks task as closed in beads
5. **Repeat**: Continues until no more ready tasks or stop requested

## Label to Repo Mapping

Tasks are routed to working directories based on labels:

| Label | Working Directory |
|-------|-------------------|
| `trading-bot`, `polyjuiced` | `/workspace/polyjuiced` |
| `home-server`, `infrastructure` | `/workspace/home-server` |
| `homelab-ai`, `ai-services` | `/workspace/homelab-ai` |
| `pokedex` | `/workspace/pokedex` |
| `agent-gateway` | `/workspace/agent-gateway` |
| `beads-viewer` | `/workspace/beads-viewer` |
| `mercury` | `/workspace` (cross-repo) |
| (default) | `/workspace` |

## Workflow Example

```bash
# 1. Create tasks locally (where bd is installed)
cd ~/repos/home-server
bd create "Add retry logic" -t feature -p 1 -l "mercury,trading-bot"
bd create "Fix auth refresh" -t bug -p 0 -l "mercury,trading-bot"
git add .beads/ && git commit -m "add mercury tasks" && git push

# 2. Start Ralph Wiggum
curl -X POST http://claude-harness.server.unarmedpuppy.com/v1/ralph/start \
  -H "Content-Type: application/json" \
  -d '{"label": "mercury"}'

# 3. Monitor with watch
watch -n 10 'curl -s http://claude-harness.server.unarmedpuppy.com/v1/ralph/status | jq'

# 4. Stop early if needed
curl -X POST http://claude-harness.server.unarmedpuppy.com/v1/ralph/stop
```

## Status Values

| Status | Description |
|--------|-------------|
| `idle` | Not running |
| `running` | Processing tasks |
| `stopping` | Stop requested, finishing current task |
| `completed` | All tasks done |
| `failed` | Error occurred |

## Direct Shell Usage

Alternative to API - run directly in the container:

```bash
docker exec -it claude-harness bash
./ralph-wiggum.sh --label mercury
./ralph-wiggum.sh --label trading-bot --priority 1 --max 3
./ralph-wiggum.sh --label infra --dry-run
```

## Files

| File | Purpose |
|------|---------|
| `/app/ralph-wiggum.sh` | Main script |
| `/workspace/.ralph-wiggum-status.json` | Status for API |
| `/workspace/.ralph-wiggum-control` | Control commands |
| `/workspace/.ralph-wiggum.log` | Log file |

## Limitations

- Only one Ralph instance can run at a time
- Sequential task execution (Claude CLI limitation)
- Tasks must have a label to be processed
- Beads must be in `/workspace/home-server/.beads/`

## See Also

- [Claude Harness README](../../claude-harness/README.md)
- [Beads Task Management](../../../home-server/agents/skills/beads-task-management/SKILL.md)
