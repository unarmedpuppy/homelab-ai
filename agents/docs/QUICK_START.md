# Agent Quick Start Guide

**5-minute guide to get started as an agent on the home server project.**

## 🚀 Essential Steps (Do These First!)

### Step 0: Start Monitoring (30 seconds)

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

1. **`AGENT_PROMPT.md`** ⭐ - Complete agent prompt (read this for full details)
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

1. Read **`AGENT_PROMPT.md`** for complete details
2. Review **`AGENT_WORKFLOW.md`** for detailed workflows
3. Explore **`MCP_TOOL_DISCOVERY.md`** for tool discovery

---

**See**: `agents/docs/README.md` for complete documentation index

