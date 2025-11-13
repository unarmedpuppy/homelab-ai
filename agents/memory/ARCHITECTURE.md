# Agent Memory Architecture

## Overview

`apps/agent_memory` is **NOT a server** - it's a **Python library** that provides memory functionality. It uses **SQLite** (just a file) for storage, so **no server process is needed**.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Memory System                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  agents/memory/                                          │
│  ├── sqlite_memory.py      ← Python library (no server)     │
│  ├── memory.db              ← SQLite file (no server)        │
│  ├── query_memory.sh        ← Helper script                  │
│  └── __init__.py            ← Exports get_memory()           │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Used by
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Access Methods                                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. MCP Tools (via server-management-mcp)                   │
│     └── Dockerized MCP server imports the library            │
│                                                               │
│  2. Direct Python Import (local)                            │
│     └── from agents.memory import get_memory            │
│                                                               │
│  3. Helper Script (command-line)                            │
│     └── ./query_memory.sh                                    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## What It Is

✅ **Python Library** - Just code, no server process  
✅ **SQLite Database** - Single file (`memory.db`), no server needed  
✅ **File-Based** - Can be accessed directly via filesystem  
✅ **No Docker Required** - Works as-is, no containerization needed  

## What It Is NOT

❌ **Not a Server** - No HTTP server, no process to run  
❌ **Not Dockerized** - The library itself doesn't need Docker  
❌ **Not a Service** - No background process or daemon  

## How It's Used

### 1. Via MCP Server (Dockerized)

The **MCP server** (`server-management-mcp`) IS dockerized and uses this library:

```python
# In server-management-mcp/tools/memory.py
from agents.memory import get_memory

memory = get_memory()  # Accesses memory.db file
```

**Flow:**
1. MCP server runs in Docker
2. MCP server imports `apps.agent_memory`
3. MCP server provides memory tools to agents
4. Agents call MCP tools → MCP server → memory library → SQLite file

### 2. Direct Python Import (Local)

When agents run locally (Cursor/Claude Desktop), they can import directly:

```python
from agents.memory import get_memory

memory = get_memory()  # Accesses memory.db file directly
```

**Flow:**
1. Agent imports library
2. Library accesses SQLite file directly
3. No server needed

### 3. Helper Script (Command-Line)

The `query_memory.sh` script we created:

```bash
./query_memory.sh decisions --project home-server
```

**Flow:**
1. Script runs `sqlite3` command
2. Directly queries `memory.db` file
3. No server needed

## Database Location

**SQLite Database**: `agents/memory/memory.db`

- Created automatically on first use
- Single file, no server process
- Can be accessed from anywhere with filesystem access
- Can be backed up by copying the file

## Should It Be Dockerized?

**No, it shouldn't be dockerized** because:

1. **It's just a library** - No server process to containerize
2. **SQLite is file-based** - Works fine as a file, no need for a database server
3. **Multiple access methods** - Needs to be accessible from:
   - MCP server (already dockerized)
   - Local agents (Cursor/Claude Desktop)
   - Helper scripts
   - Direct Python imports

4. **File access is simpler** - All access methods can read/write the same SQLite file

## Current Setup

```
agents/memory/
├── sqlite_memory.py      ← Library code
├── memory.db              ← SQLite database (file)
├── query_memory.sh        ← Helper script
└── __init__.py            ← Exports

server-management-mcp/     ← Dockerized MCP server
├── docker-compose.yml     ← Runs in Docker
├── tools/
│   └── memory.py         ← Imports apps.agent_memory
└── server.py              ← MCP server
```

## Access Patterns

### Pattern 1: Agent → MCP Server → Memory Library → SQLite File
```
Agent (Cursor) 
  → MCP Tool Call 
  → MCP Server (Docker) 
  → apps.agent_memory.get_memory() 
  → memory.db (file)
```

### Pattern 2: Agent → Memory Library → SQLite File (Direct)
```
Agent (Python script) 
  → from agents.memory import get_memory 
  → memory.db (file)
```

### Pattern 3: User → Helper Script → SQLite File
```
User 
  → ./query_memory.sh 
  → sqlite3 command 
  → memory.db (file)
```

## Summary

- **Memory system**: Just files (Python code + SQLite database)
- **No server needed**: SQLite is file-based
- **No Docker needed**: Library works as-is
- **MCP server**: IS dockerized and uses the library
- **Access**: Multiple ways (MCP tools, Python import, helper script)

The memory system is designed to be **simple and accessible** - just a library and a database file. No complexity, no servers, no Docker required for the memory system itself.

