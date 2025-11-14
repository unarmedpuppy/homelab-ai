---
name: implementation-planning
description: Create detailed implementation plans with NOW vs. LATER designation for phased implementation
category: configuration
mcp_tools_required:
  - read_file
  - write
  - codebase_search
prerequisites:
  - Architecture analysis complete
  - Understanding of current vs. future capabilities
---

# Implementation Planning Skill

## When to Use This Skill

Use this skill when:
- Creating detailed implementation plans
- Phasing features between NOW and LATER
- Preserving future plans while implementing current capabilities
- Documenting migration paths
- Planning multi-phase implementations

**This skill ensures plans are actionable NOW while preserving detailed future plans.**

## Overview

This skill provides a systematic approach to creating implementation plans that clearly separate what can be implemented NOW (with current architecture) from what needs to wait LATER (when capabilities are available).

## The Problem

Without proper planning:
- Plans mix current and future capabilities
- Implementation blocked by unavailable features
- Future plans lost when focusing on current work
- No clear migration path from NOW to LATER

## The Solution

**NOW vs. LATER Planning** - Split plans into actionable NOW sections and preserved LATER sections.

## Workflow Steps

### Step 1: Review Architecture Analysis

**Read the architecture reality check:**

```python
read_file("agents/docs/IMPLEMENTATION_PLANS/ARCHITECTURE_REALITY_CHECK.md")
```

**Understand:**
- What works NOW
- What needs LATER
- Current constraints

### Step 2: Create Plan Structure

**Create plan with clear NOW vs. LATER sections:**

```markdown
# Implementation Plan: [Feature Name]

## ⚠️ Architecture Context

**Current Architecture**: [Description]
**Future Architecture**: [Description]

This plan includes **TWO implementations**:
1. **NOW**: [What works with current architecture]
2. **LATER**: [What works with future architecture]

---

# PART 1: NOW - [Current Architecture]

**Status**: ✅ Ready to implement
**Architecture**: [Current architecture]
**Timeline**: [X weeks]

## NOW: Overview
[Description of NOW implementation]

## NOW: Architecture
[Components for NOW]

## NOW: Implementation Steps
[Detailed steps]

## NOW: Success Criteria
[What success looks like]

---

# PART 2: LATER - [Future Architecture]

**Status**: ⏸️ Deferred until [capability] available
**Architecture**: [Future architecture]
**Timeline**: [X weeks when ready]

## LATER: Overview
[Description of LATER implementation]

## LATER: Architecture
[Components for LATER]

## LATER: Implementation Steps
[Detailed steps - preserved for future]

## LATER: Success Criteria
[What success looks like]

---

## Migration Path: NOW → LATER

[How to migrate from NOW to LATER when ready]
```

### Step 3: Write NOW Section

**Focus on what can be implemented immediately:**

- Use current architecture patterns
- File-based if sessions
- MCP tools if available
- Clear, actionable steps

### Step 4: Write LATER Section

**Preserve detailed plans for future:**

- Full implementation details
- Future architecture patterns
- Process-based if needed
- Complete code examples

### Step 5: Document Migration Path

**Show how to move from NOW to LATER:**

```markdown
## Migration Path: NOW → LATER

When [capability] is available:

1. Keep [NOW component] as [fallback/persistence]
2. Add [LATER component] for [new capability]
3. Migrate [component] from [NOW] to [LATER]
4. Add [integration] for [new feature]
```

## MCP Tools Used

- `read_file()` - Read architecture analysis
- `write()` - Create implementation plan
- `codebase_search()` - Understand existing patterns

## Examples

### Example: Orchestration Layer Plan

**NOW Section:**
- Session-based orchestration
- File-based state
- MCP tool integration
- Works in Cursor sessions

**LATER Section:**
- Process-based orchestration
- In-memory state
- A2A protocol integration
- Cross-process coordination

**Migration Path:**
- Keep file state as persistence
- Add in-memory state for processes
- Add process manager
- Migrate session engine to process engine

## Error Handling

**Common Mistakes:**
- Mixing NOW and LATER in same section
- Not preserving LATER details
- Missing migration path
- Unclear status indicators

**How to Avoid:**
- Clear section headers (PART 1: NOW, PART 2: LATER)
- Status indicators (✅ NOW, ⏸️ LATER)
- Migration path section
- Architecture context at top

## Related Skills

- `architecture-analysis` - Understand current architecture
- `code-implementation` - Implement NOW sections
- `documentation-creation` - Document plans

---

**Last Updated**: 2025-01-13  
**Status**: Active  
**Created By**: Auto (implementation planning session)

