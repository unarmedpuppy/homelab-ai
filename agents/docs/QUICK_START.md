# Agent Quick Start Guide

**Complete guide to set up and get started as an agent on the home server project.**

## 📋 Prerequisites

Before starting, ensure you have:
- ✅ **Docker Desktop** installed (will be started automatically if needed)
- ✅ **Python 3.8+** installed
- ✅ **Cursor** or **VS Code with Copilot** installed
- ✅ **Git** installed

## 🔧 Initial Setup (One-Time)

### Step 1: Install MCP Server Dependencies

**Why**: The MCP server runs **locally on your machine** (not in Docker) because Cursor uses stdio transport, which requires spawning the server as a subprocess. The server then connects to your remote server via SSH to execute commands.

```bash
cd /Users/joshuajenquist/repos/personal/home-server
cd agents/apps/agent-mcp
pip install -r requirements.txt
```

**Note**: The MCP server runs locally, but it connects to your remote server (192.168.86.47) via SSH to execute Docker commands and manage services. See `agents/apps/agent-mcp/DOCKER_SETUP.md` for Docker-based deployment (advanced, for server-side execution).

### Step 2: Configure MCP Server in Cursor

**For Cursor:**

1. Open Cursor settings/preferences
2. Find MCP server configuration (or edit config file directly)
3. Add the MCP server configuration:

**macOS**: Edit `~/Library/Application Support/Cursor/User/globalStorage/mcp.json` or check Cursor settings UI

**Windows**: Edit `%APPDATA%\Cursor\User\globalStorage\mcp.json`

**Linux**: Edit `~/.config/Cursor/User/globalStorage/mcp.json`

**Configuration** (add to your MCP servers config):

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

**Note**: Replace the path with your actual project path, and add API keys if needed.

### Step 3: Configure MCP Server in VS Code with Copilot

**For VS Code with GitHub Copilot:**

VS Code doesn't natively support MCP servers like Cursor does. You have two options:

**Option A: Use Cursor** (Recommended - has native MCP support)

**Option B: Run MCP server manually** (Advanced):
```bash
# In a terminal, run:
cd /Users/joshuajenquist/repos/personal/home-server/agents/apps/agent-mcp
python server.py
# Then use MCP client tools or direct API calls
```

### Step 4: Restart Cursor/VS Code

**Important**: After configuring the MCP server, restart Cursor/VS Code to load the configuration.

### Step 5: Verify MCP Server is Running

1. Open a new chat/conversation in Cursor
2. Try calling an MCP tool (e.g., "List Docker containers")
3. If tools are available, MCP server is working! ✅

**If tools aren't available:**
- Check Cursor logs for MCP server errors
- Verify the path to `server.py` is correct
- Ensure Python dependencies are installed
- See `agents/apps/agent-mcp/README.md` for troubleshooting

## 🚀 Starting Your First Agent Session

### Option A: Using the Base Prompt (Recommended)

**In Cursor, start a new chat and paste:**

```
I am an AI agent working on the home server project. 

Please read and follow the agent prompt: agents/prompts/base.md

I will start by following the discovery workflow in that prompt.
```

**The agent will automatically:**
1. Read the base prompt
2. Start infrastructure (Docker Desktop + monitoring services)
3. Start monitoring session
4. Check messages, memory, skills, etc.
5. Begin work following all guidelines

### Option B: Direct Instructions

**In Cursor, start a new chat and say:**

```
I need to start working on the home server project. Please:

1. Start the agent infrastructure (monitoring services)
2. Start my monitoring session (agent-001)
3. Check for messages from other agents
4. Query memory for past decisions
5. Check for relevant skills
6. Show me available tasks

Follow the workflow in agents/prompts/base.md
```

### Option C: Reference the Prompt File

**In Cursor, start a new chat and say:**

```
@agents/prompts/base.md

I am agent-001. Please follow this prompt and start the discovery workflow.
```

## 🚀 Essential Steps (Do These First!)

### Step 0: Start Infrastructure (30 seconds)

**CRITICAL**: Start agent infrastructure before doing anything else.

**Option A: Using MCP Tool** (if available):
```python
await start_agent_infrastructure()
```

**Option B: Using Script** (fallback):
```bash
cd /Users/joshuajenquist/repos/personal/home-server
./agents/scripts/start-agent-infrastructure.sh
```

**Verify**: Check dashboard at `http://localhost:3012`

### Step 0.5: Start Monitoring (30 seconds)

**CRITICAL**: Make yourself visible before doing anything:

```python
# Start your session
start_agent_session(agent_id="agent-001")

# Update your status
update_agent_status(
    agent_id="agent-001",
    status="active",
    current_task_id="T1.1",  # Your task ID
    progress="Starting work"
)
```

**Why**: Your work is invisible without this! Dashboard: http://localhost:3012

### Step 1: Check Messages (30 seconds)

```python
# Check for messages from other agents
messages = await get_agent_messages(agent_id="agent-001", status="pending")

# Acknowledge urgent messages
for msg in messages["messages"]:
    if msg["priority"] in ["urgent", "high"]:
        await acknowledge_message(msg["message_id"], "agent-001")
```

### Step 2: Check Memory (1 minute)

```python
# Learn from past work
memory_query_decisions(project="home-server", limit=5)
memory_query_patterns(severity="high", limit=5)
memory_search("your task keywords")
```

**Why**: Don't repeat past decisions. Learn from what worked.

### Step 3: Check Skills (1 minute)

Review `agents/skills/README.md` for workflows:
- `standard-deployment` - Deploy code changes
- `troubleshoot-container-failure` - Diagnose issues
- `system-health-check` - System verification

**Why**: Use tested workflows instead of starting from scratch.

### Step 4: Check MCP Tools (1 minute)

Review `agents/apps/agent-mcp/README.md` for available tools (68 tools total).

**⚠️ CRITICAL**: Always prefer MCP tools over custom commands - they're observable!

## 📚 Essential Resources

### Must-Read Documents

1. **`prompts/base.md`** ⭐ - Complete agent prompt (read this for full details)
2. **`AGENT_WORKFLOW.md`** - Detailed workflow guide
3. **`MCP_TOOL_DISCOVERY.md`** - How to find and use tools

### Key Systems

- **Memory**: `agents/memory/README.md` - Store/query decisions and patterns
- **Tasks**: `agents/tasks/README.md` - Task coordination
- **Communication**: `agents/communication/README.md` - Agent messaging
- **Monitoring**: `agents/apps/agent-monitoring/README.md` - Activity dashboard

## 🛠️ Common Operations

### Record a Decision

```python
memory_record_decision(
    content="Use PostgreSQL for database",
    rationale="Need ACID compliance",
    importance=0.9,
    tags="database,architecture"
)
```

### Register a Task

```python
register_task(
    title="Setup database",
    description="Create PostgreSQL schema",
    project="home-server",
    priority="high"
)
```

### Send Message to Another Agent

```python
send_agent_message(
    from_agent="agent-001",
    to_agent="agent-002",
    type="request",
    priority="high",
    subject="Need help with deployment",
    content="I'm stuck on..."
)
```

### Deploy Changes

```python
# Use the standard-deployment skill workflow
# Or use MCP tools directly:
git_deploy(commit_message="Update configuration")
docker_compose_restart(app_path="apps/my-app", service="my-service")
```

## ⚠️ Important Rules

1. **Always use MCP tools** - They're observable in the dashboard
2. **Never use custom commands** - They're invisible
3. **Check memory first** - Learn from past work
4. **Use skills for workflows** - Don't reinvent common processes
5. **Update status regularly** - Keep monitoring dashboard current
6. **End session when done** - `end_agent_session(...)`

## 🎯 Discovery Priority

**Follow this order:**

0. **Start Monitoring** → `start_agent_session()`
1. **Check Messages** → `get_agent_messages()`
2. **Check Memory** → `memory_query_*()`
3. **Check Skills** → `agents/skills/README.md`
4. **Check MCP Tools** → `agents/apps/agent-mcp/README.md`
5. **Create New** → Only if nothing exists

## 📖 Next Steps

After this quick start:

1. Read **`prompts/base.md`** for complete details
2. Review **`AGENT_WORKFLOW.md`** for detailed workflows
3. Explore **`MCP_TOOL_DISCOVERY.md`** for tool discovery

---

**See**: `agents/docs/README.md` for complete documentation index

