# Agent Prompt - Complete Guide

## 🚀 Start Here: Discovery Workflow

**Before doing ANYTHING, follow this discovery workflow in order:**

### 1. Check Memory First ⚡
Query previous decisions and patterns to learn from past work:

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

**Why**: Don't repeat past decisions. Learn from what worked before.

### 2. Check for Specialized Agents 🤖
If your task requires domain expertise:

```python
# Check if specialized agent exists
query_agent_registry(specialization="media-download")

# If found: Assign task to existing agent
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

**49 Tools Available:**
- Memory management (9 tools)
- Docker management (8 tools)
- Media download (13 tools)
- System monitoring (5 tools)
- Git operations (4 tools)
- Troubleshooting (3 tools)
- Networking (3 tools)
- System utilities (3 tools)
- Agent management (3 tools)

**Why**: Use standardized tools. Don't write custom commands.

## Memory System - How to Use

### Before Starting Work

```python
# Query previous decisions
memory_query_decisions(project="home-server", limit=5)

# Query patterns
memory_query_patterns(severity="high", limit=5)

# Full-text search
memory_search("PostgreSQL database")
```

### During Work

```python
# Record important decisions
memory_record_decision(
    content="Use PostgreSQL for database",
    rationale="Need ACID compliance",
    project="home-server",
    importance=0.9,
    tags="database,architecture"
)

# Record patterns
memory_record_pattern(
    name="Port Conflict Resolution",
    description="Services failing due to port conflicts",
    solution="Always check port availability first",
    severity="medium",
    tags="docker,networking"
)

# Update context
memory_save_context(
    agent_id="agent-001",
    task="T1.3",
    current_work="PostgreSQL setup in progress...",
    status="in_progress"
)
```

### After Work

```python
# Save final context
memory_save_context(
    agent_id="agent-001",
    task="T1.3",
    current_work="PostgreSQL setup complete",
    status="completed"
)
```

**Available Memory Tools (9):**
- Query: `memory_query_decisions`, `memory_query_patterns`, `memory_search`, `memory_get_recent_context`, `memory_get_context_by_task`
- Record: `memory_record_decision`, `memory_record_pattern`, `memory_save_context`
- Export: `memory_export_to_markdown`

**See**: `apps/agent_memory/MCP_TOOLS_GUIDE.md` for complete reference.

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
- If you have MCP access: Use tools directly via MCP interface
- If no MCP access: Reference `server-management-mcp/README.md` for tool documentation

**See**: `apps/docs/MCP_TOOL_DISCOVERY.md` for tool discovery guide.

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
- `agents/active/agent-XXX-[specialization]/STATUS.md`
- `agents/active/agent-XXX-[specialization]/COMMUNICATION.md`

**Available Agent Management Tools:**
- `create_agent_definition` - Create new specialized agent
- `query_agent_registry` - Query for existing agents
- `assign_task_to_agent` - Assign task to existing agent

**See**: 
- `agents/ACTIVATION_GUIDE.md` - Human activation guide
- `apps/docs/AGENT_SPAWNING_ARCHITECTURE.md` - Complete architecture

## Discovery Priority (In Order)

1. **Memory** → Query previous decisions and patterns
2. **Specialized Agents** → Check registry, create if needed
3. **Skills** → Review workflows for common tasks
4. **MCP Tools** → Review available operations
5. **Create New** → Only if nothing exists
6. **Scripts** → Fallback option
7. **SSH Commands** → Last resort

## Workflow Integration

### Before Starting Work

1. ✅ Query memory for related decisions
2. ✅ Check for specialized agents
3. ✅ Review relevant skills
4. ✅ Check available MCP tools
5. ✅ Read task details

### During Work

1. ✅ Record important decisions in memory
2. ✅ Record patterns discovered
3. ✅ Update context regularly
4. ✅ Use skills for workflows
5. ✅ Use MCP tools for operations
6. ✅ Create specialized agents when needed

### After Work

1. ✅ Save final context with status="completed"
2. ✅ Update task status
3. ✅ Document decisions made
4. ✅ Commit and push changes

## Quick Reference

### Memory Tools
- Query: `memory_query_decisions()`, `memory_query_patterns()`, `memory_search()`
- Record: `memory_record_decision()`, `memory_record_pattern()`, `memory_save_context()`

### Agent Management Tools
- Create: `create_agent_definition()`
- Query: `query_agent_registry()`
- Assign: `assign_task_to_agent()`

### Key Files
- Skills: `server-management-skills/README.md`
- MCP Tools: `server-management-mcp/README.md`
- Memory Guide: `apps/agent_memory/MCP_TOOLS_GUIDE.md`
- Tool Discovery: `apps/docs/MCP_TOOL_DISCOVERY.md`

## Important Principles

1. **Memory First** - Always query memory before making decisions
2. **Use What Exists** - Skills and tools are your primary knowledge base
3. **Don't Reinvent** - Use existing workflows and operations
4. **Record Everything** - Document decisions and patterns in memory
5. **Delegate When Needed** - Create specialized agents for domain expertise

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
→ Use: `memory_query_decisions(project="home-server")`

### "Create specialized agent"
→ Use: `create_agent_definition(specialization="...", capabilities="...", initial_tasks="...")`

---

**Last Updated**: 2025-01-10
**Version**: 1.0
**Status**: Active

