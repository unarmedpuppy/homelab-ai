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

## Future Enhancements

Phase 2 will add:
- `claim_task()` - Claim/assign tasks
- `update_task_status()` - Update task status
- `get_task()` - Get single task details

Phase 3 will add:
- `check_task_dependencies()` - Check dependency status
- Dependency validation before claiming
- Automatic status updates when dependencies complete

---

**Status**: Phase 1 Complete
**Last Updated**: 2025-01-10

