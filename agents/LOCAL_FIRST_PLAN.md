# Local-First Architecture Plan

## Your Approach is Correct ✅

**Running everything locally makes perfect sense** because:
- Agent workflow is tied to the agent system (local)
- Memory is agent knowledge (should be local)
- Monitoring tracks agent activity (should be local)
- Simpler mental model (one database, one source of truth)

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│ Local Machine (Your Mac)                     │
│                                               │
│  ┌──────────────────────────────────────┐  │
│  │ Cursor Agent Session                  │  │
│  │  - Agent workflow                     │  │
│  │  - Agent memory                       │  │
│  └──────────────────────────────────────┘  │
│           │                                   │
│           ▼                                   │
│  ┌──────────────────────────────────────┐  │
│  │ MCP Server (local Python process)     │  │
│  │  - All 68 tools                       │  │
│  │  - Activity logger                    │  │
│  │  - Uses SSH for server operations     │  │
│  └──────────────────────────────────────┘  │
│           │                                   │
│           ├─► Memory System                   │
│           │   - agents/memory/memory.db       │
│           │   - Local SQLite                 │
│           │                                   │
│           └─► Agent Monitoring (local)       │
│               - Backend: localhost:3001      │
│               - Frontend: localhost:3012       │
│               - Database: local SQLite        │
└─────────────────────────────────────────────┘
           │
           │ SSH/Network (only for server operations)
           ▼
┌─────────────────────────────────────────────┐
│ Server (192.168.86.47)                      │
│  - Docker containers                         │
│  - Media download services                   │
│  - Other services                            │
│  (No agent infrastructure here)              │
└─────────────────────────────────────────────┘
```

## What Runs Where

### Local (Agent Infrastructure)
- ✅ **MCP Server** - Tool execution
- ✅ **Agent Monitoring** - Backend, frontend, database
- ✅ **Memory System** - Agent knowledge database
- ✅ **Activity Logger** - Logs to local monitoring DB
- ✅ **Agent Sessions** - Cursor/Claude Desktop

### Server (Services Only)
- ✅ **Docker Containers** - Services (Sonarr, Radarr, etc.)
- ✅ **Server File System** - Application data
- ✅ **Server Network** - Container networking

**Key Point**: Server operations (Docker, media download) still work via SSH/network, but agent infrastructure is local.

## Benefits

### 1. **Workflow & Memory Tied to Agent** ✅
- Memory lives with agent (makes sense - it's agent knowledge)
- Workflow tied to local system (consistent environment)
- No network dependency for core operations
- Faster (no network latency)

### 2. **Simpler Mental Model** ✅
- One database, one source of truth
- No sync issues between local/server
- Easier to debug (everything in one place)
- Clear separation: agent stuff = local, server stuff = server

### 3. **Better for Development** ✅
- Can work offline (except server operations)
- Faster iteration (no network calls)
- Easier to test locally
- Version control friendly

### 4. **Privacy & Control** ✅
- All agent data stays local
- No server dependency for core features
- Can work without server connection (for non-server tasks)

## What You're NOT Missing

### ✅ Server Operations Still Work
- MCP tools use SSH for server operations (already implemented)
- Docker commands execute on server via SSH
- Media download tools work via network
- **This is correct** - server operations need network, but agent infrastructure doesn't

### ✅ Multi-Agent Coordination
- All agents can use same local database
- Shared memory system (same SQLite file)
- Shared monitoring database (same SQLite file)
- Task coordination works via local database

### ✅ Monitoring Dashboard
- Runs locally on `localhost:3012`
- Accessible from your machine
- Shows all agent activity
- **Trade-off**: Only accessible locally (not from other devices)
- **Solution**: If needed, can expose via port forwarding/VPN later

### ✅ Backup & Persistence
- Local files can be git-committed
- Memory database can be exported/versioned
- Monitoring database can be backed up
- **Recommendation**: Regular git commits of agent data

## Potential Considerations

### 1. **Port Conflicts** (Minor)
**Issue**: Local ports might conflict with other services

**Solution**: 
- Use different ports if needed (e.g., `3002` instead of `3001`)
- Or run monitoring in Docker locally (isolated ports)

### 2. **Resource Usage** (Minor)
**Issue**: Running monitoring locally uses local resources

**Solution**:
- Monitoring is lightweight (SQLite, Node.js backend, Next.js frontend)
- Can run in Docker locally if preferred
- Or run directly (no Docker overhead)

### 3. **Multiple Machines** (Future)
**Issue**: If you work from multiple machines, each has separate data

**Solution**:
- **Option A**: One primary machine (simplest)
- **Option B**: Sync via git (commit agent data)
- **Option C**: Optional server mirror (sync local → server for backup)

**Recommendation**: Option A for now, Option C if needed later.

## Implementation Steps

### Step 1: Run Monitoring Locally

**Option A: Docker Compose (Recommended)**
```bash
cd agents/apps/agent-monitoring
docker-compose up -d
```

**Option B: Direct Execution**
```bash
# Backend
cd agents/apps/agent-monitoring/backend
npm install
npm start  # Runs on localhost:3001

# Frontend (separate terminal)
cd agents/apps/agent-monitoring/frontend
npm install
npm run dev  # Runs on localhost:3012
```

### Step 2: Update Activity Logger

Already done! ✅ The activity logger already supports network-based logging:
- Uses `AGENT_MONITORING_API_URL` environment variable
- Defaults to `http://192.168.86.47:3001` (server)
- Change to `http://localhost:3001` (local)

### Step 3: Update MCP Server Config

**Cursor Config** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "home-server": {
      "command": "python",
      "args": ["/Users/joshuajenquist/repos/personal/home-server/agents/apps/agent-mcp/server.py"],
      "env": {
        "AGENT_MONITORING_API_URL": "http://localhost:3001",
        "SONARR_API_KEY": "...",
        "RADARR_API_KEY": "..."
      }
    }
  }
}
```

### Step 4: Verify Everything Works

1. **Start monitoring locally**: `cd agents/apps/agent-monitoring && docker-compose up -d`
2. **Check dashboard**: `http://localhost:3012`
3. **Call MCP tool**: Test any tool via Cursor
4. **Verify logging**: Check dashboard shows action
5. **Verify memory**: Memory queries work locally

## Migration Checklist

- [ ] Stop server monitoring (if running)
- [ ] Run monitoring locally (docker-compose or direct)
- [ ] Update `AGENT_MONITORING_API_URL` to `http://localhost:3001`
- [ ] Update Cursor config (if using MCP server)
- [ ] Test MCP tools (should work via SSH)
- [ ] Test monitoring (dashboard should show actions)
- [ ] Verify memory works locally
- [ ] Update documentation

## What Stays on Server

**These MUST stay on server** (they're server resources):
- ✅ Docker containers (services)
- ✅ Media download services (Sonarr, Radarr, etc.)
- ✅ Server file system
- ✅ Server network

**These MOVE to local**:
- ✅ MCP server execution
- ✅ Agent monitoring (backend, frontend, database)
- ✅ Activity logging
- ✅ Memory system

## Summary

**Your approach is correct!** ✅

**Benefits:**
- Workflow & memory tied to agent system
- Simpler mental model
- Faster (no network latency)
- Better for development
- Privacy & control

**What you're NOT missing:**
- Server operations still work (via SSH)
- Multi-agent coordination works (shared local DB)
- Monitoring works (local dashboard)
- Backup works (git/version control)

**The only trade-off:**
- Dashboard only accessible locally (not from other devices)
- But this is probably fine for your use case

**Recommendation**: Proceed with local-first architecture. It's the right approach for agent workflow and memory.

