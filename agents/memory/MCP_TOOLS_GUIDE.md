# Memory MCP Tools - Quick Reference

## Overview

**9 MCP tools** are available for agents to interact with memory. These tools are discoverable via the MCP server and work with Cursor/Claude Desktop.

## How Agents Discover Memory Tools

1. **Check MCP Server**: Review `server-management-mcp/README.md` for available tools
2. **Memory Tools Section**: Look for "Memory Management" category
3. **Use Tools**: Call memory tools like any other MCP tool

## Available Memory Tools

### Query Tools

#### `memory_query_decisions`
Query decisions from memory.

**Parameters:**
- `project` (optional): Filter by project name
- `task` (optional): Filter by task ID or name
- `tags` (optional): Comma-separated tags (e.g., "database,architecture")
- `min_importance` (optional): Minimum importance 0.0-1.0
- `search_text` (optional): Full-text search query
- `limit` (optional): Max results (default: 10)

**Example:**
```python
# Find decisions about PostgreSQL
memory_query_decisions(
    project="trading-journal",
    search_text="PostgreSQL",
    min_importance=0.7
)

# Find decisions by tags
memory_query_decisions(
    tags="database,architecture",
    limit=5
)
```

#### `memory_query_patterns`
Query patterns from memory.

**Parameters:**
- `severity` (optional): low, medium, or high
- `tags` (optional): Comma-separated tags
- `min_frequency` (optional): Minimum frequency count
- `search_text` (optional): Full-text search query
- `limit` (optional): Max results (default: 10)

**Example:**
```python
# Find high-severity patterns
memory_query_patterns(
    severity="high",
    limit=10
)

# Search for patterns about type hints
memory_query_patterns(
    search_text="type hints",
    limit=5
)
```

#### `memory_search`
Full-text search across all memories.

**Parameters:**
- `query`: Search query text
- `limit` (optional): Max results per type (default: 20)

**Example:**
```python
# Search for anything about PostgreSQL
memory_search("PostgreSQL database setup")
```

#### `memory_get_recent_context`
Get recent work context.

**Parameters:**
- `agent_id` (optional): Filter by agent ID
- `limit` (optional): Max results (default: 5)

**Example:**
```python
# Get my recent work
memory_get_recent_context(agent_id="agent-001", limit=5)

# Get all recent work
memory_get_recent_context(limit=10)
```

#### `memory_get_context_by_task`
Get context for a specific task.

**Parameters:**
- `task`: Task ID or name

**Example:**
```python
# Get context for task T1.3
memory_get_context_by_task(task="T1.3")
```

### Recording Tools

#### `memory_record_decision`
Record a decision in memory.

**Parameters:**
- `content`: Decision description (required)
- `rationale`: Why this decision was made
- `project`: Project name (default: "home-server")
- `task`: Task ID or name
- `importance`: Importance score 0.0-1.0 (default: 0.5)
- `tags`: Comma-separated tags

**Example:**
```python
# Record an important decision
memory_record_decision(
    content="Use PostgreSQL for database",
    rationale="Need ACID compliance and complex queries. SQLite doesn't support concurrent writes well.",
    project="trading-journal",
    task="T1.3",
    importance=0.9,
    tags="database,architecture,postgresql"
)
```

#### `memory_record_pattern`
Record or update a pattern in memory.

**Parameters:**
- `name`: Pattern name (required)
- `description`: Pattern description (required)
- `solution`: Solution or workaround
- `severity`: low, medium, or high (default: "medium")
- `frequency`: Frequency count (default: 1, increments if exists)
- `tags`: Comma-separated tags

**Example:**
```python
# Record a pattern
memory_record_pattern(
    name="Missing Type Hints",
    description="Python functions missing type hints, causing review issues",
    solution="Add type hints to all functions. Use typing module for complex types.",
    severity="medium",
    tags="python,code-quality,type-hints"
)

# Pattern frequency auto-increments if pattern already exists
```

#### `memory_save_context`
Save or update current work context.

**Parameters:**
- `agent_id`: Agent identifier (required)
- `task`: Task ID or name (required)
- `current_work`: Description of current work (required)
- `status`: in_progress, completed, or blocked (default: "in_progress")
- `notes`: Additional notes

**Example:**
```python
# Save current work
memory_save_context(
    agent_id="agent-001",
    task="T1.3",
    current_work="Setting up PostgreSQL database. Created docker-compose.yml, configured environment variables. Next: Run migrations.",
    status="in_progress",
    notes="Database password generated with openssl rand -hex 32"
)
```

### Export Tools

#### `memory_export_to_markdown`
Export all memories to markdown files.

**Parameters:**
- `output_path` (optional): Output directory (defaults to agents/memory/memory/export/)

**Example:**
```python
# Export to default location
memory_export_to_markdown()

# Export to custom location
memory_export_to_markdown(output_path="/path/to/export")
```

## Agent Workflow with Memory

### Before Starting Work

```python
# 1. Check for related decisions
decisions = memory_query_decisions(
    project="trading-journal",
    limit=5
)

# 2. Check for common patterns
patterns = memory_query_patterns(
    severity="high",
    limit=5
)

# 3. Search for related work
results = memory_search("PostgreSQL database")
```

### During Work

```python
# Record important decisions as you make them
memory_record_decision(
    content="Use FastAPI for backend API",
    rationale="Consistent with trading-bot, async support",
    project="trading-journal",
    importance=0.9,
    tags="api,framework,fastapi"
)

# Record patterns when you discover them
memory_record_pattern(
    name="Port Conflict Resolution",
    description="Services failing to start due to port conflicts",
    solution="Always check port availability with check_port_status before assigning",
    severity="medium",
    tags="docker,networking,ports"
)

# Update context regularly
memory_save_context(
    agent_id="agent-001",
    task="T1.3",
    current_work="PostgreSQL setup in progress...",
    status="in_progress"
)
```

### After Work

```python
# Save final context
memory_save_context(
    agent_id="agent-001",
    task="T1.3",
    current_work="PostgreSQL setup complete. Database running, migrations applied.",
    status="completed"
)
```

## Benefits of MCP Tools

✅ **Discoverable**: Tools appear in MCP server catalog
✅ **Consistent**: Same pattern as other MCP tools
✅ **Type-safe**: Parameters validated
✅ **Documented**: Tool descriptions in MCP server
✅ **Fast**: SQLite queries (1-10ms)
✅ **Searchable**: Full-text search built-in

## Integration with Skills

Skills can use memory tools to:
- Check previous decisions before making new ones
- Record decisions made during workflow
- Query patterns to avoid common issues
- Save context at workflow completion

**Example in skill:**
```markdown
## Workflow Steps

1. **Check Previous Decisions**
   - Use `memory_query_decisions(project="trading-journal")`
   - Review relevant decisions before proceeding

2. **Make Decision**
   - [Make decision]
   - Use `memory_record_decision(...)` to record

3. **Complete Work**
   - Use `memory_save_context(...)` to save context
```

## ⚠️ Fallback: When MCP Tools Aren't Available

**If MCP tools are not available**, use the helper script:

```bash
# Use helper script for command-line access
cd apps/agent_memory
./query_memory.sh decisions --project home-server --limit 5
./query_memory.sh patterns --severity high --limit 5
./query_memory.sh search "your query"
./query_memory.sh recent --limit 10
```

**See**: `QUERY_MEMORY_README.md` for complete helper script usage guide.

## See Also

- **MCP Server README**: `server-management-mcp/README.md` - Complete tool reference
- **Memory System README**: `agents/memory/README.md` - Memory system details
- **Memory Usage Examples**: `agents/memory/MEMORY_USAGE_EXAMPLES.md` - Real-world examples ⭐
- **Helper Script Guide**: `agents/memory/QUERY_MEMORY_README.md` - Fallback script usage
- **Tool Discovery Guide**: `agents/docs/MCP_TOOL_DISCOVERY.md` - How to discover tools

---

**Status**: Ready to use
**Total Tools**: 9 memory management tools
**Integration**: Fully integrated with MCP server
**Fallback**: Helper script available when MCP unavailable

