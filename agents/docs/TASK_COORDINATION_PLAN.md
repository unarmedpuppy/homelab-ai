# Task Coordination System - Implementation Plan

## Overview

Create a centralized task coordination system that allows agents to register, claim, update, and query tasks across all agents. This prevents conflicts, tracks dependencies, and enables better coordination.

## Current State Analysis

### What Exists Now
- ✅ Individual `TASKS.md` files per agent (e.g., `apps/trading-journal/TASKS.md`)
- ✅ `assign_task_to_agent()` MCP tool that appends to agent TASKS.md
- ✅ Task status tracking within individual files
- ❌ No central view of all tasks
- ❌ No cross-agent dependency tracking
- ❌ No way to query tasks by status, assignee, priority
- ❌ No conflict prevention

### Problems This Solves
1. **Task Conflicts**: Multiple agents working on same task
2. **Dependency Misses**: Agents don't know about dependencies in other agents' tasks
3. **No Visibility**: Can't see what all agents are working on
4. **Inefficient Coordination**: Hard to coordinate parallel work

## Proposed Solution

### Architecture

```
agents/
├── tasks/
│   ├── registry.md              # Central task registry (markdown table)
│   ├── registry.json            # Machine-readable format (optional, for complex queries)
│   └── README.md                # Task coordination guide
```

### Task Registry Structure

**Markdown Format** (`registry.md`):
```markdown
# Task Registry

Central registry of all tasks across all agents.

## Task Status Legend
- `pending` - Available to claim
- `claimed` - Claimed by agent, not started
- `in_progress` - Actively being worked on
- `blocked` - Waiting on dependencies
- `review` - Needs review
- `completed` - Finished
- `cancelled` - Cancelled

## Tasks

| Task ID | Title | Description | Status | Assignee | Priority | Dependencies | Project | Created | Updated |
|---------|-------|-------------|--------|----------|----------|--------------|---------|---------|---------|
| T1.1 | Setup project structure | Create directories | completed | agent-001 | high | - | trading-journal | 2025-01-10 | 2025-01-10 |
| T1.2 | Configure Docker | Setup docker-compose | in_progress | agent-001 | high | T1.1 | trading-journal | 2025-01-10 | 2025-01-11 |
| T2.1 | Add root folder | Add to Sonarr | pending | - | medium | - | media-download | 2025-01-11 | 2025-01-11 |
```

### MCP Tools to Create

1. **`register_task()`** - Register a new task in the central registry
   - Parameters: title, description, priority, dependencies, project, created_by
   - Returns: task_id, status
   - Auto-generates task ID (e.g., T1.1, T1.2, T2.1)

2. **`claim_task()`** - Claim a task (assign to agent)
   - Parameters: task_id, agent_id
   - Returns: success/error
   - Validates: task exists, not already claimed, dependencies met

3. **`update_task_status()`** - Update task status
   - Parameters: task_id, status, notes (optional)
   - Returns: success/error
   - Validates: task exists, agent has permission

4. **`query_tasks()`** - Query tasks with filters
   - Parameters: status, assignee, project, priority, dependencies, search_text
   - Returns: List of matching tasks

5. **`get_task()`** - Get single task details
   - Parameters: task_id
   - Returns: Full task details

6. **`check_task_dependencies()`** - Check if task dependencies are met
   - Parameters: task_id
   - Returns: List of dependencies and their status

### Integration Points

1. **Agent Management**: When agent is created, can register initial tasks
2. **Memory System**: Record task decisions in memory
3. **Skills**: Skills can reference tasks
4. **Individual TASKS.md**: Keep for agent-specific context, sync with registry

## Implementation Steps

### Phase 1: Core Registry (Day 1)

1. **Create directory structure**
   ```bash
   mkdir -p agents/tasks
   ```

2. **Create registry.md template**
   - Markdown table format
   - Status legend
   - Empty task table

3. **Create MCP tool: `register_task()`**
   - Parse registry.md
   - Add new task row
   - Generate task ID
   - Write back to registry.md

4. **Create MCP tool: `query_tasks()`**
   - Parse registry.md
   - Filter by parameters
   - Return matching tasks

### Phase 2: Task Management (Day 1-2)

5. **Create MCP tool: `claim_task()`**
   - Validate task exists
   - Check dependencies
   - Update assignee and status
   - Write back to registry.md

6. **Create MCP tool: `update_task_status()`**
   - Validate task exists
   - Check permissions (assignee or creator)
   - Update status
   - Write back to registry.md

7. **Create MCP tool: `get_task()`**
   - Parse registry.md
   - Find task by ID
   - Return full details

### Phase 3: Dependency Tracking (Day 2)

8. **Create MCP tool: `check_task_dependencies()`**
   - Parse task dependencies
   - Query dependent tasks
   - Return status of each dependency

9. **Enhance `claim_task()`**
   - Check dependencies before allowing claim
   - Return error if dependencies not met

10. **Enhance `update_task_status()`**
    - When task completed, notify dependent tasks
    - Update dependent task status if appropriate

### Phase 4: Integration (Day 2-3)

11. **Update `assign_task_to_agent()`**
    - Also register task in central registry
    - Keep backward compatibility with TASKS.md

12. **Create sync mechanism**
    - Option to sync individual TASKS.md with registry
    - Or: Registry is source of truth

13. **Create README.md**
    - Guide for agents on using task coordination
    - Examples and best practices

14. **Update agent prompt**
    - Add task coordination instructions
    - When to use registry vs individual TASKS.md

## Task ID Generation Strategy

**Format**: `T{project_number}.{task_number}`

**Examples**:
- `T1.1`, `T1.2`, `T1.3` - Project 1 tasks
- `T2.1`, `T2.2` - Project 2 tasks

**Implementation**:
- Parse existing tasks to find max project number
- For new project, increment project number
- For existing project, increment task number

**Alternative**: Use project name prefix
- `trading-journal-T1.1`
- `media-download-T1.1`

## Dependency Format

**In Registry**:
- Single dependency: `T1.1`
- Multiple dependencies: `T1.1,T1.2`
- Agent dependencies: `agent-001:T1.1` (task from specific agent)

**Validation**:
- Dependencies must exist
- Dependencies must be completed before claiming
- Circular dependencies detected

## Status Workflow

```
pending → claimed → in_progress → review → completed
                ↓
            blocked (if dependencies not met)
                ↓
            in_progress (when dependencies met)
```

## Error Handling

1. **Task not found**: Return clear error
2. **Already claimed**: Return error with current assignee
3. **Dependencies not met**: Return list of unmet dependencies
4. **Permission denied**: Return error if agent not assignee/creator
5. **Invalid status transition**: Return error with valid transitions

## Testing Strategy

1. **Unit tests**: Test each MCP tool independently
2. **Integration tests**: Test workflow (register → claim → update → complete)
3. **Dependency tests**: Test dependency validation
4. **Conflict tests**: Test concurrent claims

## Migration Strategy

1. **Backward compatible**: Keep existing TASKS.md files
2. **Optional registration**: Agents can opt-in to registry
3. **Gradual migration**: Migrate existing tasks over time
4. **Dual tracking**: Both registry and TASKS.md (registry is source of truth)

## Future Enhancements

1. **Task priorities**: Auto-sort by priority
2. **Task estimates**: Time estimates for tasks
3. **Task templates**: Pre-defined task templates
4. **Task notifications**: Notify agents of task updates
5. **Task analytics**: Track completion rates, bottlenecks
6. **Task search**: Full-text search across tasks
7. **Task history**: Track task status changes over time

## Files to Create

1. `agents/tasks/registry.md` - Central task registry
2. `agents/tasks/README.md` - Task coordination guide
3. `server-management-mcp/tools/task_coordination.py` - MCP tools
4. Update `server-management-mcp/server.py` - Register tools
5. Update `agents/docs/AGENT_PROMPT.md` - Add instructions

## Success Criteria

✅ Agents can register tasks in central registry
✅ Agents can query tasks by status, assignee, project
✅ Agents can claim tasks with dependency validation
✅ Agents can update task status
✅ Dependencies are tracked and validated
✅ No task conflicts (same task claimed by multiple agents)
✅ Backward compatible with existing TASKS.md files

---

**Status**: Planning Complete
**Next Steps**: Begin Phase 1 implementation
**Estimated Effort**: 2-3 days

