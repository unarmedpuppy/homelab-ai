# Templates as Discovery Shortcuts

## Your Insight is Correct! ✅

**Templates ARE shortcuts for skill & tool discovery.**

Looking at the discovery workflow in `prompts/base.md`:
1. Check Memory
2. Check for Specialized Agents
3. **Check Skills** ← Template lists these
4. **Check MCP Tools** ← Template lists these
5. Check Domain Knowledge ← Template lists this

**Templates = Pre-curated discovery results for a specialization**

## Current Redundancy

### The Problem

**Prompts** tell you HOW to discover:
- "Check skills using `suggest_relevant_skills()`"
- "Review `agents/apps/agent-mcp/README.md` for tools"

**Templates** tell you WHAT to discover:
- "Skills: `standard-deployment`, `troubleshoot-container-failure`"
- "MCP Tools: All Docker management tools (8 tools)"

**But**: If you have `prompts/server.md`, why doesn't it just include the template info?

### Current State

**`prompts/server.md`**:
- Lists server-specific MCP tools (Docker, Media Download, System Monitoring)
- References `prompts/base.md` for discovery workflow
- But doesn't list skills or provide curated tool list

**`templates/server-management-agent.md`**:
- Lists skills: `standard-deployment`, `troubleshoot-container-failure`, etc.
- Lists MCP tools: "All Docker management tools (8 tools)"
- Lists domain knowledge
- References `prompts/server.md`

**Redundancy**: Both list tools, but in different formats!

## Better Design Options

### Option A: Embed Template Info in Prompts ✅ RECOMMENDED

**Prompts include template information:**

```markdown
# Server Agent Prompt

## Your Capabilities (Discovery Shortcuts)

### Relevant Skills
- `standard-deployment` - Complete deployment workflow
- `troubleshoot-container-failure` - Container diagnostics
- `system-health-check` - Comprehensive system verification
- `troubleshoot-stuck-downloads` - Download queue issues
- `deploy-new-service` - New service setup

### Relevant MCP Tools
- **Docker Management** (8 tools): `docker_list_containers`, `docker_restart_container`, etc.
- **System Monitoring** (5 tools): `check_disk_space`, `check_system_resources`, etc.
- **Troubleshooting** (3 tools): `troubleshoot_failed_downloads`, etc.

### Domain Knowledge
- Docker and Docker Compose
- Linux system administration
- Networking and port management
- Service lifecycle management
- Git workflows and deployment

[Rest of prompt...]
```

**Benefits:**
- Single source of truth
- Prompt knows its capabilities
- No need to cross-reference
- Templates become optional (just for agent creation tool)

### Option B: Templates as Metadata Only

**Templates become minimal metadata:**

```markdown
# Server Management Agent Template

## Specialization
Server infrastructure management

## Prompt
`prompts/server.md`

## Typical Tasks
- Deploy services
- Troubleshoot containers
- System monitoring
```

**Capabilities come from prompt, not template.**

### Option C: Keep Separate, Acknowledge Relationship

**Current design, but clarify:**
- Templates = Discovery shortcuts (pre-curated skills/tools)
- Prompts = How to work (workflow, principles)
- Agent definitions = Combine both

**Templates are optional** - agents can discover from scratch using prompt workflow.

## Recommendation: Option A ✅ IMPLEMENTED

**Embed template info in prompts** because:

1. **Single source of truth** - Prompt contains everything
2. **No cross-referencing** - Agent reads prompt, gets capabilities
3. **Templates become optional** - Just used by `create_agent_definition` tool
4. **Simpler mental model** - One file to read, not two

**Templates now:**
- Minimal metadata for agent creation tool
- Quick reference for humans
- Optional starting point

**Prompts now include:**
- Workflow and principles (HOW)
- Curated capabilities (WHAT) ← Moved from templates
- Discovery shortcuts (pre-curated skills/tools)

## Implementation Status

✅ **COMPLETE**: 
1. ✅ Added "Your Capabilities" section to `prompts/server.md`
2. ✅ Includes pre-curated skills list
3. ✅ Includes pre-curated MCP tools list
4. ✅ Includes domain knowledge
5. ✅ Templates remain as optional helpers for agent creation

**Result**: 
- Server prompt is now self-contained
- Agents reading `prompts/server.md` get capabilities directly
- Templates are optional (just for `create_agent_definition` tool)
- No need to cross-reference between prompt and template

---

**Your insight was spot-on**: Templates are discovery shortcuts, and they're now embedded in prompts for simplicity.

