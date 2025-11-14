# Agent Registry

Master registry of all agents (active, ready, and archived).

## Registry Status

- **Active Agents**: Agents currently working on tasks
- **Ready Agents**: Agent definitions ready for activation
- **Archived Agents**: Completed agents moved to archive

## Active Agents

| Agent ID | Specialization | Created By | Created Date | Status | Location |
|----------|---------------|------------|--------------|--------|----------|
| - | - | - | - | - | - |

## Ready Agents

| Agent ID | Specialization | Created By | Created Date | Definition | Tasks |
|----------|---------------|------------|--------------|------------|-------|
| - | - | - | - | - | - |

## Archived Agents

| Agent ID | Specialization | Created By | Completed Date | Archive Location |
|----------|---------------|------------|----------------|------------------|
| - | - | - | - | - |

## How to Use

### For Agents Creating New Agents

1. Choose a template from `agents/registry/agent-templates/` (defines capabilities)
2. Choose a prompt from `agents/prompts/` (defines workflow)
   - General: `prompts/base.md`
   - Server: `prompts/server.md`
3. Use `create_agent_definition` MCP tool to create agent definition
4. Agent will be added to "Ready Agents" table
5. Human activates agent by opening new Cursor session with agent definition

### For Humans Activating Agents

1. Review agent definition in `agents/registry/agent-definitions/`
2. Check which prompt the agent uses (from definition metadata)
3. Open new Cursor session
4. Load both the agent definition AND the referenced prompt
5. Agent will move to "Active Agents" when working

### For Agents Checking Registry

1. Query registry using `query_agent_registry` MCP tool
2. Or read this file directly
3. Check for existing agents with required specialization

## Templates and Prompts

**Templates** (`agents/registry/agent-templates/`) define WHAT agents can do:
- Specialization
- Capabilities (skills, tools, knowledge)
- Typical tasks

**Prompts** (`agents/prompts/`) define HOW agents work:
- Workflow and principles
- Discovery process
- System usage (memory, monitoring, communication)

**Agent Definitions** combine both:
- Template provides capabilities
- Prompt provides workflow
- Definition combines them into complete agent instance

See `agents/registry/REGISTRY_AND_PROMPTS.md` for complete explanation.

---

**Last Updated**: 2025-01-10
**Total Agents**: 0 active, 0 ready, 0 archived

