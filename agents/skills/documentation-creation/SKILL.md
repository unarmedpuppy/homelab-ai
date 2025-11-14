---
name: documentation-creation
description: Create comprehensive documentation following established patterns and formats
category: configuration
mcp_tools_required:
  - write
  - read_file
prerequisites:
  - Implementation complete
  - Understanding of documentation needs
---

# Documentation Creation Skill

## When to Use This Skill

Use this skill when:
- Documenting implementations
- Creating README files
- Writing usage guides
- Documenting architecture decisions
- Creating skill documentation

**This skill ensures documentation is comprehensive and follows patterns.**

## Overview

This skill provides a systematic approach to creating documentation that is clear, comprehensive, and follows established patterns.

## The Problem

Without proper documentation:
- Future agents don't understand implementations
- Usage unclear
- Integration points unknown
- Examples missing
- Maintenance difficult

## The Solution

**Comprehensive Documentation** - Document everything: overview, usage, examples, integration.

## Workflow Steps

### Step 1: Understand Documentation Needs

**Determine what needs documentation:**

- Implementation overview
- Usage examples
- Integration points
- Testing results
- Architecture decisions

### Step 2: Follow Documentation Patterns

**Study existing documentation:**

```python
read_file("agents/specializations/learning_agent/README.md")
read_file("agents/skills/README.md")
```

**Follow patterns:**
- Overview section
- Components section
- Usage examples
- Integration points
- Status/version

### Step 3: Create Documentation Structure

**Structure documentation clearly:**

```markdown
# [Title]

**Status**: ✅ Implemented
**Version**: 0.1.0

## Overview
[What this is]

## Components
[What components exist]

## Usage
[How to use]

## Examples
[Real examples]

## Integration
[How it integrates]

## Testing
[Test results]

## Next Steps
[What's next]
```

### Step 4: Include Examples

**Provide real, working examples:**

```markdown
## Examples

### Recording Feedback
```python
await record_feedback(
    feedback_type="correction",
    agent_id="agent-001",
    context='{"task_type": "deployment"}',
    issue="Deployment failed",
    correction="Check disk space first",
    provided_by="human"
)
```
```

### Step 5: Document Integration Points

**Show how it integrates:**

```markdown
## Integration

- **MCP Server**: Tools registered in `agents/apps/agent-mcp/tools/learning.py`
- **Server Registration**: Added to `agents/apps/agent-mcp/server.py`
- **File-Based**: Works with Cursor session architecture
```

### Step 6: Document Test Results

**Show what was tested:**

```markdown
## Testing

✅ All components tested and working:
- Feedback recording
- Pattern extraction
- Rule generation
- Knowledge base storage
- Rule application
```

## MCP Tools Used

- `write()` - Create documentation
- `read_file()` - Study patterns

## Examples

### Example: Learning Agent README

**Structure:**
- Overview
- Components
- MCP Tools
- Usage
- Workflow
- Integration
- Testing
- Next Steps

**Key Sections:**
- Clear status indicators
- Working code examples
- Integration points
- Test results
- Future plans

## Error Handling

**Common Mistakes:**
- Missing examples
- Unclear usage
- No integration points
- Missing test results
- Outdated information

**How to Avoid:**
- Include real examples
- Show actual usage
- Document all integration points
- Include test results
- Keep documentation updated

## Related Skills

- `code-implementation` - Document implementations
- `testing-validation` - Document test results

---

**Last Updated**: 2025-01-13  
**Status**: Active  
**Created By**: Auto (documentation session)

