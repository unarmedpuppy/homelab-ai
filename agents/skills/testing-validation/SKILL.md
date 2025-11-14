---
name: testing-validation
description: Test implementations incrementally, validate components, and verify integration
category: configuration
mcp_tools_required:
  - run_terminal_cmd
  - read_file
  - read_lints
prerequisites:
  - Code implementation complete
  - Understanding of what to test
---

# Testing & Validation Skill

## When to Use This Skill

Use this skill when:
- Testing new implementations
- Validating component functionality
- Verifying integration
- Checking for errors
- Ensuring code works end-to-end

**This skill ensures implementations are tested and validated before completion.**

## Overview

This skill provides a systematic approach to testing implementations incrementally, validating each component, and verifying full integration.

## The Problem

Without proper testing:
- Errors discovered too late
- Integration issues not caught
- Components don't work together
- MCP tools not functional
- Code doesn't match requirements

## The Solution

**Incremental Testing** - Test each component as you create it, then test integration.

## Workflow Steps

### Step 1: Test Individual Components

**Test each component in isolation:**

```python
# Test feedback recorder
run_terminal_cmd(
    "python3 -c 'from agents.specializations.learning_agent.feedback_recorder import FeedbackRecorder; ...'"
)
```

**Test:**
- Component initialization
- Core functionality
- Error handling
- Edge cases

### Step 2: Test Component Integration

**Test components working together:**

```python
# Test full flow
run_terminal_cmd(
    """python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from agents.specializations.learning_agent.feedback_recorder import FeedbackRecorder
from agents.specializations.learning_agent.pattern_extractor import PatternExtractor
# ... test full flow
EOF"""
)
```

**Test:**
- Components calling each other
- Data flow between components
- Integration points
- Full workflows

### Step 3: Check for Linter Errors

**Use linter to find issues:**

```python
read_lints(paths=["agents/specializations/learning_agent"])
```

**Fix:**
- Import errors
- Type errors
- Syntax errors
- Style issues

### Step 4: Test MCP Tool Integration

**Verify MCP tools are registered and work:**

```python
# Check server.py has registration
grep("register_learning_tools", "agents/apps/agent-mcp/server.py")

# Test MCP tool (if possible)
# Note: Full MCP testing requires MCP server running
```

**Verify:**
- Tools registered in server.py
- Import paths correct
- Tool functions work
- Error handling works

### Step 5: Test End-to-End

**Test complete workflow:**

```python
# Test full learning cycle
run_terminal_cmd(
    """python3 << 'EOF'
# 1. Record feedback
# 2. Extract patterns
# 3. Generate rules
# 4. Apply rules
# Verify all steps work
EOF"""
)
```

**Test:**
- Complete workflows
- Real-world scenarios
- Error scenarios
- Edge cases

### Step 6: Document Test Results

**Document what was tested and results:**

```markdown
## Test Results

✅ Feedback recorder works
✅ Pattern extraction works
✅ Rule generation works
✅ Knowledge base storage works
✅ All components tested successfully
```

## MCP Tools Used

- `run_terminal_cmd()` - Run test commands
- `read_lints()` - Check for errors
- `read_file()` - Verify integration
- `grep()` - Check registration

## Examples

### Example: Learning Agent Testing

**Component Tests:**
```python
# Test feedback recorder
✅ Feedback recorder works: fb-8ded1728

# Test pattern extraction
✅ Extracted 1 patterns

# Test rule generation
✅ Generated rule: rule-51444b3d
```

**Integration Test:**
```python
# Test full flow
✅ Recorded feedback 1: fb-9dc5ec08
✅ Recorded feedback 2: fb-ae1701b5
✅ Recorded feedback 3: fb-5705d710
✅ Extracted 1 patterns
✅ Generated rule: rule-51444b3d
✅ Total rules in knowledge base: 1
✅ Learning Agent components working!
```

## Error Handling

**Common Issues:**
- Import path errors
- Module not found
- Directory naming (hyphens)
- Missing dependencies
- Type errors

**How to Fix:**
- Check import paths
- Verify directory names (underscores)
- Add missing dependencies
- Fix type errors
- Test incrementally

## Related Skills

- `code-implementation` - Implement testable code
- `documentation-creation` - Document test results

---

**Last Updated**: 2025-01-13  
**Status**: Active  
**Created By**: Auto (testing session)

