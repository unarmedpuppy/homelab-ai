# Agents System

**Main entry point for all agent-related features, documentation, and tools.**

## 🚀 START HERE

**New to agents?** Follow this path:

1. **`docs/QUICK_START.md`** ⭐⭐⭐ - **5-MINUTE QUICK START** - Essential steps to get started
2. **`docs/AGENT_PROMPT.md`** ⭐⭐ - **COMPLETE GUIDE** - Full agent prompt with discovery workflow
3. **`docs/AGENT_WORKFLOW.md`** - Detailed workflow guide and best practices
4. **`docs/SERVER_AGENT_PROMPT.md`** - Server-specific agent context (if working on server)
5. **`docs/MCP_TOOL_DISCOVERY.md`** - How to discover and use MCP tools

**For humans activating agents**: See `ACTIVATION_GUIDE.md`

## Directory Structure

```
agents/
├── README.md              # This file - main entry point
├── docs/                  # Agent documentation
│   ├── AGENT_PROMPT.md    # Main agent prompt ⭐ START HERE
│   ├── AGENT_WORKFLOW.md  # Workflow guide
│   ├── SERVER_AGENT_PROMPT.md
│   ├── MCP_TOOL_DISCOVERY.md
│   └── templates/         # Workflow templates
├── memory/                # Memory system (SQLite-based)
│   ├── README.md          # Memory system overview
│   ├── MCP_TOOLS_GUIDE.md # Memory MCP tools reference
│   ├── sqlite_memory.py   # Memory implementation
│   └── memory.db          # SQLite database
├── registry/              # Agent registry
│   ├── agent-registry.md  # Master registry
│   ├── agent-definitions/ # Agent definition files
│   └── agent-templates/   # Agent templates
├── tasks/                 # Task coordination
│   ├── registry.md        # Central task registry
│   └── README.md          # Task coordination guide
├── active/                # Active agent directories
├── archive/               # Archived agents
└── ACTIVATION_GUIDE.md     # How to activate agents
```

## Core Features

### 1. Agent Documentation (`docs/`)

Complete documentation for agents:
- **AGENT_PROMPT.md** - Main prompt with discovery workflow
- **AGENT_WORKFLOW.md** - Complete workflow guide
- **SERVER_AGENT_PROMPT.md** - Server management context
- **MCP_TOOL_DISCOVERY.md** - Tool discovery guide
- **AGENT_SPAWNING_*.md** - Agent spawning workflows

### 2. Memory System (`memory/`)

SQLite-based memory system for agents:
- **9 MCP tools** for querying and recording memories
- Stores decisions, patterns, and context
- Full-text search capabilities
- Markdown export for human review

**See**: `memory/README.md` for complete guide

### 3. Agent Registry (`registry/`)

Central registry for all agents:
- Track active, ready, and archived agents
- Agent definitions and templates
- Agent spawning support

**See**: `registry/agent-registry.md` for registry

### 4. Task Coordination (`tasks/`)

Central task registry for coordinating work:
- Register, claim, and update tasks
- Track dependencies
- Prevent conflicts
- 5 MCP tools for task management

**See**: `tasks/README.md` for complete guide

## Related Infrastructure

These are at the repository root (shared infrastructure):

- **`server-management-mcp/`** - MCP server with 68 tools
  - Memory tools (9 tools)
  - Agent management tools (3 tools)
  - Task coordination tools (5 tools)
  - Server management tools (37 tools)
  - Skill management tools (3 tools)

- **`server-management-skills/`** - Reusable workflow skills
  - Skills catalog
  - Skill creation workflow
  - 7 implemented skills

## Getting Started

### For New Agents (Recommended Path)

1. **Start with `docs/QUICK_START.md`** ⭐ - 5-minute quick start
2. **Read `docs/AGENT_PROMPT.md`** - Complete guide with all details
3. **Review `docs/AGENT_WORKFLOW.md`** - Detailed workflows
4. **Explore systems**:
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

## Documentation Index

### Core Documentation
- `docs/QUICK_START.md` ⭐⭐⭐ - **START HERE** - 5-minute quick start
- `docs/AGENT_PROMPT.md` ⭐⭐ - Main agent prompt (complete guide)
- `docs/AGENT_WORKFLOW.md` - Workflow guide
- `docs/SERVER_AGENT_PROMPT.md` - Server context (if working on server)
- `docs/MCP_TOOL_DISCOVERY.md` - Tool discovery

### Memory System
- `memory/README.md` - Memory system overview
- `memory/MCP_TOOLS_GUIDE.md` - MCP tools reference
- `memory/MEMORY_USAGE_EXAMPLES.md` - Real-world examples ⭐

### Agent Management
- `registry/agent-registry.md` - Agent registry
- `ACTIVATION_GUIDE.md` - How to activate agents
- `docs/AGENT_SPAWNING_WORKFLOW.md` - Spawning guide

### Task Coordination
- `tasks/README.md` - Task coordination guide
- `tasks/registry.md` - Central task registry

## Quick Reference

### Memory Operations
```python
# Query decisions
memory_query_decisions(project="trading-journal", search_text="database")

# Record decision
memory_record_decision(
    content="Use PostgreSQL for database",
    rationale="Need ACID compliance",
    project="trading-journal",
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
    project="trading-journal",
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

## Status

- ✅ **Documentation**: Complete and consolidated
- ✅ **Memory System**: SQLite-based, 9 MCP tools
- ✅ **Task Coordination**: Phase 2 complete, 5 MCP tools
- ✅ **Agent Registry**: Active, ready, archived tracking
- ✅ **Agent Spawning**: Manual creation workflow

## Navigation Guide

### I'm a New Agent - Where Do I Start?

1. **Read `docs/QUICK_START.md`** (5 minutes) - Essential steps
2. **Read `docs/AGENT_PROMPT.md`** (15 minutes) - Complete guide
3. **Start working** - Follow the discovery workflow

### I Need to Find Something

- **Tools**: `docs/MCP_TOOL_DISCOVERY.md` or `server-management-mcp/README.md`
- **Workflows**: `server-management-skills/README.md`
- **Memory**: `memory/README.md`
- **Tasks**: `tasks/README.md`
- **Communication**: `communication/README.md`
- **Monitoring**: `apps/agent-monitoring/README.md`

### I'm Working on Server Management

- **Read `docs/SERVER_AGENT_PROMPT.md`** - Server-specific context
- **Reference `docs/AGENT_PROMPT.md`** - For common workflows

### I Want to Create a New Agent

- **See `ACTIVATION_GUIDE.md`** - Human activation guide
- **See `docs/AGENT_SPAWNING_WORKFLOW.md`** - Agent spawning workflow

## System Status

- ✅ **Documentation**: Complete and organized
- ✅ **Memory System**: SQLite-based, 9 MCP tools
- ✅ **Task Coordination**: Central registry, 6 MCP tools
- ✅ **Communication**: Protocol implemented, 5 MCP tools
- ✅ **Monitoring**: Dashboard available, 4 MCP tools
- ✅ **Agent Management**: Registry, lifecycle, 5 MCP tools
- ✅ **Skills**: Pattern learning, auto-creation, 5 MCP tools

**Total MCP Tools**: 67 tools available

---

**Last Updated**: 2025-01-13
**Status**: Active Development
**Quick Start**: `docs/QUICK_START.md` ⭐

