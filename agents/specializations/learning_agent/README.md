# Learning Agent

**Status**: ✅ Implemented  
**Version**: 0.1.0  
**Priority**: ⭐⭐⭐ HIGH

---

## Overview

The Learning Agent records feedback, extracts patterns, and generates reusable rules to improve the agent system over time.

## Components

### Core Modules

- **`types.py`**: Type definitions (Feedback, LearnedRule, Pattern, enums)
- **`feedback_recorder.py`**: Records feedback to JSONL files
- **`pattern_extractor.py`**: Extracts patterns from feedback
- **`rule_generator.py`**: Generates rules from patterns
- **`knowledge_base.py`**: Stores and manages learned rules
- **`rule_applier.py`**: Applies learned rules automatically

### Data Storage

- **Feedback**: `data/feedback.jsonl` (JSON Lines format)
- **Rules**: `data/rules.json` (JSON format)

## MCP Tools

The Learning Agent provides 5 MCP tools:

1. **`record_feedback()`** - Record feedback for learning
2. **`find_applicable_rules()`** - Find rules applicable to current context
3. **`apply_rule()`** - Apply a learned rule
4. **`record_rule_success()`** - Record whether rule application was successful
5. **`get_learning_stats()`** - Get statistics about the learning system

## Usage

### Recording Feedback

```python
await record_feedback(
    feedback_type="correction",
    agent_id="agent-001",
    context='{"task_type": "deployment", "error": "disk_full"}',
    issue="Deployment failed - disk space issue",
    correction="Check disk space before deployment",
    provided_by="human"
)
```

### Finding Applicable Rules

```python
await find_applicable_rules(
    context='{"task_type": "deployment"}',
    error="disk_full"
)
```

### Applying Rules

```python
await apply_rule(
    rule_id="rule-51444b3d",
    context='{"task_type": "deployment"}'
)
```

## Workflow

1. **Feedback Received** → Recorded to file
2. **Pattern Extraction** → Automatic after recording (checks recent feedback)
3. **Rule Generation** → Automatic when patterns found (≥2 occurrences)
4. **Rule Storage** → Saved to knowledge base
5. **Rule Application** → Agents query for applicable rules
6. **Success Tracking** → Rule success rates updated

## Integration

- **MCP Server**: Tools registered in `agents/apps/agent-mcp/tools/learning.py`
- **Server Registration**: Added to `agents/apps/agent-mcp/server.py`
- **File-Based**: Works with Cursor session architecture
- **No Dependencies**: Self-contained, uses only standard library + pathlib

## Testing

✅ All components tested and working:
- Feedback recording
- Pattern extraction
- Rule generation
- Knowledge base storage
- Rule application

## Next Steps

1. **Integration with Critiquing Agent**: Receive feedback from critiquing agent
2. **Integration with Agents**: Agents query for applicable rules before actions
3. **Memory System Integration**: Store rules in memory system for persistence
4. **Evaluation Integration**: Track rule success rates for evaluation

---

**Last Updated**: 2025-01-13  
**Status**: ✅ Complete and Tested

