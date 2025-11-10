# Agent Memory Integration - mem-layer

## Overview

This document outlines how to integrate [mem-layer](https://github.com/0xSero/mem-layer) - a graph-based memory management system - into the AI agent workflow to enable persistent memory and knowledge sharing across agent sessions.

## Why Agent Memory Matters

### Current Limitations

**Without Memory System:**
- ❌ Each agent session starts from scratch
- ❌ Decisions made in previous sessions are forgotten
- ❌ Agents repeat the same mistakes
- ❌ No knowledge sharing between agents
- ❌ Architectural decisions get lost
- ❌ Context must be re-established each time
- ❌ No relationship tracking between tasks/decisions

**With Memory System:**
- ✅ Persistent context across sessions
- ✅ Decision tracking and recall
- ✅ Knowledge graph of project relationships
- ✅ Agent-to-agent communication
- ✅ Learning from past mistakes
- ✅ Pattern recognition across tasks
- ✅ Automatic context retrieval

## Benefits for Agent Workflow

### 1. Decision Tracking

**Problem**: Architectural decisions get documented but not easily queried or related.

**Solution**: Store decisions as nodes with relationships:
```python
# Agent makes architectural decision
api.create_node(
    type=NodeType.DECISION,
    content="Use PostgreSQL for trading journal database",
    metadata={
        "project": "trading-journal",
        "task": "T1.3",
        "rationale": "Need ACID compliance and complex queries"
    },
    importance=0.9
)

# Later, another agent can query
decisions = api.query("type:decision AND metadata.project:trading-journal")
```

### 2. Cross-Agent Knowledge Sharing

**Problem**: Agent A learns something, Agent B doesn't know it.

**Solution**: Shared memory graph:
```python
# Agent 1 (Reviewer) finds issue
api.create_node(
    type=NodeType.NOTE,
    content="Missing type hints in trade_service.py",
    metadata={"severity": "medium", "file": "trade_service.py"}
)
api.send_message(
    to_context="implementer",
    subject="Type hints required",
    priority="MEDIUM"
)

# Agent 2 (Implementer) receives
messages = api.receive_messages(context="implementer")
```

### 3. Task Relationship Tracking

**Problem**: Tasks are independent, relationships unclear.

**Solution**: Graph relationships:
```python
# Task T1.3 depends on T1.2
task_1_2 = api.get_node_by_content("T1.2: Docker Compose Configuration")
task_1_3 = api.get_node_by_content("T1.3: PostgreSQL Database Setup")

api.create_edge(
    source_id=task_1_2.id,
    target_id=task_1_3.id,
    type=EdgeType.DEPENDS_ON,
    weight=1.0
)

# Query: What tasks depend on T1.2?
dependents = api.traverse(task_1_2.id, direction="outgoing")
```

### 4. Pattern Recognition

**Problem**: Same issues occur repeatedly, no learning.

**Solution**: Track patterns:
```python
# Track common review issues
api.create_node(
    type=NodeType.PATTERN,
    content="Missing type hints in Python functions",
    metadata={
        "frequency": 5,
        "severity": "medium",
        "solution": "Add type hints to all functions"
    }
)

# Agents can query before submitting
patterns = api.query("type:pattern AND metadata.severity:medium")
# Review their code against known patterns
```

### 5. Session Continuity

**Problem**: Agent starts new session, loses context.

**Solution**: Session-based memory:
```python
# Start session
session = api.start_session(scope="trading-journal")

# All operations tagged with session
api.create_node(...)  # Tagged with session.id
api.create_edge(...)  # Tagged with session.id

# End session with summary
summary = api.end_session(session.id, save=True)

# Next session: Load context
context = api.get_session_context(session.id)
```

## Integration Architecture

### Memory Scopes

Use mem-layer's scoping for different contexts:

1. **Project Scope** (`trading-journal`)
   - Project-specific decisions
   - Task relationships
   - Architecture decisions
   - Project patterns

2. **Agent Scope** (`agent-001`, `agent-002`)
   - Agent-specific notes
   - Personal learnings
   - Agent preferences

3. **Global Scope** (`home-server`)
   - Cross-project patterns
   - Server-wide decisions
   - Shared knowledge

### Integration Points

#### 1. Agent Prompt Integration

Add to `TRADING_JOURNAL_AGENTS_PROMPT.md`:

```markdown
## Memory System

Before starting work:
1. Load project context: `api.load_context(scope="trading-journal")`
2. Query recent decisions: `api.query("type:decision AND age:<7days")`
3. Check for related work: `api.search("similar task")`

After completing work:
1. Document decisions: `api.create_node(type=DECISION, ...)`
2. Link to related tasks: `api.create_edge(...)`
3. Save session: `api.end_session(save=True)`
```

#### 2. Reviewer Integration

Add to `TRADING_JOURNAL_AGENT_REVIEWER_PROMPT.md`:

```markdown
## Memory Integration

During review:
1. Check for similar issues: `api.query("type:issue AND metadata.pattern:missing-types")`
2. Document new patterns: `api.create_node(type=PATTERN, ...)`
3. Link to related reviews: `api.create_edge(...)`
```

#### 3. Task Tracking Integration

Enhance `TASKS.md` with memory links:

```markdown
### T1.3: PostgreSQL Database Setup
**Status**: `[COMPLETED]`
**Memory Node ID**: `node_abc123`
**Related Decisions**: `decision_xyz789`
**Patterns Found**: `pattern_missing_types`
```

## Implementation Plan

### Phase 1: Setup (Week 1)

1. **Install mem-layer**
   ```bash
   pip install mem-layer
   ```

2. **Initialize for home-server**
   ```bash
   mem-layer init --scope home-server
   ```

3. **Create project scope**
   ```bash
   mem-layer scope create trading-journal --type project
   ```

4. **Add to agent workflow**
   - Update agent prompts
   - Update reviewer prompts
   - Create memory helpers

### Phase 2: Basic Integration (Week 2)

1. **Decision Tracking**
   - Agents document decisions
   - Query decisions before making new ones
   - Link related decisions

2. **Task Relationships**
   - Link tasks in memory graph
   - Track dependencies
   - Visualize task graph

3. **Pattern Tracking**
   - Document common issues
   - Query before submitting
   - Learn from patterns

### Phase 3: Advanced Features (Week 3+)

1. **Agent Communication**
   - Message queue system
   - Context sharing
   - Coordination

2. **Learning System**
   - Pattern recognition
   - Automatic suggestions
   - Best practice tracking

3. **Visualization**
   - Graph visualization
   - Relationship exploration
   - Knowledge discovery

## Usage Examples

### Example 1: Decision Tracking

```python
from mem_layer import MemoryAPI, NodeType

api = MemoryAPI(scope="trading-journal")

# Agent makes decision
decision = api.create_node(
    type=NodeType.DECISION,
    content="Use FastAPI for backend API",
    metadata={
        "task": "T1.4",
        "rationale": "Consistent with trading-bot, async support",
        "alternatives_considered": ["Flask", "Django"]
    },
    importance=0.9
)

# Link to related task
task_node = api.get_node_by_metadata("task", "T1.4")
api.create_edge(
    source_id=task_node.id,
    target_id=decision.id,
    type=EdgeType.RESULTS_FROM
)
```

### Example 2: Issue Pattern Tracking

```python
# Reviewer finds issue
issue = api.create_node(
    type=NodeType.NOTE,
    content="Missing type hints in trade_service.py",
    metadata={
        "file": "trade_service.py",
        "severity": "medium",
        "task": "T1.7"
    }
)

# Check if this is a pattern
similar_issues = api.query(
    "type:note AND metadata.severity:medium AND content:*type hints*"
)

if len(similar_issues) >= 3:
    # Create pattern
    pattern = api.create_node(
        type=NodeType.PATTERN,
        content="Missing type hints in Python functions",
        metadata={
            "frequency": len(similar_issues),
            "solution": "Add type hints to all functions"
        }
    )
    # Link issues to pattern
    for issue in similar_issues:
        api.create_edge(issue.id, pattern.id, type=EdgeType.EXAMPLE_OF)
```

### Example 3: Cross-Session Context

```python
# Session 1: Agent starts work
session = api.start_session(scope="trading-journal")
api.create_node(
    type=NodeType.NOTE,
    content="Working on T1.7: Trade CRUD API",
    metadata={"session": session.id, "task": "T1.7"}
)
api.end_session(session.id, save=True)

# Session 2: Different agent continues
previous_session = api.get_latest_session(scope="trading-journal")
context = api.get_session_context(previous_session.id)
# Agent has full context of previous work
```

### Example 4: Agent Communication

```python
# Agent 1 (Reviewer) finds critical issue
api.send_message(
    to_context="implementer",
    subject="Security vulnerability in API authentication",
    content="API key validation missing in trade endpoints",
    priority="CRITICAL",
    metadata={"task": "T1.7", "file": "api/routes/trades.py"}
)

# Agent 2 (Implementer) receives
messages = api.receive_messages(context="implementer", unread_only=True)
for msg in messages:
    if msg.priority == "CRITICAL":
        # Address immediately
        fix_issue(msg)
        api.mark_message_read(msg.id)
```

## Configuration

### Setup for Home Server

```yaml
# ~/.mem-layer/config.yaml
version: "1.0"

storage:
  backend: sqlite
  path: ~/server/.mem-layer/memory.db
  auto_save: true
  save_interval: 300

graph:
  default_scope: home-server
  max_nodes: 50000

memory:
  consolidation:
    enabled: true
    interval: daily
  decay:
    enabled: true
    half_life: 90  # Days

scopes:
  - name: home-server
    type: global
  - name: trading-journal
    type: project
  - name: trading-bot
    type: project
```

### Integration with Agent Workflow

Add to `AGENT_WORKFLOW.md`:

```markdown
## Memory System Integration

### For Agents
1. Load context at start: `api.load_context(scope="project")`
2. Document decisions: `api.create_node(type=DECISION, ...)`
3. Link related work: `api.create_edge(...)`
4. Save session: `api.end_session(save=True)`

### For Reviewers
1. Check patterns: `api.query("type:pattern")`
2. Document issues: `api.create_node(type=NOTE, ...)`
3. Track patterns: Link similar issues
```

## Benefits Summary

### Immediate Benefits
- ✅ Persistent memory across sessions
- ✅ Decision tracking and recall
- ✅ Knowledge sharing between agents
- ✅ Pattern recognition

### Long-term Benefits
- ✅ Learning system (agents learn from past)
- ✅ Reduced repetition
- ✅ Better coordination
- ✅ Knowledge graph of project

### Metrics to Track
- Decisions documented
- Patterns identified
- Issues prevented (by querying patterns)
- Context retrieval time
- Agent coordination efficiency

## Migration Path

### Step 1: Install and Setup
- Install mem-layer
- Initialize for home-server
- Create project scopes

### Step 2: Pilot Project
- Use trading-journal as pilot
- Integrate into agent prompts
- Track decisions and patterns

### Step 3: Expand
- Roll out to other projects
- Create global patterns
- Build knowledge graph

### Step 4: Advanced Features
- Agent communication
- Learning system
- Visualization

## Considerations

### Pros
- ✅ Persistent memory
- ✅ Knowledge sharing
- ✅ Pattern recognition
- ✅ Relationship tracking
- ✅ Open source (MIT license)
- ✅ Python-based (fits our stack)

### Cons
- ⚠️ Additional dependency
- ⚠️ Learning curve
- ⚠️ Storage overhead (minimal with SQLite)
- ⚠️ Requires discipline (agents must use it)

### Mitigation
- Start with pilot project
- Make it easy (helper functions)
- Integrate into prompts (required, not optional)
- Track usage metrics

## Next Steps

1. **Evaluate**: Review mem-layer documentation
2. **Pilot**: Start with trading-journal project
3. **Integrate**: Update agent and reviewer prompts
4. **Measure**: Track benefits and usage
5. **Expand**: Roll out to other projects

## References

- **mem-layer GitHub**: https://github.com/0xSero/mem-layer
- **Documentation**: See mem-layer docs/
- **Architecture**: See mem-layer ARCHITECTURE.md

---

**Status**: Proposal - Ready for evaluation
**Priority**: High (significant workflow improvement)
**Effort**: Low-Medium (integration work)

