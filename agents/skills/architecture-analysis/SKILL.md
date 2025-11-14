---
name: architecture-analysis
description: Analyze system architecture, identify gaps, and create reality-checked implementation plans
category: configuration
mcp_tools_required:
  - codebase_search
  - read_file
  - list_dir
  - grep
prerequisites:
  - Understanding of current system architecture
  - Access to documentation and codebase
---

# Architecture Analysis Skill

## When to Use This Skill

Use this skill when:
- Reviewing new protocols or standards for adoption
- Auditing current system against best practices
- Identifying gaps between current and desired architecture
- Creating implementation plans that match reality
- Understanding constraints (e.g., Cursor sessions vs. process-based)

**This skill ensures implementation plans are grounded in actual system capabilities.**

## Overview

This skill provides a systematic approach to analyzing architecture, understanding constraints, and creating realistic implementation plans that distinguish between what can be done NOW vs. what needs to wait for LATER capabilities.

## The Problem

Without proper architecture analysis:
- Plans assume capabilities that don't exist
- Implementation fails because constraints weren't understood
- Time wasted on features that can't work in current architecture
- Confusion between ideal and actual system state

## The Solution

**Reality-Checked Architecture Analysis** - Always understand current architecture before planning.

## Workflow Steps

### Step 1: Understand Current Architecture

**Use codebase search to understand how system actually works:**

```python
# Search for how agents are executed
codebase_search(
    query="How are agents currently executed? Are they spawned as processes or run in sessions?",
    target_directories=[]
)

# Search for communication patterns
codebase_search(
    query="How do agents communicate? File-based or protocol-based?",
    target_directories=[]
)

# Read key architecture documents
read_file("agents/docs/AGENT_SPAWNING_ARCHITECTURE.md")
read_file("agents/README.md")
```

**Key Questions to Answer:**
- Are agents processes or sessions?
- How is state managed (files vs. memory)?
- What communication mechanisms exist?
- What are the actual constraints?

### Step 2: Identify Architecture Constraints

**Document what the system CAN and CANNOT do:**

```markdown
## Current Architecture Reality

**Agents = Cursor Sessions**
- Ephemeral (session ends when Cursor closes)
- Human-initiated (human opens new Cursor session)
- File-based coordination
- No runtime process spawning

**Communication**
- File-based messaging
- A2A protocol implemented but agents don't spawn processes
- MCP tools provide capabilities

**State Management**
- File-based state
- SQLite memory system
- Monitoring dashboard
```

### Step 3: Compare Against Desired Architecture

**Analyze what the new protocol/standard requires:**

```markdown
## Desired Architecture (from protocol/standard)

**Requirements:**
- Process-based agents
- Dynamic spawning
- In-memory state
- Protocol-based communication

## Gap Analysis

**What Works NOW:**
- File-based features ✅
- Session-based features ✅
- MCP tool integration ✅

**What Needs LATER:**
- Process spawning ⏸️
- Dynamic agent creation ⏸️
- Cross-process coordination ⏸️
```

### Step 4: Create Reality-Checked Plan

**Split implementation into NOW vs. LATER:**

```markdown
## Implementation Plan

### NOW - Works with Current Architecture
- Feature A (file-based) ✅
- Feature B (session-based) ✅

### LATER - Needs Dynamic Spawning
- Feature C (process-based) ⏸️
- Feature D (cross-process) ⏸️
```

### Step 5: Document Architecture Context

**Create architecture reality check document:**

```markdown
# Architecture Reality Check

**Current**: [What actually exists]
**Future**: [What will exist when capability available]
**Gap**: [What's missing]
**Recommendation**: [What to do NOW vs. LATER]
```

## MCP Tools Used

- `codebase_search()` - Understand how system works
- `read_file()` - Read architecture docs
- `list_dir()` - Explore directory structure
- `grep()` - Find specific patterns

## Examples

### Example: A2A Protocol Analysis

**Step 1: Understand Current**
- Agents are Cursor sessions
- Communication is file-based
- A2A endpoints exist but agents don't spawn

**Step 2: Identify Constraints**
- Can't spawn agents dynamically
- Can't coordinate across processes
- Can use A2A endpoints for discovery

**Step 3: Create Plan**
- NOW: Use A2A for discovery, file-based messaging
- LATER: Full A2A when process spawning available

## Error Handling

**Common Mistakes:**
- Assuming process-based when sessions are used
- Planning features that require unavailable capabilities
- Not checking actual architecture before planning

**How to Avoid:**
- Always search codebase first
- Read architecture documentation
- Test assumptions with codebase_search
- Create reality check document

## Related Skills

- `implementation-planning` - Create NOW vs. LATER plans
- `code-implementation` - Implement following patterns
- `documentation-creation` - Document architecture decisions

---

**Last Updated**: 2025-01-13  
**Status**: Active  
**Created By**: Auto (architecture analysis session)

