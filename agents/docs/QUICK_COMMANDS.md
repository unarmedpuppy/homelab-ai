# Quick Commands Reference

**Common workflow shortcuts for agents to save time and ensure consistency.**

---

## Planning & Dev Docs

### Create Dev Docs from Approved Plan

```python
create_dev_docs(
    agent_id="agent-001",
    task_name="implement-feature-x",
    plan_content="# Approved plan content...",
    context_content="Key files: apps/my-app/src/index.ts",
    initial_tasks="- [ ] Setup database\n- [ ] Configure API\n- [ ] Deploy frontend"
)
```

### Update Dev Docs Before Compaction

```python
update_dev_docs(
    agent_id="agent-001",
    task_name="implement-feature-x",
    context_updates="Database configured, API key set",
    completed_tasks="Setup database, Configure API",
    next_steps="Deploy frontend, test integration"
)
```

### Read Dev Docs at Session Start

```python
# Check for active dev docs
active_docs = list_active_dev_docs(agent_id="agent-001")

# Read dev docs to refresh context
docs = read_dev_docs(agent_id="agent-001", task_name="implement-feature-x")
```

---

## Quality & Review

### Check Code Quality After Edits

```python
result = check_code_quality(
    file_paths="apps/my-app/src/index.ts,apps/my-app/src/utils.ts",
    check_types="all"  # or "build,errors,security,handling"
)

# Review results
if result["has_errors"]:
    print(result["summary"])
    # Fix errors...
```

### Request Code Review

```python
review = request_code_review(
    file_paths="apps/my-app/src/index.ts,apps/my-app/src/utils.ts",
    review_type="self"
)

print(review["summary"])
# Address issues...
```

### Get Self-Review Checklist

```python
checklist = self_review_checklist(
    file_paths="apps/my-app/src/index.ts,apps/my-app/src/utils.ts"
)

# Verify each item
for item in checklist["items"]:
    # Verify item...
```

---

## Skill Activation

### Get Skill Suggestions

```python
# Based on context
suggest_relevant_skills(
    prompt_text="How do I deploy code changes?",
    file_paths="apps/my-app/docker-compose.yml",
    task_description="Deploy latest changes to production"
)

# Quick reminder
get_skill_activation_reminder(
    context_summary="Deploying code changes to trading-bot service"
)
```

---

## Service Debugging

### Get Service Logs

```python
# All logs
logs = get_service_logs(
    service_name="trading-bot",
    lines=200,
    level="all"
)

# Error logs only
error_logs = get_service_logs(
    service_name="trading-bot",
    lines=500,
    level="error"
)
```

### Monitor Service Status

```python
status = monitor_service_status(service_name="trading-bot")
# Returns: state, health, running status, restart count
```

### Restart Service

```python
restart_service(
    service_name="trading-bot",
    method="docker"  # or "compose"
)
```

### Get Service Metrics

```python
metrics = get_service_metrics(service_name="trading-bot")
# Returns: CPU, memory, network usage
```

---

## Task Management

### Register New Task

```python
register_task(
    title="Implement feature X",
    description="Add new feature to application",
    project="my-app",
    priority="high",
    dependencies=["T1.1", "T1.2"]  # Optional
)
```

### Claim Task

```python
claim_task(
    task_id="T1.1",
    agent_id="agent-001"
)
```

### Update Task Status

```python
update_task_status(
    task_id="T1.1",
    status="in_progress",
    progress="50% complete"
)
```

### Query Tasks

```python
# Get pending tasks
tasks = query_tasks(
    status="pending",
    priority="high"
)

# Get tasks for project
project_tasks = query_tasks(
    project="my-app",
    status="in_progress"
)
```

---

## Memory

### Query Previous Decisions

```python
# By project
decisions = memory_query_decisions(
    project="home-server",
    limit=5
)

# By search
decisions = memory_query_decisions(
    search_text="deployment",
    limit=10
)
```

### Record Decision

```python
memory_record_decision(
    content="Use PostgreSQL for database",
    rationale="Need ACID compliance and concurrent writes",
    project="my-app",
    task="T1.1",
    importance=0.9,
    tags="database,architecture"
)
```

### Query Patterns

```python
# By severity
patterns = memory_query_patterns(
    severity="high",
    limit=5
)

# All patterns
all_patterns = memory_query_patterns(limit=10)
```

### Record Pattern

```python
memory_record_pattern(
    name="Port Conflict Resolution",
    description="Services failing due to port conflicts",
    solution="Always check port availability first",
    severity="medium",
    tags="docker,networking,ports"
)
```

### Full-Text Search

```python
results = memory_search("deployment workflow")
```

### Save Context

```python
memory_save_context(
    agent_id="agent-001",
    task="T1.1",
    current_work="Working on database setup",
    status="in_progress",
    notes="Database password generated"
)
```

---

## Agent Management

### Create Specialized Agent

```python
create_agent_definition(
    specialization="media-download",
    capabilities="troubleshoot-stuck-downloads skill, sonarr tools",
    initial_tasks="Fix stuck downloads in Sonarr queue",
    parent_agent_id="agent-001"
)
```

### Query Agent Registry

```python
agents = query_agent_registry(
    specialization="media-download"
)
```

### Assign Task to Agent

```python
assign_task_to_agent(
    agent_id="agent-002",
    task_description="Fix stuck downloads in Sonarr"
)
```

---

## Communication

### Send Message to Agent

```python
send_agent_message(
    from_agent_id="agent-001",
    to_agent_id="agent-002",
    message_type="request",
    subject="Need help with deployment",
    body="Can you help me deploy the trading-bot service?",
    priority="high"
)
```

### Get Messages

```python
messages = get_agent_messages(
    agent_id="agent-001",
    status="pending"
)

# Acknowledge urgent messages
for msg in messages["messages"]:
    if msg["priority"] in ["urgent", "high"]:
        acknowledge_message(msg["message_id"], "agent-001")
```

---

## Activity Monitoring

### Start Session

```python
session = start_agent_session(agent_id="agent-001")
```

### Update Status

```python
update_agent_status(
    agent_id="agent-001",
    status="active",
    current_task_id="T1.1",
    progress="Working on database setup",
    blockers="None"
)
```

### End Session

```python
end_agent_session(
    agent_id="agent-001",
    session_id=session["session_id"],
    tasks_completed=3,
    tools_called=25,
    total_duration_ms=3600000
)
```

---

## Deployment

### Standard Deployment

```python
# Use standard-deployment skill
# Or use git_deploy directly
git_deploy(
    commit_message="Update configuration",
    files=["apps/my-app/docker-compose.yml"]
)

# Restart services
docker_compose_restart(
    app_path="apps/my-app",
    service="my-service"
)
```

---

## Common Workflow Patterns

### Starting a New Feature

```python
# 1. Start monitoring
start_agent_session(agent_id="agent-001")
update_agent_status(agent_id="agent-001", status="active", ...)

# 2. Check for messages
messages = get_agent_messages(agent_id="agent-001", status="pending")

# 3. Check memory
decisions = memory_query_decisions(project="my-app", limit=5)

# 4. Get skill suggestions
skills = suggest_relevant_skills(
    prompt_text="Implement new feature",
    task_description="Add feature X to application"
)

# 5. Plan (if major feature)
# ... create plan ...

# 6. Create dev docs
create_dev_docs(...)

# 7. Register task
register_task(...)

# 8. Start implementation
```

### Continuing Work

```python
# 1. Start monitoring
start_agent_session(agent_id="agent-001")

# 2. Check active dev docs
active_docs = list_active_dev_docs(agent_id="agent-001")

# 3. Read dev docs
docs = read_dev_docs(agent_id="agent-001", task_name="task-name")

# 4. Continue from where you left off
```

### Before Compaction

```python
# Update dev docs
update_dev_docs(
    agent_id="agent-001",
    task_name="task-name",
    context_updates="Current progress...",
    completed_tasks="Task 1, Task 2",
    next_steps="Next steps..."
)
```

### After Making Edits

```python
# Check code quality
result = check_code_quality(
    file_paths="files you edited",
    check_types="all"
)

# Fix any errors
if result["has_errors"]:
    # Fix errors...

# Request review
review = request_code_review(
    file_paths="files you edited",
    review_type="self"
)
```

### Debugging Service Issues

```python
# Get error logs
logs = get_service_logs(
    service_name="service-name",
    lines=500,
    level="error"
)

# Check status
status = monitor_service_status(service_name="service-name")

# Restart if needed
if not status["is_running"]:
    restart_service(service_name="service-name")
```

---

**Last Updated**: 2025-01-13  
**Status**: Active  
**See Also**:
- `agents/prompts/base.md` - Main agent prompt
- `agents/docs/AGENT_WORKFLOW.md` - Complete workflow guide
- `agents/docs/QUICK_START.md` - Quick start guide

