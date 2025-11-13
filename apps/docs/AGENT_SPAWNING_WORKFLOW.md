# Agent Spawning Workflow

## Overview

This document defines how agents can create specialized agents to handle domain-specific tasks or complex workflows that require specialized knowledge.

## When to Spawn an Agent

### Use Cases

1. **Domain Expertise Required**
   - Task requires specialized knowledge (e.g., database optimization, security hardening)
   - Current agent lacks domain expertise
   - Task would benefit from specialized agent

2. **Complex Multi-Step Workflow**
   - Task involves multiple independent sub-tasks
   - Can be parallelized with specialized agents
   - Requires coordination between agents

3. **Long-Running Task**
   - Task will take multiple sessions
   - Needs dedicated agent to maintain context
   - Requires continuous monitoring

4. **Reusable Specialization**
   - Similar tasks will recur
   - Specialized agent can be reused
   - Worth creating persistent agent

### When NOT to Spawn

- Task can be completed in single session
- No specialized knowledge required
- Task is one-off (won't recur)
- Current agent has sufficient knowledge

## Agent Spawning Process

### Step 1: Identify Need

Agent identifies that spawning is beneficial:

```markdown
## Spawning Decision

**Task**: [Task description]
**Why Spawn**: [Reason - domain expertise, complexity, etc.]
**Specialization Needed**: [Domain or skill]
**Expected Duration**: [Single session | Multiple sessions]
**Reusability**: [One-off | Recurring]
```

### Step 2: Check Agent Registry

Check if specialized agent already exists:

```markdown
## Check Agent Registry

1. Review `agents/registry/agent-registry.md`
2. Search for existing agents with required specialization
3. If exists: Assign task to existing agent
4. If not: Proceed to create new agent
```

### Step 3: Create Agent Proposal

Create agent proposal document:

```markdown
---
proposed_by: agent-XXX
date: 2025-01-10
specialization: [domain]
status: proposal|approved|rejected
---

# Agent Proposal: [Agent Name]

## Specialization
[Domain or skill this agent specializes in]

## Purpose
[What this agent will do]

## Capabilities
- Skills: [list of skills]
- MCP Tools: [list of tools]
- Domain Knowledge: [specific knowledge]

## First Task
[Initial task to assign]

## Expected Duration
[How long this agent will be active]

## Reusability
[Will this agent be reused?]
```

### Step 4: Create Agent Instance

If approved, create agent instance:

```bash
# Create agent directory
mkdir -p agents/active/agent-XXX-[specialization]

# Create agent configuration
touch agents/active/agent-XXX-[specialization]/AGENT_CONFIG.md

# Create agent prompt
touch agents/active/agent-XXX-[specialization]/AGENT_PROMPT.md
```

### Step 5: Register Agent

Add to agent registry:

```markdown
## agents/registry/agent-registry.md

### agent-XXX-[specialization]
- **Created**: 2025-01-10
- **Created By**: agent-YYY
- **Specialization**: [domain]
- **Status**: active
- **Capabilities**: [list]
- **Location**: `agents/active/agent-XXX-[specialization]/`
```

### Step 6: Assign Initial Task

Assign first task to new agent:

```markdown
## Task Assignment

**Agent**: agent-XXX-[specialization]
**Task**: [Task description]
**Assigned By**: agent-YYY
**Due Date**: [if applicable]
**Priority**: [high|medium|low]
```

### Step 7: Monitor Progress

Monitor specialized agent's work:

```markdown
## Agent Monitoring

- Check agent status files
- Review progress updates
- Provide guidance if needed
- Integrate results when complete
```

## Agent Templates

### Base Agent Template

```markdown
---
agent_id: agent-XXX
specialization: [domain]
created_by: agent-YYY
created_date: 2025-01-10
status: active|completed|archived
---

# Agent XXX: [Specialization]

## Purpose
[What this agent specializes in]

## Capabilities
- Skills: [list]
- MCP Tools: [list]
- Domain Knowledge: [list]

## Current Tasks
[List of active tasks]

## Communication
[How this agent communicates]

## Status
[Current status and progress]
```

### Specialized Agent Templates

#### Server Management Agent
```markdown
---
agent_id: agent-XXX
specialization: server-management
template: server-management-agent
---

# Server Management Agent

## Specialization
Home server infrastructure management

## Capabilities
- Skills: standard-deployment, troubleshoot-container-failure, system-health-check
- MCP Tools: All server-management-mcp tools
- Domain Knowledge: Docker, networking, system administration

## Typical Tasks
- Deploy services
- Troubleshoot issues
- System maintenance
- Configuration management
```

#### Media Download Agent
```markdown
---
agent_id: agent-XXX
specialization: media-download
template: media-download-agent
---

# Media Download Agent

## Specialization
Sonarr/Radarr/NZBGet management

## Capabilities
- Skills: troubleshoot-stuck-downloads, add-root-folder
- MCP Tools: Media download MCP tools
- Domain Knowledge: Sonarr, Radarr, download clients, media organization

## Typical Tasks
- Fix download queues
- Configure download clients
- Manage root folders
- Troubleshoot media issues
```

## Agent Registry Structure

```
agents/
├── registry/
│   ├── agent-registry.md          # Master registry
│   ├── agent-templates/           # Agent templates
│   │   ├── base-agent.md
│   │   ├── server-management-agent.md
│   │   └── media-download-agent.md
│   └── specializations/          # Specialization definitions
│       ├── server-management.md
│       └── media-download.md
├── active/
│   ├── agent-001-server-mgmt/
│   │   ├── AGENT_CONFIG.md
│   │   ├── AGENT_PROMPT.md
│   │   └── status/
│   └── agent-002-media-download/
│       ├── AGENT_CONFIG.md
│       ├── AGENT_PROMPT.md
│       └── status/
└── archive/
    └── agent-001-completed/
```

## Agent Communication

### Parent-Child Communication

**Parent Agent** (spawner) communicates with **Child Agent** (spawned):

1. **Task Assignment**: Parent assigns task via task file
2. **Status Updates**: Child updates status files
3. **Progress Reports**: Child provides progress updates
4. **Result Integration**: Parent integrates child's results

### Communication Files

```
agents/active/agent-XXX/
├── tasks/
│   └── task-001.md              # Assigned tasks
├── status/
│   └── status-001.md            # Status updates
└── results/
    └── result-001.md            # Completed work
```

## Agent Lifecycle

### 1. Creation
- Agent proposal created
- Agent instance created
- Agent registered

### 2. Active
- Agent working on tasks
- Regular status updates
- Communication with parent

### 3. Completion
- Tasks completed
- Results integrated
- Agent archived

### 4. Reuse (Optional)
- Agent kept active for future tasks
- Agent capabilities updated
- Agent remains in registry

## Best Practices

1. **Only Spawn When Needed**: Don't spawn for simple tasks
2. **Reuse Existing Agents**: Check registry first
3. **Clear Specialization**: Define specialization clearly
4. **Monitor Progress**: Track specialized agent's work
5. **Integrate Results**: Properly integrate child's work
6. **Archive When Done**: Archive completed agents

## Integration with Memory System

If memory system is integrated:

```python
# Parent agent creates child agent
api.create_node(
    type=NodeType.AGENT,
    content="Created agent-XXX for media-download specialization",
    metadata={
        "parent_agent": "agent-YYY",
        "specialization": "media-download",
        "task": "T1.5"
    }
)

# Link parent and child
api.create_edge(
    source_id=parent_agent.id,
    target_id=child_agent.id,
    type=EdgeType.SPAWNED
)
```

## Examples

### Example 1: Spawn Media Download Agent

**Parent Agent** (server-management) needs to fix Sonarr queue:

```markdown
## Spawning Decision

**Task**: Fix 163 stuck downloads in Sonarr
**Why Spawn**: Requires specialized knowledge of Sonarr/Radarr
**Specialization Needed**: media-download
**Expected Duration**: Single session
**Reusability**: Recurring (queue issues happen often)

## Action: Spawn agent-002-media-download

1. Check registry: No existing media-download agent
2. Create agent proposal
3. Create agent instance
4. Register agent
5. Assign task: "Fix Sonarr queue"
6. Monitor progress
7. Integrate results
```

### Example 2: Reuse Existing Agent

**Parent Agent** needs database optimization:

```markdown
## Spawning Decision

**Task**: Optimize PostgreSQL database
**Why Spawn**: Requires database expertise
**Specialization Needed**: database-optimization

## Check Registry

Found: agent-005-database (active)
**Action**: Assign task to existing agent
```

## Status

**Status**: Proposal
**Priority**: High
**Implementation**: See `AGENT_WORKFLOW_GAPS_AND_IMPROVEMENTS.md`

---

**Last Updated**: 2025-01-10
**Maintained By**: Agent workflow system

