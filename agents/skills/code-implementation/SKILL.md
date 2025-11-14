---
name: code-implementation
description: Implement code following existing patterns, testing as you go, and integrating with MCP tools
category: configuration
mcp_tools_required:
  - read_file
  - write
  - codebase_search
  - grep
  - run_terminal_cmd
prerequisites:
  - Implementation plan complete
  - Understanding of existing code patterns
---

# Code Implementation Skill

## When to Use This Skill

Use this skill when:
- Implementing features from plans
- Following existing code patterns
- Creating new MCP tools
- Integrating with existing systems
- Testing implementations

**This skill ensures code follows established patterns and integrates properly.**

## Overview

This skill provides a systematic approach to implementing code that matches existing patterns, integrates with MCP tools, and is tested as you go.

## The Problem

Without following patterns:
- Code doesn't match existing style
- Integration breaks
- MCP tools not registered
- Testing happens too late
- Inconsistent structure

## The Solution

**Pattern-Following Implementation** - Study existing code, follow patterns, test incrementally.

## Workflow Steps

### Step 1: Study Existing Patterns

**Find similar implementations to understand patterns:**

```python
# Search for similar implementations
codebase_search(
    query="How are MCP tools registered? Show me the pattern",
    target_directories=["agents/apps/agent-mcp"]
)

# Read example files
read_file("agents/apps/agent-mcp/tools/communication.py")
read_file("agents/apps/agent-mcp/server.py")
```

**Understand:**
- Directory structure
- Import patterns
- Tool registration
- Error handling
- Logging patterns

### Step 2: Create Directory Structure

**Follow existing structure:**

```bash
# Example: Learning Agent
mkdir -p agents/specializations/learning_agent/data
```

**Key Points:**
- Use underscores, not hyphens (Python modules)
- Follow existing naming conventions
- Create data directories if needed

### Step 3: Implement Core Components

**Start with types, then core logic:**

```python
# 1. Types first
write("agents/specializations/learning_agent/types.py", ...)

# 2. Core components
write("agents/specializations/learning_agent/feedback_recorder.py", ...)
write("agents/specializations/learning_agent/pattern_extractor.py", ...)

# 3. Integration components
write("agents/specializations/learning_agent/knowledge_base.py", ...)
```

**Follow existing patterns:**
- Use dataclasses for types
- File-based storage for persistence
- JSON/JSONL for data
- Path objects for file paths

### Step 4: Create MCP Tools

**Follow MCP tool pattern:**

```python
# Create tools file
write("agents/apps/agent-mcp/tools/learning.py", ...)

# Register in server
read_file("agents/apps/agent-mcp/server.py")
# Add import
# Add register call
```

**MCP Tool Pattern:**
```python
def register_learning_tools(server: Server):
    """Register learning agent MCP tools."""
    
    @server.tool()
    @with_automatic_logging()
    async def tool_name(...) -> Dict[str, Any]:
        """Tool description."""
        # Implementation
```

### Step 5: Test Incrementally

**Test each component as you create it:**

```python
# Test core component
run_terminal_cmd(
    "python3 -c 'from agents.specializations.learning_agent.feedback_recorder import FeedbackRecorder; ...'"
)

# Test full flow
run_terminal_cmd(
    "python3 << 'EOF'\n# Full test script\nEOF"
)
```

**Test:**
- Individual components
- Integration between components
- MCP tool registration
- End-to-end workflows

### Step 6: Fix Issues

**Use linter and fix errors:**

```python
read_lints(paths=["agents/specializations/learning_agent"])
# Fix any errors
```

**Common Fixes:**
- Import path issues
- Type errors
- Missing dependencies
- Directory naming (hyphens → underscores)

### Step 7: Create Documentation

**Document what was created:**

```python
write("agents/specializations/learning_agent/README.md", ...)
```

**Include:**
- Overview
- Components
- Usage examples
- Integration points
- Testing results

## MCP Tools Used

- `read_file()` - Study existing code
- `codebase_search()` - Find patterns
- `grep()` - Find specific patterns
- `write()` - Create new files
- `run_terminal_cmd()` - Test code
- `read_lints()` - Check for errors

## Examples

### Example: Learning Agent Implementation

**Step 1: Study Pattern**
- Read `communication.py` for MCP tool pattern
- Read `server.py` for registration pattern

**Step 2: Create Structure**
- `learning_agent/` directory
- Core component files
- MCP tools file

**Step 3: Implement**
- Types with dataclasses
- File-based storage
- JSON/JSONL format
- MCP tool registration

**Step 4: Test**
- Test feedback recorder
- Test pattern extraction
- Test rule generation
- Test full flow

**Step 5: Integrate**
- Register in server.py
- Test MCP tools
- Verify integration

## Error Handling

**Common Mistakes:**
- Not following existing patterns
- Wrong directory structure
- MCP tools not registered
- Import path errors
- Not testing incrementally

**How to Avoid:**
- Always study existing code first
- Follow established patterns exactly
- Test each component
- Check linter errors
- Verify MCP registration

## Related Skills

- `implementation-planning` - Follow implementation plan
- `testing-validation` - Test implementations
- `documentation-creation` - Document implementations

---

**Last Updated**: 2025-01-13  
**Status**: Active  
**Created By**: Auto (code implementation session)

