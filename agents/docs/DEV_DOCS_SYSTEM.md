# Dev Docs System Guide

**Context preservation system to prevent agents from losing track during long sessions.**

---

## The Problem

Agents can "lose the plot" during long sessions, especially after auto-compaction. Without structured context preservation, agents forget:
- What they were implementing
- Key decisions made
- Current progress
- Next steps

## The Solution

**Dev Docs System** - Structured task documentation that persists across sessions.

---

## What Are Dev Docs?

Dev docs are three markdown files created for each major task:

1. **`{task-name}-plan.md`** - The approved plan
2. **`{task-name}-context.md`** - Key files, decisions, next steps
3. **`{task-name}-tasks.md`** - Checklist of work with status

**Location**: `agents/active/{agent-id}/dev-docs/`

---

## When to Use Dev Docs

### Create Dev Docs For:
- ✅ Major features or tasks
- ✅ Work that spans multiple sessions
- ✅ Complex implementations
- ✅ Before compacting conversation

### Don't Create Dev Docs For:
- ❌ Quick fixes (under 30 minutes)
- ❌ Simple tasks (single file changes)
- ❌ One-off operations

---

## Quick Start

### 1. Create Dev Docs (After Planning)

```python
create_dev_docs(
    agent_id="agent-001",
    task_name="deploy-trading-bot",
    plan_content="# Plan\n\n1. Setup database...",
    context_content="Key files:\n- apps/trading-bot/docker-compose.yml\n- apps/trading-bot/.env",
    initial_tasks="- [ ] Setup database\n- [ ] Configure API\n- [ ] Deploy frontend"
)
```

**Creates**:
- `agents/active/agent-001/dev-docs/deploy-trading-bot-plan.md`
- `agents/active/agent-001/dev-docs/deploy-trading-bot-context.md`
- `agents/active/agent-001/dev-docs/deploy-trading-bot-tasks.md`

### 2. Continue Work (At Session Start)

```python
# Check for active dev docs
active_docs = list_active_dev_docs(agent_id="agent-001")

# Read dev docs to refresh context
docs = read_dev_docs(agent_id="agent-001", task_name="deploy-trading-bot")

# Now you have:
# - docs["plan"] - The original plan
# - docs["context"] - Key files and decisions
# - docs["tasks"] - Current task checklist
```

### 3. Update Before Compaction

```python
update_dev_docs(
    agent_id="agent-001",
    task_name="deploy-trading-bot",
    context_updates="Database configured, API key set in .env",
    completed_tasks="Setup database, Configure API",
    new_tasks="- [ ] Deploy frontend\n- [ ] Test integration",
    next_steps="Deploy frontend service, test API integration"
)
```

---

## Dev Docs Structure

### Plan File (`{task-name}-plan.md`)

Contains the approved plan:
- Executive summary
- Phases and tasks
- Architecture decisions
- Risks and mitigation
- Success metrics

**Purpose**: Reference the original plan to stay on track.

### Context File (`{task-name}-context.md`)

Contains:
- **Key Files**: Important files being modified
- **Decisions Made**: Important decisions with timestamps
- **Next Steps**: Current progress and next actions

**Purpose**: Preserve context and decisions across sessions.

### Tasks File (`{task-name}-tasks.md`)

Contains:
- Task checklist with status
- Completed tasks (marked with [x])
- Pending tasks (marked with [ ])
- New tasks added as work progresses

**Purpose**: Track progress and maintain focus.

---

## Workflow Integration

### Complete Workflow

```
1. Planning Phase
   ↓
2. Create Dev Docs (from approved plan)
   ↓
3. Implementation Phase
   - Read dev docs at session start
   - Update context as decisions are made
   - Mark tasks complete as you go
   ↓
4. Before Compaction
   - Update dev docs with progress
   - Record next steps
   ↓
5. New Session
   - Read dev docs to refresh context
   - Continue from where you left off
   ↓
6. Task Complete
   - Final dev docs update
   - Archive or keep for reference
```

---

## Available MCP Tools

### `create_dev_docs()`

Create dev docs for a new task.

**Parameters**:
- `agent_id`: Your agent ID
- `task_name`: Task name (kebab-case)
- `plan_content`: The approved plan (markdown)
- `context_content`: Initial context (optional)
- `initial_tasks`: Initial task checklist (optional)

**Returns**: Paths to created files

### `update_dev_docs()`

Update dev docs with current progress.

**Parameters**:
- `agent_id`: Your agent ID
- `task_name`: Task name (must match existing)
- `context_updates`: New context to add (optional)
- `completed_tasks`: Comma-separated completed tasks (optional)
- `new_tasks`: New tasks to add (optional)
- `next_steps`: Next steps to record (optional)

**Returns**: Updated file paths

### `list_active_dev_docs()`

List all active dev docs for an agent.

**Parameters**:
- `agent_id`: Your agent ID

**Returns**: List of active dev docs with last updated times

### `read_dev_docs()`

Read all dev docs for a specific task.

**Parameters**:
- `agent_id`: Your agent ID
- `task_name`: Task name to read

**Returns**: Complete dev docs content (plan, context, tasks)

---

## Example: Complete Workflow

### Step 1: Planning

```python
# Agent creates plan (or human approves plan)
plan = """
# Deploy Trading Bot

## Phase 1: Database Setup
1. Create PostgreSQL database
2. Run migrations
3. Seed initial data

## Phase 2: Backend Deployment
1. Configure environment variables
2. Deploy backend service
3. Verify API endpoints

## Phase 3: Frontend Deployment
1. Build frontend
2. Deploy to server
3. Test integration
"""
```

### Step 2: Create Dev Docs

```python
create_dev_docs(
    agent_id="agent-001",
    task_name="deploy-trading-bot",
    plan_content=plan,
    context_content="Key files:\n- apps/trading-bot/backend/docker-compose.yml\n- apps/trading-bot/backend/.env.example",
    initial_tasks="- [ ] Create database\n- [ ] Run migrations\n- [ ] Configure backend\n- [ ] Deploy backend\n- [ ] Deploy frontend\n- [ ] Test integration"
)
```

### Step 3: Work Session 1

```python
# At start of session
docs = read_dev_docs(agent_id="agent-001", task_name="deploy-trading-bot")

# Work on Phase 1
# ... create database, run migrations ...

# Update dev docs
update_dev_docs(
    agent_id="agent-001",
    task_name="deploy-trading-bot",
    context_updates="Database created, migrations applied successfully",
    completed_tasks="Create database, Run migrations",
    next_steps="Configure backend environment variables"
)
```

### Step 4: Work Session 2 (After Compaction)

```python
# At start of new session
docs = read_dev_docs(agent_id="agent-001", task_name="deploy-trading-bot")

# Context refreshed! You know:
# - What the plan was
# - What's been done
# - What's next

# Continue with Phase 2
# ... configure backend, deploy ...

# Update dev docs
update_dev_docs(
    agent_id="agent-001",
    task_name="deploy-trading-bot",
    context_updates="Backend deployed, API endpoints verified",
    completed_tasks="Configure backend, Deploy backend",
    next_steps="Deploy frontend, test integration"
)
```

---

## Best Practices

### 1. Create Early
- Create dev docs right after planning
- Don't wait until you're deep in implementation

### 2. Update Regularly
- Update context as you make decisions
- Mark tasks complete immediately
- Add new tasks as they come up

### 3. Update Before Compaction
- Always update dev docs before compacting
- Record current progress and next steps
- This preserves context across sessions

### 4. Read at Session Start
- Always read dev docs at the start of a new session
- Refresh your context before continuing
- Don't assume you remember everything

### 5. Keep Focused
- Reference the plan to stay on track
- Don't go off on tangents
- If plan needs to change, update dev docs

---

## Integration with Other Systems

### Task Coordination
- Dev docs complement task coordination
- Tasks track high-level coordination
- Dev docs track detailed implementation

### Memory System
- Important decisions from dev docs can be recorded in memory
- Dev docs provide context for memory queries
- Memory provides patterns, dev docs provide specifics

### Agent Communication
- Dev docs can be shared with other agents
- Other agents can read dev docs to understand context
- Dev docs provide background for communication

---

## Troubleshooting

### "Dev docs not found"

**Solution**: 
- Check task name matches exactly (case-sensitive)
- Use `list_active_dev_docs()` to see all active docs
- Create dev docs if they don't exist

### "Lost track despite dev docs"

**Solution**:
- Update dev docs more frequently
- Be more detailed in context updates
- Read dev docs at the start of EVERY session

### "Dev docs getting too long"

**Solution**:
- Keep context focused on current work
- Archive completed sections
- Create new dev docs for new phases if needed

---

**Last Updated**: 2025-01-13  
**Status**: Active  
**See Also**:
- `agents/docs/AGENT_PROMPT.md` - Main agent prompt
- `agents/docs/AGENT_WORKFLOW.md` - Workflow guide
- `agents/docs/AGENT_SYSTEM_ENHANCEMENT_PLAN.md` - Enhancement plan

