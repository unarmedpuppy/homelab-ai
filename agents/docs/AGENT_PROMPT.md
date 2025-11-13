# Agent Prompt - Complete Guide

## 🚀 Start Here: Discovery Workflow

**Before doing ANYTHING, follow this discovery workflow in order:**

### 0. Start Agent Monitoring Session 📊
**CRITICAL**: Always start your session and update your status so you can be observed:

```python
# Start session (do this first!)
start_agent_session(agent_id="agent-001")

# Update your status
update_agent_status(
    agent_id="agent-001",
    status="active",
    current_task_id="T1.1",
    progress="Starting work on deployment task"
)
```

**Why**: The agent monitoring dashboard tracks all agent activity. Without this, your work is invisible!

**Available Activity Monitoring Tools** (4 tools):
- `start_agent_session(agent_id)` - Start a new session (call this first!)
- `update_agent_status(agent_id, status, current_task_id, progress, blockers)` - Update your status regularly
- `get_agent_status(agent_id)` - Check your current status
- `end_agent_session(agent_id, session_id, tasks_completed, tools_called, total_duration_ms)` - End session when done

**See**: `apps/agent-monitoring/README.md` for dashboard access and `apps/agent-monitoring/INTEGRATION_GUIDE.md` for complete integration guide.

### 1. Check Memory First ⚡
Query previous decisions and patterns to learn from past work:

**If MCP tools available:**
```python
# Find related decisions
memory_query_decisions(project="home-server", limit=5)

# Find common patterns
memory_query_patterns(severity="high", limit=5)

# Full-text search
memory_search("your search query")

# Check recent context
memory_get_recent_context(limit=5)
```

**If MCP tools NOT available** (fallback):
```bash
# Direct SQLite query
cd apps/agent_memory
sqlite3 memory.db "SELECT * FROM decisions ORDER BY created_at DESC LIMIT 5;"
sqlite3 memory.db "SELECT * FROM patterns WHERE severity='high' LIMIT 5;"
```

**Why**: Don't repeat past decisions. Learn from what worked before.

### 1.5. Check for Messages 📬
**CRITICAL**: Check for messages from other agents at the start of your session:

```python
# Get pending messages for you
messages = await get_agent_messages(
    agent_id="agent-001",
    status="pending"
)

# Acknowledge urgent/high priority messages immediately
for msg in messages["messages"]:
    if msg["priority"] in ["urgent", "high"]:
        await acknowledge_message(msg["message_id"], "agent-001")
        # Respond or escalate as needed
```

**Why**: Other agents may need your help or have important information to share.

**Available Communication Tools** (5 tools):
- `send_agent_message()` - Send message to another agent
- `get_agent_messages()` - Get messages for you (with filters)
- `acknowledge_message()` - Acknowledge receipt
- `mark_message_resolved()` - Mark message as resolved
- `query_messages()` - Query messages with multiple filters

**See**: `agents/communication/README.md` for complete communication guide and `agents/communication/protocol.md` for protocol specification.

### 2. Check for Specialized Agents 🤖
If your task requires domain expertise:

```python
# Check if specialized agent exists
query_agent_registry(specialization="media-download")

# If found: Assign task to existing agent
# (This automatically registers in central task registry too)
assign_task_to_agent(agent_id="agent-002", task_description="...")

# If not found: Create specialized agent
create_agent_definition(
    specialization="media-download",
    capabilities="troubleshoot-stuck-downloads skill, sonarr tools",
    initial_tasks="Fix stuck downloads in Sonarr queue...",
    parent_agent_id="agent-001"
)
```

**Why**: Delegate to domain experts. Don't reinvent specialized knowledge.

**Note**: `assign_task_to_agent()` now also registers tasks in the central task registry for cross-agent coordination.

### 3. Check Skills 📚
Review `server-management-skills/README.md` for complete workflows:

- `standard-deployment` - Deploy changes workflow
- `troubleshoot-container-failure` - Container diagnostics
- `system-health-check` - System verification
- `troubleshoot-stuck-downloads` - Download queue fixes
- `deploy-new-service` - New service setup

**Why**: Use tested workflows. Don't reinvent common processes.

### 4. Check MCP Tools 🔧
Review `server-management-mcp/README.md` for available operations:

**⚠️ CRITICAL: Prioritize Observable Tools**
**Always prefer MCP tools over custom commands** - MCP tools are automatically logged and visible in the agent monitoring dashboard. Custom commands are invisible!

**68 Tools Available:**
- **Activity Monitoring** (4 tools) - ⭐ **USE THESE FIRST** - Start sessions, update status
- Memory management (9 tools)
- Task coordination (6 tools)
- Agent management (6 tools)
- Agent communication (5 tools)
- Docker management (8 tools)
- Media download (13 tools)
- System monitoring (5 tools)
- Git operations (4 tools)
- Troubleshooting (3 tools)
- Networking (3 tools)
- System utilities (3 tools)
- Skill management (3 tools)

**Why**: 
- **Observability**: MCP tools are automatically logged and visible in the dashboard
- **Standardization**: Type-safe, tested, and documented
- **Visibility**: Your work is tracked and can be monitored
- **Don't write custom commands** - They won't be visible in monitoring!

## Memory System - How to Use

### Before Starting Work

**Example: Starting a new deployment task**

```python
# Check for previous deployment decisions
memory_query_decisions(project="home-server", search_text="deployment", limit=5)

# Check for common deployment patterns
memory_query_patterns(severity="high", tags="deployment,docker", limit=5)

# Search for related work
memory_search("docker-compose setup")
```

**What to look for:**
- Previous decisions about similar services
- Common patterns or issues encountered
- Port conflicts or configuration patterns

### During Work

**Example: Recording decisions as you make them**

```python
# Record important decisions
memory_record_decision(
    content="Use PostgreSQL for trading-journal database",
    rationale="Need ACID compliance, concurrent writes, and complex queries. SQLite doesn't support concurrent writes well.",
    project="trading-journal",
    task="T1.3",
    importance=0.9,
    tags="database,architecture,postgresql"
)

# Record patterns when you discover them
memory_record_pattern(
    name="Port Conflict Resolution",
    description="Services failing to start due to port conflicts. Common when adding new services without checking existing port usage.",
    solution="Always check port availability first using check_port_status MCP tool. Reference apps/docs/APPS_DOCUMENTATION.md for port list.",
    severity="medium",
    tags="docker,networking,ports,troubleshooting"
)

# Update context regularly
memory_save_context(
    agent_id="agent-001",
    task="T1.3",
    current_work="PostgreSQL setup in progress. Created docker-compose.yml, configured environment variables. Next: Run migrations.",
    status="in_progress",
    notes="Database password generated with openssl rand -hex 32"
)
```

### After Work

**Example: Completing a task**

```python
# Save final context
memory_save_context(
    agent_id="agent-001",
    task="T1.3",
    current_work="PostgreSQL setup complete. Database running, migrations applied, connection tested.",
    status="completed",
    notes="Used port 5432 internally, exposed via docker network"
)
```

**See**: `agents/memory/MEMORY_USAGE_EXAMPLES.md` for complete examples and best practices.

**Available Memory Tools (9):**
- Query: `memory_query_decisions`, `memory_query_patterns`, `memory_search`, `memory_get_recent_context`, `memory_get_context_by_task`
- Record: `memory_record_decision`, `memory_record_pattern`, `memory_save_context`
- Export: `memory_export_to_markdown`

**See**: 
- `agents/memory/MCP_TOOLS_GUIDE.md` - Complete MCP tool reference
- `agents/memory/MEMORY_USAGE_EXAMPLES.md` - Real-world usage examples and best practices

### ⚠️ Fallback: When MCP Tools Aren't Available

**If MCP tools are not available** (e.g., MCP server not connected), use these fallback methods:

#### Option 1: Use Helper Script (Recommended)

Use the `query_memory.sh` helper script for easy command-line access:

```bash
# Query decisions
cd apps/agent_memory
./query_memory.sh decisions --project home-server --limit 5

# Query patterns
./query_memory.sh patterns --severity high --limit 10

# Full-text search
./query_memory.sh search "search_term"

# Get recent decisions
./query_memory.sh recent --limit 5
```

**See**: `agents/memory/QUERY_MEMORY_README.md` for complete usage guide.

#### Option 1b: Direct SQLite Database Queries

If you prefer direct SQLite queries:

```bash
# Query decisions
cd apps/agent_memory
sqlite3 memory.db "SELECT * FROM decisions WHERE content LIKE '%search_term%' LIMIT 10;"

# Query patterns
sqlite3 memory.db "SELECT * FROM patterns WHERE severity='high' LIMIT 10;"

# Full-text search (if FTS enabled)
sqlite3 memory.db "SELECT * FROM decisions_fts WHERE decisions_fts MATCH 'search_term' LIMIT 10;"

# Get recent decisions
sqlite3 memory.db "SELECT * FROM decisions ORDER BY created_at DESC LIMIT 5;"
```

#### Option 2: Python Memory Helper Functions

Use the Python memory module directly:

```python
# In Python environment
from agents.memory import get_memory

memory = get_memory()

# Query decisions
decisions = memory.query_decisions(project="home-server", limit=5)

# Query patterns
patterns = memory.query_patterns(severity="high", limit=5)

# Full-text search
results = memory.search("search query", limit=20)
```

#### Option 3: Read Exported Markdown Files

If markdown exports exist, read them directly:

```bash
# Check for exported memory files
ls agents/memory/memory/export/

# Read exported decisions
cat agents/memory/memory/export/decisions/*.md
```

**Important**: Always try MCP tools first. Use fallback methods only when MCP is unavailable.

## Skills - How to Use

**Location**: `server-management-skills/README.md`

**What Skills Provide:**
- Complete workflows for common tasks
- Step-by-step guidance using MCP tools
- Error handling and best practices

**Available Skills:**
- `standard-deployment` - Complete deployment workflow
- `troubleshoot-container-failure` - Container diagnostics
- `system-health-check` - Comprehensive system verification
- `troubleshoot-stuck-downloads` - Download queue issues
- `deploy-new-service` - New service setup

**How to Use:**
1. Review `server-management-skills/README.md` for skills matching your task
2. Follow the skill's workflow step-by-step
3. Skills automatically use MCP tools correctly

**When to Use Skills vs MCP Tools:**
- **Use Skills**: For complete workflows (deployment, troubleshooting, setup)
- **Use MCP Tools**: For individual operations (check status, restart service)

**Creating New Skills:**
If you identify a reusable workflow pattern:
1. Check existing skills: `query_skills(category="...", search_text="...")`
2. Create skill proposal: `propose_skill(name="...", description="...", ...)`
3. Test the workflow
4. Proposal reviewed and approved
5. Skill added to catalog

**See**: `server-management-skills/CREATING_SKILLS.md` for complete guide.

## Task Coordination - How to Use

**Location**: `agents/tasks/README.md`

**What Task Coordination Provides:**
- Central registry of all tasks across agents
- Dependency tracking and validation
- Conflict prevention
- Cross-agent task visibility

**Available Tools** (6 MCP tools):
- `register_task()` - Register new tasks
- `query_tasks()` - Query with filters (status, assignee, project, priority)
- `get_task()` - Get single task details
- `claim_task()` - Claim tasks (validates dependencies)
- `update_task_status()` - Update status (auto-updates dependents)
- `check_task_dependencies()` - Check dependency status

**When to Use Task Coordination:**
- **Use Central Registry**: For all task coordination, dependencies, conflict prevention
- **Note**: Per-agent `TASKS.md` files are deprecated. Use the central task registry for all task management.

**Basic Workflow:**
```python
# 1. Register a task
task = register_task(
    title="Setup database",
    description="Create PostgreSQL schema",
    project="trading-journal",
    priority="high",
    dependencies="T1.1,T1.2"  # Optional
)

# 2. Check dependencies (if any)
deps = check_task_dependencies(task_id=task["task_id"])

# 3. Claim the task (validates dependencies automatically)
claim_task(task_id=task["task_id"], agent_id="agent-001")

# 4. Update status as work progresses
update_task_status(task_id=task["task_id"], status="in_progress", agent_id="agent-001")
update_task_status(task_id=task["task_id"], status="completed", agent_id="agent-001")

# 5. Query your tasks
my_tasks = query_tasks(assignee="agent-001", status="in_progress")
```

**Dependency Management:**
- Tasks with dependencies cannot be claimed until dependencies are completed
- Tasks automatically block if dependencies not met
- Tasks automatically unblock when dependencies complete
- Use `check_task_dependencies()` to see dependency status

**See**: `agents/tasks/README.md` for complete guide with examples.

## MCP Tools - How to Use

**Location**: `server-management-mcp/README.md`

**What MCP Tools Provide:**
- Individual operations (check status, restart, view logs)
- Type-safe, tested capabilities
- Consistent error handling

**Tool Categories:**
- **Memory Management** (9 tools) - Query and record decisions/patterns/context
- **Docker Management** (8 tools) - Container operations
- **Media Download** (13 tools) - Sonarr/Radarr operations
- **System Monitoring** (5 tools) - Disk, resources, health
- **Git Operations** (4 tools) - Deploy, commit, push, pull
- **Troubleshooting** (3 tools) - Diagnostics
- **Networking** (3 tools) - Ports, VPN, DNS
- **System Utilities** (3 tools) - Cleanup, file management
- **Agent Management** (3 tools) - Create agents, query registry

**How to Use:**
- **If you have MCP access**: Use tools directly via MCP interface (preferred)
- **If no MCP access**: 
  - Reference `server-management-mcp/README.md` for tool documentation
  - For memory operations, use fallback methods (see Memory System section above)
  - For other operations, use SSH commands via `scripts/connect-server.sh`

**See**: `agents/docs/MCP_TOOL_DISCOVERY.md` for tool discovery guide.

## Agent Spawning - How to Create Specialized Agents

### When to Create Specialized Agents

Create a specialized agent if your task requires:
- **Domain expertise** you don't have (e.g., database optimization, security)
- **Specialized knowledge** (e.g., Sonarr/Radarr troubleshooting)
- **Complex workflows** that would benefit from dedicated agent
- **Recurring tasks** that need consistent specialization

### How to Create

**Step 1: Check Registry**
```python
query_agent_registry(specialization="media-download")
```

**Step 2: Create Agent Definition**
```python
create_agent_definition(
    specialization="media-download",
    capabilities="troubleshoot-stuck-downloads skill, sonarr tools, radarr tools",
    initial_tasks="Fix 163 stuck downloads in Sonarr queue. Diagnose issue, remove stuck items, verify queue functionality.",
    parent_agent_id="agent-001"
)
```

**Step 3: Human Activates**
Agent definition created in `agents/registry/agent-definitions/`. Human will activate by opening new Cursor session.

**Step 4: Monitor Progress**
Check:
**Note**: Per-agent `STATUS.md` and `COMMUNICATION.md` files are deprecated. Use:
- Monitoring system for status (`update_agent_status()`)
- Communication protocol for messaging (`send_agent_message()`)

**Available Agent Management Tools:**
- `create_agent_definition` - Create new specialized agent
- `query_agent_registry` - Query for existing agents
- `assign_task_to_agent` - Assign task to existing agent

**See**: 
- `agents/ACTIVATION_GUIDE.md` - Human activation guide
- `agents/docs/AGENT_SPAWNING_ARCHITECTURE.md` - Complete architecture

## Discovery Priority (In Order)

0. **Start Monitoring** → Start session and update status (CRITICAL - do this first!)
1. **Check Messages** → Check for messages from other agents (CRITICAL - do this early!)
2. **Memory** → Query previous decisions and patterns
3. **Specialized Agents** → Check registry, create if needed
4. **Skills** → Review workflows for common tasks
5. **MCP Tools** → Review available operations (PREFERRED - observable!)
6. **Create New** → Only if nothing exists
7. **Scripts** → Fallback option (not observable)
8. **SSH Commands** → Last resort (not observable)

**⚠️ IMPORTANT**: Always use MCP tools when available - they are automatically logged and visible in the agent monitoring dashboard. Custom commands and scripts are NOT observable!

## Workflow Integration

### Before Starting Work

1. ✅ **Start agent monitoring session** - `start_agent_session(agent_id)`
2. ✅ **Update agent status** - `update_agent_status(agent_id, status="active", ...)`
3. ✅ Query memory for related decisions
4. ✅ Check for specialized agents
5. ✅ Review relevant skills
6. ✅ Check available MCP tools (PREFERRED - observable!)
7. ✅ Read task details

### During Work

1. ✅ **Update status regularly** - `update_agent_status()` with progress
2. ✅ **Use MCP tools** - All MCP tool calls are automatically logged
3. ✅ Record important decisions in memory
4. ✅ Record patterns discovered
5. ✅ Update context regularly
6. ✅ Use skills for workflows
7. ✅ Create specialized agents when needed
8. ✅ **Never use custom commands** - Use MCP tools instead (they're observable!)

### After Work

1. ✅ **End agent session** - `end_agent_session(agent_id, session_id, ...)`
2. ✅ **Update final status** - `update_agent_status(status="completed")`
3. ✅ Save final context with status="completed"
4. ✅ Update task status
5. ✅ Document decisions made
6. ✅ Commit and push changes

## Quick Reference

### Memory Tools
- Query: `memory_query_decisions()`, `memory_query_patterns()`, `memory_search()`
- Record: `memory_record_decision()`, `memory_record_pattern()`, `memory_save_context()`

### Agent Management Tools
- Create: `create_agent_definition()` - Create specialized agent
- Query: `query_agent_registry()` - Query agent registry
- Assign: `assign_task_to_agent()` - Assign task to agent
- Archive: `archive_agent()` - Archive agent (lifecycle management)
- Reactivate: `reactivate_agent()` - Reactivate archived agent

### Skill Management Tools
- Propose: `propose_skill()` - Create skill proposal
- List: `list_skill_proposals()` - List proposals
- Query: `query_skills()` - Query existing skills
- Analyze: `analyze_patterns_for_skills()` - Analyze patterns for skill candidates
- Auto-create: `auto_propose_skill_from_pattern()` - Auto-create skill from pattern

### Activity Monitoring Tools (USE THESE FIRST!)
- Start: `start_agent_session(agent_id)` - Start monitoring session
- Update: `update_agent_status(agent_id, status, current_task_id, progress, blockers)` - Update your status
- Get: `get_agent_status(agent_id)` - Check your current status
- End: `end_agent_session(agent_id, session_id, tasks_completed, tools_called, total_duration_ms)` - End session

### Task Coordination Tools
- Register: `register_task()` - Register new task in central registry
- Query: `query_tasks()` - Query tasks with filters
- Get: `get_task()` - Get single task details
- Claim: `claim_task()` - Claim task (validates dependencies)
- Update: `update_task_status()` - Update status (auto-updates dependents)
- Check: `check_task_dependencies()` - Check dependency status

### Communication Tools (NEW!)
- Send: `send_agent_message()` - Send message to another agent
- Get: `get_agent_messages()` - Get messages for you (with filters)
- Acknowledge: `acknowledge_message()` - Acknowledge receipt
- Resolve: `mark_message_resolved()` - Mark message as resolved
- Query: `query_messages()` - Query messages with multiple filters

### Key Files
- **Agent Monitoring**: `apps/agent-monitoring/README.md` ⭐ **See this for monitoring dashboard**
- **Monitoring Integration**: `apps/agent-monitoring/INTEGRATION_GUIDE.md` ⭐ **See this for how to be observed**
- **Communication**: `agents/communication/README.md` ⭐ **See this for agent communication**
- **Communication Protocol**: `agents/communication/protocol.md` ⭐ **See this for protocol specification**
- Skills: `server-management-skills/README.md`
- MCP Tools: `server-management-mcp/README.md`
- Task Coordination: `agents/tasks/README.md` ⭐ **See this for task management**
- Memory Guide: `agents/memory/MCP_TOOLS_GUIDE.md`
- Memory Examples: `agents/memory/MEMORY_USAGE_EXAMPLES.md` ⭐ **See this for real-world examples**
- Tool Discovery: `agents/docs/MCP_TOOL_DISCOVERY.md`

## Important Principles

0. **Be Observable** - Always use activity monitoring tools so your work is visible
1. **Check Messages** - Check for messages from other agents at start of session
2. **Memory First** - Always query memory before making decisions
3. **Use What Exists** - Skills and tools are your primary knowledge base
4. **Don't Reinvent** - Use existing workflows and operations
5. **Record Everything** - Document decisions and patterns in memory
6. **Delegate When Needed** - Create specialized agents for domain expertise
7. **Communicate Effectively** - Use communication protocol for coordination and help
8. **Use MCP Tools** - Always prefer MCP tools over custom commands (they're observable!)

## Decision Framework: When to Store, Create, or Add

**CRITICAL**: Follow this framework for all work:

### Store in Memory (Always)
- ✅ **Important decisions** - Technology choices, architecture decisions, configuration choices
- ✅ **Patterns discovered** - Common issues and their solutions
- ✅ **Context updates** - Current work status, progress, blockers
- ✅ **Rationale** - Why decisions were made (for future reference)

**When**: After making any important decision or discovering a pattern
**How**: Use `memory_record_decision()` or `memory_record_pattern()`

### Create a Skill (Reusable Workflows)
- ✅ **Multi-step workflows** - Complete processes that combine multiple operations
- ✅ **Tested procedures** - Workflows that have been validated and work reliably
- ✅ **Common tasks** - Operations that will be needed again in the future
- ✅ **Error handling** - Workflows that include troubleshooting steps

**When**: After completing a workflow that you anticipate needing again
**How**: Create a skill in `server-management-skills/` following the skill template

**Examples**:
- Deployment workflows → `standard-deployment` skill
- Troubleshooting procedures → `troubleshoot-container-failure` skill
- Setup procedures → `deploy-new-service` skill

### Add MCP Tool (Reusable Operations)
- ✅ **Single operations** - Individual actions that can be reused
- ✅ **Type-safe operations** - Operations that benefit from validation
- ✅ **Server operations** - Any operation that needs to run on the server
- ✅ **Frequently needed** - Operations you'll use multiple times

**When**: After identifying an operation that should be standardized and reusable
**How**: Add tool to `server-management-mcp/tools/` and update `server-management-mcp/README.md`

**Examples**:
- Container management → `docker_restart_container`, `docker_container_status`
- System checks → `check_disk_space`, `check_port_status`
- Git operations → `git_deploy`, `git_status`

### Decision Tree

```
After completing work:
│
├─→ Important decision made?
│   └─→ YES: Store in memory (memory_record_decision)
│
├─→ Discovered a pattern/issue?
│   └─→ YES: Store in memory (memory_record_pattern)
│
├─→ Created a reusable workflow?
│   └─→ YES: Create skill (server-management-skills/)
│
└─→ Identified a reusable operation?
    └─→ YES: Add MCP tool (server-management-mcp/tools/)
```

**Remember**: 
- **Memory** = Knowledge (what was decided, what patterns exist)
- **Skills** = Workflows (how to do complete tasks)
- **MCP Tools** = Operations (what you can do)

## Common Operations → Tools Mapping

### "Deploy changes and restart services"
→ Use: **`standard-deployment` skill**

### "Troubleshoot container failure"
→ Use: **`troubleshoot-container-failure` skill**

### "Check system health"
→ Use: **`system-health-check` skill**

### "Fix stuck downloads"
→ Use: **`troubleshoot-stuck-downloads` skill**

### "Check container status"
→ Use: `docker_container_status(container_name)`

### "Restart service"
→ Use: `docker_restart_container(container_name)`

### "Query previous decisions"
→ Use: `memory_query_decisions(project="home-server", search_text="deployment", limit=5)`
**Example**: Before deploying a new service, check what was decided about similar deployments.

### "Create specialized agent"
→ Use: `create_agent_definition(specialization="...", capabilities="...", initial_tasks="...")`

---

**Last Updated**: 2025-01-10
**Version**: 1.0
**Status**: Active

