# Communication Channel Guidelines

**Clear guidelines for when to use which communication/coordination channel.**

## Overview

The agent system provides multiple channels for coordination and communication. This document clarifies when to use each channel to avoid confusion and duplication.

## Available Channels

### 1. Task Coordination (`agents/tasks/`)

**Purpose**: Centralized task assignment, tracking, and dependency management.

**When to Use**:
- ✅ **Task Assignment** - Assigning tasks to agents
- ✅ **Task Tracking** - Tracking task status across agents
- ✅ **Dependency Management** - Managing task dependencies
- ✅ **Cross-Agent Coordination** - Coordinating work between agents
- ✅ **Conflict Prevention** - Preventing multiple agents from working on the same task

**MCP Tools**:
- `register_task()` - Register new task
- `query_tasks()` - Query tasks with filters
- `get_task()` - Get single task details
- `claim_task()` - Claim task (validates dependencies)
- `update_task_status()` - Update status (auto-updates dependents)
- `check_task_dependencies()` - Check dependency status

**Example**:
```python
# Register a task
register_task(
    title="Setup database",
    description="Create PostgreSQL schema",
    project="home-server",
    priority="high",
    dependencies="T1.1"  # Depends on task T1.1
)

# Claim a task
claim_task(task_id="T1.2", agent_id="agent-001")

# Update status
update_task_status(
    task_id="T1.2",
    status="in_progress",
    agent_id="agent-001"
)
```

**See**: `agents/tasks/README.md` for complete guide.

---

### 2. Agent Communication Protocol (`agents/communication/`)

**Purpose**: Structured messaging between agents (requests, responses, notifications, escalations).

**When to Use**:
- ✅ **Request Help** - Asking another agent for help or information
- ✅ **Respond to Requests** - Replying to requests from other agents
- ✅ **Share Information** - Notifying other agents about findings or updates
- ✅ **Escalate Issues** - Escalating critical issues requiring immediate attention
- ✅ **Coordination** - Coordinating on shared work or handoffs

**MCP Tools**:
- `send_agent_message()` - Send message to another agent
- `get_agent_messages()` - Get messages for you (with filters)
- `acknowledge_message()` - Acknowledge receipt
- `mark_message_resolved()` - Mark message as resolved
- `query_messages()` - Query messages with multiple filters

**Message Types**:
- **Request** - Ask for help/information (requires response)
- **Response** - Reply to a request
- **Notification** - Informational (no response needed)
- **Escalation** - Critical issue (immediate attention)

**Example**:
```python
# Send a request for help
send_agent_message(
    from_agent="agent-001",
    to_agent="agent-002",
    type="request",
    priority="high",
    subject="Need help with Docker deployment",
    content="I'm stuck on deploying service X. Can you help?",
    related_task_id="T1.5"
)

# Check for messages
messages = get_agent_messages(agent_id="agent-002", status="pending")

# Respond to a message
send_agent_message(
    from_agent="agent-002",
    to_agent="agent-001",
    type="response",
    priority="medium",
    subject="Re: Need help with Docker deployment",
    content="Here's the solution: [your response]",
    related_message_id="MSG-2025-01-13-001"
)
```

**See**: `agents/communication/README.md` for complete guide.

---

### 3. Memory System (`agents/memory/`)

**Purpose**: Persistent storage for decisions, patterns, and context sharing.

**When to Use**:
- ✅ **Record Decisions** - Storing important decisions and rationale
- ✅ **Record Patterns** - Storing common issues and solutions
- ✅ **Save Context** - Saving current work context
- ✅ **Query Past Work** - Learning from previous decisions and patterns
- ✅ **Knowledge Sharing** - Sharing knowledge across agents

**MCP Tools**:
- `memory_query_decisions()` - Query decisions
- `memory_query_patterns()` - Query patterns
- `memory_search()` - Full-text search
- `memory_record_decision()` - Record decision
- `memory_record_pattern()` - Record pattern
- `memory_save_context()` - Save context
- `memory_get_recent_context()` - Get recent context
- `memory_get_context_by_task()` - Get task context
- `memory_export_to_markdown()` - Export to markdown

**Example**:
```python
# Record a decision
memory_record_decision(
    content="Use PostgreSQL for database",
    rationale="Need ACID compliance and concurrent writes",
    project="home-server",
    importance=0.9,
    tags="database,architecture"
)

# Query related decisions
decisions = memory_query_decisions(
    project="home-server",
    search_text="database",
    limit=5
)

# Record a pattern
memory_record_pattern(
    name="Port Conflict Resolution",
    description="Services failing due to port conflicts",
    solution="Always check port availability first using get_available_port MCP tool",
    severity="medium",
    tags="docker,networking,ports"
)
```

**See**: `agents/memory/README.md` for complete guide.

---

### 4. Monitoring System (`apps/agent-monitoring/`)

**Purpose**: Real-time visibility into agent activity, status, and progress.

**When to Use**:
- ✅ **Status Updates** - Updating your current status
- ✅ **Activity Logging** - All MCP tools are automatically logged
- ✅ **Progress Tracking** - Tracking progress on tasks
- ✅ **Visibility** - Making your work visible to others
- ✅ **Session Management** - Starting and ending agent sessions

**MCP Tools**:
- `start_agent_session()` - Start monitoring session
- `update_agent_status()` - Update agent status
- `get_agent_status()` - Get current status
- `end_agent_session()` - End session

**Example**:
```python
# Start session (do this first!)
start_agent_session(agent_id="agent-001")

# Update status regularly
update_agent_status(
    agent_id="agent-001",
    status="active",
    current_task_id="T1.2",
    progress="Setting up database schema",
    blockers="None"
)

# End session when done
end_agent_session(
    agent_id="agent-001",
    session_id=session_id,
    tasks_completed=1,
    tools_called=15
)
```

**See**: `apps/agent-monitoring/README.md` for complete guide.

---

### 5. Agent Registry (`agents/registry/`)

**Purpose**: Agent discovery and management.

**When to Use**:
- ✅ **Agent Discovery** - Finding agents with specific specializations
- ✅ **Agent Creation** - Creating new specialized agents
- ✅ **Agent Management** - Archiving/reactivating agents
- ✅ **Registry Queries** - Querying agent registry

**MCP Tools**:
- `create_agent_definition()` - Create new agent
- `query_agent_registry()` - Query registry
- `assign_task_to_agent()` - Assign task to agent
- `archive_agent()` - Archive agent
- `reactivate_agent()` - Reactivate archived agent
- `sync_agent_registry()` - Sync registry from DB

**Example**:
```python
# Query for existing agents
agents = query_agent_registry(specialization="database")

# Create new agent
create_agent_definition(
    specialization="database-management",
    capabilities="PostgreSQL, migrations, optimization",
    initial_tasks="Setup database schema",
    parent_agent_id="agent-001"
)

# Assign task to existing agent
assign_task_to_agent(
    agent_id="agent-002",
    task_description="Optimize database queries",
    priority="high"
)
```

**See**: `agents/registry/agent-registry.md` for registry.

---

## Decision Tree

**Which channel should I use?**

```
Need to coordinate with other agents?
│
├─→ Task Assignment/Tracking?
│   └─→ Use Task Coordination (agents/tasks/)
│       └─→ register_task(), claim_task(), update_task_status()
│
├─→ Agent-to-Agent Messaging?
│   └─→ Use Communication Protocol (agents/communication/)
│       └─→ send_agent_message(), get_agent_messages()
│
├─→ Knowledge/Context Sharing?
│   └─→ Use Memory System (agents/memory/)
│       └─→ memory_record_decision(), memory_query_patterns()
│
├─→ Status/Activity Visibility?
│   └─→ Use Monitoring System (apps/agent-monitoring/)
│       └─→ update_agent_status(), start_agent_session()
│
└─→ Agent Discovery/Management?
    └─→ Use Agent Registry (agents/registry/)
        └─→ query_agent_registry(), create_agent_definition()
```

---

## Common Scenarios

### Scenario 1: Starting a New Task

**Use**:
1. **Monitoring System** - `start_agent_session()` and `update_agent_status()`
2. **Task Coordination** - `claim_task()` or `register_task()`
3. **Memory System** - `memory_query_decisions()` to learn from past work

**Don't Use**:
- Per-agent `TASKS.md` (use task coordination instead)
- Per-agent `STATUS.md` (use monitoring system instead)

### Scenario 2: Need Help from Another Agent

**Use**:
1. **Communication Protocol** - `send_agent_message()` with type="request"
2. **Task Coordination** - Reference related task if applicable

**Don't Use**:
- Per-agent `COMMUNICATION.md` (use communication protocol instead)

### Scenario 3: Discovered a Pattern or Made a Decision

**Use**:
1. **Memory System** - `memory_record_pattern()` or `memory_record_decision()`

**Don't Use**:
- Task coordination (not for knowledge storage)
- Communication protocol (not for knowledge sharing)

### Scenario 4: Completed a Task

**Use**:
1. **Task Coordination** - `update_task_status(status="completed")`
2. **Monitoring System** - `update_agent_status()` with progress
3. **Memory System** - `memory_save_context(status="completed")`

**Don't Use**:
- Per-agent `TASKS.md` (use task coordination instead)

---

## Deprecated/Simplified Channels

### Per-Agent Files

**Status**: Deprecated in favor of centralized systems

**Old Approach**:
- `agents/active/{agent-id}/TASKS.md` - Per-agent task list
- `agents/active/{agent-id}/COMMUNICATION.md` - Parent-child communication
- `agents/active/{agent-id}/STATUS.md` - Per-agent status

**New Approach**:
- **Tasks** → Use task coordination registry (`agents/tasks/registry.md`)
- **Communication** → Use communication protocol (`agents/communication/`)
- **Status** → Use monitoring system (`apps/agent-monitoring/`)

**When to Keep Per-Agent Files**:
- Agent-specific notes/work (not for coordination)
- Human-readable summaries (can be auto-generated from systems)

---

## Best Practices

### 1. Use the Right Channel

- **Task work** → Task coordination
- **Agent messaging** → Communication protocol
- **Knowledge sharing** → Memory system
- **Status updates** → Monitoring system

### 2. Avoid Duplication

- Don't store the same information in multiple places
- Use the primary channel for each type of information
- Reference other channels when needed, don't duplicate

### 3. Check Early

- Check messages at the start of your session
- Check memory before starting work
- Check task registry for available tasks

### 4. Update Regularly

- Update status regularly (monitoring system)
- Update task status as you progress (task coordination)
- Record decisions and patterns (memory system)

### 5. Use MCP Tools

- Always use MCP tools when available (they're observable)
- Custom commands/scripts are NOT observable (avoid when possible)

---

## Quick Reference

| Need | Channel | MCP Tool |
|------|---------|----------|
| Assign task | Task Coordination | `register_task()` |
| Claim task | Task Coordination | `claim_task()` |
| Update task status | Task Coordination | `update_task_status()` |
| Send message | Communication Protocol | `send_agent_message()` |
| Check messages | Communication Protocol | `get_agent_messages()` |
| Record decision | Memory System | `memory_record_decision()` |
| Query patterns | Memory System | `memory_query_patterns()` |
| Update status | Monitoring System | `update_agent_status()` |
| Start session | Monitoring System | `start_agent_session()` |
| Find agent | Agent Registry | `query_agent_registry()` |
| Create agent | Agent Registry | `create_agent_definition()` |

---

**Last Updated**: 2025-01-13  
**Status**: Active  
**See Also**:
- `agents/docs/SYSTEM_ARCHITECTURE.md` - System architecture overview
- `agents/tasks/README.md` - Task coordination guide
- `agents/communication/README.md` - Communication protocol guide
- `agents/memory/README.md` - Memory system guide
- `apps/agent-monitoring/README.md` - Monitoring system guide

