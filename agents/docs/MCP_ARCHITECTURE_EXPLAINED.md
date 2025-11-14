# MCP Architecture Explained

**Why agents can't directly call the MCP server, and why Cursor configuration is required.**

## The MCP Protocol

MCP (Model Context Protocol) is a protocol designed by Anthropic for AI assistants to interact with external tools and data sources. It uses a **client-server architecture** where:

- **MCP Server**: Provides tools and resources (our `agents/apps/agent-mcp/server.py`)
- **MCP Client**: Connects to the server and makes tools available to the AI (Cursor/Claude Desktop)

## How MCP Communication Works

### Transport: stdio (Standard Input/Output)

Looking at our MCP server code:

```python
# agents/apps/agent-mcp/server.py
from mcp.server.stdio import stdio_server

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, ...)
```

**Key Point**: MCP uses **stdio transport** by default. This means:
- The server reads from **stdin** (standard input)
- The server writes to **stdout** (standard output)
- Communication happens via **pipes**, not network sockets

### Why This Matters

**stdio transport requires a parent process to manage the pipes:**

```
┌─────────────────┐
│  Cursor/Claude │  ← MCP Client (manages stdio pipes)
│     Desktop     │
└────────┬────────┘
         │ spawns subprocess
         │ manages stdin/stdout pipes
         ▼
┌─────────────────┐
│   MCP Server    │  ← Our server.py (reads stdin, writes stdout)
│  (server.py)    │
└─────────────────┘
```

**The agent (running inside Cursor) cannot directly:**
- Start the MCP server process itself (Cursor manages process lifecycle)
- Manage stdio pipes (Cursor handles this)
- Directly communicate with the server (must go through Cursor's MCP client)

## Why Cursor Configuration is Required

### What Cursor Does

When you configure MCP in Cursor's config file:

```json
{
  "mcpServers": {
    "home-server": {
      "command": "python",
      "args": ["/path/to/agents/apps/agent-mcp/server.py"],
      "env": { ... }
    }
  }
}
```

**Cursor automatically:**
1. **Spawns the MCP server** as a subprocess when Cursor starts
2. **Manages stdio pipes** (connects stdin/stdout)
3. **Handles the MCP protocol** (sends requests, receives responses)
4. **Exposes tools to the agent** (makes tools available in the conversation)
5. **Manages server lifecycle** (restarts if it crashes, stops when Cursor closes)

### What the Agent Sees

Once configured, the agent sees tools as if they're built-in:

```python
# Agent can call tools directly
await start_agent_infrastructure()
await docker_list_containers()
await memory_query_decisions(...)
```

**But behind the scenes:**
1. Agent requests tool → Cursor's MCP client
2. MCP client → Formats MCP protocol message
3. MCP client → Writes to MCP server's stdin
4. MCP server → Reads from stdin, processes request
5. MCP server → Writes response to stdout
6. MCP client → Reads from stdout, parses response
7. MCP client → Returns result to agent

## Why Agents Can't Just "Call Into" the MCP Server

### Problem 1: Process Management

**If the agent tried to start the MCP server itself:**

```python
# Agent tries to do this (WON'T WORK):
import subprocess
subprocess.Popen(["python", "server.py"])
# Now what? How does the agent connect to it?
```

**Issues:**
- Agent would need to manage the subprocess lifecycle
- Agent would need to handle stdin/stdout pipes
- Agent would need to implement the MCP protocol client
- Agent would need to handle reconnection if server crashes
- Multiple agents would spawn multiple servers (conflicts)

### Problem 2: stdio Transport Requires Parent Process

**stdio pipes are created by the parent process:**

```python
# This is what Cursor does internally:
import subprocess
process = subprocess.Popen(
    ["python", "server.py"],
    stdin=subprocess.PIPE,  # Cursor creates this pipe
    stdout=subprocess.PIPE, # Cursor creates this pipe
    stderr=subprocess.PIPE
)
# Cursor manages these pipes and implements MCP protocol
```

**The agent can't do this because:**
- The agent is running **inside** Cursor, not as a separate process
- The agent doesn't have access to spawn subprocesses with stdio pipes
- The agent would need to implement the entire MCP client protocol

### Problem 3: Multiple Agents, One Server

**If each agent started its own MCP server:**
- Multiple servers would conflict (port conflicts, resource conflicts)
- No shared state (each agent has its own memory, tasks, etc.)
- Inefficient (duplicate processes)

**With Cursor managing it:**
- One MCP server process shared by all conversations
- Shared state across all agents
- Efficient resource usage

## Could We Make It Automatic?

### Option 1: Agent Starts MCP Server (Current Limitation)

**Why it's hard:**
- Agent would need to implement MCP client protocol
- Agent would need to manage process lifecycle
- Agent would need to handle stdio pipes
- Would break the "one server, multiple agents" model

**Not recommended** - breaks MCP architecture.

### Option 2: HTTP/SSE Transport (Future Possibility)

**MCP supports HTTP/SSE transport:**

```python
# Could modify server.py to support HTTP:
from mcp.server.sse import sse_server

async def main():
    async with sse_server(port=8000) as server:
        await server.run(...)
```

**Then agent could:**
```python
# Agent could connect directly:
import requests
response = requests.post("http://localhost:8000/mcp/call_tool", ...)
```

**Benefits:**
- Agent could start server and connect directly
- No Cursor configuration needed
- More flexible architecture

**Drawbacks:**
- Need to implement HTTP/SSE transport
- Need to manage server lifecycle
- Need to handle authentication/security
- More complex than stdio

**Status**: Not implemented yet. stdio is simpler and works well with Cursor.

### Option 3: Auto-Configuration Script (Possible Workaround)

**Could create a script that:**
1. Checks if MCP is configured in Cursor config
2. If not, automatically adds configuration
3. Prompts user to restart Cursor

**Example:**
```bash
./agents/scripts/setup-mcp.sh
# Checks ~/Library/Application Support/Claude/claude_desktop_config.json
# Adds MCP server config if missing
# Prompts user to restart Cursor
```

**Benefits:**
- Makes setup easier
- Still requires Cursor restart (limitation of MCP)

**Status**: Could be implemented, but still requires one-time setup.

## Current Architecture (Recommended)

### Why This Works Well

1. **Cursor manages everything**: Process lifecycle, stdio pipes, protocol handling
2. **One server, multiple agents**: Shared state, efficient resource usage
3. **Simple stdio transport**: No network configuration, no ports, no authentication
4. **Automatic tool discovery**: Cursor exposes tools to agent automatically
5. **Built-in error handling**: Cursor handles server crashes, reconnections

### The One-Time Setup

**User needs to:**
1. Configure MCP server in Cursor config (one-time)
2. Restart Cursor (one-time)
3. Done! MCP server starts automatically for all future sessions

**Agent then:**
- Automatically has access to all MCP tools
- Can call tools directly
- No additional setup needed

## Summary

**Why agents can't directly call the MCP server:**
1. **stdio transport** requires a parent process to manage pipes
2. **MCP protocol** requires a client implementation (Cursor provides this)
3. **Process management** is handled by Cursor (lifecycle, restarts, etc.)
4. **Shared state** requires one server for all agents

**Why Cursor configuration is required:**
1. Cursor needs to know **how to start** the MCP server
2. Cursor needs to know **where the server is** (path to server.py)
3. Cursor needs to know **environment variables** (API keys, etc.)
4. Cursor manages the **entire connection lifecycle**

**Could we make it automatic?**
- **Not easily with stdio transport** (requires parent process management)
- **Possibly with HTTP/SSE transport** (would need implementation)
- **Could add auto-configuration script** (still requires Cursor restart)

**Current approach is recommended** because:
- Simple stdio transport (no network config)
- Cursor handles everything automatically
- One-time setup, then works forever
- Shared state across all agents

---

**See Also**:
- `agents/apps/agent-mcp/README.md` - MCP server setup
- `agents/apps/agent-mcp/server.py` - MCP server implementation
- [MCP Protocol Documentation](https://modelcontextprotocol.io/) - Official MCP docs

