# Agent Monitoring Integration Guide

How to integrate agent monitoring with your existing systems.

## MCP Tool Integration

The activity logger is designed to be called by MCP tools to log agent actions. Here's how to integrate it:

### Basic Integration

```python
from agents.apps.agent_monitoring.activity_logger import log_action, update_agent_status

# Log an MCP tool call
log_action(
    agent_id="agent-001",
    action_type="mcp_tool",
    tool_name="docker_list_containers",
    parameters={"filters": "running"},
    result_status="success",
    duration_ms=150
)

# Update agent status
update_agent_status(
    agent_id="agent-001",
    status="active",
    current_task_id="T1.1",
    progress="Working on deployment",
    blockers=None
)
```

### Automatic Logging (Recommended)

For automatic logging of all MCP tool calls, you can wrap your MCP tools:

```python
import time
from functools import wraps
from agents.apps.agent_monitoring.activity_logger import log_action

def log_mcp_tool(agent_id: str):
    """Decorator to automatically log MCP tool calls."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            tool_name = func.__name__
            result_status = "success"
            error_message = None
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                result_status = "error"
                error_message = str(e)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                log_action(
                    agent_id=agent_id,
                    action_type="mcp_tool",
                    tool_name=tool_name,
                    parameters=kwargs,
                    result_status=result_status,
                    duration_ms=duration_ms,
                    error_message=error_message
                )
        return wrapper
    return decorator

# Usage
@log_mcp_tool(agent_id="agent-001")
async def my_mcp_tool(param1: str):
    # Tool implementation
    pass
```

## Homepage Integration

The agent monitoring dashboard is automatically added to your homepage via Docker labels in `docker-compose.yml`:

```yaml
labels:
  - "homepage.group=Infrastructure"
  - "homepage.name=Agent Monitoring"
  - "homepage.icon=si-claude"
  - "homepage.href=http://192.168.86.47:3012"
```

After starting the services, the link should appear in your homepage automatically.

## Traefik Integration

The frontend service includes Traefik labels for reverse proxy:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.agent-monitoring.rule=Host(`agent-dashboard.server.unarmedpuppy.com`)"
  - "traefik.http.routers.agent-monitoring.entrypoints=websecure"
  - "traefik.http.routers.agent-monitoring.tls.certresolver=myresolver"
```

Access via: https://agent-dashboard.server.unarmedpuppy.com

## Task Coordination Integration

The backend automatically reads from the task coordination registry at `agents/tasks/registry.md`. No additional configuration needed.

## Memory System Integration

Memory operations are logged automatically when agents use memory MCP tools:
- `memory_query_decisions`
- `memory_record_decision`
- `memory_query_patterns`
- `memory_record_pattern`
- `memory_save_context`

These are logged with `action_type="memory_query"` or `action_type="memory_record"`.

## Best Practices

1. **Always log tool calls**: Use the activity logger for all MCP tool invocations
2. **Update status regularly**: Call `update_agent_status()` when task status changes
3. **Start/end sessions**: Use `start_agent_session()` and `end_agent_session()` for tracking
4. **Include context**: Log parameters and results for better debugging
5. **Handle errors**: Log error messages when tools fail

## Example: Complete Agent Workflow

```python
from agents.apps.agent_monitoring.activity_logger import (
    start_agent_session,
    end_agent_session,
    update_agent_status,
    log_action
)

# Start session
session_id = start_agent_session("agent-001")

try:
    # Update status
    update_agent_status(
        agent_id="agent-001",
        status="active",
        current_task_id="T1.1",
        progress="Starting deployment"
    )
    
    # Log tool calls
    log_action("agent-001", "mcp_tool", "docker_list_containers", {}, "success", 100)
    log_action("agent-001", "mcp_tool", "git_deploy", {"branch": "main"}, "success", 5000)
    
    # Update status on completion
    update_agent_status(
        agent_id="agent-001",
        status="idle",
        current_task_id=None,
        progress="Deployment complete"
    )
    
finally:
    # End session
    end_agent_session(
        agent_id="agent-001",
        session_id=session_id,
        tasks_completed=1,
        tools_called=2,
        total_duration_ms=5100
    )
```

---

For more details, see:
- [Activity Logger README](activity_logger/README.md)
- [Backend API Documentation](backend/README.md)
- [Frontend Documentation](frontend/README.md)

