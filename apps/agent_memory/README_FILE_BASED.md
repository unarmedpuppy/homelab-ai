# File-Based Memory System

## Overview

Since agents run in **Cursor/Claude Desktop** (not Python), we use a **file-based memory system** that agents can read/write directly. This works because agents have file access.

## How It Works

Memory is stored as **markdown files** organized by type:

```
apps/agent_memory/memory/
├── decisions/
│   ├── 2025-01-10-14-30-00-use-postgresql.md
│   └── 2025-01-11-09-15-00-docker-network-config.md
├── patterns/
│   ├── missing-type-hints.md
│   └── port-conflict-resolution.md
├── context/
│   ├── agent-001-T1.3-2025-01-10.md
│   └── agent-002-T2.1-2025-01-11.md
├── sessions/
│   └── 2025-01-10-session-summary.md
└── index.json
```

## Usage for Agents

### Recording a Decision

Agents can record decisions by creating markdown files:

```markdown
# Decision: Use PostgreSQL for database

**Date**: 2025-01-10 14:30:00
**Project**: home-server
**Task**: T1.3
**Importance**: 0.9

## Decision

Use PostgreSQL for trading journal database

## Rationale

Need ACID compliance and complex queries. SQLite doesn't support concurrent writes well.

## Alternatives Considered

- SQLite (too limited for concurrent access)
- MySQL (PostgreSQL has better JSON support)

## Tags

- database
- architecture
- trading-journal
```

### Recording a Pattern

Agents can record patterns (common issues, solutions):

```markdown
# Pattern: Missing Type Hints

**Severity**: medium
**Frequency**: 5
**Last Updated**: 2025-01-10

## Description

Python functions missing type hints, causing review issues.

## Solution

Add type hints to all functions. Use `typing` module for complex types.

## Examples

1. trade_service.py - missing return type
2. api/routes/trades.py - missing parameter types
```

### Saving Context

Agents can save current work context:

```markdown
# Context: T1.3 - PostgreSQL Setup

**Agent**: agent-001
**Date**: 2025-01-10
**Status**: in_progress

## Current Work

Setting up PostgreSQL database for trading journal.
- Created docker-compose.yml
- Configured environment variables
- Next: Run migrations

## Notes

Database password generated with openssl rand -hex 32
```

## Helper Functions (Optional)

If agents have Python access, they can use helper functions:

```python
from apps.agent_memory.file_based_memory import get_memory

memory = get_memory()

# Record decision
memory.record_decision(
    content="Use PostgreSQL for database",
    rationale="Need ACID compliance",
    project="trading-journal",
    importance=0.9
)

# Query decisions
decisions = memory.query_decisions(project="trading-journal", limit=5)

# Record pattern
memory.record_pattern(
    name="Missing Type Hints",
    description="Python functions missing type hints",
    solution="Add type hints to all functions",
    severity="medium"
)
```

## Integration with Agent Workflow

### Agent Startup

Agents should check memory at startup:

1. **Read recent decisions**: Check `memory/decisions/` for relevant decisions
2. **Check patterns**: Review `memory/patterns/` for common issues
3. **Load context**: Check `memory/context/` for current work

### During Work

Agents should:
1. **Document decisions**: Create decision files when making architectural choices
2. **Record patterns**: Document common issues and solutions
3. **Update context**: Save current work context regularly

### After Work

Agents should:
1. **Save session summary**: Document what was accomplished
2. **Update patterns**: If new patterns discovered, record them
3. **Link related work**: Reference related decisions/patterns

## File Structure

### Decision Files

**Location**: `memory/decisions/YYYY-MM-DD-HH-MM-SS-description.md`

**Required fields**:
- Decision description
- Rationale
- Date
- Project
- Task (optional)
- Importance (0.0-1.0)
- Tags (optional)

### Pattern Files

**Location**: `memory/patterns/pattern-name.md`

**Required fields**:
- Pattern name
- Description
- Solution
- Severity (low, medium, high)
- Frequency (number of occurrences)
- Tags (optional)

### Context Files

**Location**: `memory/context/agent-id-task-date.md`

**Required fields**:
- Agent ID
- Task
- Current work description
- Status (in_progress, completed, blocked)
- Notes (optional)

## Index File

`index.json` maintains a searchable index of all memories:

```json
{
  "decisions": [
    {
      "file": "decisions/2025-01-10-14-30-00-use-postgresql.md",
      "content": "Use PostgreSQL for database",
      "date": "2025-01-10",
      "project": "trading-journal",
      "importance": 0.9,
      "tags": ["database", "architecture"]
    }
  ],
  "patterns": [
    {
      "file": "patterns/missing-type-hints.md",
      "name": "Missing Type Hints",
      "severity": "medium",
      "frequency": 5,
      "tags": ["python", "code-quality"]
    }
  ],
  "contexts": [
    {
      "file": "context/agent-001-T1.3-2025-01-10.md",
      "agent_id": "agent-001",
      "task": "T1.3",
      "status": "in_progress",
      "date": "2025-01-10"
    }
  ],
  "last_updated": "2025-01-10T14:30:00"
}
```

## Benefits

✅ **Works with Cursor/Claude Desktop**: Agents can read/write files
✅ **No code injection needed**: Just file access
✅ **Human readable**: Markdown files are easy to read
✅ **Version controlled**: Files can be committed to git
✅ **Searchable**: Index file enables quick queries
✅ **Simple**: No complex setup required

## Comparison with Memori

| Feature | Memori | File-Based |
|---------|--------|------------|
| **Works with Cursor/Claude** | ❌ No | ✅ Yes |
| **Automatic** | ✅ Yes | ❌ Manual |
| **Setup complexity** | Medium | Low |
| **Human readable** | ❌ No | ✅ Yes |
| **Version control** | ❌ No | ✅ Yes |
| **Query speed** | Fast | Medium |

## Next Steps

1. **Create memory directory**: Already created by helper
2. **Start recording**: Agents begin documenting decisions
3. **Build knowledge base**: Patterns and decisions accumulate
4. **Query before work**: Agents check memory before starting

---

**Status**: Ready to use
**Priority**: High
**Effort**: Low (just create files!)

