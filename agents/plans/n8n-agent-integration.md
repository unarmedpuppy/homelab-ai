# n8n + Agent Integration Plan

**Status**: In Progress
**Created**: 2025-12-31
**Last Updated**: 2025-12-31
**Purpose**: Integrate n8n workflow automation with the Local AI Router agent endpoint

## Overview

Connect n8n's event detection capabilities with the agent endpoint's skill-based task execution to create an autonomous server management system.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Server Events  │────►│      n8n        │────►│  Agent Endpoint │
│  (Docker, disk, │     │   (detection,   │     │  (analysis,     │
│   health, etc.) │     │    routing)     │     │   action)       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## Phase 1: Quick Win (CURRENT)

### Goal
Prove the integration works with a single use case: container crash analysis.

### Implementation

**Workflow**: `container-crash-agent-analysis.json`

```
Every 5 min → Check containers → Filter failures → Get logs → Call /agent/run → Log result
```

**What it does**:
1. Checks for crashed/unhealthy containers every 5 minutes
2. Collects container logs
3. Sends task to agent: "Analyze why X crashed"
4. Agent uses skills to diagnose
5. Returns analysis (read-only, no auto-fix)

**Limitations**:
- Synchronous HTTP call (may timeout for complex analysis)
- 120 second timeout
- No notifications yet (just logs result)
- Single container per run

### Files Created

| File | Purpose |
|------|---------|
| `apps/n8n/workflows/container-crash-agent-analysis.json` | The workflow |
| `agents/plans/n8n-agent-integration.md` | This plan |

### Setup Instructions

1. **Import workflow in n8n**:
   ```
   n8n UI → Workflows → Import from File → container-crash-agent-analysis.json
   ```

2. **Activate workflow**:
   - Review nodes
   - Toggle "Active" switch

3. **Test manually**:
   - Stop a container: `docker stop homepage`
   - Wait for next 5-minute check, or trigger manually
   - Check execution results in n8n

### Success Criteria

- [ ] Workflow imports without errors
- [ ] Agent endpoint receives task
- [ ] Agent returns meaningful analysis
- [ ] Execution completes in < 60 seconds

---

## Phase 2: Add Notifications

### Goal
Send agent analysis results to Mattermost/Telegram.

### Implementation

Add nodes after Format Success/Error:
```
Format Success → Post to Mattermost
Format Error → Post to Mattermost (with alert emoji)
```

**Mattermost message format**:
```
## Container Crash Analysis

**Container**: homepage
**Exit Code**: 1
**Agent Analysis**:

The container crashed due to [reason]. 

**Recommended fix**: [fix]

---
_Analyzed by Local AI Agent at 2025-12-31 10:00:00_
```

### Files to Modify

- `container-crash-agent-analysis.json` - Add notification nodes
- May need `post-to-mattermost` skill for agent to use

---

## Phase 3: Async with Callback

### Problem
Current synchronous approach has issues:
- 120s timeout may not be enough for complex analysis
- n8n worker blocked during agent execution
- No way to queue multiple tasks

### Solution: Async Execution with Webhook Callback

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    n8n      │────►│  /agent/run     │────►│  Agent Worker   │
│  (trigger)  │     │  (returns       │     │  (async exec)   │
└─────────────┘     │   task_id)      │     └────────┬────────┘
       ▲            └─────────────────┘              │
       │                                             │
       └─────────────────────────────────────────────┘
              POST to n8n webhook when done
              (includes task_id, result)
```

### Agent Endpoint Changes

Add optional `callback_url` parameter:

```json
POST /agent/run
{
  "task": "Analyze container crash",
  "callback_url": "https://n8n.server.unarmedpuppy.com/webhook/agent-callback",
  "callback_headers": {
    "X-Task-ID": "abc123"
  }
}
```

**Response** (immediate):
```json
{
  "accepted": true,
  "task_id": "abc123",
  "status": "queued"
}
```

**Callback** (when complete):
```json
POST https://n8n.server.unarmedpuppy.com/webhook/agent-callback
{
  "task_id": "abc123",
  "success": true,
  "final_answer": "...",
  "steps": [...],
  "duration_seconds": 45
}
```

### n8n Workflow Changes

1. **Trigger workflow**: POST to /agent/run with callback_url
2. **Receive webhook**: New workflow triggered by callback
3. **Process result**: Send notifications, take actions

### Implementation Tasks

- [ ] Add `callback_url` parameter to agent endpoint
- [ ] Add async execution mode (background task)
- [ ] Add task status endpoint: `GET /agent/status/{task_id}`
- [ ] Create n8n webhook receiver workflow
- [ ] Add task timeout/cancellation

---

## Phase 4: Queue-Based Architecture

### Problem
Multiple simultaneous events could overwhelm the agent.

### Solution: Redis Queue

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    n8n      │────►│   Redis     │────►│   Agent     │────►│  Results    │
│  (events)   │     │   Queue     │     │  Worker(s)  │     │   Store     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                          │                    │
                          │   Task lifecycle:  │
                          │   queued → running │
                          │   → completed/failed
                          │
                    ┌─────────────┐
                    │   Status    │
                    │   API       │
                    └─────────────┘
```

### Components

**Redis Queue**:
- Task queue with priority
- Deduplication (don't analyze same crash twice)
- Rate limiting

**Agent Worker**:
- Pulls tasks from queue
- Executes agent loop
- Stores results

**Results Store**:
- Task results in Redis or SQLite
- TTL for cleanup
- Queryable history

**Status API**:
- `GET /agent/tasks` - List tasks
- `GET /agent/tasks/{id}` - Get task status/result
- `DELETE /agent/tasks/{id}` - Cancel task

### Docker Compose Addition

```yaml
services:
  agent-worker:
    build: ./local-ai-router
    command: python worker.py
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379
      - WORKER_CONCURRENCY=2

  redis:
    image: harbor.server.unarmedpuppy.com/docker-hub/library/redis:7-alpine
    volumes:
      - redis_data:/data
```

### Implementation Tasks

- [ ] Add Redis to local-ai-router stack
- [ ] Create task queue module
- [ ] Create worker process
- [ ] Create results store
- [ ] Create status API endpoints
- [ ] Update n8n workflows to use queue
- [ ] Add task deduplication
- [ ] Add priority levels

---

## Phase 5: Auto-Remediation

### Goal
Allow agent to take actions (with guardrails).

### Action Levels

| Level | Actions | Approval |
|-------|---------|----------|
| **Read-only** | Analyze, diagnose, recommend | None |
| **Safe actions** | Restart container, clear cache | Automatic |
| **Risky actions** | Modify config, redeploy | Require approval |
| **Dangerous** | Delete data, stop services | Blocked |

### Approval Flow

For risky actions:
```
Agent: "I recommend restarting nginx with new config. Approve?"
        ↓
n8n: Send approval request to Mattermost
        ↓
Human: React with ✅ or ❌
        ↓
n8n: Receive reaction webhook
        ↓
Agent: Execute or abort
```

### Implementation Tasks

- [ ] Define action levels in skills
- [ ] Add action approval queue
- [ ] Create Mattermost approval workflow
- [ ] Add approval timeout (default: deny)
- [ ] Log all actions for audit

---

## Event Types to Support

### Phase 1 (Current)
- [x] Container crash/exit

### Phase 2
- [ ] Container unhealthy
- [ ] High memory/CPU usage
- [ ] Disk space warning

### Phase 3
- [ ] Service health check failure
- [ ] Backup failure
- [ ] SSL certificate expiring
- [ ] Docker build failure

### Phase 4
- [ ] Security alerts (fail2ban, etc.)
- [ ] Network connectivity issues
- [ ] ZFS pool degraded

---

## Skills for Agent

The agent needs skills for each task type:

| Skill | Purpose | Status |
|-------|---------|--------|
| `troubleshoot-container-failure` | Diagnose container crashes | ✅ Exists |
| `docker-container-management` | Restart, stop, start containers | ✅ Exists |
| `cleanup-disk-space` | Free disk space | ✅ Exists |
| `check-service-health` | Check service endpoints | ✅ Exists |
| `analyze-logs` | Parse and analyze log files | ❌ TODO |
| `check-resource-usage` | Analyze CPU/memory usage | ❌ TODO |

---

## Security Considerations

### Agent Permissions
- Agent runs with limited filesystem access (`AGENT_ALLOWED_PATHS`)
- Shell commands have timeout (`AGENT_SHELL_TIMEOUT`)
- No direct server SSH - uses `connect-server` skill

### n8n Webhook Security
- Callback webhooks should use authentication
- Rate limit incoming webhooks
- Validate callback origin

### Action Guardrails
- Whitelist of allowed container actions
- Blacklist of protected containers (database, critical infra)
- Maximum restarts per hour (prevent restart loops)

---

## Monitoring

### Metrics to Track
- Tasks queued / completed / failed
- Average task duration
- Agent token usage
- Actions taken vs recommended

### Dashboards
- Add to Grafana: Agent task status
- Alert on: High failure rate, queue backup

---

## Timeline Estimate

| Phase | Effort | Dependencies |
|-------|--------|--------------|
| Phase 1 (Quick Win) | 1 hour | None |
| Phase 2 (Notifications) | 2 hours | Phase 1 |
| Phase 3 (Async) | 4-6 hours | Phase 1 |
| Phase 4 (Queue) | 8-12 hours | Phase 3, Redis |
| Phase 5 (Auto-Remediation) | 8-12 hours | Phase 4, Mattermost |

---

## References

- [Agent Endpoint Usage](../skills/agent-endpoint-usage/SKILL.md)
- [Local AI Router README](../../apps/local-ai-router/README.md)
- [n8n Workflows](../../apps/n8n/workflows/)
- [Troubleshoot Container Failure](../skills/troubleshoot-container-failure/SKILL.md)
