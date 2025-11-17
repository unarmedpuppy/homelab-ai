# Agent System Architecture

**Unified architecture documentation for the agent system.**

## Overview

The agent system provides a comprehensive framework for AI agents to work collaboratively on the home server project. It includes memory, task coordination, communication, monitoring, and agent management capabilities.

## Core Components

### 1. Agent Monitoring System

**Location**: `agents/apps/agent-monitoring/`

**Purpose**: Real-time visibility into agent activity, status, and progress.

**Components**:
- **SQLite Database** (`agents/apps/agent-monitoring/data/agent_activity.db`) - Stores agent status, sessions, and actions
- **Backend API** (Node.js/Express/TypeScript) - REST API for querying agent data
- **Frontend Dashboard** (Next.js/TypeScript) - Real-time agent status dashboard
- **Grafana Integration** - Time-series metrics and visualizations
- **InfluxDB** - Metrics storage for Grafana

**MCP Tools** (4 tools):
- `start_agent_session()` - Start monitoring session
- `update_agent_status()` - Update agent status
- `get_agent_status()` - Get current status
- `end_agent_session()` - End session

**See**: `agents/apps/agent-monitoring/README.md` for complete documentation.

---

### 2. Memory System

**Location**: `agents/memory/`

**Purpose**: Persistent storage for decisions, patterns, and context.

**Components**:
- **SQLite Database** (`agents/memory/memory.db`) - Primary storage (fast queries)
- **Markdown Exports** (`agents/memory/memory/export/`) - Human-readable exports
- **Python API** (`agents/memory/sqlite_memory.py`) - Memory operations

**MCP Tools** (9 tools):
- `memory_query_decisions()` - Query decisions
- `memory_query_patterns()` - Query patterns
- `memory_search()` - Full-text search
- `memory_record_decision()` - Record decision
- `memory_record_pattern()` - Record pattern
- `memory_save_context()` - Save context
- `memory_get_recent_context()` - Get recent context
- `memory_get_context_by_task()` - Get task context
- `memory_export_to_markdown()` - Export to markdown

**See**: `agents/memory/README.md` for complete documentation.

---

### 3. Task Coordination System

**Location**: `agents/tasks/`

**Purpose**: Centralized task registry for cross-agent coordination.

**Components**:
- **Task Registry** (`agents/tasks/registry.md`) - Markdown table of all tasks
- **MCP Tools** - Task management operations

**MCP Tools** (6 tools):
- `register_task()` - Register new task
- `query_tasks()` - Query tasks with filters
- `get_task()` - Get single task details
- `claim_task()` - Claim task (validates dependencies)
- `update_task_status()` - Update status (auto-updates dependents)
- `check_task_dependencies()` - Check dependency status

**See**: `agents/tasks/README.md` for complete documentation.

---

### 4. Agent Communication Protocol

**Location**: `agents/communication/`

**Purpose**: Structured messaging between agents.

**Components**:
- **Message Files** (`agents/communication/messages/*.md`) - Individual message files
- **Message Index** (`agents/communication/messages/index.json`) - Message index
- **Protocol Specification** (`agents/communication/protocol.md`) - Protocol definition

**MCP Tools** (5 tools):
- `send_agent_message()` - Send message
- `get_agent_messages()` - Get messages (with filters)
- `acknowledge_message()` - Acknowledge receipt
- `mark_message_resolved()` - Mark as resolved
- `query_messages()` - Query messages

**Message Types**:
- **Request** - Ask for help/information (requires response)
- **Response** - Reply to a request
- **Notification** - Informational (no response needed)
- **Escalation** - Critical issue (immediate attention)

**See**: `agents/communication/README.md` for complete documentation.

---

### 5. Agent Registry & Management

**Location**: `agents/registry/`

**Purpose**: Track and manage agent definitions, status, and lifecycle.

**Components**:
- **Agent Registry** (`agents/registry/agent-registry.md`) - Master registry (auto-generated from DB)
- **Agent Definitions** (`agents/registry/agent-definitions/*.md`) - Agent definition files
- **Agent Templates** (`agents/registry/agent-templates/*.md`) - Templates for creating agents
- **Sync Script** (`agents/registry/sync_registry.py`) - Generates registry from monitoring DB

**MCP Tools** (6 tools):
- `create_agent_definition()` - Create new agent
- `query_agent_registry()` - Query registry
- `assign_task_to_agent()` - Assign task to agent
- `archive_agent()` - Archive agent
- `reactivate_agent()` - Reactivate archived agent
- `sync_agent_registry()` - Sync registry from DB

**Agent States**:
- **Ready** - Definition exists, not yet activated
- **Active** - Currently working on tasks
- **Idle** - Completed tasks, ready for new work
- **Archived** - Moved to archive

**See**: `agents/registry/agent-registry.md` for registry and `agents/lifecycle/policy.md` for lifecycle policy.

---

### 6. Skill Management

**Location**: `agents/skills/`

**Purpose**: Reusable workflows for common tasks.

**Components**:
- **Skills Catalog** (`agents/skills/README.md`) - List of available skills
- **Skill Definitions** (`agents/skills/*/SKILL.md`) - Individual skill definitions
- **Skill Proposals** (`agents/skills/proposals/`) - Proposed skills awaiting review

**MCP Tools** (5 tools):
- `propose_skill()` - Propose new skill
- `list_skill_proposals()` - List proposals
- `query_skills()` - Query existing skills
- `analyze_patterns_for_skills()` - Analyze patterns for skill candidates
- `auto_propose_skill_from_pattern()` - Auto-create skill from pattern

**See**: `agents/skills/README.md` for complete documentation.

---

## Data Flow

### Agent Status Flow

```
Agent Action
    ↓
update_agent_status() MCP Tool
    ↓
Monitoring DB (agent_status table)
    ↓
sync_registry.py (auto-generates)
    ↓
agent-registry.md (read-only view)
```

**Source of Truth**: Monitoring DB  
**Human-Readable View**: Registry markdown (auto-generated)

### Task Flow

```
Agent Registers Task
    ↓
register_task() MCP Tool
    ↓
tasks/registry.md (markdown table)
    ↓
Agent Claims Task
    ↓
claim_task() MCP Tool
    ↓
Updates registry.md
    ↓
Agent Updates Status
    ↓
update_task_status() MCP Tool
    ↓
Updates registry.md + auto-unblocks dependents
```

**Source of Truth**: `tasks/registry.md` (markdown)

### Memory Flow

```
Agent Records Decision
    ↓
memory_record_decision() MCP Tool
    ↓
SQLite Database (memory.db)
    ↓
(Optional) Export to Markdown
    ↓
memory/export/decisions/*.md
```

**Source of Truth**: SQLite Database  
**Human-Readable View**: Markdown exports (optional)

### Communication Flow

```
Agent Sends Message
    ↓
send_agent_message() MCP Tool
    ↓
agents/communication/messages/*.md (message file)
    ↓
index.json (updated)
    ↓
Recipient Checks Messages
    ↓
get_agent_messages() MCP Tool
    ↓
Returns pending messages
```

**Source of Truth**: Message markdown files + index.json

---

## System Integration

### MCP Server

**Location**: `agents/apps/agent-mcp/`

**Purpose**: Unified interface for all agent operations.

**Tool Count**: Dynamic based on enabled categories. Use `list_tool_categories()` MCP tool to get current count.

**Tool Categories**:
- **Core** (default enabled): Infrastructure, Activity Monitoring, Communication
- **Docker** (default enabled): Container and compose management
- **Monitoring** (default enabled): System health, resources, service monitoring
- **Memory** (default enabled): Decision and pattern storage
- **Agents** (default enabled): Agent creation, registry, lifecycle
- **Tasks** (default enabled): Task registry and coordination
- **Skills** (default enabled): Skill library and activation
- **Media** (optional): Sonarr, Radarr, download client management
- **Git** (optional): Repository management and deployment
- **Networking** (optional): Network, VPN, DNS, port management
- **Dev** (optional): Dev docs, quality checks, code review
- **Learning** (optional): Agent learning, critiquing, evaluation
- **Productivity** (optional): Personal productivity tools

**See**: 
- `agents/apps/agent-mcp/README.md` - Complete tool catalog
- `agents/apps/agent-mcp/MCP_TOOLS_REFERENCE.md` - Tool count reference
- Use `list_tool_categories()` MCP tool - Get current tool count dynamically

---

## Communication Channels

### When to Use Which Channel

**Decision Tree**:

```
Need to coordinate with other agents?
│
├─→ Task Assignment/Tracking?
│   └─→ Use Task Coordination (agents/tasks/)
│
├─→ Agent-to-Agent Messaging?
│   └─→ Use Communication Protocol (agents/communication/)
│
├─→ Knowledge/Context Sharing?
│   └─→ Use Memory System (agents/memory/)
│
└─→ Status/Activity Visibility?
    └─→ Use Monitoring System (agents/apps/agent-monitoring/)
```

**Primary Channels**:
1. **Task Coordination** - For task assignment, tracking, dependencies
2. **Communication Protocol** - For agent-to-agent messaging
3. **Memory System** - For knowledge, decisions, patterns, context
4. **Monitoring System** - For status, activity, progress

**Deprecated/Removed**:
- ❌ Per-agent `TASKS.md` → **REMOVED** - Use Task Coordination System (`agents/tasks/registry.md`)
- ❌ Per-agent `COMMUNICATION.md` → **REMOVED** - Use Communication Protocol (`agents/communication/`)
- ❌ Per-agent `STATUS.md` → **REMOVED** - Use Monitoring System (dashboard at `localhost:3012`)

**See**: `agents/docs/COMMUNICATION_GUIDELINES.md` for detailed usage guidelines.

---

## File Structure

```
agents/
├── README.md                # Main entry point and navigation
├── ACTIVATION_GUIDE.md      # How to activate agents (for humans)
│
├── prompts/                 # Agent prompts (identity, role, workflow)
│   ├── base.md             # Core agent prompt ⭐ START HERE
│   ├── server.md           # Server management extension
│   └── README.md           # Prompt system overview
│
├── docs/                    # Agent documentation
│   ├── QUICK_START.md      # Instructions for using prompts/base.md
│   ├── SYSTEM_ARCHITECTURE.md # This file - comprehensive source of truth
│   ├── AGENT_WORKFLOW.md   # Detailed workflow guide
│   ├── WORKFLOW_GENERATOR_PROMPT.md # Meta-prompt for generating workflows
│   ├── COMMUNICATION_GUIDELINES.md # Communication channel usage
│   ├── MCP_TOOL_DISCOVERY.md # How to discover and use tools
│   └── archive/            # Archived proposals/plans
│
├── apps/                    # Agent applications (run locally)
│   ├── agent-mcp/          # MCP server (all tools)
│   │   ├── server.py       # Main MCP server
│   │   ├── tools/          # All MCP tools
│   │   ├── README.md       # Tool catalog
│   │   └── MCP_TOOLS_REFERENCE.md # Tool count reference
│   │
│   └── agent-monitoring/    # Monitoring dashboard (local-first)
│       ├── backend/        # Node.js API (localhost:3001)
│       ├── frontend/       # Next.js dashboard (localhost:3012)
│       ├── docker-compose.yml # Local infrastructure
│       └── README.md       # Monitoring guide
│
├── memory/                  # Memory system (SQLite-based, local)
│   ├── sqlite_memory.py    # Memory implementation
│   ├── memory.db           # SQLite database (local)
│   └── README.md           # Memory system overview
│
├── tasks/                   # Task coordination
│   ├── registry.md         # Central task registry (source of truth)
│   └── README.md           # Task coordination guide
│
├── communication/           # Agent communication
│   ├── protocol.md         # Protocol specification
│   ├── messages/           # Message files
│   └── README.md           # Communication guide
│
├── registry/                # Agent registry
│   ├── agent-registry.md   # Master registry (auto-generated)
│   ├── agent-definitions/  # Agent definition files
│   ├── agent-templates/     # Agent templates
│   └── sync_registry.py    # Registry sync script
│
├── skills/                  # Reusable workflow skills
│   ├── README.md           # Skills catalog
│   └── [skill-name]/        # Individual skills
│
├── scripts/                 # Utility scripts
│   └── start-agent-infrastructure.sh # Start monitoring locally
│
├── active/                  # Active agent directories
│   └── agent-XXX/          # Agent-specific documentation
│       └── docs/            # Agent-specific docs (plans, notes, etc.)
│
├── archive/                 # Archived agents and state
│   └── state/               # Archived state files
│
└── lifecycle/               # Lifecycle policies
    ├── policy.md            # Lifecycle management
    └── pattern_learning.md  # Pattern learning system
```

**Note**: Per-agent `TASKS.md`, `COMMUNICATION.md`, and `STATUS.md` files are **removed**. Use centralized systems instead.

---

## Key Principles

### Single Source of Truth

- **Agent Status**: Monitoring DB (auto-generates registry markdown)
- **Tasks**: Task Coordination System (`agents/tasks/registry.md`) - **ONLY** source for task tracking
- **Memory**: SQLite database (optional markdown exports)
- **Messages**: Communication Protocol (`agents/communication/messages/`) - **ONLY** source for agent messaging
- **Agent Definitions**: Registry (`agents/registry/agent-registry.md`)

**Removed**: Per-agent `TASKS.md`, `COMMUNICATION.md`, `STATUS.md` files are no longer created or used.

### Human Readability

- All data stored in markdown where possible
- SQLite used for fast queries, markdown for human review
- Auto-generated views from databases

### Observability

- **All MCP tools are automatically logged** - Use MCP tools for all operations
- Monitoring dashboard provides real-time visibility (`localhost:3012`)
- Custom commands/scripts are **NOT observable** - Avoid when possible
- Always start monitoring session before work: `start_agent_session()`

### Consistency

- Use MCP tools for all operations (when available)
- Follow established patterns and workflows
- Document decisions in memory system
- Use centralized systems (Task Coordination, Communication Protocol) - not per-agent files

## Agent Workflow

### Standard Agent Startup Sequence

1. **Start Infrastructure** (if not running):
   ```python
   await start_agent_infrastructure()
   ```

2. **Start Monitoring Session**:
   ```python
   start_agent_session(agent_id="agent-001")
   update_agent_status(agent_id="agent-001", status="active", ...)
   ```

3. **Check Messages**:
   ```python
   messages = await get_agent_messages(agent_id="agent-001", status="pending")
   ```

4. **Check Memory**:
   ```python
   memory_query_decisions(project="home-server", limit=5)
   memory_query_patterns(severity="high", limit=5)
   ```

5. **Check Skills**:
   - Review `agents/skills/README.md`

6. **Check Available Tasks**:
   ```python
   tasks = query_tasks(status="pending", project="home-server")
   ```

7. **Start Work**:
   - Claim task: `claim_task(task_id="T1.1", agent_id="agent-001")`
   - Update status: `update_task_status(task_id="T1.1", status="in_progress", ...)`

8. **End Session**:
   ```python
   end_agent_session(agent_id="agent-001", session_id=..., ...)
   ```

**See**: `agents/prompts/base.md` for complete discovery workflow.

---

## Related Documentation

### Getting Started
- **`agents/docs/QUICK_START.md`** - Instructions for using `prompts/base.md`
- **`agents/prompts/base.md`** - Complete agent prompt with discovery workflow
- **`agents/README.md`** - Main entry point and navigation

### Detailed Guides
- **`agents/docs/AGENT_WORKFLOW.md`** - Detailed workflow guide
- **`agents/docs/MCP_TOOL_DISCOVERY.md`** - How to discover and use tools
- **`agents/docs/COMMUNICATION_GUIDELINES.md`** - Communication channel usage
- **`agents/docs/DATA_MODEL.md`** - Data model and storage structure

### System Components
- **`agents/memory/README.md`** - Memory system documentation
- **`agents/tasks/README.md`** - Task coordination guide
- **`agents/communication/README.md`** - Communication protocol guide
- **`agents/apps/agent-monitoring/README.md`** - Monitoring dashboard guide
- **`agents/apps/agent-mcp/README.md`** - MCP tools catalog

---

**Last Updated**: 2025-11-11  
**Status**: Active - Comprehensive Source of Truth  
**Maintained By**: This document is the authoritative reference for agent system architecture

