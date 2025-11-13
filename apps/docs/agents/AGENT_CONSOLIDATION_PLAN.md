# Agent System Consolidation Plan

## Current Structure Analysis

### Current Scattered Locations

1. **`agents/`** (root)
   - `registry/` - Agent registry, definitions, templates
   - `active/` - Active agent directories
   - `archive/` - Archived agents
   - `tasks/` - Task coordination registry
   - `ACTIVATION_GUIDE.md` - Agent activation guide

2. **`apps/docs/agents/`**
   - Agent documentation (workflows, prompts, guides)
   - 18 files including AGENT_PROMPT.md, AGENT_WORKFLOW.md, etc.

3. **`apps/agent_memory/`**
   - Memory system (SQLite, Python code)
   - Documentation and guides
   - Memory database and exports

4. **`server-management-skills/`** (root)
   - Skills library
   - Skill definitions and proposals

5. **`server-management-mcp/`** (root)
   - MCP tools (including agent management, memory, skills, task coordination)
   - Server management tools

## Problems with Current Structure

1. **Documentation Scattered**: Agent docs in `apps/docs/agents/`, but agent registry in `agents/`
2. **Memory System Isolated**: Memory in `apps/agent_memory/` but used by agents
3. **Cross-References Complex**: Hard to find related files
4. **No Clear Entry Point**: Where do agents start?
5. **Inconsistent Naming**: `apps/docs/agents/` vs `agents/` vs `apps/agent_memory/`

## Proposed Consolidated Structure

### Option A: Full Consolidation (Recommended)

```
agents/
├── README.md                    # Main entry point - START HERE
├── docs/                        # All agent documentation
│   ├── README.md                # Documentation index
│   ├── AGENT_PROMPT.md          # Main agent prompt
│   ├── AGENT_WORKFLOW.md        # Workflow guide
│   ├── AGENT_SPAWNING_*.md      # Spawning docs
│   ├── MCP_TOOL_DISCOVERY.md    # Tool discovery
│   └── templates/               # Templates
├── memory/                       # Memory system
│   ├── __init__.py
│   ├── sqlite_memory.py
│   ├── README.md
│   ├── MCP_TOOLS_GUIDE.md
│   └── memory.db
├── registry/                     # Agent registry (keep as-is)
│   ├── agent-registry.md
│   ├── agent-definitions/
│   └── agent-templates/
├── tasks/                        # Task coordination (keep as-is)
│   ├── registry.md
│   └── README.md
├── active/                       # Active agents (keep as-is)
├── archive/                      # Archived agents (keep as-is)
└── ACTIVATION_GUIDE.md           # Keep as-is
```

**MCP Tools & Skills**: Keep at root level (they're infrastructure)
- `server-management-mcp/` - MCP server (used by agents and other systems)
- `server-management-skills/` - Skills library (used by agents and other systems)

### Option B: Minimal Consolidation

```
agents/
├── README.md                    # Main entry point
├── docs/                        # Move from apps/docs/agents/
├── memory/                       # Move from apps/agent_memory/
├── registry/                     # Keep as-is
├── tasks/                        # Keep as-is
├── active/                       # Keep as-is
└── archive/                      # Keep as-is
```

**Keep separate**:
- `apps/docs/agents/` → Move to `agents/docs/`
- `apps/agent_memory/` → Move to `agents/memory/`

## Recommended Approach: Option A

### Benefits

1. **Single Entry Point**: `agents/README.md` - everything agents need
2. **Clear Structure**: All agent-related code/docs in one place
3. **Better Discovery**: Easier to find related files
4. **Logical Grouping**: Memory, docs, registry, tasks all together
5. **Maintains Separation**: MCP and Skills stay at root (infrastructure)

### Migration Steps

1. **Create `agents/docs/`**
   - Move `apps/docs/agents/*` → `agents/docs/`
   - Update all cross-references

2. **Create `agents/memory/`**
   - Move `apps/agent_memory/*` → `agents/memory/`
   - Update imports in MCP tools
   - Update documentation references

3. **Create `agents/README.md`**
   - Main entry point
   - Links to all subdirectories
   - Quick start guide

4. **Update Cross-References**
   - Update all docs that reference old paths
   - Update MCP tool imports
   - Update agent prompts

5. **Update .gitignore**
   - Ensure memory.db and other files are handled

### File Moves

```
apps/docs/agents/*          → agents/docs/
apps/agent_memory/*         → agents/memory/
```

### Import Updates Needed

**MCP Tools** (`server-management-mcp/tools/memory.py`):
```python
# Old
from apps.agent_memory import get_memory

# New
from agents.memory import get_memory
```

**MCP Tools** (`server-management-mcp/tools/task_coordination.py`):
```python
# Already uses project_root, should work with new structure
```

### Documentation Updates Needed

1. **All docs in `agents/docs/`** - Update paths
2. **`agents/README.md`** - Create new entry point
3. **`server-management-mcp/README.md`** - Update memory import path
4. **`server-management-skills/README.md`** - Update any agent references

## Alternative: Keep Current Structure, Improve Organization

If full consolidation is too disruptive:

### Option C: Better Documentation & Symlinks

1. **Create `agents/README.md`** as main entry point
2. **Add symlinks or clear references**:
   - `agents/docs/` → symlink to `apps/docs/agents/`
   - `agents/memory/` → symlink to `apps/agent_memory/`
3. **Improve cross-references** in all docs
4. **Create navigation structure**

## Recommendation

**Go with Option A (Full Consolidation)** because:
- ✅ Cleaner structure
- ✅ Easier for agents to discover resources
- ✅ Better organization
- ✅ Single source of truth
- ⚠️ Requires migration work (but worth it)

**Timing**: Do this after Phase 2 testing, before Phase 3 implementation.

---

**Status**: Proposal
**Next Steps**: 
1. Test Phase 2
2. Get approval for consolidation approach
3. Execute migration if approved

