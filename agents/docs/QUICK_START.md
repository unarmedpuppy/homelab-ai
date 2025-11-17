# Quick Start Guide

**Instructions for using `agents/prompts/base.md` to start working as an agent.**

This guide explains the prerequisites and how to prompt with `prompts/base.md` to get started.

## 📋 Prerequisites

Before you can use `prompts/base.md`, ensure these are in place:

### 1. Docker Desktop

**Required**: Docker Desktop must be installed and running.

- **macOS/Windows**: Install Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)
- **Linux**: Install Docker Engine

**Note**: The agent infrastructure startup script will automatically start Docker Desktop on macOS if it's not running. On other platforms, ensure Docker is running before starting.

**Verify Docker is running**:
```bash
docker ps
```

### 2. Python 3.8+

**Required**: Python 3.8 or higher must be installed.

**Verify Python**:
```bash
python3 --version
```

### 3. MCP Server Setup

**Required**: MCP server must be configured in Cursor/Claude Desktop.

#### Install MCP Server Dependencies

```bash
cd /Users/joshuajenquist/repos/personal/home-server
cd agents/apps/agent-mcp
pip install -r requirements.txt
```

#### Configure MCP Server in Cursor

**macOS**: Edit `~/Library/Application Support/Cursor/User/globalStorage/mcp.json`

**Windows**: Edit `%APPDATA%\Cursor\User\globalStorage\mcp.json`

**Linux**: Edit `~/.config/Cursor/User/globalStorage/mcp.json`

**Add configuration**:
```json
{
  "mcpServers": {
    "home-server": {
      "command": "python",
      "args": [
        "/Users/joshuajenquist/repos/personal/home-server/agents/apps/agent-mcp/server.py"
      ],
      "env": {
        "SONARR_API_KEY": "your-sonarr-api-key",
        "RADARR_API_KEY": "your-radarr-api-key"
      }
    }
  }
}
```

**Important**: Replace the path with your actual project path.

#### Restart Cursor

After configuring, **restart Cursor** to load the MCP server configuration.

#### Verify MCP Server

1. Open a new chat in Cursor
2. Try: "List Docker containers" or "Check agent infrastructure status"
3. If MCP tools are available, setup is complete! ✅

**If tools aren't available**:
- Check Cursor logs for MCP server errors
- Verify the path to `server.py` is correct
- Ensure Python dependencies are installed
- See `agents/apps/agent-mcp/README.md` for troubleshooting

### 4. Git

**Required**: Git must be installed for deployment operations.

**Verify Git**:
```bash
git --version
```

---

## 🚀 How to Use `prompts/base.md`

### Method 1: Direct Reference (Recommended)

**In Cursor, start a new chat and say**:

```
@agents/prompts/base.md

I am an AI agent working on the home server project. Please follow this prompt and start the discovery workflow.
```

**What happens**:
1. Agent reads `prompts/base.md` (complete guide with discovery workflow)
2. Agent starts infrastructure (Docker Desktop + monitoring services)
3. Agent starts monitoring session
4. Agent follows discovery workflow (check messages, memory, skills, tasks)
5. Agent begins work following all guidelines

### Method 2: Explicit Instruction

**In Cursor, start a new chat and say**:

```
I am an AI agent working on the home server project.

Please read and follow the agent prompt: agents/prompts/base.md

I will start by following the discovery workflow in that prompt.
```

### Method 3: With Specific Task

**In Cursor, start a new chat and say**:

```
@agents/prompts/base.md

I am agent-001. I need to work on [your task description].

Please follow this prompt and help me complete this task.
```

---

## 📖 What `prompts/base.md` Contains

The `prompts/base.md` file is the **complete agent prompt** that includes:

1. **Discovery Workflow** - Step-by-step process to:
   - Start infrastructure
   - Start monitoring session
   - Check messages from other agents
   - Query memory for past decisions
   - Check available skills
   - Find available tasks
   - Start work

2. **Agent Identity** - Role, responsibilities, and guidelines

3. **System Integration** - How to use:
   - Memory system
   - Task coordination
   - Communication protocol
   - Monitoring dashboard
   - MCP tools

4. **Best Practices** - Workflow patterns and standards

5. **Tool Reference** - How to discover and use MCP tools

**You don't need to read it manually** - just reference it in your prompt and the agent will read and follow it.

---

## 🔍 Understanding the Discovery Workflow

When you use `prompts/base.md`, the agent follows this discovery workflow:

### 0. Start Infrastructure
- Checks if Docker Desktop is running (starts it on macOS if needed)
- Starts monitoring services (backend, frontend, Grafana, InfluxDB)
- Verifies all services are healthy

### 0.5. Start Monitoring Session
- Starts agent monitoring session
- Updates agent status to "active"
- Makes work visible in dashboard (`localhost:3012`)

### 1. Check Messages
- Checks for pending messages from other agents
- Acknowledges urgent/high priority messages

### 2. Check Memory
- Queries recent decisions
- Queries common patterns
- Searches for related work

### 3. Check Skills
- Reviews available skills in `agents/skills/README.md`
- Identifies relevant workflows

### 4. Check MCP Tools
- Reviews available MCP tools
- Uses tools for all operations (observable!)

### 5. Check Available Tasks
- Queries task coordination system for available tasks
- Claims tasks as needed

### 6. Start Work
- Follows established patterns
- Uses MCP tools for all operations
- Updates status regularly

**See**: `agents/prompts/base.md` for the complete discovery workflow.

---

## 🎯 What Happens After Starting

Once you've prompted with `prompts/base.md`, the agent will:

1. **Automatically start infrastructure** (if not running)
2. **Make itself visible** in the monitoring dashboard
3. **Check for messages** from other agents
4. **Learn from past work** by querying memory
5. **Discover available capabilities** (skills, tools, tasks)
6. **Begin work** following all guidelines

**You can monitor progress** at:
- **Dashboard**: `http://localhost:3012` - Real-time agent activity
- **Grafana**: `http://localhost:3011` - Metrics and visualizations

---

## 📚 Additional Resources

### Core Documentation
- **`agents/docs/SYSTEM_ARCHITECTURE.md`** - Comprehensive system architecture (source of truth)
- **`agents/prompts/base.md`** - Complete agent prompt (what you're using)
- **`agents/docs/AGENT_WORKFLOW.md`** - Detailed workflow guide

### System Components
- **`agents/memory/README.md`** - Memory system documentation
- **`agents/tasks/README.md`** - Task coordination guide
- **`agents/communication/README.md`** - Communication protocol guide
- **`agents/apps/agent-monitoring/README.md`** - Monitoring dashboard guide
- **`agents/apps/agent-mcp/README.md`** - MCP tools catalog

### Tool Discovery
- **`agents/docs/MCP_TOOL_DISCOVERY.md`** - How to discover and use tools
- **`agents/apps/agent-mcp/MCP_TOOLS_REFERENCE.md`** - Tool count reference
- Use `list_tool_categories()` MCP tool - Get current tool count dynamically

---

## ⚠️ Important Notes

1. **Docker must be running** - Infrastructure services run in Docker
2. **MCP server must be configured** - Required for all MCP tools
3. **Use `prompts/base.md`** - It contains the complete workflow
4. **Monitor your work** - Dashboard at `localhost:3012`
5. **Use MCP tools** - They're observable, custom commands are not

---

## 🆘 Troubleshooting

### MCP Tools Not Available

1. Check MCP server configuration in Cursor
2. Verify Python dependencies are installed
3. Restart Cursor after configuration changes
4. Check Cursor logs for errors
5. See `agents/apps/agent-mcp/README.md` for troubleshooting

### Infrastructure Won't Start

1. Ensure Docker Desktop is running
2. Check Docker Desktop logs
3. Verify ports are available (3001, 3012, 3011, 8087)
4. Try running startup script manually: `./agents/scripts/start-agent-infrastructure.sh`

### Agent Not Visible in Dashboard

1. Ensure infrastructure is running
2. Verify agent called `start_agent_session()`
3. Check dashboard at `localhost:3012`
4. Review monitoring logs

---

**Last Updated**: 2025-01-13  
**Status**: Active  
**See Also**: 
- `agents/docs/SYSTEM_ARCHITECTURE.md` - Comprehensive system architecture
- `agents/prompts/base.md` - Complete agent prompt
- `agents/README.md` - Main entry point
