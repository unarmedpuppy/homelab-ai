# Automatic Logging Integration Guide

This guide explains how to integrate automatic logging into MCP tools.

## Overview

The `logging_decorator.py` module provides automatic logging for all MCP tool calls. When applied, it automatically:
- Logs tool calls to the activity database
- Tracks duration, parameters, and results
- Handles errors gracefully
- Extracts agent_id from tool parameters

## Usage

### Basic Integration

Add the decorator to any MCP tool:

```python
from tools.logging_decorator import with_automatic_logging

@server.tool()
@with_automatic_logging()
async def my_tool(param1: str, param2: int) -> Dict[str, Any]:
    # Tool implementation
    ...
```

### Agent ID Detection

The decorator automatically extracts `agent_id` from tool parameters by checking:
1. `agent_id` parameter
2. `from_agent` parameter (used in communication tools)
3. `parent_agent_id` parameter (used in agent management)
4. Falls back to `"agent-001"` if none found

### Parameter Logging

- All parameters are logged (with sensitive data redacted)
- Parameters longer than 200 chars are truncated
- Non-serializable parameters are marked as `<non-serializable>`

## Applying to All Tools

To apply automatic logging to all tools in a file:

1. **Import the decorator** at the top:
   ```python
   from tools.logging_decorator import with_automatic_logging
   ```

2. **Add decorator** before each `@server.tool()`:
   ```python
   @server.tool()
   @with_automatic_logging()
   async def tool_name(...):
       ...
   ```

3. **Note**: The decorator must be placed **after** `@server.tool()` but **before** the function definition.

## Tool Files to Update

Apply the decorator to these tool files:

- ✅ `docker.py` - Done
- ⏳ `git.py` - Pending
- ⏳ `monitoring.py` - Pending
- ⏳ `memory.py` - Pending
- ⏳ `media_download.py` - Pending
- ⏳ `networking.py` - Pending
- ⏳ `system.py` - Pending
- ⏳ `troubleshooting.py` - Pending
- ⏳ `agent_management.py` - Pending
- ⏳ `skill_management.py` - Pending
- ⏳ `task_coordination.py` - Pending
- ⏳ `communication.py` - Pending
- ⏳ `skill_activation.py` - Pending
- ⏳ `dev_docs.py` - Pending
- ⏳ `quality_checks.py` - Pending
- ⏳ `code_review.py` - Pending
- ⏳ `service_debugging.py` - Pending
- ⏳ `agent_documentation.py` - Pending

## Testing

After applying the decorator:

1. Call a tool via MCP
2. Check the dashboard at http://192.168.86.47:3012
3. Verify the action appears in the activity feed
4. Check that parameters, duration, and result status are logged correctly

## Notes

- The decorator handles errors gracefully - if logging fails, the tool still works
- Activity monitoring tools (`start_agent_session`, `update_agent_status`) don't need the decorator (they log themselves)
- Tools that already have manual logging can keep it or remove it in favor of the decorator

