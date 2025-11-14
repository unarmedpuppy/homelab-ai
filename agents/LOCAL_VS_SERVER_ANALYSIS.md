# Local vs Server Architecture Analysis

## Your Proposal: Everything Local

**Goal**: Run all agent infrastructure locally so workflow & memory is tied to the system running the agents.

## Current State

### What Runs Where

| Component | Current Location | Purpose |
|-----------|----------------|---------|
| **Cursor Agent (You)** | Local | Agent session |
| **MCP Server** | Server (Docker) or Local | Tool execution |
| **Agent Monitoring Backend** | Server (Docker) | Activity tracking API |
| **Agent Monitoring Frontend** | Server (Docker) | Dashboard UI |
| **Agent Monitoring Database** | Server (Docker volume) | Activity data |
| **Memory System** | Local (SQLite) | Agent knowledge |
| **Activity Logger** | Local (via MCP) | Logs tool calls |

### Current Issues

1. **Database Split**: Activity logger writes locally, backend reads from server
2. **Network Dependency**: MCP server needs network access to server for Docker/media tools
3. **Monitoring Visibility**: Dashboard on server, but agents run locally

## Local-First Architecture (Your Proposal)

### Proposed Setup

```
┌─────────────────────────────────────────┐
│ Local Machine (Your Mac)                │
│                                          │
│  ┌──────────────────────────────────┐  │
│  │ Cursor Agent Session              │  │
│  └──────────────────────────────────┘  │
│           │                              │
│           ▼                              │
│  ┌──────────────────────────────────┐  │
│  │ MCP Server (local)                 │  │
│  │  - All tools                        │  │
│  │  - Activity logger                  │  │
│  └──────────────────────────────────┘  │
│           │                              │
│           ├─► Memory System (local)     │
│           │   - agents/memory/memory.db  │
│           │                              │
│           └─► Agent Monitoring (local)  │
│               - Backend (localhost:3001) │
│               - Frontend (localhost:3012)│
│               - Database (local SQLite)  │
└─────────────────────────────────────────┘
           │
           │ SSH/Network (for server operations)
           ▼
┌─────────────────────────────────────────┐
│ Server (192.168.86.47)                   │
│  - Docker containers                     │
│  - Media download services               │
│  - Other services                        │
└─────────────────────────────────────────┘
```

## Benefits of Local-First ✅

### 1. **Workflow & Memory Tied to Agent**
- ✅ Memory lives with agent (makes sense - it's agent knowledge)
- ✅ Workflow tied to local system (consistent environment)
- ✅ No network dependency for core operations
- ✅ Faster (no network latency for logging/memory)

### 2. **Simpler Mental Model**
- ✅ Everything agent-related is local
- ✅ One database, one source of truth
- ✅ No sync issues between local/server
- ✅ Easier to debug (everything in one place)

### 3. **Better for Development**
- ✅ Can work offline (except server operations)
- ✅ Faster iteration (no network calls)
- ✅ Easier to test locally
- ✅ Version control friendly (local files)

### 4. **Privacy & Control**
- ✅ All agent data stays local
- ✅ No server dependency for core features
- ✅ Can work without server connection (for non-server tasks)

## What You Might Be Missing ⚠️

### 1. **Server Operations Still Need Network**

**Issue**: MCP tools that manage server still need network access:
- Docker operations (list containers, restart, logs)
- Media download tools (Sonarr, Radarr)
- System monitoring (disk space, resources)

**Solution**: This is fine! MCP tools use SSH/network for server operations, but:
- Tool execution happens locally
- Logging happens locally
- Memory happens locally
- Only the actual server operations need network

**Not a problem**: This is expected and necessary.

### 2. **Multi-Agent Coordination**

**Issue**: If you run multiple agents:
- Each agent has its own local database
- No shared state between agents
- Task coordination might be split

**Solution Options**:
- **Option A**: Single agent at a time (simplest)
- **Option B**: Shared local database (all agents use same DB)
- **Option C**: Network-based coordination (agents POST to shared API)

**Recommendation**: Option B (shared local database) - all agents read/write to same local files.

### 3. **Monitoring Dashboard Access**

**Issue**: Dashboard runs locally, so:
- Only accessible from your machine
- Can't view from other devices
- No remote monitoring

**Solution Options**:
- **Option A**: Keep dashboard local (only you can see it)
- **Option B**: Expose dashboard via network (port forwarding, VPN, etc.)
- **Option C**: Optional server mirror (sync local → server for remote viewing)

**Recommendation**: Option A for now (local-only), Option C if you need remote access later.

### 4. **Backup & Persistence**

**Issue**: Local files can be lost:
- Machine crashes
- Disk failures
- Laptop replacement

**Solution**: 
- ✅ Git commit agent data (memory, monitoring DB)
- ✅ Regular backups of local database
- ✅ Version control for agent definitions

**Recommendation**: Add local database to git (or git-ignored with regular exports).

### 5. **Server-Specific Context**

**Issue**: Some tools need server context:
- Docker socket access (for docker commands)
- Server file system access (for docker-compose)
- Network access to containers

**Solution**: MCP tools use SSH/network for these operations. This is fine - the tool execution is local, but the operations happen on server.

**Not a problem**: This is the correct architecture.

## Recommended Local-First Architecture

### Components

1. **MCP Server** (Local)
   - Runs locally via Cursor config
   - All tools execute locally
   - Uses SSH/network for server operations only

2. **Agent Monitoring** (Local)
   - Backend: `localhost:3001`
   - Frontend: `localhost:3012`
   - Database: `agents/apps/agent-monitoring/data/agent_activity.db` (local)

3. **Memory System** (Local)
   - Database: `agents/memory/memory.db` (local)
   - All queries/updates local

4. **Activity Logger** (Local)
   - Writes to local monitoring database
   - No network calls needed

### Configuration

**Cursor MCP Config** (local):
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

**Agent Monitoring** (local):
- Run `docker-compose up` locally
- Or run backend/frontend directly (not in Docker)
- Database: local SQLite file

## Migration Plan

### Phase 1: Move Monitoring to Local

1. **Stop server monitoring** (if running)
2. **Run monitoring locally**:
   ```bash
   cd agents/apps/agent-monitoring
   docker-compose up -d
   # Or run backend/frontend directly
   ```
3. **Update activity logger** to use `http://localhost:3001`
4. **Test**: Call MCP tool, verify dashboard shows action

### Phase 2: Update MCP Server Config

1. **Update Cursor config** to run MCP server locally
2. **Set environment variables**:
   - `AGENT_MONITORING_API_URL=http://localhost:3001`
3. **Test**: Verify tools work and log correctly

### Phase 3: Verify Everything Works

1. **Test MCP tools** (should work via SSH for server ops)
2. **Test monitoring** (dashboard should show actions)
3. **Test memory** (should work locally)
4. **Verify no network dependency** (except for server operations)

## What Stays on Server

**These MUST stay on server** (they're server resources):
- Docker containers (services)
- Media download services (Sonarr, Radarr, etc.)
- Server file system
- Server network

**These MOVE to local**:
- MCP server execution
- Agent monitoring
- Activity logging
- Memory system

## Potential Issues & Solutions

### Issue 1: Docker Socket Access
**Problem**: Local MCP server can't access server Docker socket directly

**Solution**: MCP tools use SSH to execute docker commands on server:
```python
# MCP tool uses SSH to run docker commands
ssh unarmedpuppy@192.168.86.47 "docker ps"
```

**Status**: ✅ Already implemented in `remote_exec.py`

### Issue 2: File System Access
**Problem**: Local MCP server can't access server files directly

**Solution**: MCP tools use SSH to read/write server files:
```python
# MCP tool uses SSH to read files
ssh unarmedpuppy@192.168.86.47 "cat /path/to/file"
```

**Status**: ✅ Already implemented in `remote_exec.py`

### Issue 3: Container Network Access
**Problem**: Local MCP server can't access container networks directly

**Solution**: MCP tools use SSH to execute commands that access containers:
```python
# MCP tool uses SSH to exec into container
ssh unarmedpuppy@192.168.86.47 "docker exec container command"
```

**Status**: ✅ Already implemented

## My Recommendation ✅

**YES, run everything locally!** Here's why:

1. **Makes Sense**: Agent workflow and memory should be tied to the agent system
2. **Simpler**: One database, one source of truth, no sync issues
3. **Faster**: No network latency for logging/memory
4. **Better for Development**: Easier to test, iterate, debug
5. **Privacy**: All agent data stays local

**What you're NOT missing**:
- Server operations still work (via SSH/network)
- Multi-agent coordination can use shared local DB
- Monitoring dashboard works locally
- Backup via git/version control

**The only trade-off**:
- Dashboard only accessible locally (not from other devices)
- But this is probably fine for your use case

## Implementation Checklist

- [ ] Stop server monitoring (if running)
- [ ] Run monitoring locally (docker-compose or direct)
- [ ] Update activity logger to use `localhost:3001`
- [ ] Update Cursor config to run MCP server locally
- [ ] Set `AGENT_MONITORING_API_URL=http://localhost:3001`
- [ ] Test MCP tools (should work via SSH)
- [ ] Test monitoring (dashboard should show actions)
- [ ] Verify memory works locally
- [ ] Update documentation

---

**Bottom Line**: Your instinct is correct. Running everything locally makes the most sense for agent workflow and memory. Server operations still work via SSH/network, which is the right architecture.

