# Agent Lifecycle Management Policy

## Overview

This policy defines how agents move through their lifecycle: from creation to activation, work, idle periods, and eventual archiving.

## Lifecycle States

### 1. Ready
**Definition**: Agent definition created, waiting for activation.

**Characteristics**:
- Agent definition exists in `agents/registry/agent-definitions/`
- Listed in "Ready Agents" table in registry
- No active work session
- Waiting for human activation

**Transitions**:
- → **Active**: When human activates agent in new session

### 2. Active
**Definition**: Agent is currently working on tasks.

**Characteristics**:
- Agent has active monitoring session
- Working on assigned tasks
- Regular status updates
- Listed in "Active Agents" table in registry

**Transitions**:
- → **Idle**: When agent completes work and ends session
- → **Archived**: When all tasks complete and agent is no longer needed

### 3. Idle
**Definition**: Agent has completed work but may be needed again.

**Characteristics**:
- No active monitoring session
- All assigned tasks completed
- Agent definition still available
- May be reactivated for new tasks

**Transitions**:
- → **Active**: When new tasks assigned and agent reactivated
- → **Archived**: After inactivity period (auto-archive policy)

### 4. Archived
**Definition**: Agent is no longer needed, moved to archive.

**Characteristics**:
- Agent files moved to `agents/archive/`
- Listed in "Archived Agents" table in registry
- Definition preserved for reference
- Can be reactivated if needed

**Transitions**:
- → **Active**: When reactivated for new work (via `reactivate_agent()`)

## Lifecycle Flow

```
ready → active → idle → archived
         ↓         ↑
         └─────────┘ (reactivate)
```

## Auto-Archive Policies

### Policy 1: Inactivity-Based Archiving

**Rule**: Archive agents that have been idle for a specified period.

**Default**: 30 days of inactivity

**Conditions**:
- Agent status is "idle"
- No activity for 30+ days
- All tasks completed
- No pending messages

**Action**: Automatically move to archived state

### Policy 2: Task Completion Archiving

**Rule**: Archive agents when all tasks complete and no new tasks expected.

**Conditions**:
- All assigned tasks completed
- Agent status is "idle"
- No new tasks assigned for 7+ days
- Agent explicitly marked as "ready to archive"

**Action**: Move to archived state

### Policy 3: Manual Archiving

**Rule**: Agents can be manually archived at any time.

**Conditions**:
- Agent is in "ready", "active", or "idle" state
- Human or agent decides to archive
- Use `archive_agent()` MCP tool

**Action**: Immediately move to archived state

## Archive Process

### When Archiving an Agent

1. **Verify State**: Ensure agent is ready to archive
   - All tasks completed
   - No active sessions
   - No pending messages

2. **Move Files**: Move agent directory to archive
   - From: `agents/active/{agent_id}-{specialization}/`
   - To: `agents/archive/{agent_id}-{specialization}/`

3. **Update Registry**: Update agent-registry.md
   - Remove from "Active Agents" or "Ready Agents" table
   - Add to "Archived Agents" table
   - Update status to "archived"
   - Record archive date

4. **Update Definition**: Update agent definition frontmatter
   - Set `status: archived`
   - Add `archived_date: YYYY-MM-DD`
   - Add `archived_reason: [reason]`

5. **Preserve Context**: Keep all files for reference
   - TASKS.md (completed tasks)
   - STATUS.md (final status)
   - RESULTS.md (work results)
   - COMMUNICATION.md (messages)

## Reactivation Process

### When Reactivating an Agent

1. **Verify Archive**: Check agent exists in archive
   - Verify agent definition exists
   - Check archive location

2. **Move Files**: Move agent directory back to active
   - From: `agents/archive/{agent_id}-{specialization}/`
   - To: `agents/active/{agent_id}-{specialization}/`

3. **Update Registry**: Update agent-registry.md
   - Remove from "Archived Agents" table
   - Add to "Ready Agents" or "Active Agents" table
   - Update status to "ready" or "active"
   - Record reactivation date

4. **Update Definition**: Update agent definition frontmatter
   - Set `status: ready` or `status: active`
   - Add `reactivated_date: YYYY-MM-DD`
   - Remove or update `archived_date`

5. **Prepare for Work**: Ensure agent is ready
   - Clear old status (or preserve as history)
   - Create new TASKS.md if needed
   - Update STATUS.md

## Status Tracking

### Agent Status Fields

In agent definition frontmatter:
```yaml
status: ready|active|idle|archived
created_date: YYYY-MM-DD
activated_date: YYYY-MM-DD (optional)
idle_since: YYYY-MM-DD (optional)
archived_date: YYYY-MM-DD (optional)
archived_reason: [reason] (optional)
reactivated_date: YYYY-MM-DD (optional)
```

### Registry Status

In agent-registry.md:
- **Active Agents**: Currently working
- **Ready Agents**: Waiting for activation
- **Archived Agents**: Moved to archive

## Best Practices

### When to Archive

1. **All Tasks Complete**: Agent finished all assigned work
2. **No Future Need**: Agent specialization no longer needed
3. **Long Inactivity**: Agent idle for extended period (30+ days)
4. **Resource Cleanup**: Need to clean up inactive agents

### When to Keep Active/Ready

1. **Recurring Tasks**: Agent handles recurring work
2. **Specialized Knowledge**: Agent has unique expertise needed regularly
3. **Recent Activity**: Agent was recently active
4. **Pending Tasks**: Agent has pending or upcoming tasks

### When to Reactivate

1. **Similar Work**: New tasks match agent's specialization
2. **Historical Context**: Agent has relevant past work/context
3. **Efficiency**: Faster than creating new agent
4. **Knowledge Preservation**: Agent has valuable institutional knowledge

## Integration with Other Systems

### Agent Monitoring

- Lifecycle state visible in monitoring dashboard
- Status transitions logged as activity
- Archive/reactivate actions tracked

### Task Coordination

- Archived agents removed from task assignments
- Reactivated agents can claim new tasks
- Task history preserved in archived agent files

### Memory System

- Agent decisions/patterns preserved in memory
- Archived agent context remains queryable
- Reactivated agents can access past context

### Communication

- Archived agents don't receive new messages
- Historical messages preserved in COMMUNICATION.md
- Reactivated agents can access message history

## MCP Tools

### `archive_agent()`

Archive an agent (move to archive state).

**Parameters**:
- `agent_id`: Agent ID to archive
- `reason`: Reason for archiving (optional)
- `force`: Force archive even if tasks pending (optional, default: false)

**Process**:
1. Verify agent can be archived
2. Move files to archive directory
3. Update registry
4. Update definition frontmatter

### `reactivate_agent()`

Reactivate an archived agent.

**Parameters**:
- `agent_id`: Agent ID to reactivate
- `new_tasks`: Optional new tasks to assign

**Process**:
1. Verify agent exists in archive
2. Move files back to active directory
3. Update registry
4. Update definition frontmatter
5. Optionally assign new tasks

## Auto-Archive Implementation

### Checking for Auto-Archive Candidates

Periodically (e.g., daily):
1. Query all agents with status "idle"
2. Check last activity date
3. Verify all tasks completed
4. Check for pending messages
5. If conditions met, auto-archive

### Manual Review

Before auto-archiving:
- Consider agent's specialization value
- Check for upcoming tasks
- Review agent's historical importance
- May require human approval for important agents

## Examples

### Example 1: Archive Completed Agent

```python
# Agent completed all tasks, ready to archive
await archive_agent(
    agent_id="agent-002",
    reason="All tasks completed, no future work expected"
)
```

### Example 2: Reactivate for Similar Work

```python
# Need agent with database specialization
# Check archive for existing agent
archived_agents = await query_agent_registry(
    specialization="database",
    status="archived"
)

if archived_agents["agents"]:
    # Reactivate existing agent
    await reactivate_agent(
        agent_id=archived_agents["agents"][0]["agent_id"],
        new_tasks="Optimize database performance for new service"
    )
```

### Example 3: Auto-Archive Check

```python
# Check for agents to auto-archive
idle_agents = await query_agent_registry(status="idle")

for agent in idle_agents["agents"]:
    # Check inactivity period
    idle_since = agent.get("idle_since")
    if idle_since:
        days_idle = (datetime.now() - parse_date(idle_since)).days
        if days_idle >= 30:
            # Auto-archive
            await archive_agent(
                agent_id=agent["agent_id"],
                reason=f"Auto-archived after {days_idle} days of inactivity"
            )
```

## Policy Updates

This policy can be updated as the system evolves:
- Adjust inactivity periods
- Add new lifecycle states
- Modify archive criteria
- Update reactivation processes

---

**Last Updated**: 2025-01-13
**Status**: Active
**Version**: 1.0

