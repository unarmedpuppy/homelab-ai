# MCP Observability Flow

**How automatic logging decorators work when MCP tools are called via Cursor.**

## Short Answer

**✅ YES, the decorators will work!** The observability features are independent of how the tool is called (via MCP or directly).

## How It Works

### The Decorator Chain

```
Agent (in Cursor)
    ↓ calls tool via MCP
    ↓
Cursor's MCP Client
    ↓ sends MCP protocol message via stdio
    ↓
MCP Server (server.py subprocess)
    ↓ receives tool call request
    ↓ executes decorated function
    ↓
@with_automatic_logging() decorator
    ↓ wraps function execution
    ↓ calls log_action()
    ↓
Activity Logger
    ↓ tries HTTP API first (localhost:3001)
    ↓ falls back to SQLite if API unavailable
    ↓
Monitoring Backend (localhost:3001)
    ↓ receives action log
    ↓ stores in SQLite database
    ↓
Dashboard (localhost:3012)
    ↓ displays logged actions
```

### Key Points

1. **Decorator is on the function itself** - Not dependent on how it's called
2. **Runs during function execution** - Executes when MCP server runs the function
3. **HTTP requests from MCP server process** - MCP server makes HTTP calls to localhost:3001
4. **Works regardless of transport** - stdio, HTTP, or direct call - decorator always runs

## Code Flow

### 1. Tool Definition (with decorator)

```python
# agents/apps/agent-mcp/tools/infrastructure.py
@server.tool()
@with_automatic_logging()  # ← Decorator applied here
async def start_agent_infrastructure(check_only: bool = False):
    # Tool implementation
    ...
```

### 2. Decorator Execution

```python
# agents/apps/agent-mcp/tools/logging_decorator.py
@wraps(func)
async def wrapper(*args, **kwargs):
    start_time = time.time()
    result_status = "success"
    error_message = None
    
    # Extract agent_id
    agent_id = get_agent_id_from_kwargs(kwargs)
    
    try:
        # Call actual tool function
        result = await func(*args, **kwargs)
        return result
    except Exception as e:
        result_status = "error"
        error_message = str(e)
        raise
    finally:
        # Always log, even on error
        duration_ms = (time.time() - start_time) * 1000
        _log_action(  # ← Calls activity logger
            agent_id=agent_id,
            action_type="mcp_tool",
            tool_name=actual_tool_name,
            parameters=log_params,
            result_status=result_status,
            duration_ms=duration_ms,
            error=error_message
        )
```

### 3. Activity Logger

```python
# agents/apps/agent-monitoring/activity_logger/activity_logger.py
def log_action(...):
    # Try API first (HTTP request to localhost:3001)
    if API_LOGGING_AVAILABLE and is_api_available():
        success = log_action_via_api(...)
        if success:
            return  # Success, done!
    
    # Fallback to local SQLite
    _log_action_to_sqlite(...)
```

### 4. HTTP Client

```python
# agents/apps/agent-monitoring/activity_logger/http_client.py
def log_action_via_api(...):
    url = f"{API_URL}/api/actions"  # Default: http://localhost:3001
    response = requests.post(url, json=data, timeout=5)
    return response.status_code in [200, 201]
```

## Why It Works

### 1. Decorator is Function-Level

The decorator wraps the function itself, not the MCP protocol layer:

```python
# This decorator runs whenever the function is called
@with_automatic_logging()
async def my_tool(...):
    # Function code
```

**Whether called via:**
- MCP protocol (Cursor → MCP server → function)
- Direct Python call (function())
- HTTP API (if we add HTTP transport)

**The decorator always runs** because it's part of the function definition.

### 2. MCP Server Process Can Make HTTP Requests

The MCP server runs as a subprocess spawned by Cursor. This process:
- Has network access
- Can make HTTP requests
- Can connect to localhost:3001 (monitoring backend)
- Runs in the same environment as the agent

**No issues with network access** - the MCP server process can reach localhost:3001.

### 3. Local-First Architecture

With local-first architecture:
- Monitoring backend runs on `localhost:3001`
- MCP server runs locally (spawned by Cursor)
- Both can communicate via localhost
- No network configuration needed

**Perfect for local-first** - everything runs on the same machine.

## Potential Issues & Solutions

### Issue 1: Monitoring Backend Not Running

**Problem**: MCP server tries to log, but backend isn't running.

**Solution**: Activity logger falls back to SQLite automatically:

```python
# Tries API first
if is_api_available():
    log_action_via_api(...)
else:
    # Falls back to SQLite
    _log_action_to_sqlite(...)
```

**Result**: Actions are still logged, just to local SQLite instead of centralized backend.

### Issue 2: Context Variables (agent_id)

**Problem**: How does decorator know which agent called the tool?

**Solution**: Multiple strategies for agent_id detection:

```python
def get_agent_id_from_kwargs(kwargs):
    # Priority 1: Context variable (set by start_agent_session)
    if context_agent_id:
        return context_agent_id
    
    # Priority 2: agent_id parameter
    if "agent_id" in kwargs:
        return kwargs["agent_id"]
    
    # Priority 3: from_agent parameter
    if "from_agent" in kwargs:
        return kwargs["from_agent"]
    
    # Priority 4: Default
    return "agent-001"
```

**Result**: Agent ID is automatically detected from context or parameters.

### Issue 3: MCP Server Process Isolation

**Problem**: Does the MCP server process have access to the same filesystem?

**Solution**: 
- MCP server runs in same environment as Cursor
- Can access project files (same filesystem)
- Can make HTTP requests to localhost
- Can access SQLite database (if fallback needed)

**Result**: No isolation issues - MCP server has full access.

## Verification

### How to Verify It's Working

1. **Start monitoring backend**:
   ```bash
   ./agents/scripts/start-agent-infrastructure.sh
   ```

2. **Call an MCP tool from agent**:
   ```python
   await start_agent_infrastructure()
   ```

3. **Check dashboard**:
   - Open http://localhost:3012
   - Should see the tool call logged
   - Should see action in "Recent Actions" table

4. **Check backend logs**:
   ```bash
   cd agents/apps/agent-monitoring
   docker-compose logs backend | grep "POST /api/actions"
   ```

5. **Check database**:
   ```bash
   sqlite3 agents/apps/agent-monitoring/data/agent_activity.db \
     "SELECT * FROM agent_actions ORDER BY timestamp DESC LIMIT 5;"
   ```

### Expected Behavior

✅ **When backend is running**:
- Decorator logs via HTTP API
- Actions appear in dashboard immediately
- Stored in centralized SQLite database

✅ **When backend is not running**:
- Decorator falls back to local SQLite
- Actions still logged (just not in dashboard)
- Can sync later when backend starts

## Summary

**The decorators work perfectly with MCP because:**

1. ✅ **Decorator is function-level** - Runs regardless of how function is called
2. ✅ **MCP server can make HTTP requests** - Has network access to localhost:3001
3. ✅ **Local-first architecture** - Everything runs on same machine
4. ✅ **Automatic fallback** - Falls back to SQLite if API unavailable
5. ✅ **Context-aware** - Automatically detects agent_id from context or parameters

**No special configuration needed** - the decorators work automatically when:
- MCP server is configured in Cursor
- Monitoring backend is running (or falls back to SQLite)
- Tools are called via MCP protocol

---

**See Also**:
- `agents/apps/agent-mcp/tools/logging_decorator.py` - Decorator implementation
- `agents/apps/agent-monitoring/activity_logger/activity_logger.py` - Activity logger
- `agents/apps/agent-monitoring/INTEGRATION_GUIDE.md` - Integration guide

