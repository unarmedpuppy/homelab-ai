# Capability Extractor - Documentation

**Purpose**: Extract capabilities from agent prompts and map them to AgentCard format.

**Date**: 2025-01-13

---

## Overview

The capability extractor system extracts capabilities from:
1. **Base Prompt** (`agents/prompts/base.md`) - Universal capabilities
2. **Specialized Prompts** (e.g., `agents/prompts/server.md`) - Specialization-specific capabilities
3. **Skills Directory** (`agents/skills/`) - All available skills

These capabilities are then mapped to AgentCard format for A2A protocol compliance.

---

## Files

### `capability_extractor.py`

**Purpose**: Extract capabilities from prompt files.

**Functions**:
- `extract_skills_from_prompt()` - Extract skill names from prompt
- `extract_mcp_tool_categories_from_prompt()` - Extract MCP tool categories
- `extract_domain_knowledge_from_prompt()` - Extract domain knowledge
- `get_all_skills_from_directory()` - Get all skills from skills directory
- `extract_capabilities_from_prompt()` - Extract all capabilities from a prompt
- `get_base_capabilities()` - Get base capabilities from base.md
- `get_specialization_capabilities()` - Get specialization-specific capabilities
- `combine_capabilities()` - Combine base and specialization capabilities
- `get_capabilities_for_agent()` - Get complete capability list for an agent

### `capability_mapping.py`

**Purpose**: Map capabilities to AgentCard format.

**Functions**:
- `get_specialization_extra_capabilities()` - Get extra capabilities for specializations
- `map_capabilities_to_agentcard()` - Map capabilities to AgentCard format
- `get_capability_summary()` - Get summary statistics
- `format_capabilities_for_agentcard()` - Format capabilities for AgentCard

---

## Usage

### Extract Capabilities for an Agent

```python
from agents.registry.capability_mapping import map_capabilities_to_agentcard

# Get capabilities for server management agent
capabilities = map_capabilities_to_agentcard("server-management")
print(capabilities)
# Output: ['add-root-folder', 'add-subdomain', 'agent-self-documentation', ...]
```

### Get Base Capabilities

```python
from agents.registry.capability_extractor import get_base_capabilities

base = get_base_capabilities()
print(base['skills'])  # Skills from base prompt
print(base['mcp_tool_categories'])  # MCP tool categories
print(base['domain_knowledge'])  # Domain knowledge
```

### Get Specialization Capabilities

```python
from agents.registry.capability_extractor import get_specialization_capabilities

server = get_specialization_capabilities("server-management")
print(server['skills'])  # Server-specific skills
```

---

## Capability Sources

### 1. Skills

**Source**: 
- `agents/prompts/base.md` - "Available Skills" section
- `agents/prompts/server.md` - "Relevant Skills" section
- `agents/skills/` directory - All skill directories

**Examples**:
- `standard-deployment`
- `troubleshoot-container-failure`
- `system-health-check`
- `deploy-new-service`

### 2. MCP Tool Categories

**Source**: 
- `agents/prompts/base.md` - "MCP Tools" section
- `agents/prompts/server.md` - "Relevant MCP Tools" section

**Examples**:
- `memory_management`
- `docker_management`
- `system_monitoring`
- `git_operations`
- `troubleshooting`

### 3. Domain Knowledge

**Source**: 
- `agents/prompts/server.md` - "Domain Knowledge" section

**Examples**:
- `docker_and_docker_compose`
- `linux_system_administration`
- `networking_and_port_management`
- `container_orchestration`

### 4. Specialization Extras

**Source**: 
- `capability_mapping.py` - `SPECIALIZATION_EXTRA_CAPABILITIES` dictionary

**Examples**:
- Server management: `deployment`, `troubleshooting`, `system_monitoring`
- Media download: `sonarr_management`, `radarr_management`
- Database: `database_management`, `migrations`

---

## Capability Format

All capabilities are normalized to:
- **snake_case** or **kebab-case**
- Lowercase
- No special characters
- No duplicates

**Examples**:
- ✅ `standard-deployment`
- ✅ `docker_management`
- ✅ `system_monitoring`
- ❌ `Standard Deployment` (not normalized)
- ❌ `Docker Management` (not normalized)

---

## Testing

### Run Extractor Test

```bash
cd /Users/joshuajenquist/repos/personal/home-server
python3 agents/registry/capability_extractor.py
```

**Output**:
- Base capabilities (skills, MCP tools, domain knowledge)
- Specialization capabilities
- Combined capabilities

### Run Mapping Test

```bash
python3 agents/registry/capability_mapping.py
```

**Output**:
- Capabilities for server management agent
- Capability summary statistics

---

## Integration with AgentCard Generation

The capability extractor is used by `sync_registry.py` to generate AgentCards:

```python
from agents.registry.capability_mapping import map_capabilities_to_agentcard
from agents.communication.a2a import create_agentcard

# Get capabilities
capabilities = map_capabilities_to_agentcard("server-management")

# Create AgentCard
card = create_agentcard(
    agent_id="agent-001",
    name="Server Management Agent",
    capabilities=capabilities
)
```

---

## Current Status

✅ **Implemented**:
- Skill extraction from prompts
- MCP tool category extraction
- Domain knowledge extraction (basic)
- Skills directory scanning
- Capability combination
- Specialization mapping

⚠️ **Needs Improvement**:
- Domain knowledge extraction (currently empty for base prompt)
- Better handling of edge cases in prompt parsing

---

## Next Steps

1. ✅ **Capability Extractor Created** - This file
2. **Extend sync_registry.py** - Add AgentCard generation
3. **Test with Real Agents** - Generate AgentCards for existing agents
4. **Update Documentation** - Document the full flow

---

**Last Updated**: 2025-01-13  
**Status**: Implemented and Tested

