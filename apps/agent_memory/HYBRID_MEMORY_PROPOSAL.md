# Hybrid Memory System: SQLite + Markdown

## The Question

**File-based vs Database for memory?**

## Comparison

| Feature | File-Based | SQLite/Database |
|---------|------------|-----------------|
| **Query Speed** | Slow (read all files) | Fast (indexed queries) |
| **Search** | Manual grep | Full-text search |
| **Relationships** | None | Foreign keys |
| **Human Readable** | ✅ Yes | ❌ No |
| **Version Control** | ✅ Yes | ⚠️ Binary file |
| **Setup Complexity** | Low | Medium |
| **Agent Access** | Direct file read/write | Requires query API |

## The Problem with File-Based

**Current file-based approach:**
- ❌ Slow queries (must read all files)
- ❌ No relationships between memories
- ❌ Hard to search across files
- ❌ Manual indexing

**Example**: Finding "all decisions related to PostgreSQL" requires:
1. Read all decision files
2. Search each file for "PostgreSQL"
3. No way to link related decisions

## Solution: Hybrid Approach

**Best of both worlds:**

1. **SQLite for storage** - Fast queries, relationships, indexing
2. **Markdown export** - Human-readable, version controlled
3. **Query API** - Agents can query efficiently
4. **Auto-sync** - Changes sync between SQLite and markdown

### Architecture

```
Agent Action
    ↓
Query API (SQLite)
    ↓
Fast Query Results
    ↓
(Optional) Export to Markdown for human review
```

### Benefits

✅ **Fast queries**: SQLite indexed queries
✅ **Relationships**: Link decisions to patterns, tasks, etc.
✅ **Full-text search**: SQLite FTS5
✅ **Human readable**: Export to markdown when needed
✅ **Version controlled**: Markdown files in git
✅ **Agent-friendly**: Query API + file access

## Implementation

### Option 1: SQLite Primary (Recommended)

**Storage**: SQLite database
**Export**: Markdown files (for human review)
**Query**: Python API or simple query script

**Pros:**
- Fast queries
- Structured data
- Relationships
- Full-text search

**Cons:**
- Requires query API (but agents can use it)
- Binary database file

### Option 2: Hybrid (SQLite + Markdown Sync)

**Storage**: Both SQLite and markdown
**Sync**: Auto-sync between them
**Query**: SQLite for speed, markdown for human review

**Pros:**
- Fast queries (SQLite)
- Human readable (markdown)
- Best of both worlds

**Cons:**
- More complex (sync logic)
- Potential sync issues

### Option 3: Enhanced File-Based (Current + Index)

**Storage**: Markdown files
**Index**: SQLite index for fast queries
**Query**: Query index, read files for details

**Pros:**
- Human readable (primary)
- Fast queries (index)
- Simple

**Cons:**
- Index can get out of sync
- Still need to read files for details

## Recommendation: SQLite Primary with Markdown Export

**Why:**
1. **Fast queries** - Critical for agents finding relevant context
2. **Relationships** - Link decisions to patterns, tasks, etc.
3. **Full-text search** - Find memories quickly
4. **Export to markdown** - Human-readable when needed
5. **Simple query API** - Agents can use helper functions

**Implementation:**
- SQLite database stores all memories
- Markdown export for human review (optional, on-demand)
- Query API for agents
- Full-text search built-in

## Example: SQLite Schema

```sql
CREATE TABLE decisions (
    id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    rationale TEXT,
    project TEXT,
    task TEXT,
    importance REAL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE patterns (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    solution TEXT,
    severity TEXT,
    frequency INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE context (
    id INTEGER PRIMARY KEY,
    agent_id TEXT,
    task TEXT,
    current_work TEXT,
    status TEXT,
    notes TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE tags (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE
);

CREATE TABLE decision_tags (
    decision_id INTEGER,
    tag_id INTEGER,
    FOREIGN KEY (decision_id) REFERENCES decisions(id),
    FOREIGN KEY (tag_id) REFERENCES tags(id)
);

-- Full-text search
CREATE VIRTUAL TABLE decisions_fts USING fts5(
    content, rationale, project, task,
    content_rowid=id
);
```

## Query Examples

**Fast queries with SQLite:**

```python
# Find all decisions about PostgreSQL
decisions = db.query("""
    SELECT * FROM decisions 
    WHERE content LIKE '%PostgreSQL%' 
    OR rationale LIKE '%PostgreSQL%'
    ORDER BY importance DESC, created_at DESC
    LIMIT 10
""")

# Full-text search
decisions = db.query("""
    SELECT * FROM decisions_fts 
    WHERE decisions_fts MATCH 'PostgreSQL database'
    ORDER BY rank
""")

# Find related patterns
patterns = db.query("""
    SELECT p.* FROM patterns p
    JOIN pattern_tags pt ON p.id = pt.pattern_id
    JOIN tags t ON pt.tag_id = t.id
    WHERE t.name IN ('database', 'postgresql')
""")
```

## Agent Usage

**Agents can query efficiently:**

```python
from apps.agent_memory import get_memory

memory = get_memory()

# Fast query
decisions = memory.query_decisions(
    project="trading-journal",
    tags=["database"],
    min_importance=0.7
)

# Full-text search
results = memory.search("PostgreSQL setup configuration")
```

**Or agents can still read markdown files** (exported from SQLite)

## Performance Comparison

**File-based (current):**
- Query time: ~100-500ms (read all files)
- Search: Manual grep, slow
- Relationships: None

**SQLite:**
- Query time: ~1-10ms (indexed)
- Search: Full-text search, fast
- Relationships: Foreign keys

**Improvement**: 10-100x faster queries

## Recommendation

**Use SQLite primary with markdown export:**

1. **Storage**: SQLite database (fast, structured)
2. **Query**: Python API (agents can use)
3. **Export**: Markdown files (human-readable, optional)
4. **Sync**: Auto-export to markdown on changes (optional)

**Benefits:**
- ✅ Fast queries (critical for agents)
- ✅ Relationships (link related memories)
- ✅ Full-text search
- ✅ Human-readable export
- ✅ Simple for agents (query API)

---

**Status**: Proposal
**Priority**: High (significant performance improvement)
**Effort**: Medium (implement SQLite + query API)

