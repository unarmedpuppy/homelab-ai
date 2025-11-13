# Task Coordination System

Central task registry for coordinating tasks across all agents.

## Overview

The Task Coordination System provides a centralized way to:
- Register tasks across all agents
- Query tasks by status, assignee, project, priority
- Track dependencies between tasks
- Prevent task conflicts
- Coordinate parallel work

## Location

- **Registry**: `agents/tasks/registry.md` - Central task registry (markdown table)
- **MCP Tools**: Available via `server-management-mcp` MCP server

## Task Status

Tasks can have the following statuses:
- `pending` - Available to claim
- `claimed` - Claimed by agent, not started
- `in_progress` - Actively being worked on
- `blocked` - Waiting on dependencies
- `review` - Needs review
- `completed` - Finished
- `cancelled` - Cancelled

## Using Task Coordination

### Register a New Task

```python
register_task(
    title="Setup database schema",
    description="Create PostgreSQL schema with tables for trades, positions, and metrics",
    project="trading-journal",
    priority="high",
    dependencies="T1.1,T1.2",  # Optional: comma-separated task IDs
    created_by="agent-001"
)
```

**Returns**: Task ID (e.g., `T1.1`)

### Query Tasks

```python
# Query by status
query_tasks(status="pending")

# Query by assignee
query_tasks(assignee="agent-001")

# Query by project
query_tasks(project="trading-journal")

# Query by priority
query_tasks(priority="high")

# Search in title/description
query_tasks(search_text="database")

# Combine filters
query_tasks(
    status="pending",
    project="trading-journal",
    priority="high",
    limit=10
)
```

## Task ID Format

Tasks use the format: `T{project_number}.{task_number}`

Examples:
- `T1.1`, `T1.2`, `T1.3` - First project's tasks
- `T2.1`, `T2.2` - Second project's tasks

Task IDs are auto-generated based on the project name.

## Dependencies

Tasks can depend on other tasks. Dependencies are specified as comma-separated task IDs:

```
dependencies="T1.1,T1.2"
```

**Note**: Dependency validation (checking if dependencies are completed) will be added in Phase 3.

## Integration with Individual TASKS.md

The central registry is the **source of truth** for task coordination. Individual agent `TASKS.md` files can still exist for agent-specific context, but:

- **Registry**: Cross-agent coordination, dependency tracking, conflict prevention
- **Individual TASKS.md**: Agent-specific notes, detailed context, implementation details

## Best Practices

1. **Register tasks early**: Register tasks when they're identified, not when work starts
2. **Use clear titles**: Keep titles concise but descriptive
3. **Include dependencies**: Always specify dependencies to enable coordination
4. **Update status**: Keep task status current as work progresses
5. **Use projects**: Group related tasks under the same project name

## Examples

### Example 1: Register a Simple Task

```python
result = register_task(
    title="Add root folder to Sonarr",
    description="Add /media/tv as root folder in Sonarr configuration",
    project="media-download",
    priority="medium",
    created_by="agent-001"
)
# Returns: {"task_id": "T1.1", ...}
```

### Example 2: Register Task with Dependencies

```python
result = register_task(
    title="Deploy frontend",
    description="Deploy React frontend to production",
    project="trading-journal",
    priority="high",
    dependencies="T1.1,T1.2",  # Depends on backend and database setup
    created_by="agent-001"
)
# Returns: {"task_id": "T1.3", ...}
```

### Example 3: Query Pending High-Priority Tasks

```python
result = query_tasks(
    status="pending",
    priority="high",
    limit=10
)
# Returns: {"count": 3, "tasks": [...]}
```

### Example 4: Find Tasks for Specific Agent

```python
result = query_tasks(
    assignee="agent-001",
    status="in_progress"
)
# Returns: {"count": 2, "tasks": [...]}
```

## Task Management (Phase 2)

### Get Task Details

```python
get_task(task_id="T1.1")
```

**Returns**: Full task details including all fields

### Claim a Task

```python
claim_task(
    task_id="T1.1",
    agent_id="agent-001"
)
```

**Validation**:
- Task must exist
- Task must be in `pending` or `claimed` status
- If already claimed, must be by the same agent

**Status Changes**:
- `pending` → `claimed` (when first claimed)

### Update Task Status

```python
update_task_status(
    task_id="T1.1",
    status="in_progress",
    agent_id="agent-001",
    notes="Started working on database setup"
)
```

**Valid Statuses**:
- `pending` - Available to claim
- `claimed` - Claimed by agent, not started
- `in_progress` - Actively being worked on
- `blocked` - Waiting on dependencies
- `review` - Needs review
- `completed` - Finished
- `cancelled` - Cancelled

**Status Transitions**:
- `pending` → `claimed` → `in_progress` → `review` → `completed`
- Any status → `blocked` (if dependencies not met)
- Any status → `cancelled`
- Cannot change from `completed` or `cancelled` to other statuses

**Permissions**:
- Only the assigned agent can update task status
- If unassigned, any agent can update

## Example Workflow

```python
# 1. Register a task
result = register_task(
    title="Setup database",
    description="Create PostgreSQL schema",
    project="trading-journal",
    priority="high",
    created_by="agent-001"
)
task_id = result["task_id"]  # e.g., "T1.1"

# 2. Claim the task
claim_task(task_id=task_id, agent_id="agent-001")

# 3. Update status as work progresses
update_task_status(task_id=task_id, status="in_progress", agent_id="agent-001")
update_task_status(task_id=task_id, status="review", agent_id="agent-001", notes="Ready for review")
update_task_status(task_id=task_id, status="completed", agent_id="agent-001")

# 4. Query tasks
my_tasks = query_tasks(assignee="agent-001", status="in_progress")
```

## Dependency Management (Phase 3)

### Check Task Dependencies

```python
check_task_dependencies(task_id="T1.3")
```

**Returns**:
- List of all dependencies with their status
- Whether all dependencies are completed
- Whether task can proceed
- Details about blocking dependencies

**Example Response**:
```json
{
  "status": "success",
  "task_id": "T1.3",
  "has_dependencies": true,
  "dependencies": [
    {
      "task_id": "T1.1",
      "title": "Setup project structure",
      "status": "completed",
      "is_completed": true,
      "can_proceed": true
    },
    {
      "task_id": "T1.2",
      "title": "Configure Docker",
      "status": "in_progress",
      "is_completed": false,
      "can_proceed": false
    }
  ],
  "all_completed": false,
  "can_proceed": false,
  "message": "1 dependencies not ready"
}
```

### Dependency Validation

**Automatic Validation**:
- `claim_task()` now validates dependencies before allowing claim
- Tasks with unmet dependencies cannot be claimed
- Returns error with details about blocking dependencies

**Automatic Status Updates**:
- When a task is marked `completed`, dependent tasks are automatically checked
- If all dependencies are now completed and task was `blocked`, status changes to `pending`
- Tasks with unmet dependencies are automatically set to `blocked` when status changes

**Blocking Logic**:
- Tasks with unmet dependencies are automatically blocked
- Blocked tasks cannot be claimed until dependencies are completed
- Status automatically changes from `blocked` to `pending` when dependencies complete

### Example: Dependency Workflow

```python
# 1. Register tasks with dependencies
t1 = register_task(title="Setup DB", project="app", created_by="agent-001")
t2 = register_task(title="Setup API", project="app", dependencies=t1["task_id"], created_by="agent-001")
t3 = register_task(title="Setup Frontend", project="app", dependencies=f"{t1['task_id']},{t2['task_id']}", created_by="agent-001")

# 2. Try to claim T3 (will fail - dependencies not met)
result = claim_task(task_id=t3["task_id"], agent_id="agent-001")
# Returns: error - dependencies not completed

# 3. Check dependencies
deps = check_task_dependencies(task_id=t3["task_id"])
# Shows: T1 and T2 are not completed

# 4. Complete T1
update_task_status(task_id=t1["task_id"], status="completed", agent_id="agent-001")

# 5. Complete T2
update_task_status(task_id=t2["task_id"], status="completed", agent_id="agent-001")
# T3 automatically changes from blocked to pending

# 6. Now T3 can be claimed
claim_task(task_id=t3["task_id"], agent_id="agent-001")
# Success!
```

---

**Status**: Phase 3 Complete
**Last Updated**: 2025-01-10

