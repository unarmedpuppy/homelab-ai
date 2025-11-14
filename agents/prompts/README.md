# Agent Prompts

This directory contains agent prompts that define agent identity, role, workflow, and operating principles.

## Overview

**Prompts** define:
- **WHO** the agent is (role, responsibilities)
- **HOW** the agent works (discovery workflow, principles)
- **WHEN** to use what systems (memory, skills, tools)
- **WHY** certain approaches are taken

**Skills** (in `agents/skills/`) provide ready-made workflows for specific tasks. Prompts and skills are complementary:
- Prompts = Agent operating system
- Skills = Ready-made workflows the agent can use

## Available Prompts

### Base Prompt (`base.md`)
**Universal agent prompt** - Use this for general-purpose agents or as a foundation for specialized agents.

**Contains:**
- Discovery workflow (memory, skills, tools, agents)
- Universal systems (monitoring, communication, task coordination)
- Memory system usage
- Agent spawning
- Quality checks
- Code review
- Planning mode
- General principles

**Self-contained:** Can be used alone for general-purpose agents.

### Server Prompt (`server.md`)
**Server management extension** - Extends `base.md` with server-specific context.

**Contains:**
- Server connection methods
- Server project structure
- Server-specific MCP tools (Docker, Media Download, System Monitoring)
- Server-specific deployment workflows
- Server-specific patterns and learnings

**Extension pattern:** References `base.md` for common workflows, adds server-specific content.

## Usage

### For General-Purpose Agents
Use `prompts/base.md` alone.

### For Server Management Agents
Use both:
1. Read `prompts/base.md` first (universal workflows)
2. Then read `prompts/server.md` (server-specific context)

### For Future Specialized Agents
Create new prompts following the extension pattern:
- Reference `prompts/base.md` for common workflows
- Add domain-specific context only
- Don't duplicate base content

## Extension Pattern

When creating a new specialized prompt:

```markdown
# [Domain] Agent Prompt

## ⚠️ IMPORTANT: Read Base Prompt First

**This extends `prompts/base.md` with [domain]-specific context.**

**Before reading this**, read:
1. `prompts/base.md` ⭐ - Core agent prompt
2. `prompts/README.md` - Prompt system overview

**This document adds:**
- [Domain]-specific context
- [Domain]-specific tools
- [Domain]-specific patterns

**For universal workflows**, see `prompts/base.md`.
```

## Prompt vs Skill

**Prompts** tell agents:
- "You are a system administrator. Here's how you work, what systems to use, and your principles."

**Skills** tell agents:
- "Here's a tested workflow for deploying code: Step 1, Step 2, Step 3..."

**Together:**
1. Agent reads prompt → understands identity and workflow
2. Agent discovers skills → uses ready-made workflows
3. Agent uses MCP tools → executes operations

## Related Documentation

- **Skills**: `agents/skills/README.md` - Reusable workflows
- **MCP Tools**: `agents/apps/agent-mcp/README.md` - Available operations
- **Memory System**: `agents/memory/README.md` - Memory system guide
- **Task Coordination**: `agents/tasks/README.md` - Task management
- **Agent Workflow**: `agents/docs/AGENT_WORKFLOW.md` - Detailed workflow guide

## Future Extensions

Potential future prompts:
- `trading-bot.md` - Trading bot development agent
- `media-download.md` - Media download management agent
- `database.md` - Database management agent
- `frontend.md` - Frontend development agent
- `backend.md` - Backend development agent

Each would extend `base.md` with domain-specific context.

---

**Last Updated**: 2025-01-13
**Status**: Active

