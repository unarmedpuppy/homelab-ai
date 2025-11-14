# Agent Template: Server Management Specialist

Template for creating server management specialized agents.

## Specialization

Home server infrastructure management, Docker, networking, system administration.

## Capabilities

**Note**: Capabilities are now embedded in `prompts/server.md` under "Your Capabilities" section.

**This template is for reference only** - the prompt contains the complete, authoritative list.

**Quick Reference:**
- **Skills**: See `prompts/server.md` "Your Capabilities" → "Relevant Skills"
- **MCP Tools**: See `prompts/server.md` "Your Capabilities" → "Relevant MCP Tools"
- **Domain Knowledge**: See `prompts/server.md` "Your Capabilities" → "Domain Knowledge"

**Why**: Prompts are the source of truth. This template is just metadata for the agent creation tool.

## Typical Tasks

- Deploy services to server
- Troubleshoot container issues
- System health monitoring
- Service configuration
- Network troubleshooting
- Deployment automation

## Prompt

**Use**: `agents/prompts/server.md` (extends `agents/prompts/base.md`)

The server prompt provides:
- Server connection methods
- Server-specific MCP tools
- Server-specific workflows
- Server-specific patterns

**Read both prompts**:
1. First read `agents/prompts/base.md` (universal workflows)
2. Then read `agents/prompts/server.md` (server-specific context)

## Usage

Copy this template when creating a server management specialized agent.

When creating the agent definition, reference:
- **Template**: `server-management-agent.md` (this file)
- **Prompt**: `agents/prompts/server.md`

---

**Template Version**: 1.1
**Last Updated**: 2025-01-13

