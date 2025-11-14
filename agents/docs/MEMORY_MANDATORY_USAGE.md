# Memory Usage - Mandatory Requirements

**Status**: ⚠️ **MANDATORY**  
**Last Updated**: 2025-01-13

---

## Overview

**Memory is the source of truth for all architectural decisions and patterns.** Memory usage is **MANDATORY**, not optional. All agents MUST use memory to:

1. **Learn from past work** - Query decisions and patterns before making new decisions
2. **Preserve knowledge** - Record decisions and patterns as they are made
3. **Share knowledge** - Make knowledge available to all future agents

---

## Mandatory Memory Workflow

### 1. Before ANY Decision ⚡ **MANDATORY**

**⚠️ ALWAYS query memory before making decisions:**

```python
# 1. Query related decisions
decisions = memory_query_decisions(
    project="home-server",
    search_text="your task keywords",
    limit=5
)

# 2. Query related patterns
patterns = memory_query_patterns(
    severity="high",
    tags="your,relevant,tags",
    limit=5
)

# 3. Search for related work
results = memory_search("your search query")

# 4. Check recent context
context = memory_get_recent_context(limit=5)
```

**Why this is mandatory:**
- Prevents repeating past mistakes
- Ensures consistency with established decisions
- Leverages proven patterns
- Avoids reinventing solutions

**⚠️ If you skip this, you may:**
- Make decisions that conflict with past decisions
- Ignore established patterns
- Repeat mistakes that were already solved
- Waste time reinventing solutions

---

### 2. After ANY Decision ⚡ **MANDATORY**

**⚠️ ALWAYS record decisions IMMEDIATELY (don't wait until the end):**

```python
# Record decision immediately after making it
memory_record_decision(
    content="Your decision",
    rationale="Why you made this decision",
    project="home-server",
    task="T1.1",
    importance=0.8,
    tags="relevant,tags"
)
```

**When to record:**
- ✅ Technology choices
- ✅ Architecture decisions
- ✅ Configuration choices
- ✅ Design patterns
- ✅ Any decision that affects future work

**⚠️ Don't wait until the end - record as you make decisions!**

---

### 3. When Discovering Patterns ⚡ **MANDATORY**

**⚠️ ALWAYS record patterns IMMEDIATELY when discovered:**

```python
# Record pattern immediately when discovered
memory_record_pattern(
    name="Pattern Name",
    description="What the pattern is about",
    solution="How to solve it",
    severity="medium",  # low, medium, high
    tags="relevant,tags"
)
```

**When to record:**
- ✅ Common issues encountered
- ✅ Solutions that work
- ✅ Anti-patterns to avoid
- ✅ Best practices discovered
- ✅ Troubleshooting steps

**⚠️ Don't wait until the end - record as you discover patterns!**

---

### 4. During Work ⚡ **MANDATORY**

**⚠️ ALWAYS update context regularly (at least every major step):**

```python
# Update context regularly during work
memory_save_context(
    agent_id="agent-001",
    task="T1.1",
    current_work="What you're currently working on",
    status="in_progress",
    notes="Any important notes or blockers"
)
```

**When to update:**
- ✅ After completing a major step
- ✅ When encountering blockers
- ✅ When making progress
- ✅ When status changes

**⚠️ Regular context updates preserve work state and help future agents understand progress.**

---

### 5. After Work ⚡ **MANDATORY**

**⚠️ ALWAYS save final context (this is not optional):**

```python
# Save final context when completing work
memory_save_context(
    agent_id="agent-001",
    task="T1.1",
    current_work="Summary of what was accomplished",
    status="completed",  # or "failed", "blocked"
    notes="Final notes, decisions made, patterns discovered"
)
```

**What to include:**
- ✅ Final status (completed, failed, blocked)
- ✅ Summary of accomplishments
- ✅ Key decisions made (if not already recorded)
- ✅ Patterns discovered (if not already recorded)
- ✅ Notes for future reference

**⚠️ Always save final context - it's how future agents learn what was done.**

---

## Memory Checklist

### Before Starting Work
- [ ] Query decisions related to your task
- [ ] Query patterns related to your work
- [ ] Search memory for related work
- [ ] Check recent context

### During Work
- [ ] Record decisions immediately as you make them
- [ ] Record patterns immediately as you discover them
- [ ] Update context regularly (at least every major step)

### After Work
- [ ] Record any remaining decisions
- [ ] Record any remaining patterns
- [ ] Save final context with status

---

## Why Memory is Mandatory

### 1. Knowledge Preservation
- Decisions and patterns are preserved for all future agents
- Knowledge doesn't get lost between sessions
- Context is maintained across agent sessions

### 2. Consistency
- All agents follow the same decisions
- Patterns are applied consistently
- Architecture remains coherent

### 3. Efficiency
- Agents learn from past work
- Don't repeat mistakes
- Leverage proven solutions

### 4. Collaboration
- Knowledge is shared across all agents
- Decisions are visible to everyone
- Patterns are accessible to all

---

## Consequences of Not Using Memory

**If you don't use memory:**

❌ **You may:**
- Repeat past mistakes
- Ignore established patterns
- Make conflicting decisions
- Waste time reinventing solutions
- Create inconsistencies in the codebase

❌ **Future agents will:**
- Not know about your decisions
- Not learn from your patterns
- Potentially repeat your mistakes
- Make conflicting decisions

**⚠️ Memory is not optional - it's how knowledge is preserved and shared.**

---

## Memory Tools Reference

### Query Tools
- `memory_query_decisions()` - Query decisions
- `memory_query_patterns()` - Query patterns
- `memory_search()` - Full-text search
- `memory_get_recent_context()` - Get recent context
- `memory_get_context_by_task()` - Get context by task

### Record Tools
- `memory_record_decision()` - Record decision
- `memory_record_pattern()` - Record pattern
- `memory_save_context()` - Save/update context

**See**: `agents/memory/MCP_TOOLS_GUIDE.md` for complete tool reference.

---

## Examples

### Example 1: Before Making a Decision

```python
# Before deciding on database technology:
decisions = memory_query_decisions(
    project="home-server",
    search_text="database",
    limit=5
)

# Review decisions - if PostgreSQL was chosen before, use it again
# If no decision exists, make new decision and record it immediately
```

### Example 2: Recording a Decision

```python
# After deciding to use PostgreSQL:
memory_record_decision(
    content="Use PostgreSQL for trading-journal database",
    rationale="Need ACID compliance, concurrent writes, and complex queries",
    project="trading-journal",
    task="T1.3",
    importance=0.9,
    tags="database,architecture,postgresql"
)
```

### Example 3: Recording a Pattern

```python
# After discovering port conflict issue:
memory_record_pattern(
    name="Port Conflict Resolution",
    description="Services failing to start due to port conflicts",
    solution="Always check port availability first using check_port_status MCP tool",
    severity="medium",
    tags="docker,networking,ports,troubleshooting"
)
```

---

## Summary

**Memory usage is MANDATORY:**

1. ✅ **Before decisions** - Always query memory first
2. ✅ **After decisions** - Always record decisions immediately
3. ✅ **When discovering patterns** - Always record patterns immediately
4. ✅ **During work** - Always update context regularly
5. ✅ **After work** - Always save final context

**Memory is the source of truth. Use it. Record in it. Share knowledge through it.**

---

**Last Updated**: 2025-01-13  
**Status**: ⚠️ **MANDATORY**

