# Agent Registry

Master registry of all agents (active, ready, and archived).

**⚠️ NOTE**: This file is auto-generated from:
- Agent definitions (`agents/registry/agent-definitions/`)
- Monitoring DB (`agents/apps/agent-monitoring/data/agent_activity.db`)
- Active/archive directories

**Source of Truth**: Monitoring DB for status, Definition files for metadata.

**Last Synced**: 2025-11-13 19:38:07

## Registry Status

- **Active Agents**: Agents currently working on tasks (status from monitoring DB)
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
2. Agent will be added to "Ready Agents" table (after sync)
3. Human activates agent by opening new Cursor session with agent definition
4. Agent status updates automatically via monitoring system

### For Humans Activating Agents

1. Review agent definition in `agents/registry/agent-definitions/`
2. Open new Cursor session
3. Load agent definition as prompt
4. Agent will move to "Active Agents" when working (via monitoring system)

### For Agents Checking Registry

1. Query registry using `query_agent_registry` MCP tool
2. Or read this file directly
3. Check for existing agents with required specialization

### Syncing Registry

To regenerate this file:
```bash
python agents/registry/sync_registry.py
```

Or use MCP tool: `sync_agent_registry()`

---

**Last Updated**: 2025-11-13 19:38:07
**Total Agents**: 0 active, 0 ready, 0 archived
