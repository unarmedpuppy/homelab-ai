# Critiquing Agent

**Status**: ✅ Implemented  
**Version**: 0.1.0  
**Priority**: ⭐⭐⭐ HIGH

---

## Overview

The Critiquing Agent reviews agent outputs, detects issues, applies learned rules, and provides quality feedback to improve agent performance.

## Components

### Core Modules

- **`types.py`**: Type definitions (QualityIssue, QualityReport, enums)
- **`quality_checker.py`**: Evaluates quality of agent outputs
- **`issue_detector.py`**: Detects issues in outputs
- **`feedback_generator.py`**: Generates actionable feedback

### Data Storage

- **Reports**: Generated on-demand (not persisted)
- **Feedback**: Sent to agents via communication protocol
- **Learning**: Issues recorded to Learning Agent

## MCP Tools

The Critiquing Agent provides 2 MCP tools:

1. **`review_agent_output()`** - Review agent output and provide comprehensive feedback
2. **`check_output_quality()`** - Quick quality check without full review

## Usage

### Reviewing Agent Output

```python
await review_agent_output(
    agent_id="agent-001",
    output_type="code",
    output_content="def deploy():\n    docker_compose_up()",
    task_id="T1.1",
    context='{"task_type": "deployment"}'
)
```

### Quick Quality Check

```python
await check_output_quality(
    output_type="code",
    output_content="password = 'secret123'"
)
```

## Workflow

1. **Receive Output** → Agent produces output
2. **Check Quality** → Evaluate systematically
3. **Detect Issues** → Identify problems automatically
4. **Apply Rules** → Use learned rules from Learning Agent
5. **Generate Feedback** → Create actionable feedback
6. **Send to Agent** → Communicate via messages
7. **Record for Learning** → Store issues for pattern extraction

## Integration

- **With Learning Agent**: Applies learned rules, records issues for learning
- **With All Agents**: Reviews outputs, provides feedback
- **With Communication**: Sends feedback via messages
- **With Evaluation**: Quality scores feed evaluation system

## Quality Checks

### Code Quality
- Hardcoded passwords (CRITICAL)
- SQL injection risks (HIGH)
- Missing error handling (HIGH)
- TODO/FIXME comments (MEDIUM)

### Documentation Quality
- Missing examples (LOW)
- Too short (LOW)
- Missing sections (MEDIUM)

### Plan Quality
- Missing required sections (MEDIUM)
- Missing testing strategy (MEDIUM)

## Quality Scoring

Quality score calculated from issues:
- **1.0**: No issues
- **0.9+**: Excellent (minor issues)
- **0.7-0.9**: Good (some issues)
- **<0.7**: Needs improvement (significant issues)

Score calculation:
- Critical issues: -0.5 each
- High issues: -0.3 each
- Medium issues: -0.15 each
- Low issues: -0.05 each

## Examples

### Example: Code Review

```
Input: Code with hardcoded password
Output:
- Quality Score: 0.5
- Issues:
  - CRITICAL: Hardcoded password detected
  - HIGH: Missing error handling
- Recommendations:
  - Fix 1 critical issue immediately
  - Address 1 high priority issue
```

### Example: Documentation Review

```
Input: Short documentation
Output:
- Quality Score: 0.95
- Issues:
  - LOW: Documentation missing examples
- Recommendations:
  - Review documentation (1 issue)
```

## Testing

✅ All components tested and working:
- Quality checking
- Issue detection
- Feedback generation
- Learning Agent integration
- Rule application

## Next Steps

1. **Integration with Agents**: Agents request reviews automatically
2. **Enhanced Detection**: More sophisticated issue detection
3. **Rule Refinement**: Better rule application logic
4. **Evaluation Integration**: Feed quality scores to evaluation system

---

**Last Updated**: 2025-01-13  
**Status**: ✅ Complete and Tested

