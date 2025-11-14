# Memory Query Helper Script

## Overview

`query_memory.sh` is a fallback tool for querying agent memory when MCP tools are not available. This script provides a command-line interface to the SQLite memory database.

## Usage

```bash
./query_memory.sh [command] [options]
```

## Commands

### Query Decisions

```bash
./query_memory.sh decisions [--project PROJECT] [--limit N] [--search TEXT]
```

**Examples:**
```bash
# Get recent decisions for a project
./query_memory.sh decisions --project home-server --limit 5

# Search decisions
./query_memory.sh decisions --search "PostgreSQL" --limit 10

# Combine filters
./query_memory.sh decisions --project home-server --search "database" --limit 5
```

### Query Patterns

```bash
./query_memory.sh patterns [--severity low|medium|high] [--limit N] [--search TEXT]
```

**Examples:**
```bash
# Get high-severity patterns
./query_memory.sh patterns --severity high

# Search patterns
./query_memory.sh patterns --search "type hints" --limit 5
```

### Full-Text Search

```bash
./query_memory.sh search QUERY [--limit N]
```

**Examples:**
```bash
# Search across all memories
./query_memory.sh search "PostgreSQL database"

# Limit results
./query_memory.sh search "Wonder" --limit 5
```

### Get Recent Decisions

```bash
./query_memory.sh recent [--limit N]
```

**Examples:**
```bash
# Get 5 most recent decisions
./query_memory.sh recent --limit 5

# Get 10 most recent
./query_memory.sh recent --limit 10
```

### Get Context by Task

```bash
./query_memory.sh context --task TASK
```

**Examples:**
```bash
# Get context for a specific task
./query_memory.sh context --task T1.3

# Partial task match
./query_memory.sh context --task memory-test
```

## Help

```bash
./query_memory.sh help
```

## When to Use

- **MCP tools not available**: When the MCP server is not connected or accessible
- **Quick queries**: For fast command-line queries without starting Python
- **Debugging**: To verify memory contents directly
- **Scripting**: Can be used in shell scripts for automation

## Database Location

The script automatically finds the database at:
```
agents/memory/memory.db
```

## Requirements

- `sqlite3` command-line tool must be installed
- Database file must exist at the expected location

## Integration with Documentation

This script implements the fallback methods documented in:
- `agents/prompts/base.md` - Fallback section
- `agents/docs/MCP_TOOL_DISCOVERY.md` - Memory Operations fallback
- `agents/prompts/server.md` - Memory System fallback
- `agents/docs/AGENT_WORKFLOW.md` - Memory fallback methods

## Examples

```bash
# Find all decisions about databases
./query_memory.sh search "database"

# Get high-priority patterns
./query_memory.sh patterns --severity high --limit 10

# Find recent work on a project
./query_memory.sh decisions --project home-server --limit 5

# Search for specific content
./query_memory.sh decisions --search "PostgreSQL" --project home-server
```

---

**Note**: Always prefer MCP tools when available. Use this script only as a fallback when MCP is unavailable.

