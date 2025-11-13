# Agent Monitoring Normalization Plan

## Current State Summary

### ✅ What's Working
- **Backend API**: Running on server, accessible from local (`http://192.168.86.47:3001`)
- **Frontend Dashboard**: Running on server (`http://192.168.86.47:3012`)
- **Database on Server**: Exists and accessible to backend
- **Database Locally**: Exists but separate from server (53KB, last modified Nov 13)

### ❌ What's Broken
- **MCP Server**: Not running in Docker (container not found)
- **Activity Logger**: Writing to **local** database file
- **Backend**: Reading from **server** database file
- **Result**: Two separate databases, no data sync

## Root Cause

The activity logger uses a **file path** to write to SQLite:
```python
DB_PATH = PROJECT_ROOT / "apps" / "agent-monitoring" / "data" / "agent_activity.db"
```

When MCP server runs locally:
- Activity logger writes to: `/Users/joshuajenquist/repos/personal/home-server/agents/apps/agent-monitoring/data/agent_activity.db` (local)
- Backend reads from: `/data/agent_activity.db` in Docker container (server)

**These are two different files!**

## Solution: Network-Based Logging (Recommended)

### Why This Solution?

1. **Minimal Changes**: Activity logger already exists, just change write method
2. **Works with Current Setup**: MCP server can stay local (faster)
3. **Single Source of Truth**: Backend API handles all writes
4. **Scalable**: Multiple agents can log simultaneously
5. **No File System Dependencies**: No shared volumes needed

### Implementation Steps

#### Step 1: Add HTTP Client to Activity Logger

Create `agents/apps/agent-monitoring/activity_logger/http_client.py`:
```python
"""HTTP client for activity logger to send data to backend API."""
import requests
import os
from typing import Optional, Dict, Any
import json

API_URL = os.getenv('AGENT_MONITORING_API_URL', 'http://192.168.86.47:3001')

def log_action_via_api(
    agent_id: str,
    action_type: str,
    tool_name: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
    result_status: str = "success",
    duration_ms: Optional[int] = None,
    error: Optional[str] = None
) -> bool:
    """Log action via backend API."""
    try:
        response = requests.post(
            f"{API_URL}/api/actions",
            json={
                "agent_id": agent_id,
                "action_type": action_type,
                "tool_name": tool_name,
                "parameters": json.dumps(parameters) if parameters else None,
                "result_status": result_status,
                "duration_ms": duration_ms,
                "error": error
            },
            timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False
```

#### Step 2: Update Activity Logger to Use API

Modify `agents/apps/agent-monitoring/activity_logger/activity_logger.py`:
- Add `AGENT_MONITORING_API_URL` environment variable support
- Change `log_action()` to try API first, fallback to SQLite
- Update `update_agent_status()` to use API
- Update `start_agent_session()` to use API

#### Step 3: Verify Backend API Endpoints

Check if these endpoints exist:
- `POST /api/actions` - Log action
- `POST /api/agents/status` - Update agent status
- `POST /api/sessions` - Start/end session

If missing, add them to backend.

#### Step 4: Update MCP Server Environment

Add to MCP server environment (or Cursor config):
```json
{
  "env": {
    "AGENT_MONITORING_API_URL": "http://192.168.86.47:3001"
  }
}
```

#### Step 5: Test

1. Set environment variable: `export AGENT_MONITORING_API_URL=http://192.168.86.47:3001`
2. Call a tool via MCP
3. Check dashboard: `http://192.168.86.47:3012`
4. Verify action appears

## Alternative: All-in-Docker

If network-based logging has issues, run MCP server in Docker:

1. Deploy MCP server docker-compose on server
2. Mount database volume: `./data:/data`
3. Configure MCP to use HTTP/SSE transport
4. Update Cursor to connect via network

**Pros**: Single database, no network calls
**Cons**: Network latency, requires MCP transport changes

## Migration Checklist

- [ ] Create HTTP client module
- [ ] Update activity logger to use API (with SQLite fallback)
- [ ] Verify backend API endpoints exist
- [ ] Add CORS if needed (for local machine)
- [ ] Set environment variable in MCP server
- [ ] Test logging from local MCP server
- [ ] Verify data appears in dashboard
- [ ] Update documentation

## Testing Plan

1. **Unit Test**: Test HTTP client with mock server
2. **Integration Test**: Call tool via MCP, verify API receives data
3. **End-to-End Test**: Check dashboard shows action
4. **Fallback Test**: Disable API, verify SQLite fallback works

## Rollback Plan

If network-based logging fails:
1. Revert activity logger to SQLite-only
2. Use shared volume (NFS/SMB) to mount server database
3. Or deploy MCP server in Docker with shared volume

