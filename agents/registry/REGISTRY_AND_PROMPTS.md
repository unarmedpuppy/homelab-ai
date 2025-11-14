# Registry and Prompts: How They Work Together

## Overview

The agent system has three complementary components:

1. **Prompts** (`agents/prompts/`) - Define HOW agents work
2. **Templates** (`agents/registry/agent-templates/`) - Define WHAT agents can do
3. **Agent Definitions** (`agents/registry/agent-definitions/`) - Complete agent instances

## Component Roles

### Prompts (`agents/prompts/`)
**Purpose**: Define agent identity, workflow, operating principles, AND capabilities

**Contains:**
- Discovery workflow (memory, skills, tools, agents)
- Universal systems (monitoring, communication, task coordination)
- How to work (principles, best practices)
- When to use what systems
- **Your Capabilities** (pre-curated skills, tools, knowledge) ⭐ Discovery shortcuts

**Examples:**
- `prompts/base.md` - Universal agent prompt
- `prompts/server.md` - Server management extension (includes capabilities)

**Answer**: "HOW do I work?" AND "WHAT can I do?"

**Key Insight**: Prompts now include discovery shortcuts (pre-curated capabilities) so agents don't have to discover everything from scratch.

### Templates (`agents/registry/agent-templates/`)
**Purpose**: Minimal metadata for agent creation tool (optional helpers)

**Contains:**
- Specialization (what domain)
- Prompt reference (which prompt to use)
- Typical tasks
- Usage instructions

**Examples:**
- `base-agent-template.md` - General purpose
- `server-management-agent.md` - Server management (references `prompts/server.md`)
- `database-agent.md` - Database operations
- `media-download-agent.md` - Media download management

**Answer**: "Which prompt should I use?" and "What tasks does this specialization handle?"

**Note**: Capabilities are now in prompts, not templates. Templates are optional helpers for the `create_agent_definition` tool.

### Agent Definitions (`agents/registry/agent-definitions/`)
**Purpose**: Complete agent instance combining template + prompt

**Contains:**
- Agent ID
- Specialization
- Created by
- Status
- Full agent definition (from template)
- Reference to prompt

**Answer**: "WHO am I and what's my complete configuration?"

## How They Work Together

### Creating a New Agent

1. **Choose a Template** (defines capabilities)
   - Select from `agents/registry/agent-templates/`
   - Or use `base-agent-template.md` for general purpose

2. **Choose a Prompt** (defines workflow)
   - Use `prompts/base.md` for general agents
   - Use `prompts/server.md` for server management agents
   - Future: `prompts/trading-bot.md`, `prompts/media-download.md`, etc.

3. **Create Agent Definition** (combines both)
   - Template provides: capabilities, specialization, typical tasks
   - Prompt provides: workflow, principles, discovery process
   - Agent definition references both

### Example: Server Management Agent

**Prompt** (`prompts/server.md`) - **Source of Truth**:
- How to work: Discovery workflow, memory usage, task coordination
- Principles: Zero-tolerance for mistakes, always use Git workflow
- Systems: Monitoring, communication, memory
- **Your Capabilities**: Pre-curated skills (`standard-deployment`, `troubleshoot-container-failure`, etc.)
- **Your Capabilities**: Pre-curated MCP tools (Docker, monitoring, troubleshooting, etc.)
- **Your Capabilities**: Domain knowledge (Docker, Linux, networking, etc.)

**Template** (`server-management-agent.md`) - **Optional Helper**:
- Specialization: Server infrastructure management
- Prompt reference: `prompts/server.md`
- Typical tasks: Deploy services, troubleshoot containers, system monitoring
- **Note**: Capabilities are in the prompt, not here

**Agent Definition** (created from template):
```markdown
---
agent_id: agent-002
specialization: server-management
created_by: agent-001
created_date: 2025-01-13
status: ready
prompt: prompts/server.md
template: server-management-agent
---

# Agent 002: Server Management Specialist

[Agent-specific details + reference to prompt for capabilities]
```

## Template Structure

Templates should include:

1. **Specialization** - What domain
2. **Prompt Reference** - Which prompt to use (prompt contains capabilities)
3. **Typical Tasks** - What this agent does
4. **Note** - That capabilities are in the prompt

Example:
```markdown
# Agent Template: [Specialization]

## Specialization
[Domain description]

## Prompt
**Use**: `prompts/base.md` (or `prompts/[domain].md` if exists)

**Capabilities are in the prompt** - See "Your Capabilities" section.

## Typical Tasks
- [List typical tasks]
```

**Key Change**: Capabilities moved to prompts. Templates are now minimal metadata.

## Prompt Structure

Prompts should include:

1. **Identity** - Who the agent is
2. **Workflow** - How the agent works
3. **Discovery** - How to find resources
4. **Principles** - Operating principles

Example:
```markdown
# [Domain] Agent Prompt

## ⚠️ IMPORTANT: Read Base Prompt First

**This extends `prompts/base.md` with [domain]-specific context.**

[Domain-specific content only]
```

## Best Practices

### For Templates
- Focus on **WHAT** the agent can do
- List capabilities (skills, tools, knowledge)
- Don't duplicate prompt content
- Reference which prompt to use

### For Prompts
- Focus on **HOW** the agent works
- Define workflow and principles
- Don't duplicate template content
- Reference which templates are relevant

### For Agent Definitions
- Combine template + prompt
- Include agent-specific details
- Reference both template and prompt
- Include status and metadata

## Current Templates and Their Prompts

| Template | Prompt | Notes |
|----------|--------|-------|
| `base-agent-template.md` | `prompts/base.md` | General purpose |
| `server-management-agent.md` | `prompts/server.md` | Server management |
| `database-agent.md` | `prompts/base.md` | Database operations (no specific prompt yet) |
| `media-download-agent.md` | `prompts/base.md` | Media download (no specific prompt yet) |

## Future Extensions

When creating domain-specific prompts:
1. Create prompt in `agents/prompts/[domain].md`
2. Update relevant templates to reference new prompt
3. Follow extension pattern (reference `base.md`)

Example:
- Create `prompts/database.md` for database agents
- Update `database-agent.md` template to reference `prompts/database.md`

---

**Last Updated**: 2025-01-13
**Status**: Active

