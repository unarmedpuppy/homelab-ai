# Agent Self-Documentation Guide

**How agents should organize and store their own documentation, plans, and notes.**

---

## The Problem

Agents may create documentation, plans, and notes in various locations, making it hard to:
- Find agent-specific documentation
- Clean up when agent work is complete
- Archive agent work properly
- Maintain organized project structure

## The Solution

**Namespaced Agent Documentation** - All agent-specific files go in the agent's own directory.

---

## Directory Structure

### Active Agent Directory

```
agents/active/{agent-id}/
├── dev-docs/              # Dev docs (plan, context, tasks) - managed by dev docs system
│   ├── {task-name}-plan.md
│   ├── {task-name}-context.md
│   └── {task-name}-tasks.md
├── docs/                  # Agent-specific documentation (YOU create this)
│   ├── plans/             # Implementation plans
│   │   └── feature-x-plan.md
│   ├── notes/             # Working notes, research, decisions
│   │   ├── research-notes.md
│   │   └── decision-log.md
│   ├── architecture/       # Architecture diagrams, designs
│   │   └── system-design.md
│   └── references/        # Reference materials, links
│       └── api-docs.md
└── (other agent files)
```

### Archived Agent Directory

When agent is archived, entire directory moves to:

```
agents/archive/{agent-id}/
├── dev-docs/              # Archived dev docs
├── docs/                  # Archived documentation
└── (all other agent files)
```

---

## When to Create Agent Documentation

### Create Documentation For:

- ✅ **Implementation Plans** - Detailed plans for features/tasks
- ✅ **Research Notes** - Findings from codebase research
- ✅ **Decision Logs** - Important decisions made during work
- ✅ **Architecture Designs** - System designs, diagrams
- ✅ **Reference Materials** - Links, API docs, external resources
- ✅ **Working Notes** - Temporary notes during implementation

### Don't Create Documentation For:

- ❌ **Memory Entries** - Use memory system instead (`memory_record_decision()`)
- ❌ **Task Lists** - Use task coordination system instead
- ❌ **Messages** - Use communication system instead
- ❌ **Dev Docs** - Use dev docs system instead (`create_dev_docs()`)

---

## Quick Start

### 1. Create Agent Documentation Directory

```python
# Use MCP tool to create properly namespaced documentation
create_agent_doc(
    agent_id="agent-001",
    doc_type="plan",  # or "note", "architecture", "reference"
    doc_name="feature-x-implementation",
    content="# Implementation Plan\n\n..."
)
```

### 2. Or Create Manually

```bash
# Create directory structure
mkdir -p agents/active/agent-001/docs/{plans,notes,architecture,references}

# Create documentation file
touch agents/active/agent-001/docs/plans/feature-x-plan.md
```

### 3. Reference in Your Work

```python
# When creating plans or notes, reference your agent directory
# Example: "See agents/active/agent-001/docs/plans/feature-x-plan.md"
```

---

## Documentation Types

### Plans (`docs/plans/`)

**Purpose**: Detailed implementation plans for features or tasks.

**When to Create**:
- Before implementing major features
- When planning complex workflows
- When breaking down large tasks

**Example**:
```markdown
# Feature X Implementation Plan

## Overview
[Feature description]

## Architecture
[System design]

## Implementation Steps
1. Step 1
2. Step 2

## Dependencies
[List dependencies]
```

### Notes (`docs/notes/`)

**Purpose**: Working notes, research findings, temporary documentation.

**When to Create**:
- During codebase research
- When taking notes during implementation
- When documenting findings

**Example**:
```markdown
# Research Notes: Database Options

## Findings
- Option 1: PostgreSQL
- Option 2: SQLite

## Decision
[Decision made]
```

### Architecture (`docs/architecture/`)

**Purpose**: System designs, architecture diagrams, technical specifications.

**When to Create**:
- When designing system architecture
- When creating technical specifications
- When documenting system structure

**Example**:
```markdown
# System Architecture

## Components
[Component descriptions]

## Data Flow
[Data flow diagrams]

## Integration Points
[Integration details]
```

### References (`docs/references/`)

**Purpose**: External references, API documentation, links to resources.

**When to Create**:
- When collecting external resources
- When documenting API references
- When saving useful links

**Example**:
```markdown
# API References

## External APIs
- API 1: [link]
- API 2: [link]

## Documentation
- Doc 1: [link]
```

---

## Best Practices

### 1. Use Proper Namespacing

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

### 5. Clean Up When Done

**✅ DO:**
- Archive documentation when task complete
- Move to archive via lifecycle management
- Keep active directory clean

**❌ DON'T:**
- Leave old documentation in active directory
- Never archive completed work

---

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

---

## Lifecycle Management

### When Agent is Active

All documentation lives in:
```
agents/active/{agent-id}/docs/
```

### When Agent is Archived

All documentation moves to:
```
agents/archive/{agent-id}/docs/
```

**This happens automatically** when `archive_agent()` is called.

### When Agent is Reactivated

Documentation can be accessed from archive:
```
agents/archive/{agent-id}/docs/
```

Or copied back to active if needed.

---

## MCP Tools

### Create Agent Documentation

```python
create_agent_doc(
    agent_id="agent-001",
    doc_type="plan",  # "plan", "note", "architecture", "reference"
    doc_name="feature-x-implementation",
    content="# Plan content..."
)
```

### List Agent Documentation

```python
list_agent_docs(
    agent_id="agent-001",
    doc_type="plan"  # Optional filter
)
```

### Read Agent Documentation

```python
read_agent_doc(
    agent_id="agent-001",
    doc_type="plan",
    doc_name="feature-x-implementation"
)
```

### Update Agent Documentation

```python
update_agent_doc(
    agent_id="agent-001",
    doc_type="plan",
    doc_name="feature-x-implementation",
    content="# Updated content..."
)
```

---

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

### Example 3: Architecture Design

```python
# Create architecture document
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

---

## File Naming Conventions

### Plans
- `{feature-name}-plan.md`
- `{task-name}-implementation.md`
- `{component-name}-design.md`

### Notes
- `{topic}-research-notes.md`
- `{date}-working-notes.md`
- `{topic}-findings.md`

### Architecture
- `{system-name}-architecture.md`
- `{component-name}-design.md`
- `{integration-name}-spec.md`

### References
- `{topic}-references.md`
- `{api-name}-docs.md`
- `{resource-name}-links.md`

---

## Troubleshooting

### "Where should I put this documentation?"

**Answer**: In your agent directory: `agents/active/{agent-id}/docs/`

### "Should this go in memory or agent docs?"

**Answer**:
- **Memory**: Important decisions/patterns that should be shared
- **Agent docs**: Agent-specific plans, notes, research

### "What happens when I'm archived?"

**Answer**: All your documentation moves to `agents/archive/{agent-id}/docs/` automatically.

### "Can I access archived documentation?"

**Answer**: Yes, it's in `agents/archive/{agent-id}/docs/` and can be read/referenced.

---

**Last Updated**: 2025-01-13  
**Status**: Active  
**See Also**:
- `agents/docs/DEV_DOCS_SYSTEM.md` - Dev docs system (separate from agent docs)
- `agents/docs/AGENT_PROMPT.md` - Main agent prompt
- `agents/lifecycle/policy.md` - Lifecycle management policy

