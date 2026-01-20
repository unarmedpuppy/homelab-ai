# Ralph Wiggum - Autonomous Task Loop

Ralph Wiggum is an autonomous task loop that processes tasks through the Claude Harness. Named after the Simpsons character, it cheerfully works through tasks one by one.

## Overview

- **Location**: Runs inside the `claude-harness` container
- **Control**: HTTP API (curl) or direct shell
- **Task Source**: Tasks API backed by `/workspace/home-server/tasks.md`
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
  -d '{"label": "multi-ralph"}'

# With all options
curl -X POST http://claude-harness.server.unarmedpuppy.com/v1/ralph/start \
  -H "Content-Type: application/json" \
  -d '{
    "label": "multi-ralph",
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
  "label": "multi-ralph",
  "remaining_tasks": 5,
  "completed_tasks": 3,
  "failed_tasks": 0,
  "current_task": "multi-ralph-001",
  "current_task_title": "Add RalphInstance dataclass",
  "message": "Working on task 4"
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
| `label` | **Yes** | - | Label to filter tasks |
| `priority` | No | all | Filter by priority (0=critical, 1=high, 2=medium, 3=low) |
| `max_tasks` | No | 0 | Maximum tasks (0=unlimited) |
| `dry_run` | No | false | Preview without executing |

## How It Works

1. **Query**: Parses `tasks.md` for open tasks matching the label
2. **Claim**: Updates task status to IN_PROGRESS in tasks.md
3. **Execute**: Runs Claude CLI in the target repo directory
4. **Review**: Runs fresh-eyes review to verify completion
5. **Complete**: Updates task status to CLOSED in tasks.md
6. **Repeat**: Continues until no more ready tasks or stop requested

## Task Format

Tasks are defined in `/workspace/home-server/tasks.md`:

```markdown
### [OPEN] Task Title {#task-id}
| priority | repo | labels |
|----------|------|--------|
| P1 | polyjuiced | feature, api |

Task description here.

#### Verification
```bash
# Commands to verify completion
test -f src/api.py && echo 'PASS'
```
```

The `repo` field determines which directory Ralph works in:

| Repo Value | Working Directory |
|------------|-------------------|
| `polyjuiced` | `/workspace/polyjuiced` |
| `home-server` | `/workspace/home-server` |
| `homelab-ai` | `/workspace/homelab-ai` |
| `pokedex` | `/workspace/pokedex` |

## Workflow Example

```bash
# 1. Edit tasks.md to add tasks
vim /workspace/home-server/tasks.md

# 2. Commit and push
cd /workspace/home-server
git add tasks.md && git commit -m "add multi-ralph tasks" && git push

# 3. Start Ralph Wiggum
curl -X POST http://claude-harness.server.unarmedpuppy.com/v1/ralph/start \
  -H "Content-Type: application/json" \
  -d '{"label": "multi-ralph"}'

# 4. Monitor with watch
watch -n 10 'curl -s http://claude-harness.server.unarmedpuppy.com/v1/ralph/status | jq'

# 5. Stop early if needed
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
./ralph-wiggum.sh --label multi-ralph
./ralph-wiggum.sh --label dashboard --priority 1 --max 3
./ralph-wiggum.sh --label infra --dry-run
```

## Files

| File | Purpose |
|------|---------|
| `/app/ralph-wiggum.sh` | Main script |
| `/workspace/.ralph-{label}-status.json` | Status for API (per-instance) |
| `/workspace/.ralph-{label}-control` | Control commands (per-instance) |
| `/workspace/.ralph-{label}.log` | Log file (per-instance) |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WORKSPACE_DIR` | `/workspace` | Base workspace directory |
| `TASKS_API_URL` | `http://llm-router:8013` | Tasks API endpoint |
| `STATUS_FILE` | `/workspace/.ralph-{label}-status.json` | Status file path |
| `CONTROL_FILE` | `/workspace/.ralph-{label}-control` | Control file path |

## Limitations

- Sequential task execution (Claude CLI limitation)
- Tasks must have a label to be processed
- Tasks must have a `repo` field in the metadata table

## See Also

- [Claude Harness README](../../claude-harness/README.md)
- [Tasks.md](../../../home-server/tasks.md)
