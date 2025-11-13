# Activity Logger

Python module for logging agent actions to the monitoring database.

## Purpose

This module provides functions that MCP tools can call to automatically log:
- MCP tool calls (with parameters and results)
- Memory operations (queries, records)
- Task updates (status changes, claims)
- Agent status updates

## Usage

### In MCP Tools

```python
from activity_logger import log_action, log_agent_status

@server.tool()
async def docker_list_containers(...):
    agent_id = get_current_agent_id()  # Get from context
    start_time = time.time()
    
    try:
        result = await actual_docker_list_containers(...)
        duration_ms = (time.time() - start_time) * 1000
        
        # Log successful action
        log_action(
            agent_id=agent_id,
            action_type="mcp_tool",
            tool_name="docker_list_containers",
            parameters={"filters": ...},
            result_status="success",
            duration_ms=duration_ms
        )
        
        return result
    except Exception as e:
        # Log failed action
        log_action(
            agent_id=agent_id,
            action_type="mcp_tool",
            tool_name="docker_list_containers",
            parameters={"filters": ...},
            result_status="error",
            error=str(e)
        )
        raise
```

### Update Agent Status

```python
from activity_logger import update_agent_status

update_agent_status(
    agent_id="agent-001",
    status="active",
    current_task_id="T1.3",
    progress="Setting up database schema",
    blockers=None
)
```

## Installation

The activity logger needs to be accessible from the MCP server. Options:

1. **Install as package** (recommended):
   ```bash
   cd apps/agent-monitoring/activity_logger
   pip install -e .
   ```

2. **Add to Python path**:
   ```python
   import sys
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "agent-monitoring" / "activity_logger"))
   ```

3. **Copy to MCP server** (simple):
   ```bash
   cp activity_logger.py server-management-mcp/tools/
   ```

## Database Location

The logger writes to:
- **SQLite**: `apps/agent-monitoring/data/agent_activity.db`
- **InfluxDB**: Via backend export service (optional)

## Functions

### `log_action(agent_id, action_type, tool_name=None, parameters=None, result_status="success", duration_ms=None, error=None)`

Log an agent action to the database.

**Parameters:**
- `agent_id` (str): ID of the agent performing the action
- `action_type` (str): Type of action (`mcp_tool`, `memory_query`, `memory_record`, `task_update`)
- `tool_name` (str, optional): Name of the tool/function called
- `parameters` (dict, optional): Parameters passed to the tool
- `result_status` (str): `"success"` or `"error"`
- `duration_ms` (int, optional): Duration in milliseconds
- `error` (str, optional): Error message if failed

### `update_agent_status(agent_id, status, current_task_id=None, progress=None, blockers=None)`

Update an agent's current status.

**Parameters:**
- `agent_id` (str): ID of the agent
- `status` (str): Current status (`active`, `idle`, `blocked`, `completed`)
- `current_task_id` (str, optional): Current task ID
- `progress` (str, optional): Progress description
- `blockers` (str, optional): Blockers/issues

### `get_agent_status(agent_id)`

Get current status of an agent.

**Returns:** Dict with agent status information

---

**Status**: Phase 1 Implementation

