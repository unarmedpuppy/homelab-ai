# Agents System

**Main entry point for all agent-related features, documentation, and tools.**

## 🚀 START HERE

**New to agents?** Follow this path:

1. **Start Infrastructure** - Run `agents/scripts/start-agent-infrastructure.sh` or use `start_agent_infrastructure()` MCP tool
2. **`docs/QUICK_START.md`** ⭐⭐⭐ - **5-MINUTE QUICK START** - Essential steps to get started
3. **`prompts/base.md`** ⭐⭐ - **COMPLETE GUIDE** - Full agent prompt with discovery workflow
4. **`docs/AGENT_WORKFLOW.md`** - Detailed workflow guide and best practices
5. **`prompts/server.md`** - Server-specific agent context (if working on server)
6. **`docs/MCP_TOOL_DISCOVERY.md`** - How to discover and use MCP tools

**For humans activating agents**: See `ACTIVATION_GUIDE.md`

## Directory Structure

```
agents/
├── README.md                    # This file - main entry point
├── ACTIVATION_GUIDE.md           # How to activate agents (for humans)
│
├── prompts/                      # Agent prompts (identity, role, workflow)
│   ├── base.md                  # Core agent prompt ⭐ START HERE
│   ├── server.md                # Server management extension
│   └── README.md                # Prompt system overview
│
├── docs/                         # Agent documentation
│   ├── QUICK_START.md           # 5-minute quick start ⭐⭐⭐
│   ├── AGENT_WORKFLOW.md        # Workflow guide
│   ├── MCP_TOOL_DISCOVERY.md    # Tool discovery
│   ├── COMPLETE_SYSTEM_VISUALIZATION.md  # Visual system guide
│   ├── AGENT_SELF_DOCUMENTATION.md       # How agents organize docs
│   └── templates/               # Workflow templates
│
├── apps/                         # Agent applications (run locally)
│   ├── agent-mcp/               # MCP server (71 tools)
│   │   ├── server.py            # Main MCP server
│   │   ├── tools/               # All MCP tools (22 files)
│   │   └── README.md            # Tool catalog
│   │
│   └── agent-monitoring/        # Monitoring dashboard (local-first)
│       ├── backend/             # Node.js API (localhost:3001)
│       ├── frontend/            # Next.js dashboard (localhost:3012)
│       ├── activity_logger/     # Python logging module
│       ├── docker-compose.yml   # Local infrastructure
│       └── README.md            # Monitoring guide
│
├── memory/                       # Memory system (SQLite-based, local)
│   ├── sqlite_memory.py         # Memory implementation
│   ├── memory.db                # SQLite database (local)
│   ├── README.md                # Memory system overview
│   └── MCP_TOOLS_GUIDE.md       # Memory MCP tools reference
│
├── registry/                     # Agent registry
│   ├── agent-registry.md        # Master registry
│   ├── agent-definitions/       # Agent definition files
│   ├── agent-templates/         # Agent templates
│   └── sync_registry.py         # Auto-sync script
│
├── tasks/                        # Task coordination
│   ├── registry.md               # Central task registry
│   └── README.md                 # Task coordination guide
│
├── communication/                # Agent communication
│   ├── messages/                 # Message files
│   ├── protocol.md               # Communication protocol
│   └── README.md                 # Communication guide
│
├── skills/                       # Reusable workflow skills
│   ├── README.md                 # Skills catalog
│   ├── standard-deployment/      # Deployment workflow
│   ├── troubleshoot-container-failure/  # Troubleshooting
│   └── [7+ skills]               # Other skills
│
├── scripts/                      # Utility scripts
│   ├── start-agent-infrastructure.sh  # Start monitoring locally
│   ├── query_tasks.sh           # Task query helper
│   └── query_messages.sh        # Message query helper
│
├── active/                       # Active agent directories
│   └── agent-001/               # Example: agent-001
│       └── docs/                 # Agent-specific documentation
│           ├── plans/            # Implementation plans
│           ├── notes/            # Working notes, research
│           ├── architecture/     # System designs
│           └── references/       # External references
│
├── archive/                      # Archived agents and state
│   ├── state/                    # Archived state files
│   └── README.md                 # Archive documentation
│
└── lifecycle/                    # Lifecycle policies
    ├── policy.md                 # Lifecycle management
    └── pattern_learning.md       # Pattern learning system
```

## Architecture Overview

### Local-First Architecture

**All agent infrastructure runs locally** on your machine:

```
Local Machine:
├── Agent Infrastructure (localhost)
│   ├── Backend API: localhost:3001
│   ├── Frontend Dashboard: localhost:3012
│   ├── Grafana: localhost:3011
│   └── InfluxDB: localhost:8087
│
├── MCP Server (local Python)
│   └── 71 tools (all operations)
│
├── Memory System (local SQLite)
│   └── agents/memory/memory.db
│
└── Activity Logger → localhost:3001

Server (192.168.86.47):
└── Services only (Docker, media download, etc.)
    └── Accessed via SSH/network from MCP tools
```

**Why Local-First?**
- ✅ Workflow & memory tied to agent system
- ✅ Simpler mental model (one database, one source of truth)
- ✅ Faster (no network latency)
- ✅ Better for development
- ✅ Privacy (all agent data stays local)

**Server Operations**: MCP tools use SSH/network for server operations (Docker, media download, etc.), but agent infrastructure is local.

## Core Features

### 1. Agent Prompts (`prompts/`)

Agent prompts define identity, role, and workflow:
- **`prompts/base.md`** - Core agent prompt with discovery workflow
- **`prompts/server.md`** - Server management extension
- **`prompts/README.md`** - Prompt system overview

### 2. Agent Infrastructure (`apps/`)

**Agent Monitoring** (`apps/agent-monitoring/`):
- Backend API (Node.js/TypeScript) - `localhost:3001`
- Frontend Dashboard (Next.js) - `localhost:3012`
- Grafana - `localhost:3011`
- InfluxDB - `localhost:8087`
- Activity Logger (Python) - Logs to local backend

**MCP Server** (`apps/agent-mcp/`):
- 71 MCP tools across all categories
- Runs locally (Python process)
- Uses SSH for server operations
- Automatic logging to monitoring dashboard

**Start Infrastructure**:
```bash
# Option 1: Script
./agents/scripts/start-agent-infrastructure.sh

# Option 2: MCP Tool
await start_agent_infrastructure()
```

### 3. Memory System (`memory/`)

SQLite-based memory system for agents:
- **9 MCP tools** for querying and recording memories
- Stores decisions, patterns, and context
- Full-text search capabilities
- Markdown export for human review
- **Local database**: `agents/memory/memory.db`

**See**: `memory/README.md` for complete guide

### 4. Agent Registry (`registry/`)

Central registry for all agents:
- Track active, ready, and archived agents
- Agent definitions and templates
- Agent spawning support
- Auto-sync script

**See**: `registry/agent-registry.md` for registry

### 5. Task Coordination (`tasks/`)

Central task registry for coordinating work:
- Register, claim, and update tasks
- Track dependencies
- Prevent conflicts
- **6 MCP tools** for task management

**See**: `tasks/README.md` for complete guide

### 6. Agent Communication (`communication/`)

Inter-agent messaging system:
- Structured message protocol
- Message queue with status tracking
- **5 MCP tools** for messaging

**See**: `communication/README.md` for complete guide

### 7. Skills Library (`skills/`)

Reusable workflow skills:
- 7+ implemented skills
- Skill creation workflow
- Auto-proposal from patterns

**See**: `skills/README.md` for catalog

## Getting Started

### For New Agents (Recommended Path)

1. **Start Infrastructure** - Run `agents/scripts/start-agent-infrastructure.sh` or use `start_agent_infrastructure()` MCP tool
2. **Start with `docs/QUICK_START.md`** ⭐ - 5-minute quick start
3. **Read `prompts/base.md`** - Complete guide with all details
4. **Review `docs/AGENT_WORKFLOW.md`** - Detailed workflows
5. **Explore systems**:
   - `memory/README.md` - Memory system
   - `tasks/README.md` - Task coordination
   - `communication/README.md` - Agent messaging
   - `registry/agent-registry.md` - Available agents

### For Creating New Agents

1. Use `registry/agent-templates/` - Agent templates
2. Follow `docs/AGENT_SPAWNING_WORKFLOW.md` - Spawning guide
3. Register in `registry/agent-registry.md` - Registry

### For Memory Operations

1. Use MCP tools (preferred) - `memory/MCP_TOOLS_GUIDE.md`
2. Fallback: `memory/query_memory.sh` - Helper script
3. See `memory/MEMORY_USAGE_EXAMPLES.md` - Real-world examples

### For Task Management

1. Use MCP tools - `tasks/README.md`
2. Register tasks early
3. Track dependencies
4. Update status regularly

## MCP Tools (71 Total)

### Infrastructure Management (3 tools) ⭐ NEW
- `start_agent_infrastructure()` - Start all infrastructure services
- `check_agent_infrastructure()` - Check service status
- `stop_agent_infrastructure()` - Stop all services

### Activity Monitoring (4 tools)
- `start_agent_session()` - Start monitoring session
- `update_agent_status()` - Update agent status
- `get_agent_status()` - Get current status
- `end_agent_session()` - End session

### Agent Communication (5 tools)
- `send_agent_message()` - Send message to agent
- `get_agent_messages()` - Get pending messages
- `acknowledge_message()` - Acknowledge message
- `mark_message_resolved()` - Mark message resolved
- `query_messages()` - Query messages

### Memory Management (9 tools)
- `memory_query_decisions()` - Query decisions
- `memory_query_patterns()` - Query patterns
- `memory_search()` - Full-text search
- `memory_record_decision()` - Record decision
- `memory_record_pattern()` - Record pattern
- `memory_save_context()` - Save context
- `memory_get_recent_context()` - Get recent context
- `memory_get_context_by_task()` - Get task context
- `memory_export_to_markdown()` - Export to markdown

### Task Coordination (6 tools)
- `register_task()` - Register new task
- `query_tasks()` - Query tasks
- `get_task()` - Get single task
- `claim_task()` - Claim task
- `update_task_status()` - Update task status
- `check_task_dependencies()` - Check dependencies

### Agent Management (6 tools)
- `create_agent_definition()` - Create specialized agent
- `query_agent_registry()` - Query registry
- `assign_task_to_agent()` - Assign task
- `archive_agent()` - Archive agent
- `reactivate_agent()` - Reactivate agent
- `sync_agent_registry()` - Sync registry

### Skill Management (5 tools)
- `propose_skill()` - Create skill proposal
- `list_skill_proposals()` - List proposals
- `query_skills()` - Query existing skills
- `analyze_patterns_for_skills()` - Analyze patterns
- `auto_propose_skill_from_pattern()` - Auto-create skill

### Server Management (33 tools)
- Docker Management (8 tools)
- Media Download (13 tools)
- System Monitoring (5 tools)
- Troubleshooting (3 tools)
- Git Operations (4 tools)
- Networking (4 tools)
- System Utilities (3 tools)

**See**: `apps/agent-mcp/README.md` for complete tool reference

## Documentation Index

### Core Documentation
- `docs/QUICK_START.md` ⭐⭐⭐ - **START HERE** - 5-minute quick start
- `prompts/base.md` ⭐⭐ - Main agent prompt (complete guide)
- `docs/AGENT_WORKFLOW.md` - Workflow guide
- `prompts/server.md` - Server context (if working on server)
- `docs/MCP_TOOL_DISCOVERY.md` - Tool discovery
- `docs/COMPLETE_SYSTEM_VISUALIZATION.md` ⭐⭐⭐ - **Visual system guide with diagrams**

### Memory System
- `memory/README.md` - Memory system overview
- `memory/MCP_TOOLS_GUIDE.md` - MCP tools reference
- `memory/MEMORY_USAGE_EXAMPLES.md` - Real-world examples ⭐

### Agent Management
- `registry/agent-registry.md` - Agent registry
- `ACTIVATION_GUIDE.md` - How to activate agents
- `docs/AGENT_SPAWNING_WORKFLOW.md` - Spawning guide
- `docs/AGENT_SELF_DOCUMENTATION.md` ⭐ - **How agents organize their own documentation**

### Task Coordination
- `tasks/README.md` - Task coordination guide
- `tasks/registry.md` - Central task registry

### Infrastructure
- `apps/agent-monitoring/README.md` - Monitoring dashboard
- `apps/agent-mcp/README.md` - MCP tools catalog
- `scripts/README.md` - Utility scripts

## Quick Reference

### Infrastructure Startup
```bash
# Start all infrastructure
./agents/scripts/start-agent-infrastructure.sh

# Or use MCP tool
await start_agent_infrastructure()
```

### Memory Operations
```python
# Query decisions
memory_query_decisions(project="home-server", search_text="deployment")

# Record decision
memory_record_decision(
    content="Use PostgreSQL for database",
    rationale="Need ACID compliance",
    project="home-server",
    importance=0.9
)

# Search all memories
memory_search("deployment workflow")
```

### Task Operations
```python
# Register task
register_task(
    title="Setup database",
    description="Create PostgreSQL schema",
    project="home-server",
    priority="high"
)

# Claim task
claim_task(task_id="T1.1", agent_id="agent-001")

# Update status
update_task_status(task_id="T1.1", status="in_progress", agent_id="agent-001")
```

### Agent Operations
```python
# Create agent definition
create_agent_definition(
    specialization="database-management",
    capabilities="PostgreSQL, migrations, optimization",
    initial_tasks="Setup database schema",
    parent_agent_id="agent-001"
)

# Query registry
query_agent_registry(specialization="database")
```

## Important Principles

### Agent Documentation Namespacing ⚠️

**All agent-specific documentation MUST go in your agent directory:**

```
agents/active/{agent-id}/docs/
├── plans/          # Implementation plans
├── notes/          # Working notes, research
├── architecture/   # System designs
└── references/     # External references
```

**Use MCP tools**:
```python
create_agent_doc(
    agent_id="agent-001",
    doc_type="plan",
    doc_name="feature-x-implementation",
    content="# Plan content..."
)
```

**See**: `docs/AGENT_SELF_DOCUMENTATION.md` for complete guide

## Navigation Guide

### I'm a New Agent - Where Do I Start?

1. **Start Infrastructure** - `./agents/scripts/start-agent-infrastructure.sh`
2. **Read `docs/QUICK_START.md`** (5 minutes) - Essential steps
3. **Read `prompts/base.md`** (15 minutes) - Complete guide
4. **Start working** - Follow the discovery workflow

### I Need to Find Something

- **Tools**: `docs/MCP_TOOL_DISCOVERY.md` or `apps/agent-mcp/README.md`
- **Workflows**: `skills/README.md`
- **Memory**: `memory/README.md`
- **Tasks**: `tasks/README.md`
- **Communication**: `communication/README.md`
- **Monitoring**: `apps/agent-monitoring/README.md`

### I'm Working on Server Management

- **Read `prompts/server.md`** - Server-specific context
- **Reference `prompts/base.md`** - For common workflows

### I Want to Create a New Agent

- **See `ACTIVATION_GUIDE.md`** - Human activation guide
- **See `docs/AGENT_SPAWNING_WORKFLOW.md`** - Agent spawning workflow

## System Status

- ✅ **Infrastructure**: Local-first architecture (localhost)
- ✅ **Documentation**: Complete and organized
- ✅ **Memory System**: SQLite-based, 9 MCP tools
- ✅ **Task Coordination**: Central registry, 6 MCP tools
- ✅ **Communication**: Protocol implemented, 5 MCP tools
- ✅ **Monitoring**: Dashboard available, 4 MCP tools
- ✅ **Agent Management**: Registry, lifecycle, 6 MCP tools
- ✅ **Skills**: Pattern learning, auto-creation, 5 MCP tools
- ✅ **Infrastructure Management**: Startup/stop tools, 3 MCP tools

**Total MCP Tools**: 71 tools available

---

**Last Updated**: 2025-01-13
**Status**: Active Development
**Quick Start**: `docs/QUICK_START.md` ⭐
**Visual Guide**: `docs/COMPLETE_SYSTEM_VISUALIZATION.md` ⭐⭐⭐
