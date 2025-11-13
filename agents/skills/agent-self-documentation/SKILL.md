---
name: agent-self-documentation
description: How agents should organize and store their own documentation, plans, and notes in namespaced directories
category: configuration
mcp_tools_required:
  - create_agent_doc
  - list_agent_docs
  - read_agent_doc
  - update_agent_doc
  - get_agent_doc_structure
prerequisites:
  - Agent ID known
  - Understanding of agent directory structure
---

# Agent Self-Documentation Skill

## When to Use This Skill

Use this skill when:
- Creating implementation plans
- Taking research notes
- Documenting architecture decisions
- Saving reference materials
- Organizing agent-specific documentation

**This skill ensures all agent documentation is properly namespaced and can be automatically archived.**

## Overview

This skill provides guidance on how agents should organize their own documentation, plans, and notes in their namespaced directory structure. This prevents documentation from being dumped into shared directories and ensures proper cleanup when agents are archived.

## The Problem

Without proper namespacing:
- Documentation scattered across `agents/docs/`
- Hard to find agent-specific files
- Difficult to clean up when agent work completes
- No automatic archiving of agent documentation

## The Solution

**Namespaced Agent Documentation** - All agent-specific files go in `agents/active/{agent-id}/docs/`

## Directory Structure

```
agents/active/{agent-id}/
├── dev-docs/              # Dev docs (plan, context, tasks) - managed by dev docs system
│   └── {task-name}-*.md
├── docs/                  # YOUR documentation (create this!)
│   ├── plans/             # Implementation plans
│   ├── notes/             # Working notes, research
│   ├── architecture/      # System designs
│   └── references/        # External references
└── (other agent files)
```

## Workflow Steps

### Step 1: Create Documentation Directory

**Option A: Use MCP Tool (Recommended)**
```python
# Create a document - this automatically creates the directory structure
create_agent_doc(
    agent_id="agent-001",
    doc_type="plan",
    doc_name="feature-x-implementation",
    content="# Implementation Plan\n\n..."
)
```

**Option B: Create Manually**
```bash
mkdir -p agents/active/agent-001/docs/{plans,notes,architecture,references}
```

### Step 2: Create Documentation

Use MCP tools to create properly namespaced documentation:

```python
# Create implementation plan
create_agent_doc(
    agent_id="agent-001",
    doc_type="plan",
    doc_name="feature-x-implementation",
    content="# Implementation Plan\n\n## Overview\n..."
)

# Create research notes
create_agent_doc(
    agent_id="agent-001",
    doc_type="note",
    doc_name="database-options-research",
    content="# Database Options Research\n\n## Findings\n..."
)

# Create architecture design
create_agent_doc(
    agent_id="agent-001",
    doc_type="architecture",
    doc_name="system-design",
    content="# System Architecture\n\n## Components\n..."
)
```

### Step 3: Reference Documentation

Reference your documentation in your work:

```python
# List your documentation
docs = list_agent_docs(agent_id="agent-001", doc_type="plan")

# Read documentation
plan = read_agent_doc(
    agent_id="agent-001",
    doc_type="plan",
    doc_name="feature-x-implementation"
)
```

### Step 4: Update Documentation

Update documentation as work progresses:

```python
# Update with new information
update_agent_doc(
    agent_id="agent-001",
    doc_type="note",
    doc_name="research-notes",
    content="\n\n## New Finding\n\n...",
    append=True
)
```

## Documentation Types

### Plans (`docs/plans/`)

**Purpose**: Detailed implementation plans for features or tasks.

**When to Create**:
- Before implementing major features
- When planning complex workflows
- When breaking down large tasks

**Example**:
```python
create_agent_doc(
    agent_id="agent-001",
    doc_type="plan",
    doc_name="trading-bot-deployment",
    content="""
# Trading Bot Deployment Plan

## Overview
Deploy trading bot service to production.

## Steps
1. Setup database
2. Configure environment
3. Deploy service
4. Verify deployment
"""
)
```

### Notes (`docs/notes/`)

**Purpose**: Working notes, research findings, temporary documentation.

**When to Create**:
- During codebase research
- When taking notes during implementation
- When documenting findings

**Example**:
```python
create_agent_doc(
    agent_id="agent-001",
    doc_type="note",
    doc_name="database-options-research",
    content="""
# Database Options Research

## Options Considered
1. PostgreSQL - ACID compliance
2. SQLite - Simple but no concurrent writes

## Decision
PostgreSQL chosen for concurrent write support.
"""
)
```

### Architecture (`docs/architecture/`)

**Purpose**: System designs, architecture diagrams, technical specifications.

**When to Create**:
- When designing system architecture
- When creating technical specifications
- When documenting system structure

**Example**:
```python
create_agent_doc(
    agent_id="agent-001",
    doc_type="architecture",
    doc_name="trading-system-design",
    content="""
# Trading System Architecture

## Components
- API Service
- Trading Engine
- Database

## Data Flow
[Diagram description]
"""
)
```

### References (`docs/references/`)

**Purpose**: External references, API documentation, links to resources.

**When to Create**:
- When collecting external resources
- When documenting API references
- When saving useful links

**Example**:
```python
create_agent_doc(
    agent_id="agent-001",
    doc_type="reference",
    doc_name="api-documentation",
    content="""
# API References

## External APIs
- Trading API: https://api.example.com/docs
- Market Data: https://market.example.com/docs
"""
)
```

## MCP Tools Used

This skill uses the following MCP tools:

1. **`create_agent_doc()`** - Create agent documentation
2. **`list_agent_docs()`** - List all documentation for an agent
3. **`read_agent_doc()`** - Read agent documentation
4. **`update_agent_doc()`** - Update agent documentation
5. **`get_agent_doc_structure()`** - Get documentation directory structure

## Best Practices

### 1. Always Use Agent Directory

**✅ DO:**
```python
# Create in agent directory
create_agent_doc(
    agent_id="agent-001",
    doc_type="plan",
    doc_name="feature-x",
    content="..."
)
# Creates: agents/active/agent-001/docs/plans/feature-x.md
```

**❌ DON'T:**
```python
# Don't create in root docs directory
# DON'T: agents/docs/agent-001-plan.md
# DON'T: agents/docs/feature-x-plan.md
```

### 2. Use Descriptive Names

**✅ DO:**
- `feature-x-implementation-plan.md`
- `database-research-notes.md`
- `api-integration-design.md`

**❌ DON'T:**
- `plan.md`
- `notes.md`
- `doc.md`

### 3. Keep Documentation Focused

**✅ DO:**
- One document per topic
- Clear, focused content
- Easy to find and reference

**❌ DON'T:**
- One giant document with everything
- Unclear naming
- Hard to navigate

### 4. Update Documentation Regularly

**✅ DO:**
- Update plans as work progresses
- Add notes as you discover things
- Keep documentation current

**❌ DON'T:**
- Create and forget
- Leave outdated information
- Never update

## Integration with Other Systems

### Dev Docs System

**Dev docs** (`dev-docs/`) are separate from agent documentation:
- Dev docs: Task-specific context preservation
- Agent docs: Agent-specific plans, notes, research

**Both** are archived together when agent is archived.

### Memory System

**Memory** is for institutional knowledge:
- Memory: Decisions and patterns (shared across agents)
- Agent docs: Agent-specific plans and notes

**Use memory** for important decisions that should be shared.
**Use agent docs** for agent-specific planning and notes.

### Task Coordination

**Tasks** are tracked in central registry:
- Tasks: Central task registry
- Agent docs: Agent-specific planning around tasks

**Tasks** track what needs to be done.
**Agent docs** contain detailed plans for how to do it.

## Lifecycle Management

### When Agent is Active

All documentation lives in:
```
agents/active/{agent-id}/docs/
```

### When Agent is Archived

All documentation automatically moves to:
```
agents/archive/{agent-id}/docs/
```

**This happens automatically** when `archive_agent()` is called - the entire agent directory (including `docs/`) is moved to archive.

### When Agent is Reactivated

Documentation can be accessed from archive:
```
agents/archive/{agent-id}/docs/
```

Or copied back to active if needed.

## Examples

### Example 1: Creating Implementation Plan

```python
# Create plan in agent directory
create_agent_doc(
    agent_id="agent-001",
    doc_type="plan",
    doc_name="trading-bot-deployment",
    content="""
# Trading Bot Deployment Plan

## Overview
Deploy trading bot service to production.

## Steps
1. Setup database
2. Configure environment
3. Deploy service
4. Verify deployment

## Dependencies
- PostgreSQL database
- API keys configured
"""
)
```

### Example 2: Taking Research Notes

```python
# Create research notes
create_agent_doc(
    agent_id="agent-001",
    doc_type="note",
    doc_name="database-options-research",
    content="""
# Database Options Research

## Options Considered
1. PostgreSQL - ACID compliance, concurrent writes
2. SQLite - Simple, but no concurrent writes

## Decision
PostgreSQL chosen for concurrent write support.
"""
)
```

### Example 3: Listing Documentation

```python
# List all documentation
all_docs = list_agent_docs(agent_id="agent-001")

# List only plans
plans = list_agent_docs(agent_id="agent-001", doc_type="plan")
```

## Error Handling

### "Document not found"

**Solution**: 
- Check document name matches exactly
- Use `list_agent_docs()` to see all available documents
- Create document if it doesn't exist

### "Invalid doc_type"

**Solution**:
- Use one of: "plan", "note", "architecture", "reference"
- Check spelling and case

## Related Skills

- **`standard-deployment`** - For deployment workflows
- **Dev Docs System** - For task-specific context preservation

## Notes

- **All agent documentation** should go in `agents/active/{agent-id}/docs/`
- **Never create files** in `agents/docs/` - that's for shared documentation
- **Automatic archiving** - All docs move to archive when agent is archived
- **Use MCP tools** - They ensure proper namespacing and structure

---

**Last Updated**: 2025-01-13  
**Status**: Active  
**See Also**:
- `agents/docs/AGENT_SELF_DOCUMENTATION.md` - Complete guide
- `agents/docs/DEV_DOCS_SYSTEM.md` - Dev docs system (separate)

