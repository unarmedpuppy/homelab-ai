# MCP Server: Local vs Docker

**Why the MCP server runs locally (not in Docker) when used with Cursor.**

## The Short Answer

**Yes, for Cursor to use it, the MCP server must run locally (on disk) with Python dependencies installed.**

**Why**: Cursor uses **stdio transport**, which requires spawning the server as a subprocess. Docker containers can't be spawned this way easily.

## Architecture Overview

### Current Setup (Local Execution)

```
┌─────────────────┐
│     Cursor      │  ← Runs on your local machine
│   (Your IDE)    │
└────────┬────────┘
         │ spawns subprocess via stdio
         │ (requires local Python + dependencies)
         ▼
┌─────────────────┐
│   MCP Server    │  ← Runs locally (Python process)
│  (server.py)    │     Needs: pip install -r requirements.txt
└────────┬────────┘
         │ makes SSH connections
         │ executes commands remotely
         ▼
┌─────────────────┐
│  Remote Server  │  ← Your server (192.168.86.47)
│  (192.168.86.47)│     Docker commands, services, etc.
└─────────────────┘
```

**Flow:**
1. Cursor spawns MCP server as local subprocess
2. MCP server connects to remote server via SSH
3. MCP server executes commands on remote server
4. Results returned to Cursor via stdio

### Why Local Execution?

**stdio transport requires:**
- Parent process (Cursor) spawns child process (MCP server)
- Communication via stdin/stdout pipes
- Direct process execution (not container execution)

**If we used Docker locally:**
- Cursor would need to run `docker exec` or connect via HTTP
- More complex than stdio transport
- Requires Docker to be running
- Adds latency and complexity

## Docker Setup (Alternative)

The `DOCKER_SETUP.md` file describes running the MCP server **on the server** (not locally):

```
┌─────────────────┐
│     Cursor      │  ← Your local machine
│   (Your IDE)    │
└────────┬────────┘
         │ SSH tunnel or HTTP connection
         ▼
┌─────────────────┐
│  Remote Server  │
│  (192.168.86.47)│
│                 │
│  ┌───────────┐  │
│  │ MCP Server│  │  ← Runs in Docker on server
│  │ (Docker)  │  │     Can access Docker socket directly
│  └───────────┘  │
└─────────────────┘
```

**This approach:**
- MCP server runs in Docker on the server
- Cursor connects via SSH tunnel or HTTP
- More complex setup
- Better for server-side execution
- Not recommended for local-first architecture

## Why Local is Better for Our Use Case

### Local Execution (Current) ✅

**Pros:**
- ✅ Simple stdio transport (no network config)
- ✅ Cursor manages everything automatically
- ✅ One-time setup (install dependencies)
- ✅ Works with local-first architecture
- ✅ No Docker required for MCP server

**Cons:**
- ❌ Need Python + dependencies installed locally
- ❌ MCP server connects to server via SSH (adds latency)

### Docker Execution (Alternative)

**Pros:**
- ✅ Isolated environment
- ✅ Can access Docker socket directly (no SSH needed)
- ✅ Consistent environment

**Cons:**
- ❌ More complex setup (SSH tunnel or HTTP)
- ❌ Requires Docker running
- ❌ Doesn't work with stdio transport easily
- ❌ More network configuration

## What Gets Installed Locally

When you run `pip install -r requirements.txt`, you're installing:

- `mcp` - MCP protocol library
- `requests` - HTTP client (for activity logger)
- Other dependencies for tools

**These are needed** because:
- Cursor spawns `python server.py` as a subprocess
- Python needs these packages to run the server
- The server runs in your local Python environment

## The Remote Connection

**Important**: Even though the MCP server runs locally, it connects to your remote server:

```python
# The MCP server uses SSH to connect to your server
# Example: docker_list_containers() tool
# 1. MCP server (local) receives tool call
# 2. MCP server connects to server via SSH
# 3. MCP server executes: docker ps (on server)
# 4. MCP server returns results to Cursor
```

**So the architecture is:**
- **MCP Server**: Runs locally (needs local Python + deps)
- **Remote Server**: Where actual Docker/services run
- **Connection**: SSH from local MCP server to remote server

## Summary

**For Cursor with stdio transport:**
- ✅ MCP server **must** run locally (not in Docker)
- ✅ Python dependencies **must** be installed locally
- ✅ Server connects to remote server via SSH
- ✅ This is the simplest and most reliable approach

**Docker setup is for:**
- Running MCP server on the server itself
- More complex scenarios
- Not recommended for local-first architecture

---

**See Also**:
- `agents/apps/agent-mcp/README.md` - MCP server setup
- `agents/apps/agent-mcp/DOCKER_SETUP.md` - Docker-based setup (advanced)
- `agents/docs/MCP_ARCHITECTURE_EXPLAINED.md` - MCP architecture details

