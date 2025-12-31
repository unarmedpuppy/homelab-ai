# Agent Runs Persistence & Dashboard

**Created**: 2025-12-31
**Status**: In Progress
**Goal**: Persist all agent executions to database and display in dashboard

## Problem Statement

1. **Agent runs not tracked** - `/agent/run` endpoint only logs to ephemeral `/tmp/agent-audit.log`
2. **No visibility** - Dashboard only shows chat completions, not agent executions
3. **Agent lacks server access** - Container has no docker CLI or SSH, limiting capabilities

## Solution Overview

### Phase 1: Database Schema (agent_runs + agent_steps tables)

Add new tables to track agent executions:

```sql
-- Parent: Each agent execution
CREATE TABLE agent_runs (
    id TEXT PRIMARY KEY,
    task TEXT NOT NULL,
    working_directory TEXT,
    model_requested TEXT,
    model_used TEXT,
    backend TEXT,
    status TEXT NOT NULL,  -- 'running', 'completed', 'failed', 'max_steps'
    final_answer TEXT,
    total_steps INTEGER DEFAULT 0,
    started_at DATETIME NOT NULL,
    completed_at DATETIME,
    duration_ms INTEGER,
    source TEXT,  -- 'n8n', 'api', 'dashboard', 'cli'
    triggered_by TEXT,  -- workflow id, container name, user
    error TEXT,
    metadata TEXT  -- JSON for extensibility
);

-- Child: Each step within an agent run
CREATE TABLE agent_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_run_id TEXT NOT NULL,
    step_number INTEGER NOT NULL,
    action_type TEXT NOT NULL,  -- 'tool_call', 'think', 'terminate', 'response'
    tool_name TEXT,
    tool_args TEXT,  -- JSON
    tool_result TEXT,
    thinking TEXT,
    error TEXT,
    started_at DATETIME NOT NULL,
    duration_ms INTEGER,
    FOREIGN KEY (agent_run_id) REFERENCES agent_runs(id)
);

-- Indexes
CREATE INDEX idx_agent_runs_status ON agent_runs(status);
CREATE INDEX idx_agent_runs_started ON agent_runs(started_at);
CREATE INDEX idx_agent_runs_source ON agent_runs(source);
CREATE INDEX idx_agent_steps_run ON agent_steps(agent_run_id);
```

### Phase 2: Persist Agent Runs in Router

Update `/agent/run` endpoint in `router.py`:

1. Generate UUID for agent run at start
2. Insert `agent_runs` record with status='running'
3. After each step, insert `agent_steps` record
4. On completion, update `agent_runs` with final status, answer, duration

### Phase 3: API Endpoints for Agent Runs

```
GET  /agent/runs                    # List runs with filtering
GET  /agent/runs/{id}               # Get run with all steps
GET  /agent/runs/{id}/steps         # Get just steps
GET  /agent/runs/stats              # Aggregated statistics
POST /agent/runs/{id}/cancel        # Cancel running agent (future)
```

### Phase 4: SSH-Based Server Tools

Add new tools for server access via SSH:

```python
# tools/server_tools.py

def run_on_server(command: str) -> str:
    """Execute command on home server via SSH."""
    
def docker_ps() -> str:
    """List running containers on server."""
    
def docker_logs(container: str, tail: int = 50) -> str:
    """Get container logs from server."""
    
def docker_restart(container: str) -> str:
    """Restart a container on server."""
```

Configuration:
- Mount SSH key into container (read-only)
- Environment variables for host/port/user
- Strict command allowlist for security

### Phase 5: Dashboard Agent Runs Tab

New React component in `local-ai-dashboard`:

**Features:**
- Table view of agent runs (task, status, steps, duration, source)
- Status badges (running spinner, completed check, failed X)
- Click to expand and see step-by-step execution
- Filter by status, source, date range
- Real-time updates for running agents (WebSocket or polling)

**UI Layout:**
```
+----------------------------------------------------------+
| Agent Runs                                    [Refresh]   |
+----------------------------------------------------------+
| Status | Task                | Steps | Duration | Source  |
+--------+--------------------+-------+----------+---------+
| ✓      | Analyze container  | 8     | 45s      | n8n     |
| ✗      | Restart homepage   | 3     | 12s      | api     |
| ⟳      | Check disk space   | 2     | ...      | n8n     |
+----------------------------------------------------------+

[Expanded View - Click on row]
+----------------------------------------------------------+
| Run: abc123 - Analyze container crash                     |
| Status: Completed | Model: qwen2.5-coder | Backend: 3090  |
+----------------------------------------------------------+
| Step 1: search_skills("docker container")                 |
| Result: Found 3 matching skills...                        |
+----------------------------------------------------------+
| Step 2: read_skill("docker-container-management")         |
| Result: # Docker Container Management...                  |
+----------------------------------------------------------+
| Step 3: run_on_server("docker logs homepage --tail 50")   |
| Result: [logs output]                                     |
+----------------------------------------------------------+
| Final Answer: Container crashed due to OOM. Recommend...  |
+----------------------------------------------------------+
```

### Phase 6: Update n8n Workflow

Update container crash analysis workflow:
1. Remove "don't run docker commands" instruction
2. Agent now uses `run_on_server()` tool for docker access
3. Can actually investigate and take action

## Files to Modify

| File | Changes |
|------|---------|
| `apps/local-ai-router/database.py` | Add agent_runs, agent_steps tables |
| `apps/local-ai-router/models.py` | Add AgentRun, AgentStep Pydantic models |
| `apps/local-ai-router/agent.py` | Accept db connection, persist steps |
| `apps/local-ai-router/router.py` | Persist runs, add query endpoints |
| `apps/local-ai-router/tools/server_tools.py` | NEW: SSH-based server tools |
| `apps/local-ai-router/tools/__init__.py` | Register server tools |
| `apps/local-ai-router/docker-compose.yml` | Mount SSH key |
| `apps/local-ai-dashboard/src/App.tsx` | Add Agent Runs tab |
| `apps/local-ai-dashboard/src/components/AgentRuns.tsx` | NEW: Agent runs component |
| `apps/local-ai-dashboard/src/api/index.ts` | Add agent runs API calls |
| `apps/n8n/workflows/container-crash-agent-analysis.json` | Update task prompt |

## Security Considerations

1. **SSH Key Protection**
   - Mount key read-only
   - Use dedicated key with limited permissions
   - Consider jump host pattern for additional isolation

2. **Command Allowlist**
   - Only allow specific docker commands
   - No arbitrary shell access on server
   - Audit all server commands

3. **Agent Run Limits**
   - Max steps per run (already exists)
   - Rate limiting for agent endpoint
   - Resource quotas

## Success Criteria

- [ ] Agent runs visible in dashboard with full step history
- [ ] Agent can execute docker commands on server via SSH
- [ ] n8n workflow successfully analyzes crashed containers
- [ ] All agent interactions persisted for debugging/audit
- [ ] Dashboard shows real-time status of running agents

## Rollback Plan

If issues arise:
1. Agent runs table is additive - no impact on existing data
2. Server tools are opt-in - agent falls back to local tools
3. Dashboard tab can be hidden via feature flag
