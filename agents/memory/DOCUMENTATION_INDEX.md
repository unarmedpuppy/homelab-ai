# Agent Memory Documentation Index

Complete guide to all memory system documentation.

## Quick Start

**New to memory?** Start here:
1. `README.md` - Overview and quick start
2. `MEMORY_USAGE_EXAMPLES.md` - Real-world examples ⭐
3. `MCP_TOOLS_GUIDE.md` - Complete MCP tool reference

## Documentation Files

### Core Documentation

- **`README.md`** - Main overview, architecture, usage basics
- **`ARCHITECTURE.md`** - System architecture (library vs server)
- **`MEMORY_USAGE_EXAMPLES.md`** ⭐ - **Real-world examples and best practices**
- **`MCP_TOOLS_GUIDE.md`** - Complete MCP tool reference with examples
- **`QUERY_MEMORY_README.md`** - Helper script usage guide (fallback when MCP unavailable)

### Setup & Integration

- **`SETUP_GUIDE.md`** - Memori setup (for future integration)
- **`INSTALL.md`** - Installation instructions
- **`INTEGRATION_CLARIFICATION.md`** - Clarification on agent architecture

### Reference

- **`README_FILE_BASED.md`** - File-based memory system (legacy)
- **`HYBRID_MEMORY_PROPOSAL.md`** - Hybrid memory proposal

## Access Methods

### 1. MCP Tools (Preferred)

**When**: MCP server is available and connected

**Tools**: 9 memory management tools
- Query: `memory_query_decisions`, `memory_query_patterns`, `memory_search`, etc.
- Record: `memory_record_decision`, `memory_record_pattern`, `memory_save_context`
- Export: `memory_export_to_markdown`

**See**: `MCP_TOOLS_GUIDE.md` for complete reference

### 2. Helper Script (Fallback)

**When**: MCP tools are not available

**Script**: `query_memory.sh`

**Usage**:
```bash
cd apps/agent_memory
./query_memory.sh decisions --project home-server --limit 5
./query_memory.sh patterns --severity high
./query_memory.sh search "your query"
```

**See**: `QUERY_MEMORY_README.md` for complete usage guide

### 3. Direct Python Import

**When**: Writing Python scripts

**Usage**:
```python
from agents.memory import get_memory

memory = get_memory()
decisions = memory.query_decisions(project="home-server", limit=5)
```

**See**: `README.md` for Python API examples

## Integration with Documentation

### Agent Prompts

Memory is integrated into:
- `agents/docs/AGENT_PROMPT.md` - Main agent prompt
- `agents/docs/SERVER_AGENT_PROMPT.md` - Server agent prompt
- `agents/docs/AGENT_WORKFLOW.md` - Agent workflow guide
- `agents/docs/MCP_TOOL_DISCOVERY.md` - Tool discovery guide

### MCP Server

Memory tools are available via:
- `agents/apps/agent-mcp/README.md` - MCP server tool catalog
- `agents/apps/agent-mcp/tools/memory.py` - Memory tool implementation

## Quick Reference

### Before Starting Work
```python
# Check memory first
memory_query_decisions(project="home-server", limit=5)
memory_query_patterns(severity="high", limit=5)
memory_search("your search query")
```

### During Work
```python
# Record decisions
memory_record_decision(content="...", rationale="...", importance=0.9)

# Record patterns
memory_record_pattern(name="...", description="...", solution="...")

# Update context
memory_save_context(agent_id="...", task="...", current_work="...")
```

### After Work
```python
# Save final context
memory_save_context(..., status="completed")
```

### Fallback (No MCP)
```bash
./query_memory.sh decisions --project home-server --limit 5
./query_memory.sh patterns --severity high
./query_memory.sh search "your query"
```

## Best Practices

1. **Always check memory first** - Query before making decisions
2. **Record important decisions** - With clear rationale and appropriate importance
3. **Record patterns** - For common issues and solutions
4. **Update context regularly** - Keep others informed of your work
5. **Use consistent tags** - For better discovery
6. **Link related memories** - Via shared tags

**See**: `MEMORY_USAGE_EXAMPLES.md` for complete best practices and examples.

---

**Last Updated**: 2025-01-13
**Status**: Active

