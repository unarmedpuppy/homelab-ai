# Agent Monitoring Architecture Audit & Normalization Plan

## Current Architecture Analysis

### Component Locations

| Component | Current Location | Status | Database Access |
|-----------|-----------------|--------|----------------|
| **Agent Monitoring Backend** | Server (Docker) | ✅ Running | `/data/agent_activity.db` (mounted volume) |
| **Agent Monitoring Frontend** | Server (Docker) | ✅ Running | Reads from backend API |
| **Agent Monitoring Database** | Server (Docker volume) | ✅ Running | `apps/agent-monitoring/data/agent_activity.db` |
| **MCP Server** | **UNKNOWN** | ❓ | **PROBLEM: Needs access to same DB** |
| **Activity Logger** | Local (via MCP) | ✅ Code exists | **PROBLEM: Writes to local file system** |
| **Cursor Agent (You)** | Local machine | ✅ Running | Connects to MCP server |

### Critical Issues Identified

#### Issue 1: Database Location Mismatch
- **Backend** reads from: `apps/agent-monitoring/data/agent_activity.db` (server)
- **Activity Logger** writes to: `apps/agent-monitoring/data/agent_activity.db` (local)
- **Result**: Two separate databases, data doesn't sync

#### Issue 2: MCP Server Location Unknown
- MCP server has `docker-compose.yml` but unclear if it's running
- If running locally: Can't access server database
- If running in Docker: Needs shared volume or network access

#### Issue 3: Multiple Agent Instances
- If multiple agents run (local + server), they write to different databases
- No single source of truth for agent activity

## Solution Options

### Option A: All-in-Docker (Recommended) ⭐

**Architecture:**
```
┌─────────────────────────────────────────────────┐
│ Server (192.168.86.47)                          │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │ Agent Monitoring Stack (Docker)           │  │
│  │  - Backend (port 3001)                    │  │
│  │  - Frontend (port 3012)                   │  │
│  │  - Database: /data/agent_activity.db     │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │ MCP Server (Docker)                       │  │
│  │  - Mounts: /data/agent_activity.db        │  │
│  │  - Network: my-network                    │  │
│  │  - Exposes: MCP stdio (via Docker exec)  │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
         ▲
         │ MCP Protocol (SSH/Network)
         │
┌────────┴──────────────────────────────────────┐
│ Local Machine                                  │
│  - Cursor Agent (You)                          │
│  - Connects to MCP server via network          │
└────────────────────────────────────────────────┘
```

**Pros:**
- ✅ Single database instance (shared volume)
- ✅ All components on same network
- ✅ Consistent environment
- ✅ Easy to scale

**Cons:**
- ⚠️ Requires MCP server to support network transport (not just stdio)
- ⚠️ Network latency for tool calls

**Implementation:**
1. Run MCP server in Docker on server
2. Mount same database volume: `./data:/data`
3. Configure MCP to use HTTP/SSE transport (not just stdio)
4. Update Cursor config to connect via network

---

### Option B: Network-Based Logging (Hybrid)

**Architecture:**
```
┌─────────────────────────────────────────────────┐
│ Server (192.168.86.47)                          │
│  - Backend API (port 3001)                     │
│  - Database: /data/agent_activity.db            │
└─────────────────────────────────────────────────┘
         ▲
         │ HTTP POST /api/actions
         │
┌────────┴──────────────────────────────────────┐
│ Local Machine                                  │
│  - MCP Server (local)                          │
│  - Activity Logger → Backend API               │
│  - Cursor Agent                                │
└────────────────────────────────────────────────┘
```

**Pros:**
- ✅ MCP server can run locally (faster)
- ✅ Single database (backend handles writes)
- ✅ Works with existing stdio transport

**Cons:**
- ⚠️ Requires network connectivity
- ⚠️ Activity logger needs backend API URL
- ⚠️ Network dependency for logging

**Implementation:**
1. Modify activity logger to POST to backend API instead of writing SQLite
2. Add `AGENT_MONITORING_API_URL` environment variable
3. Keep MCP server running locally
4. All agents write to same backend

---

### Option C: Shared Volume (NFS/SMB)

**Architecture:**
```
┌─────────────────────────────────────────────────┐
│ Server (192.168.86.47)                          │
│  - Database: /data/agent_activity.db            │
│  - Exported via NFS/SMB                         │
└─────────────────────────────────────────────────┘
         ▲
         │ Mounted Volume
         │
┌────────┴──────────────────────────────────────┐
│ Local Machine                                  │
│  - MCP Server (local)                          │
│  - Activity Logger → Mounted DB                 │
│  - Cursor Agent                                │
└────────────────────────────────────────────────┘
```

**Pros:**
- ✅ Direct database access
- ✅ MCP server can run locally

**Cons:**
- ⚠️ Requires NFS/SMB setup
- ⚠️ Network file system latency
- ⚠️ Potential file locking issues with SQLite

---

## Recommended Solution: Option B (Network-Based Logging)

### Why Option B?

1. **Minimal Changes**: Activity logger already exists, just change write method
2. **Works with Current Setup**: MCP server can stay local (faster tool execution)
3. **Single Source of Truth**: Backend API handles all writes
4. **Scalable**: Multiple agents can log simultaneously
5. **No File System Dependencies**: No need for shared volumes

### Implementation Plan

#### Phase 1: Modify Activity Logger
- [ ] Add HTTP client to activity logger
- [ ] Add `AGENT_MONITORING_API_URL` environment variable
- [ ] Change `log_action()` to POST to `/api/actions` instead of SQLite write
- [ ] Keep SQLite as fallback if API unavailable
- [ ] Update `start_agent_session()`, `update_agent_status()` to use API

#### Phase 2: Update Backend API
- [ ] Add endpoint: `POST /api/actions` (if not exists)
- [ ] Add endpoint: `POST /api/agents/status` (if not exists)
- [ ] Add endpoint: `POST /api/sessions` (if not exists)
- [ ] Ensure CORS allows local machine IP
- [ ] Add authentication (optional but recommended)

#### Phase 3: Update MCP Server Configuration
- [ ] Add `AGENT_MONITORING_API_URL` to MCP server environment
- [ ] Update activity logger imports to use API client
- [ ] Test connectivity from local machine to server

#### Phase 4: Update Documentation
- [ ] Document new architecture
- [ ] Update agent prompts with API URL requirement
- [ ] Add troubleshooting guide

### Alternative: Option A (All-in-Docker)

If network-based logging doesn't work well, fall back to Option A:

1. Run MCP server in Docker on server
2. Use HTTP/SSE transport for MCP (not just stdio)
3. Configure Cursor to connect via network
4. Mount database volume to MCP container

---

## Current State Audit Checklist

- [ ] Check if MCP server is currently running (where?)
- [ ] Check if MCP server docker-compose is deployed
- [ ] Verify agent-monitoring backend is accessible from local machine
- [ ] Test network connectivity: `curl http://192.168.86.47:3001/health`
- [ ] Check if database file exists on server: `apps/agent-monitoring/data/agent_activity.db`
- [ ] Check if database file exists locally: `apps/agent-monitoring/data/agent_activity.db`
- [ ] Verify Cursor MCP configuration (local vs network)

---

## Next Steps

1. **Immediate**: Audit current running state
2. **Short-term**: Implement Option B (network-based logging)
3. **Long-term**: Consider Option A if performance issues arise

