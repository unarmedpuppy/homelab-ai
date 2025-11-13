# Agent Activation Guide

Guide for humans to activate specialized agents created by other agents.

## Overview

When an agent creates a specialized agent, it creates:
1. **Agent Definition** - Specialized prompt/config file
2. **Task Assignment** - Tasks for the specialized agent
3. **Registry Entry** - Entry in agent registry

**You** (human) need to activate the agent by opening a new Cursor session with the agent definition.

## Activation Process

### Step 1: Check Agent Registry

Review `agents/registry/agent-registry.md` for ready agents:

```markdown
## Ready Agents

| Agent ID | Specialization | Created By | Created Date | Definition | Tasks |
|----------|---------------|------------|--------------|------------|-------|
| agent-002 | media-download | agent-001 | 2025-01-10 | `agents/registry/agent-definitions/agent-002-media-download.md` | `agents/active/agent-002-media-download/TASKS.md` |
```

### Step 2: Review Agent Definition

Read the agent definition file to understand what the agent does:

```bash
# View agent definition
cat agents/registry/agent-definitions/agent-002-media-download.md
```

The definition includes:
- Specialization and purpose
- Capabilities (skills, tools, knowledge)
- Assigned tasks
- How to work

### Step 3: Review Assigned Tasks

Check the tasks file to see what the agent needs to do:

```bash
# View tasks
cat agents/active/agent-002-media-download/TASKS.md
```

### Step 4: Activate Agent

**Option A: Copy Prompt to New Cursor Session**

1. Open new Cursor session (new chat)
2. Copy the agent definition content
3. Paste as initial prompt/context
4. Agent will read its TASKS.md and begin work

**Option B: Reference Agent Definition**

1. Open new Cursor session
2. Reference the agent definition file:
   ```
   I am agent-002, a media download specialist. 
   Please read my definition: agents/registry/agent-definitions/agent-002-media-download.md
   And my tasks: agents/active/agent-002-media-download/TASKS.md
   ```
3. Agent will read files and begin work

### Step 5: Agent Works

The specialized agent will:
1. Read its TASKS.md file
2. Check memory for related decisions
3. Use specialized knowledge to complete tasks
4. Update STATUS.md with progress
5. Communicate via COMMUNICATION.md if needed

### Step 6: Monitor Progress

Check agent status:

```bash
# View current status
cat agents/active/agent-002-media-download/STATUS.md

# View communication
cat agents/active/agent-002-media-download/COMMUNICATION.md
```

## Agent File Structure

Each active agent has:

```
agents/active/agent-XXX-[specialization]/
├── TASKS.md              # Assigned tasks
├── STATUS.md             # Current status and progress
├── COMMUNICATION.md      # Parent-child communication
└── RESULTS.md            # Completed work results
```

## Example Activation

### Scenario: Media Download Agent

**Step 1: Check Registry**

```bash
cat agents/registry/agent-registry.md
```

See: `agent-002` ready for activation

**Step 2: Review Definition**

```bash
cat agents/registry/agent-definitions/agent-002-media-download.md
```

**Step 3: Review Tasks**

```bash
cat agents/active/agent-002-media-download/TASKS.md
```

**Step 4: Activate**

Open new Cursor session and say:

```
I am agent-002, a media download specialist created by agent-001.

Please read:
- My definition: agents/registry/agent-definitions/agent-002-media-download.md
- My tasks: agents/active/agent-002-media-download/TASKS.md

I'm ready to start working on my assigned tasks.
```

**Step 5: Agent Works**

Agent will:
- Read tasks
- Query memory for related decisions
- Use specialized knowledge
- Complete tasks
- Update status

## Updating Registry

After agent is activated and working, you can update the registry:

1. Move agent from "Ready Agents" to "Active Agents" table
2. Update status in agent definition file: `status: active`

## Completing Agents

When agent completes all tasks:

1. Review RESULTS.md
2. Archive agent: Move to `agents/archive/`
3. Update registry: Move to "Archived Agents" table
4. Update agent definition: `status: archived`

## Tips

- **Review before activating**: Check agent definition and tasks
- **Monitor progress**: Check STATUS.md regularly
- **Provide guidance**: Use COMMUNICATION.md if agent needs help
- **Archive when done**: Keep registry clean

## Troubleshooting

### Agent Not Finding Tasks

Make sure agent reads:
- `agents/active/agent-XXX-[specialization]/TASKS.md`

### Agent Not Updating Status

Remind agent to update:
- `agents/active/agent-XXX-[specialization]/STATUS.md`

### Communication Issues

Use:
- `agents/active/agent-XXX-[specialization]/COMMUNICATION.md`

---

**Last Updated**: 2025-01-10
**Status**: Active

