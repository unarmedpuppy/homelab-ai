# Memory System

SQLite database for persistent agent memory.

## Tables

- **decisions** - Technology choices, architecture decisions
- **patterns** - Common issues and their solutions
- **context** - Work-in-progress state
- **tags** - Tag definitions
- **decision_tags** / **pattern_tags** - Tag associations

## Usage

### Query Decisions

```bash
# Recent decisions
sqlite3 memory.db "SELECT content, rationale, project FROM decisions ORDER BY created_at DESC LIMIT 10;"

# By project
sqlite3 memory.db "SELECT * FROM decisions WHERE project='trading-bot';"

# Full-text search
sqlite3 memory.db "SELECT * FROM decisions_fts WHERE decisions_fts MATCH 'postgresql';"
```

### Record a Decision

```bash
sqlite3 memory.db "INSERT INTO decisions (content, rationale, project, importance)
VALUES ('Use FastAPI for trading-bot API', 'Async support, good performance', 'trading-bot', 0.8);"
```

### Query Patterns

```bash
# High severity patterns
sqlite3 memory.db "SELECT name, description, solution FROM patterns WHERE severity='high';"

# All patterns
sqlite3 memory.db "SELECT * FROM patterns ORDER BY frequency DESC;"
```

### Record a Pattern

```bash
sqlite3 memory.db "INSERT INTO patterns (name, description, solution, severity)
VALUES ('Docker OOM', 'Container killed due to memory', 'Increase memory limit in docker-compose', 'high');"
```

## Schema

```sql
CREATE TABLE decisions (
    id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    rationale TEXT,
    project TEXT,
    task TEXT,
    importance REAL DEFAULT 0.5,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE patterns (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    solution TEXT,
    severity TEXT DEFAULT 'medium',
    frequency INTEGER DEFAULT 1,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

## Python API

```python
from agents.memory.sqlite_memory import get_sqlite_memory

memory = get_sqlite_memory()

# Query
decisions = memory.query_decisions(project="trading-bot", limit=5)
patterns = memory.query_patterns(severity="high")

# Record
memory.record_decision(
    content="Use PostgreSQL",
    rationale="ACID compliance needed",
    project="trading-bot",
    importance=0.9
)
```
