# Agent System Architecture

**Unified architecture documentation for the agent system.**

## Overview

The agent system provides a comprehensive framework for AI agents to work collaboratively on the home server project. It includes memory, task coordination, communication, monitoring, and agent management capabilities.

## Core Components

### 1. Agent Monitoring System

**Location**: `apps/agent-monitoring/`

**Purpose**: Real-time visibility into agent activity, status, and progress.

**Components**:
- **SQLite Database** (`apps/agent-monitoring/data/agent_activity.db`) - Stores agent status, sessions, and actions
- **Backend API** (Node.js/Express/TypeScript) - REST API for querying agent data
- **Frontend Dashboard** (Next.js/TypeScript) - Real-time agent status dashboard
- **Grafana Integration** - Time-series metrics and visualizations
- **InfluxDB** - Metrics storage for Grafana

**MCP Tools** (4 tools):
- `start_agent_session()` - Start monitoring session
- `update_agent_status()` - Update agent status
- `get_agent_status()` - Get current status
- `end_agent_session()` - End session

**See**: `apps/agent-monitoring/README.md` for complete documentation.

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

**Location**: `server-management-skills/`

**Purpose**: Reusable workflows for common tasks.

**Components**:
- **Skills Catalog** (`server-management-skills/README.md`) - List of available skills
- **Skill Definitions** (`server-management-skills/*/SKILL.md`) - Individual skill definitions
- **Skill Proposals** (`server-management-skills/proposals/`) - Proposed skills awaiting review

**MCP Tools** (5 tools):
- `propose_skill()` - Propose new skill
- `list_skill_proposals()` - List proposals
- `query_skills()` - Query existing skills
- `analyze_patterns_for_skills()` - Analyze patterns for skill candidates
- `auto_propose_skill_from_pattern()` - Auto-create skill from pattern

**See**: `server-management-skills/README.md` for complete documentation.

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

**Location**: `server-management-mcp/`

**Purpose**: Unified interface for all agent operations.

**Total Tools**: 67 tools across categories:
- Activity Monitoring (4)
- Agent Communication (5)
- Memory Management (9)
- Task Coordination (6)
- Agent Management (6)
- Skill Management (5)
- Docker Management (8)
- Media Download (13)
- System Monitoring (5)
- Git Operations (4)
- Troubleshooting (3)
- Networking (4)
- System Utilities (3)

**See**: `server-management-mcp/README.md` for complete tool reference.

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
    └─→ Use Monitoring System (apps/agent-monitoring/)
```

**Primary Channels**:
1. **Task Coordination** - For task assignment, tracking, dependencies
2. **Communication Protocol** - For agent-to-agent messaging
3. **Memory System** - For knowledge, decisions, patterns, context
4. **Monitoring System** - For status, activity, progress

**Deprecated/Simplified**:
- Per-agent `TASKS.md` → Use task coordination registry
- Per-agent `COMMUNICATION.md` → Use communication protocol
- Per-agent `STATUS.md` → Use monitoring system (optional: auto-generate for readability)

**See**: `agents/docs/COMMUNICATION_GUIDELINES.md` for detailed usage guidelines.

---

## File Structure

```
agents/
├── docs/                    # Agent documentation
│   ├── QUICK_START.md       # 5-minute quick start
│   ├── AGENT_PROMPT.md      # Main agent prompt
│   ├── SERVER_AGENT_PROMPT.md # Server-specific context
│   ├── AGENT_WORKFLOW.md    # Workflow guide
│   ├── SYSTEM_ARCHITECTURE.md # This file
│   ├── COMMUNICATION_GUIDELINES.md # Communication channel usage
│   └── archive/             # Archived proposals/plans
├── memory/                  # Memory system
│   ├── memory.db            # SQLite database
│   ├── sqlite_memory.py     # Memory API
│   └── README.md            # Memory documentation
├── tasks/                   # Task coordination
│   ├── registry.md          # Task registry
│   └── README.md            # Task coordination guide
├── communication/           # Agent communication
│   ├── protocol.md          # Protocol specification
│   ├── messages/            # Message files
│   └── README.md            # Communication guide
├── registry/                # Agent registry
│   ├── agent-registry.md    # Master registry (auto-generated)
│   ├── agent-definitions/   # Agent definitions
│   ├── agent-templates/      # Agent templates
│   └── sync_registry.py     # Registry sync script
├── active/                  # Active agent directories
├── archive/                 # Archived agents
└── lifecycle/               # Lifecycle management
    ├── policy.md            # Lifecycle policy
    └── pattern_learning.md  # Pattern learning guide
```

---

## Key Principles

### Single Source of Truth

- **Agent Status**: Monitoring DB (auto-generates registry markdown)
- **Tasks**: Task registry markdown
- **Memory**: SQLite database (optional markdown exports)
- **Messages**: Message markdown files + index.json

### Human Readability

- All data stored in markdown where possible
- SQLite used for fast queries, markdown for human review
- Auto-generated views from databases

### Observability

- All MCP tools are automatically logged
- Monitoring dashboard provides real-time visibility
- Custom commands/scripts are NOT observable (avoid when possible)

### Consistency

- Use MCP tools for all operations (when available)
- Follow established patterns and workflows
- Document decisions in memory system

---

**Last Updated**: 2025-01-13  
**Status**: Active  
**See Also**: 
- `agents/docs/README.md` - Documentation index
- `agents/docs/QUICK_START.md` - Quick start guide
- `agents/docs/COMMUNICATION_GUIDELINES.md` - Communication channel usage

