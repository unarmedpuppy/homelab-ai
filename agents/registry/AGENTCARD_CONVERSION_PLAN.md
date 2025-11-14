# AgentCard Conversion Plan

**Converting Custom Agent Registry to A2A-Compliant AgentCard System**

**Date**: 2025-01-13

---

## Overview

**Goal**: Bridge the gap between our custom markdown-based registry (human-readable) and A2A-compliant AgentCards (machine-readable) while maintaining both systems.

**Strategy**: 
- Keep markdown registry for humans
- Auto-generate AgentCards from registry data
- Map base prompt capabilities to AgentCard capabilities
- Sync both systems automatically

---

## Current System Architecture

### 1. Agent Registry (Markdown)
- **Location**: `agents/registry/agent-registry.md`
- **Format**: Markdown tables
- **Purpose**: Human-readable agent listing
- **Source**: Generated from:
  - Agent definitions (`agents/registry/agent-definitions/*.md`)
  - Monitoring DB (`agents/apps/agent-monitoring/data/agent_activity.db`)
  - Active/archive directories

### 2. Agent Definitions (Markdown + YAML)
- **Location**: `agents/registry/agent-definitions/*.md`
- **Format**: Markdown with YAML frontmatter
- **Contains**: Agent metadata (ID, specialization, created_by, etc.)

### 3. Base Prompt (Capabilities)
- **Location**: `agents/prompts/base.md`
- **Format**: Markdown
- **Contains**: 
  - "Your Capabilities" section
  - Skills, MCP tools, domain knowledge
  - HOW agents work

### 4. AgentCards (JSON) - NEW
- **Location**: `agents/communication/agentcards/*.json`
- **Format**: JSON (A2A-compliant)
- **Purpose**: Machine-readable agent discovery
- **Status**: Implemented but not populated

---

## Conversion Strategy

### Phase 1: Map Base Prompt to AgentCard Capabilities

**Problem**: Base prompt defines capabilities, but AgentCards need structured capability lists.

**Solution**: Extract capabilities from base prompt and map to AgentCard format.

#### Base Prompt Capability Sources

1. **Skills** (`agents/skills/`)
   - `standard-deployment`
   - `troubleshoot-container-failure`
   - `system-health-check`
   - `troubleshoot-stuck-downloads`
   - `deploy-new-service`
   - `add-subdomain`
   - `cleanup-disk-space`
   - `add-root-folder`
   - `agent-self-documentation`

2. **MCP Tools** (`agents/apps/agent-mcp/`)
   - Memory management (9 tools)
   - Docker management (8 tools)
   - Media download (13 tools)
   - System monitoring (5 tools)
   - Git operations (4 tools)
   - Troubleshooting (3 tools)
   - Networking (3 tools)
   - System utilities (3 tools)
   - Agent management (3 tools)
   - Communication (5 tools)

3. **Domain Knowledge** (from prompts)
   - Server management
   - Docker/containers
   - Networking
   - System administration
   - Media download services
   - Database management

#### Capability Mapping

**Base Prompt → AgentCard Capabilities**:

```python
# Base prompt capabilities (universal)
BASE_CAPABILITIES = [
    # Skills
    "standard-deployment",
    "troubleshoot-container-failure",
    "system-health-check",
    "troubleshoot-stuck-downloads",
    "deploy-new-service",
    "add-subdomain",
    "cleanup-disk-space",
    "add-root-folder",
    "agent-self-documentation",
    
    # MCP Tool Categories
    "memory_management",
    "docker_management",
    "media_download_management",
    "system_monitoring",
    "git_operations",
    "troubleshooting",
    "networking",
    "system_utilities",
    "agent_management",
    "agent_communication",
    
    # Domain Knowledge
    "server_management",
    "container_orchestration",
    "system_administration"
]

# Specialization-specific capabilities (from specialized prompts)
SPECIALIZATION_CAPABILITIES = {
    "server-management": [
        "docker_management",
        "deployment",
        "troubleshooting",
        "system_monitoring",
        "git_operations",
        "networking"
    ],
    "media-download": [
        "sonarr_management",
        "radarr_management",
        "download_client_management",
        "media_organization"
    ],
    "database": [
        "database_management",
        "migrations",
        "backup_restore",
        "query_optimization"
    ]
}
```

---

### Phase 2: Auto-Generate AgentCards from Registry

**Problem**: AgentCards need to be created from existing registry data.

**Solution**: Extend `sync_registry.py` to also generate AgentCards.

#### Conversion Logic

```python
def generate_agentcard_from_registry(agent_definition: Dict) -> AgentCard:
    """Generate AgentCard from agent definition."""
    
    agent_id = agent_definition["agent_id"]
    specialization = agent_definition.get("specialization", "general")
    
    # Get base capabilities (from base prompt)
    base_capabilities = get_base_capabilities()
    
    # Get specialization-specific capabilities
    specialization_capabilities = get_specialization_capabilities(specialization)
    
    # Combine capabilities
    all_capabilities = base_capabilities + specialization_capabilities
    
    # Get transport info (from A2A config)
    transports = get_default_transports()
    
    # Create AgentCard
    card = create_agentcard(
        agent_id=agent_id,
        name=f"{specialization.replace('-', ' ').title()} Agent",
        capabilities=all_capabilities,
        transports=transports,
        metadata={
            "specialization": specialization,
            "created_by": agent_definition.get("created_by"),
            "status": get_agent_status(agent_id),  # From monitoring DB
            "prompt": agent_definition.get("prompt", "base.md")
        }
    )
    
    return card
```

---

### Phase 3: Sync Both Systems

**Problem**: Keep registry and AgentCards in sync.

**Solution**: Update `sync_registry.py` to:
1. Generate markdown registry (existing)
2. Generate AgentCards (new)
3. Keep both in sync

#### Sync Flow

```
Agent Definition Created
    ↓
sync_registry.py runs
    ↓
├─→ Generate agent-registry.md (markdown)
└─→ Generate agentcards/*.json (JSON)
    ↓
Both systems updated
```

---

## Implementation Plan

### Step 1: Extract Capabilities from Base Prompt

**File**: `agents/registry/capability_extractor.py`

**Purpose**: Parse base prompt and extract structured capabilities.

**Output**: 
- Base capabilities list
- Capability categories
- MCP tool mappings

### Step 2: Extend sync_registry.py

**File**: `agents/registry/sync_registry.py`

**Changes**:
- Add AgentCard generation
- Import AgentCard functions
- Generate AgentCards for all agents
- Update AgentCards when registry changes

### Step 3: Create Capability Mapping

**File**: `agents/registry/capability_mapping.py`

**Purpose**: Map base prompt capabilities to AgentCard format.

**Mappings**:
- Skills → AgentCard capabilities
- MCP tool categories → AgentCard capabilities
- Domain knowledge → AgentCard capabilities
- Specialization → Additional capabilities

### Step 4: Update Agent Definition Creation

**File**: `agents/apps/agent-mcp/tools/agent_management.py`

**Changes**:
- When creating agent definition, also create AgentCard
- Use capability mapping to populate capabilities
- Set transports based on A2A config

### Step 5: Add AgentCard Sync to MCP Tools

**File**: `agents/apps/agent-mcp/tools/agent_management.py`

**New Tool**: `sync_agentcards()`
- Regenerate all AgentCards from registry
- Keep AgentCards in sync with registry

---

## How Base Prompt Fits In

### Base Prompt Role

**Base Prompt** (`agents/prompts/base.md`) defines:
1. **Universal Capabilities** - What ALL agents can do
2. **Workflow** - HOW agents work
3. **Discovery Process** - How agents find things

### AgentCard Role

**AgentCard** defines:
1. **Agent-Specific Capabilities** - What THIS agent can do
2. **Transport Info** - How to reach this agent
3. **Discovery Metadata** - For A2A protocol

### Relationship

```
Base Prompt (Universal)
    ↓
    Defines base capabilities
    ↓
Agent Definition (Specific)
    ↓
    Combines base + specialization
    ↓
AgentCard (A2A-Compliant)
    ↓
    Machine-readable discovery
```

### Capability Flow

1. **Base Prompt** lists universal capabilities:
   - Skills (standard-deployment, troubleshoot-container-failure, etc.)
   - MCP tool categories (docker_management, memory_management, etc.)
   - Domain knowledge (server_management, container_orchestration, etc.)

2. **Agent Definition** adds specialization:
   - Inherits base capabilities
   - Adds specialization-specific capabilities
   - Example: Server management agent gets base + server-specific

3. **AgentCard** represents capabilities:
   - All capabilities from base + specialization
   - Structured for A2A protocol
   - Machine-readable for discovery

---

## Example Conversion

### Before (Registry)

```markdown
## Active Agents

| Agent ID | Specialization | Created By | Created Date | Status | Location |
|----------|---------------|------------|--------------|--------|----------|
| agent-001 | server-management | agent-000 | 2025-01-10 | active | `agents/active/agent-001-server-management/` |
```

### After (Registry + AgentCard)

**Registry** (unchanged - still markdown):
```markdown
| agent-001 | server-management | agent-000 | 2025-01-10 | active | `agents/active/agent-001-server-management/` |
```

**AgentCard** (new - JSON):
```json
{
  "agent_id": "agent-001",
  "name": "Server Management Agent",
  "version": "1.0.0",
  "capabilities": [
    "standard-deployment",
    "troubleshoot-container-failure",
    "system-health-check",
    "deploy-new-service",
    "add-subdomain",
    "cleanup-disk-space",
    "agent-self-documentation",
    "memory_management",
    "docker_management",
    "system_monitoring",
    "git_operations",
    "troubleshooting",
    "networking",
    "system_utilities",
    "agent_management",
    "agent_communication",
    "server_management",
    "container_orchestration",
    "system_administration",
    "deployment",
    "troubleshooting",
    "system_monitoring"
  ],
  "transports": [
    {
      "type": "http",
      "endpoint": "http://localhost:3001/a2a",
      "methods": ["POST"]
    }
  ],
  "authentication": {
    "type": "none",
    "required": false
  },
  "metadata": {
    "specialization": "server-management",
    "created_by": "agent-000",
    "status": "active",
    "prompt": "server.md"
  },
  "created_at": "2025-01-10T10:00:00Z",
  "updated_at": "2025-01-13T12:00:00Z"
}
```

---

## Benefits

### 1. Dual System
- **Registry**: Human-readable, markdown-based (for humans)
- **AgentCard**: Machine-readable, A2A-compliant (for agents)

### 2. Automatic Sync
- Registry changes → AgentCard updates
- AgentCard changes → Registry updates (if needed)
- Both stay in sync automatically

### 3. A2A Compliance
- AgentCards enable A2A protocol discovery
- Agents can find each other automatically
- Capabilities are machine-readable

### 4. Base Prompt Integration
- Base prompt capabilities automatically included
- Specialization capabilities added
- No manual capability management

---

## Migration Steps

### Step 1: Create Capability Extractor
- Parse base prompt
- Extract capabilities
- Create capability mapping

### Step 2: Extend sync_registry.py
- Add AgentCard generation
- Import AgentCard functions
- Generate AgentCards for all agents

### Step 3: Test Conversion
- Run sync_registry.py
- Verify AgentCards generated
- Check capability mapping

### Step 4: Update Agent Creation
- Update `create_agent_definition` tool
- Auto-create AgentCard on agent creation
- Test end-to-end flow

### Step 5: Documentation
- Update registry docs
- Document AgentCard generation
- Explain capability mapping

---

## Files to Create/Modify

### New Files
1. `agents/registry/capability_extractor.py` - Extract capabilities from prompts
2. `agents/registry/capability_mapping.py` - Map capabilities to AgentCard format
3. `agents/registry/AGENTCARD_CONVERSION_PLAN.md` - This file

### Modified Files
1. `agents/registry/sync_registry.py` - Add AgentCard generation
2. `agents/apps/agent-mcp/tools/agent_management.py` - Auto-create AgentCards
3. `agents/registry/agent-registry.md` - Add note about AgentCards

---

## Next Steps

1. ✅ **Plan Created** - This document
2. **Create Capability Extractor** - Parse base prompt
3. **Extend sync_registry.py** - Add AgentCard generation
4. **Test Conversion** - Verify AgentCards generated correctly
5. **Update Agent Creation** - Auto-create AgentCards
6. **Documentation** - Update docs

---

**Last Updated**: 2025-01-13  
**Status**: Planning Complete - Ready for Implementation

