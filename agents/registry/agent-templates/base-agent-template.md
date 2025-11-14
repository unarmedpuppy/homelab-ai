# Agent Template: Base Agent

Template for creating new specialized agents.

## Template Usage

When creating a new agent, copy this template and fill in the specialization-specific details.

## Agent Definition Template

```markdown
---
agent_id: agent-XXX
specialization: [specialization-name]
created_by: [parent-agent-id]
created_date: YYYY-MM-DD
status: ready|active|archived
parent_agent: [parent-agent-id]
---

# Agent XXX: [Specialization Name]

## Your Specialization

[Describe what this agent specializes in]

## Your Purpose

[What this agent is designed to do]

## Your Capabilities

### Skills
- [List relevant skills from agents/skills/]

### MCP Tools
- [List relevant MCP tools from agents/apps/agent-mcp/]

### Domain Knowledge
- [List specific domain knowledge areas]

## Your Tasks

**Primary Task Location**: `agents/active/agent-XXX-[specialization]/TASKS.md`

Read your TASKS.md file to see assigned tasks.

## How to Work

1. **Read Your Tasks**: Check `agents/active/agent-XXX-[specialization]/TASKS.md`
2. **Check Memory**: Query memory for related decisions and patterns
   - Use `memory_query_decisions()` for related decisions
   - Use `memory_query_patterns()` for common patterns
3. **Use Your Specialization**: Leverage your specialized knowledge
4. **Update Status**: Regularly update `STATUS.md` with progress
5. **Communicate**: Use `COMMUNICATION.md` to communicate with parent agent
6. **Record Decisions**: Use `memory_record_decision()` for important decisions
7. **Complete Tasks**: Mark tasks complete in TASKS.md

## Communication

### With Parent Agent

- **Task Assignment**: Check TASKS.md for new tasks
- **Status Updates**: Update STATUS.md regularly
- **Guidance**: Check COMMUNICATION.md for parent guidance
- **Results**: Document results in RESULTS.md

### File Structure

```
agents/active/agent-XXX-[specialization]/
├── TASKS.md              # Your assigned tasks
├── STATUS.md             # Your current status
├── COMMUNICATION.md      # Parent-child communication
└── RESULTS.md            # Completed work results
```

## Your Prompt

**Read your agent prompt to understand how to work:**
- **General agents**: Read `agents/prompts/base.md`
- **Server management agents**: Read `agents/prompts/server.md` (extends base.md)
- **Domain-specific agents**: Check if `agents/prompts/[domain].md` exists, otherwise use `base.md`

The prompt defines your workflow, principles, and how to use systems (memory, skills, tools).

## Discovery Workflow

Before starting work:

1. **Read Your Prompt**: Read your agent prompt (see above)
2. **Check Memory**: Query previous decisions and patterns using memory MCP tools
3. **Check Skills**: Review `agents/skills/README.md` for relevant workflows
4. **Check MCP Tools**: Review `agents/apps/agent-mcp/README.md` for available tools
5. **Read Your Tasks**: Check TASKS.md for assigned work

## Memory Integration

Use memory MCP tools throughout your work:

- **Before Work**: `memory_query_decisions()`, `memory_query_patterns()`
- **During Work**: `memory_record_decision()`, `memory_record_pattern()`
- **After Work**: `memory_save_context(status="completed")`

## Status Updates

Update STATUS.md regularly with:

- Current task progress
- Any blockers
- Next steps
- Questions for parent agent

---

**Template Version**: 1.0
**Last Updated**: 2025-01-10

