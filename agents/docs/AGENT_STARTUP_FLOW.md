# Agent Startup Flow

**How a new agent session works with the base prompt.**

## Prerequisites

Before an agent can start, these must be configured:

1. **MCP Server Configuration** (One-time setup)
   - MCP server must be configured in Cursor/Claude Desktop
   - See `agents/apps/agent-mcp/README.md` for configuration
   - MCP server is started automatically by Cursor when configured

2. **Docker Desktop** (May need to be started)
   - Docker Desktop must be installed
   - Can be started automatically by the infrastructure script

## Agent Startup Sequence

When you start a new agent session with `prompts/base.md`:

### Step 0: Start Infrastructure 🏗️

**Agent will attempt:**
```python
# Check if infrastructure is running
infra_status = await check_agent_infrastructure()

# If not running, start it
if not infra_status.get("all_running"):
    await start_agent_infrastructure()
```

**What happens:**
1. Agent calls `check_agent_infrastructure()` MCP tool
2. If services aren't running, calls `start_agent_infrastructure()` MCP tool
3. Tool runs `agents/scripts/start-agent-infrastructure.sh`
4. Script checks if Docker is running
5. If Docker not running (macOS), script runs `open -a Docker` to start Docker Desktop
6. Script waits for Docker to become available (up to 60 seconds)
7. Script runs `docker compose up -d` in `agents/apps/agent-monitoring/`
8. Script waits for services to be healthy
9. Returns success when all services are running

**Fallback** (if MCP tools not available):
- Agent can run the script directly via shell command
- Script still handles Docker Desktop startup automatically

### Step 0.5: Start Monitoring Session 📊

**Agent will:**
```python
start_agent_session(agent_id="agent-001")
update_agent_status(
    agent_id="agent-001",
    status="active",
    current_task_id="T1.1",
    progress="Starting work"
)
```

**What happens:**
- Agent becomes visible in monitoring dashboard
- Status tracked in database
- All subsequent tool calls are logged

### Step 1: Check Messages 📬

**Agent will:**
```python
messages = await get_agent_messages(
    agent_id="agent-001",
    status="pending"
)
```

**What happens:**
- Checks for messages from other agents
- Acknowledges urgent/high priority messages
- Responds if needed

### Step 2: Check Active Dev Docs 📝

**Agent will:**
```python
active_docs = list_active_dev_docs(agent_id="agent-001")
if active_docs:
    docs = read_dev_docs(agent_id="agent-001", task_name="...")
```

**What happens:**
- Checks for existing work from previous sessions
- Reads dev docs to refresh context
- Continues from where it left off

### Step 3: Query Memory 🧠

**Agent will:**
```python
memory_query_decisions(project="home-server", limit=5)
memory_query_patterns(severity="high", limit=5)
memory_search("relevant search terms")
```

**What happens:**
- Learns from past decisions
- Finds relevant patterns
- Avoids repeating mistakes

### Step 4: Check Specialized Agents 🤖

**Agent will:**
```python
query_agent_registry(specialization="relevant-specialization")
```

**What happens:**
- Checks if specialized agent exists for the task
- Delegates if appropriate
- Creates new agent if needed

### Step 5: Check Skills 📚

**Agent will:**
```python
suggest_relevant_skills(
    prompt_text="What you're working on",
    file_paths="files you're editing",
    task_description="Your task"
)
```

**What happens:**
- Gets skill suggestions based on context
- Reviews relevant skills
- Uses tested workflows instead of reinventing

### Step 6: Check MCP Tools 🔧

**Agent will:**
- Review `agents/apps/agent-mcp/README.md` for available tools
- Use MCP tools for all operations (observable!)
- Avoid custom commands (not observable)

### Step 7: Query Tasks 📋

**Agent will:**
```python
tasks = query_tasks(status="pending", priority="high")
if tasks:
    claim_task(task_id=tasks[0]["task_id"], agent_id="agent-001")
```

**What happens:**
- Finds available tasks
- Claims task (validates dependencies)
- Starts work

## What Gets Followed Automatically

✅ **Infrastructure Startup** - Agent will start Docker Desktop and services automatically  
✅ **Monitoring Session** - Agent will start session and update status  
✅ **Message Checking** - Agent will check for messages from other agents  
✅ **Memory Queries** - Agent will query past decisions and patterns  
✅ **Skill Discovery** - Agent will check for relevant skills  
✅ **Task Coordination** - Agent will query and claim tasks  
✅ **MCP Tool Usage** - Agent will use MCP tools (observable!)  
✅ **Quality Checks** - Agent will run quality checks after edits  
✅ **Self-Review** - Agent will review code before completion  

## What Requires Manual Setup

⚠️ **MCP Server Configuration** - Must be configured in Cursor/Claude Desktop (one-time)  
⚠️ **Docker Desktop Installation** - Must be installed (one-time)  

## If MCP Server Isn't Running

**If MCP tools are not available** (MCP server not configured in Cursor), the agent will:
1. Use fallback script: `./agents/scripts/start-agent-infrastructure.sh` (still works!)
2. Still follow the discovery workflow (memory, skills, tasks, etc.)
3. Use SSH commands for server operations (not observable)
4. Document work manually (not automatically logged)

**But**: The agent will still attempt to follow the prompt guidelines, just without MCP tool observability.

**To enable MCP tools**: Configure MCP server in Cursor/Claude Desktop (see `agents/apps/agent-mcp/README.md`). This is a one-time setup.

## Summary

**Yes, the agent will:**
- ✅ Attempt to start infrastructure automatically
- ✅ Follow all guidelines in the prompt
- ✅ Use tools, check skills, claim tasks, read memory, etc.
- ✅ Be observable in the monitoring dashboard

**But requires:**
- ⚠️ MCP server configured in Cursor (one-time setup)
- ⚠️ Docker Desktop installed (can be started automatically)

**The prompt is designed to be self-executing** - the agent will follow the discovery workflow automatically when given the base prompt.

---

**See Also**:
- `agents/prompts/base.md` - Complete agent prompt
- `agents/apps/agent-mcp/README.md` - MCP server setup
- `agents/ACTIVATION_GUIDE.md` - How to activate agents

