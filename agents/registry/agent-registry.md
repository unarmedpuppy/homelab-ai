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

1. Use `create_agent_definition` MCP tool to create agent definition
2. Agent will be added to "Ready Agents" table
3. Human activates agent by opening new Cursor session with agent definition

### For Humans Activating Agents

1. Review agent definition in `agents/registry/agent-definitions/`
2. Open new Cursor session
3. Load agent definition as prompt
4. Agent will move to "Active Agents" when working

### For Agents Checking Registry

1. Query registry using `query_agent_registry` MCP tool
2. Or read this file directly
3. Check for existing agents with required specialization

---

**Last Updated**: 2025-01-10
**Total Agents**: 0 active, 0 ready, 0 archived

