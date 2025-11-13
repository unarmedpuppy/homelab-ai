# Memory Usage Examples - Complete Guide

## Overview

This guide provides **real-world examples** of how agents should use the memory system effectively. These examples demonstrate best practices for querying, recording, and using memory throughout the agent workflow.

## Table of Contents

1. [Before Starting Work](#before-starting-work)
2. [During Work](#during-work)
3. [After Work](#after-work)
4. [Common Scenarios](#common-scenarios)
5. [Best Practices](#best-practices)

---

## Before Starting Work

### Example 1: Starting a New Task

**Scenario**: You're about to deploy a new service. Check memory for related decisions first.

**If MCP tools available:**
```python
# Check for previous deployment decisions
decisions = memory_query_decisions(
    project="home-server",
    search_text="deployment docker-compose",
    limit=5
)

# Check for common deployment patterns
patterns = memory_query_patterns(
    severity="high",
    tags="deployment,docker",
    limit=5
)

# Search for related work
results = memory_search("docker-compose setup")
```

**If MCP tools NOT available (fallback):**
```bash
# Use helper script
cd apps/agent_memory
./query_memory.sh decisions --project home-server --search "deployment" --limit 5
./query_memory.sh patterns --severity high --limit 5
./query_memory.sh search "docker-compose"
```

**What to look for:**
- Previous decisions about similar services
- Common patterns or issues encountered
- Port conflicts or configuration patterns
- Network setup decisions

### Example 2: Troubleshooting a Container

**Scenario**: A container won't start. Check memory for similar issues.

**If MCP tools available:**
```python
# Search for troubleshooting patterns
patterns = memory_query_patterns(
    severity="high",
    search_text="container won't start",
    limit=10
)

# Check for similar decisions
decisions = memory_query_decisions(
    search_text="container startup failure",
    limit=5
)

# Get recent context from other agents
context = memory_get_recent_context(limit=5)
```

**If MCP tools NOT available (fallback):**
```bash
./query_memory.sh patterns --severity high --search "container" --limit 10
./query_memory.sh search "startup failure"
./query_memory.sh recent --limit 5
```

**What to look for:**
- Common causes of container failures
- Solutions that worked before
- Recent work by other agents on similar issues

### Example 3: Setting Up a Database

**Scenario**: Need to set up PostgreSQL. Check what was decided before.

**If MCP tools available:**
```python
# Find database-related decisions
decisions = memory_query_decisions(
    project="home-server",
    search_text="PostgreSQL database",
    min_importance=0.7,
    limit=10
)

# Check for database patterns
patterns = memory_query_patterns(
    tags="database,postgresql",
    limit=5
)
```

**If MCP tools NOT available (fallback):**
```bash
./query_memory.sh decisions --project home-server --search "PostgreSQL" --limit 10
./query_memory.sh patterns --search "database" --limit 5
```

**What to look for:**
- Database choice rationale
- Configuration patterns
- Common issues and solutions
- Connection string formats

---

## During Work

### Example 4: Recording Important Decisions

**Scenario**: You decide to use PostgreSQL instead of SQLite. Record this decision.

**If MCP tools available:**
```python
# Record the decision
memory_record_decision(
    content="Use PostgreSQL for trading-journal database",
    rationale="Need ACID compliance, concurrent writes, and complex queries. SQLite doesn't support concurrent writes well and has limited query capabilities.",
    project="trading-journal",
    task="T1.3",
    importance=0.9,
    tags="database,architecture,postgresql"
)
```

**Why this is good:**
- Clear content describing the decision
- Detailed rationale explaining why
- High importance (0.9) for architectural decisions
- Relevant tags for future discovery
- Linked to project and task

### Example 5: Recording Patterns

**Scenario**: You discover a common issue - port conflicts. Record it as a pattern.

**If MCP tools available:**
```python
# Record the pattern
memory_record_pattern(
    name="Port Conflict Resolution",
    description="Services failing to start due to port conflicts. Common when adding new services without checking existing port usage.",
    solution="Always check port availability first using check_port_status MCP tool or grep existing docker-compose files. Reference apps/docs/APPS_DOCUMENTATION.md for port list.",
    severity="medium",
    tags="docker,networking,ports,troubleshooting"
)
```

**Why this is good:**
- Clear pattern name
- Description of the problem
- Actionable solution
- Appropriate severity
- Tags for discovery

### Example 6: Updating Context

**Scenario**: You're working on a task. Update context regularly.

**If MCP tools available:**
```python
# Save initial context
memory_save_context(
    agent_id="agent-001",
    task="T1.3",
    current_work="Setting up PostgreSQL database. Created docker-compose.yml, configured environment variables. Next: Run migrations.",
    status="in_progress",
    notes="Database password generated with openssl rand -hex 32"
)

# Update as work progresses
memory_save_context(
    agent_id="agent-001",
    task="T1.3",
    current_work="PostgreSQL running, migrations applied. Database schema created. Next: Test connection.",
    status="in_progress"
)

# Mark complete when done
memory_save_context(
    agent_id="agent-001",
    task="T1.3",
    current_work="PostgreSQL setup complete. Database running, migrations applied, connection tested.",
    status="completed"
)
```

**Why this is good:**
- Regular updates show progress
- Notes capture important details
- Status changes reflect work state
- Other agents can see what you're working on

---

## After Work

### Example 7: Completing a Task

**Scenario**: You finished setting up a service. Save final context and record decisions.

**If MCP tools available:**
```python
# Save final context
memory_save_context(
    agent_id="agent-001",
    task="T1.3",
    current_work="Service setup complete. All containers running, health checks passing, accessible via homepage.",
    status="completed",
    notes="Used port 8099, added to homepage, configured Traefik labels"
)

# Record any important decisions made
memory_record_decision(
    content="Use port 8099 for new service",
    rationale="Port 8099 was available and follows the 8000-8099 range for application services",
    project="home-server",
    task="T1.3",
    importance=0.6,
    tags="networking,ports"
)
```

### Example 8: Learning from Mistakes

**Scenario**: You encountered an issue and solved it. Record it as a pattern.

**If MCP tools available:**
```python
# Record the pattern so others don't repeat the mistake
memory_record_pattern(
    name="Missing Health Check Causes Startup Failure",
    description="Container appears to start but fails health check, causing dependent services to fail. Health check not configured in docker-compose.yml.",
    solution="Always add healthcheck section to docker-compose.yml for services that other services depend on. Use depends_on with healthcheck condition.",
    severity="high",
    tags="docker,healthcheck,dependencies"
)
```

---

## Common Scenarios

### Scenario 1: "I need to deploy a new service"

**Workflow:**
1. **Check memory first:**
   ```python
   # Check for deployment patterns
   patterns = memory_query_patterns(tags="deployment", limit=5)
   # Check for port conflicts
   decisions = memory_query_decisions(search_text="port", limit=10)
   ```

2. **Record decisions as you make them:**
   ```python
   memory_record_decision(
       content="Use port 8099 for new service",
       rationale="Available port in application range",
       importance=0.7
   )
   ```

3. **Record patterns if you discover issues:**
   ```python
   memory_record_pattern(
       name="Port Conflict Pattern",
       description="...",
       solution="Always check ports first"
   )
   ```

### Scenario 2: "A container won't start"

**Workflow:**
1. **Check memory for similar issues:**
   ```python
   patterns = memory_query_patterns(
       search_text="container startup",
       severity="high",
       limit=10
   )
   ```

2. **Check recent context:**
   ```python
   context = memory_get_recent_context(limit=5)
   # See if other agents worked on similar issues
   ```

3. **Record solution if you find one:**
   ```python
   memory_record_pattern(
       name="Container Startup Failure - Missing Environment Variables",
       description="...",
       solution="Check .env file exists and variables are set"
   )
   ```

### Scenario 3: "I'm choosing between technologies"

**Workflow:**
1. **Check previous technology decisions:**
   ```python
   decisions = memory_query_decisions(
       search_text="database technology",
       min_importance=0.8,
       limit=10
   )
   ```

2. **Record your decision:**
   ```python
   memory_record_decision(
       content="Use PostgreSQL for new project",
       rationale="Previous decision: Need ACID compliance. See decision ID 42.",
       importance=0.9,
       tags="database,postgresql"
   )
   ```

### Scenario 4: "I'm troubleshooting a recurring issue"

**Workflow:**
1. **Check if this is a known pattern:**
   ```python
   patterns = memory_query_patterns(
       search_text="your issue description",
       limit=10
   )
   ```

2. **If pattern exists, use the solution**
3. **If new pattern, record it:**
   ```python
   memory_record_pattern(
       name="Issue Name",
       description="What the issue is",
       solution="How to fix it",
       severity="high"  # If it's critical
   )
   ```

---

## Best Practices

### 1. Always Check Memory First

**Before starting any task:**
- ✅ Query related decisions
- ✅ Check for patterns
- ✅ Search for similar work
- ✅ Review recent context

**Why**: Learn from past work, avoid repeating mistakes, use proven solutions.

### 2. Record Important Decisions

**What to record:**
- ✅ Technology choices (databases, frameworks, tools)
- ✅ Architecture decisions
- ✅ Configuration choices (ports, networks, etc.)
- ✅ Design patterns used

**What NOT to record:**
- ❌ Obvious choices (e.g., "use Python for Python project")
- ❌ Temporary workarounds (unless they become permanent)
- ❌ Every small decision (only important ones)

### 3. Record Patterns for Common Issues

**When to record patterns:**
- ✅ Issue occurs multiple times
- ✅ Solution is non-obvious
- ✅ Issue affects multiple services
- ✅ Solution would help other agents

**Pattern structure:**
- Clear name
- Description of the problem
- Actionable solution
- Appropriate severity

### 4. Update Context Regularly

**When to update:**
- ✅ At start of work
- ✅ When making significant progress
- ✅ When blocked
- ✅ When completed

**What to include:**
- Current work description
- Next steps
- Important notes
- Status (in_progress, completed, blocked)

### 5. Use Appropriate Importance Levels

**Importance scale (0.0-1.0):**
- **0.9-1.0**: Critical architectural decisions (database choice, framework selection)
- **0.7-0.8**: Important decisions (port assignments, service configurations)
- **0.5-0.6**: Moderate decisions (naming conventions, minor configs)
- **0.0-0.4**: Low importance (rarely used)

### 6. Use Tags Effectively

**Good tags:**
- Technology: `postgresql`, `docker`, `python`
- Domain: `database`, `networking`, `deployment`
- Type: `architecture`, `troubleshooting`, `configuration`

**Tag examples:**
```python
tags="database,postgresql,architecture"  # Technology + domain + type
tags="docker,networking,ports"          # Technology + domain + specific
tags="troubleshooting,container,startup"  # Type + domain + specific
```

### 7. Link Related Memories

**Use tags to link:**
- Decisions and patterns with same tags are related
- Query by tags to find related memories
- Use consistent tag names

**Example:**
```python
# Decision
memory_record_decision(..., tags="database,postgresql")

# Related pattern
memory_record_pattern(..., tags="database,postgresql")

# Find both
decisions = memory_query_decisions(tags="postgresql")
patterns = memory_query_patterns(tags="postgresql")
```

---

## Real-World Example: Complete Workflow

### Task: Deploy New Service (Monica)

**Step 1: Check Memory First**
```python
# Check for deployment patterns
patterns = memory_query_patterns(tags="deployment", limit=5)
# Found: "Port Conflict Resolution" pattern

# Check for port decisions
decisions = memory_query_decisions(search_text="port 8098", limit=5)
# Found: Port 8098 used by Monica

# Check for similar service setups
results = memory_search("Laravel MySQL service")
# Found: Previous Laravel service setup decisions
```

**Step 2: Make Decisions (Record as You Go)**
```python
# Decision: Use port 8098
memory_record_decision(
    content="Use port 8098 for Monica service",
    rationale="Port 8098 is assigned to Monica in previous setup. Checked port availability.",
    project="home-server",
    importance=0.7,
    tags="networking,ports,monica"
)

# Decision: Use MySQL database
memory_record_decision(
    content="Use MySQL for Monica database",
    rationale="Monica requires MySQL. Previous decision: Use MySQL for Laravel apps.",
    project="home-server",
    importance=0.8,
    tags="database,mysql,monica"
)
```

**Step 3: Update Context**
```python
# Start
memory_save_context(
    agent_id="agent-001",
    task="deploy-monica",
    current_work="Setting up Monica service. Created docker-compose.yml, configured MySQL database.",
    status="in_progress"
)

# Progress
memory_save_context(
    agent_id="agent-001",
    task="deploy-monica",
    current_work="Monica container running, database migrations applied. Testing web interface.",
    status="in_progress"
)

# Complete
memory_save_context(
    agent_id="agent-001",
    task="deploy-monica",
    current_work="Monica service deployed successfully. Accessible at http://192.168.86.47:8098",
    status="completed"
)
```

**Step 4: Record Pattern (If Issue Found)**
```python
# If you encountered an issue and solved it
memory_record_pattern(
    name="Laravel Service Requires APP_URL Environment Variable",
    description="Laravel services fail to generate correct URLs if APP_URL is not set in environment variables.",
    solution="Always set APP_URL environment variable in docker-compose.yml for Laravel services. Use local IP for testing: http://192.168.86.47:PORT",
    severity="medium",
    tags="laravel,docker,environment-variables"
)
```

---

## Quick Reference

### Before Work
```python
# Check memory
memory_query_decisions(project="home-server", limit=5)
memory_query_patterns(severity="high", limit=5)
memory_search("your search query")
```

### During Work
```python
# Record decisions
memory_record_decision(content="...", rationale="...", importance=0.8)

# Record patterns
memory_record_pattern(name="...", description="...", solution="...")

# Update context
memory_save_context(agent_id="...", task="...", current_work="...")
```

### After Work
```python
# Save final context
memory_save_context(..., status="completed")

# Record final decisions
memory_record_decision(...)
```

---

## Fallback Methods

**If MCP tools not available:**

```bash
# Query decisions
./query_memory.sh decisions --project home-server --limit 5

# Query patterns
./query_memory.sh patterns --severity high --limit 5

# Search
./query_memory.sh search "your query"

# Recent context
./query_memory.sh recent --limit 5
```

**See**: `QUERY_MEMORY_README.md` for complete helper script usage.

---

## Tips for Effective Memory Usage

1. **Query before deciding** - Always check memory before making important decisions
2. **Record as you go** - Don't wait until the end, record decisions and patterns as you discover them
3. **Use consistent tags** - Follow tag conventions for better discovery
4. **Link related memories** - Use tags to link decisions and patterns
5. **Update context regularly** - Keep context current so others know what you're working on
6. **Record patterns for issues** - If you solve a problem, record it as a pattern
7. **Use appropriate importance** - Don't mark everything as high importance
8. **Be specific** - Clear content and rationale help future agents

---

**See Also:**
- `MCP_TOOLS_GUIDE.md` - Complete MCP tool reference
- `QUERY_MEMORY_README.md` - Helper script usage
- `ARCHITECTURE.md` - Memory system architecture
- `README.md` - Memory system overview

