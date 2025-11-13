# Agent Workflow Documentation

This directory contains all documentation related to AI agent workflows, prompts, and best practices for the home server project.

## Quick Start

**New to agent workflows?** Start here:

1. **`AGENT_PROMPT.md`** ⭐ - **START HERE** - Complete agent prompt with discovery workflow
2. **`AGENT_WORKFLOW.md`** - Detailed workflow guide and best practices
3. **`SERVER_AGENT_PROMPT.md`** - Server-specific agent context and tools
4. **`MCP_TOOL_DISCOVERY.md`** - How to discover and use MCP tools

## Documentation Files

### Core Agent Documentation

- **`QUICK_START.md`** ⭐⭐⭐ - **START HERE** - 5-minute quick start guide
  - Essential steps to get started
  - Common operations
  - Quick reference

- **`AGENT_PROMPT.md`** ⭐⭐ - Main agent prompt with complete discovery workflow
  - Memory system usage
  - Task coordination system
  - Skills and MCP tools
  - Agent spawning
  - Common operations

- **`AGENT_WORKFLOW.md`** - Complete workflow guide
  - Discovery workflow
  - Implementation workflow
  - Review workflow
  - Best practices

- **`SERVER_AGENT_PROMPT.md`** - Server management agent context
  - Server connection methods
  - Available MCP tools
  - Docker management
  - System monitoring
  - **Note**: Read `AGENT_PROMPT.md` first for common workflows

### Architecture & Guidelines

- **`SYSTEM_ARCHITECTURE.md`** - Unified architecture documentation
  - Core components overview
  - Data flow diagrams
  - System integration
  - File structure

- **`COMMUNICATION_GUIDELINES.md`** - Communication channel usage guidelines
  - When to use which channel
  - Decision tree
  - Common scenarios
  - Best practices

- **`MCP_TOOL_DISCOVERY.md`** - Tool discovery and usage guide
  - How to find tools
  - When to create new tools
  - Tool categories
  - Memory operations
  - Task coordination operations

### Agent Spawning

- **`AGENT_SPAWNING_ARCHITECTURE.md`** - Architecture for creating specialized agents
- **`AGENT_SPAWNING_WORKFLOW.md`** - Workflow for spawning specialized agents

### Workflow Generation

- **`WORKFLOW_GENERATOR_PROMPT.md`** - Meta-prompt for generating agent workflows
- **`WORKFLOW_GENERATOR_USAGE.md`** - How to use the workflow generator


### Templates

- **`templates/`** - Templates for agent workflows
  - Review templates
  - Task templates
  - Status tracking templates

## Related Documentation

### Memory System
- `agents/memory/README.md` - Memory system overview
- `agents/memory/MEMORY_USAGE_EXAMPLES.md` - Real-world examples ⭐
- `agents/memory/MCP_TOOLS_GUIDE.md` - Memory MCP tools reference

### Task Coordination
- `agents/tasks/README.md` - Task coordination system guide ⭐
- `agents/tasks/registry.md` - Central task registry

### Agent Communication
- `agents/communication/README.md` ⭐ - Complete communication guide and usage
- `agents/communication/protocol.md` ⭐ - Communication protocol specification
- `agents/docs/COMMUNICATION_GUIDELINES.md` ⭐ - When to use which channel
- **5 MCP tools** for sending/receiving messages between agents

### Agent Monitoring
- `agents/apps/agent-monitoring/README.md` ⭐ - Dashboard overview and setup
- `agents/apps/agent-monitoring/INTEGRATION_GUIDE.md` ⭐ - Complete integration guide
- **Dashboard**: http://localhost:3012 or https://agent-dashboard.server.unarmedpuppy.com
- **Grafana**: http://localhost:3011 (admin/admin123)

### Skills & Tools
- `agents/skills/README.md` - Reusable workflow skills
- `agents/apps/agent-mcp/README.md` - MCP tools catalog (68 tools, including 4 activity monitoring tools and 5 communication tools)

### Architecture & System Documentation
- `agents/docs/COMPLETE_SYSTEM_VISUALIZATION.md` ⭐⭐⭐ - **Complete visual guide with Mermaid diagrams**
- `agents/docs/SYSTEM_ARCHITECTURE.md` ⭐ - Unified architecture overview
- `agents/docs/DATA_MODEL.md` ⭐ - Data model and storage structure
- `agents/docs/COMMUNICATION_GUIDELINES.md` ⭐ - Communication channel usage
- `agents/docs/AGENT_SELF_DOCUMENTATION.md` ⭐ - **How agents should organize their own documentation** (namespacing guide)

### Enhancement Plans
- `agents/docs/AGENT_SYSTEM_ENHANCEMENT_PLAN.md` ⭐⭐ - **Enhancement opportunities based on production best practices**
- `apps/docs/APPS_DOCUMENTATION.md` - Application documentation
- `apps/docs/MCP_SERVER_PLAN.md` - MCP server architecture plan

### Archived Documentation
- `agents/docs/archive/` - Completed proposals and plans (historical reference)

## Navigation

### For Agents Starting Work
1. Read `AGENT_PROMPT.md` first
2. Follow discovery workflow in `AGENT_PROMPT.md`
3. Reference `AGENT_WORKFLOW.md` for detailed workflows
4. Use `MCP_TOOL_DISCOVERY.md` to find tools

### For Creating New Agents
1. Review `AGENT_SPAWNING_ARCHITECTURE.md`
2. Follow `AGENT_SPAWNING_WORKFLOW.md`
3. Use templates in `templates/`

### For Workflow Generation
1. Use `WORKFLOW_GENERATOR_PROMPT.md` as meta-prompt
2. Reference `WORKFLOW_GENERATOR_USAGE.md` for usage

---

**Last Updated**: 2025-01-13
**Status**: Active

