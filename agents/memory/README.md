# Agent Memory System

## Overview

Memory system for agents running in Cursor/Claude Desktop. Uses **SQLite for fast queries** with optional **markdown export for human readability**.

## Why SQLite?

**Performance Benefits:**
- ✅ **10-100x faster queries** than file-based (indexed)
- ✅ **Full-text search** across all memories
- ✅ **Relationships** between decisions, patterns, tasks
- ✅ **Structured data** with proper indexing

**Still Human-Readable:**
- ✅ **Export to markdown** when needed
- ✅ **Version controlled** (export files)
- ✅ **Simple query API** for agents

## Quick Start

### For Agents (Cursor/Claude Desktop)

**Query memories:**

```python
from agents.memory import get_memory

memory = get_memory()

# Find decisions about PostgreSQL
decisions = memory.query_decisions(
    project="trading-journal",
    tags=["database"],
    min_importance=0.7
)

# Full-text search
results = memory.search("PostgreSQL setup configuration")

# Find patterns
patterns = memory.query_patterns(
    severity="high",
    tags=["deployment"]
)
```

**Record memories:**

```python
# Record a decision
decision_id = memory.record_decision(
    content="Use PostgreSQL for database",
    rationale="Need ACID compliance and complex queries",
    project="trading-journal",
    importance=0.9,
    tags=["database", "architecture"]
)

# Record a pattern
pattern_id = memory.record_pattern(
    name="Missing Type Hints",
    description="Python functions missing type hints",
    solution="Add type hints to all functions",
    severity="medium",
    tags=["python", "code-quality"]
)

# Save context
context_id = memory.save_context(
    agent_id="agent-001",
    task="T1.3",
    current_work="Setting up PostgreSQL database",
    status="in_progress"
)
```

### Export to Markdown (Optional)

Export all memories to markdown for human review:

```python
from agents.memory import get_memory

memory = get_memory()
export_path = memory.export_to_markdown()

print(f"Exported to: {export_path}")
# Creates markdown files in agents/memory/memory/export/
```

## Database Location

**SQLite database**: `agents/memory/memory.db`

- Created automatically on first use
- No setup required
- Fast, local, no server needed
- **Just a file** - no server process, no Docker needed

## Access Methods

**Three ways to access memory:**

1. **MCP Tools** (preferred when available)
   - Use `memory_query_decisions()`, `memory_query_patterns()`, etc.
   - See `MCP_TOOLS_GUIDE.md` for complete reference

2. **Helper Script** (fallback when MCP unavailable)
   - Use `./query_memory.sh` for command-line access
   - See `QUERY_MEMORY_README.md` for usage guide

3. **Direct Python Import** (for Python scripts)
   - Use `from agents.memory import get_memory`
   - See examples in `MEMORY_USAGE_EXAMPLES.md`

## Architecture

**Important**: `apps/agent_memory` is **NOT a server** - it's a **Python library** that uses a **SQLite file**.

- ✅ **Python library** - Just code, no server process
- ✅ **SQLite file** - Single database file, no server needed
- ✅ **No Docker required** - Works as-is
- ✅ **Multiple access methods**:
  - Via MCP tools (through dockerized MCP server)
  - Direct Python import
  - Helper script (`query_memory.sh`)

**See**: `ARCHITECTURE.md` for complete architecture details.

## Query Performance

**File-based (old):**
- Query time: ~100-500ms (read all files)
- Search: Manual grep, slow
- No relationships

**SQLite (new):**
- Query time: ~1-10ms (indexed)
- Search: Full-text search, fast
- Relationships: Foreign keys

**Improvement**: 10-100x faster!

## Schema

### Decisions
- `id`, `content`, `rationale`, `project`, `task`, `importance`
- Full-text search on content, rationale, project, task
- Tags via many-to-many relationship

### Patterns
- `id`, `name`, `description`, `solution`, `severity`, `frequency`
- Full-text search on name, description, solution
- Tags via many-to-many relationship

### Context
- `id`, `agent_id`, `task`, `current_work`, `status`, `notes`
- Indexed on agent_id and task

## Full-Text Search

SQLite FTS5 provides fast full-text search:

```python
# Search across all memories
results = memory.search("PostgreSQL database setup")

# Search decisions only
decisions = memory.query_decisions(search_text="PostgreSQL")

# Search patterns only
patterns = memory.query_patterns(search_text="type hints")
```

## Relationships

Link related memories via tags:

```python
# Decisions and patterns can share tags
memory.record_decision(..., tags=["database", "postgresql"])
memory.record_pattern(..., tags=["database", "postgresql"])

# Query by shared tags
decisions = memory.query_decisions(tags=["database"])
patterns = memory.query_patterns(tags=["database"])
```

## Agent Workflow Integration

### Before Starting Work

```python
from agents.memory import get_memory

memory = get_memory()

# Check recent decisions
decisions = memory.query_decisions(project="trading-journal", limit=5)

# Check common patterns
patterns = memory.query_patterns(severity="high", limit=5)

# Search for related work
results = memory.search("database setup")
```

### During Work

```python
# Record important decisions
memory.record_decision(
    content="Use FastAPI for backend",
    rationale="Consistent with trading-bot, async support",
    project="trading-journal",
    importance=0.9
)

# Record patterns as you discover them
memory.record_pattern(
    name="Missing Type Hints",
    description="Python functions missing type hints",
    solution="Add type hints to all functions",
    severity="medium"
)
```

### After Work

```python
# Save context
memory.save_context(
    agent_id="agent-001",
    task="T1.3",
    current_work="PostgreSQL setup complete",
    status="completed"
)
```

## Export to Markdown

For human review or version control:

```python
export_path = memory.export_to_markdown()
# Creates: agents/memory/memory/export/decisions/ and patterns/
```

Exported files are human-readable markdown that can be committed to git.

## Comparison

| Feature | File-Based | SQLite |
|---------|------------|--------|
| **Query Speed** | Slow (100-500ms) | Fast (1-10ms) |
| **Full-Text Search** | Manual grep | Built-in FTS5 |
| **Relationships** | None | Foreign keys |
| **Human Readable** | ✅ Yes | ✅ Export to markdown |
| **Version Control** | ✅ Yes | ✅ Export files |
| **Setup** | None | None (auto-created) |

## Benefits

✅ **Fast queries** - Critical for agents finding relevant context
✅ **Full-text search** - Find memories quickly
✅ **Relationships** - Link decisions to patterns, tasks
✅ **Structured** - Proper indexing and constraints
✅ **Human readable** - Export to markdown when needed
✅ **Simple** - No setup, just use it

## Migration from File-Based

If you have existing file-based memories:

1. **Keep files** - They're still readable
2. **Import to SQLite** (optional script):
   ```python
   from agents.memory import get_memory, FileBasedMemory
   
   file_memory = FileBasedMemory()
   sqlite_memory = get_memory()
   
   # Import decisions
   decisions = file_memory.query_decisions(limit=1000)
   for d in decisions:
       # Read file and import to SQLite
       ...
   ```

## Next Steps

1. **Start using**: Agents can query and record memories
2. **Build knowledge base**: Decisions and patterns accumulate
3. **Query before work**: Check memory before starting tasks
4. **Export periodically**: Export to markdown for review

---

**Status**: Ready to use
**Priority**: High (significant performance improvement)
**Database**: `agents/memory/memory.db` (auto-created)
