# MCP Tools Reference

**Central reference for MCP tool counts and categories.**

## Getting Tool Count

**⚠️ IMPORTANT**: Tool count is **dynamic** based on which categories are enabled. Always use the `list_tool_categories()` MCP tool to get the current count.

### How to Get Tool Count

```python
# Use the MCP tool to get current tool count
result = await list_tool_categories()

# Get total enabled tools
total_tools = result["total_tools_enabled"]

# Get breakdown by category
for category, info in result["categories"].items():
    if info["enabled"]:
        print(f"{info['name']}: {info['tool_count']} tools")
```

### Tool Categories

Tools are organized into categories that can be enabled/disabled via the `MCP_TOOL_CATEGORIES` environment variable.

**Default Enabled Categories** (core functionality):
- `core` - Essential tools (infrastructure, activity monitoring, communication)
- `docker` - Docker management
- `monitoring` - System monitoring
- `memory` - Memory management
- `agents` - Agent management
- `tasks` - Task coordination
- `skills` - Skill management

**Optional Categories** (disabled by default):
- `media` - Media download (Sonarr, Radarr)
- `git` - Git operations
- `networking` - Networking tools
- `dev` - Development tools (dev docs, quality checks, code review)
- `learning` - Learning & evaluation
- `productivity` - Productivity tools (Monica PRM)

### Configuration

Set `MCP_TOOL_CATEGORIES` environment variable to enable specific categories:

```bash
# Enable only core and docker
export MCP_TOOL_CATEGORIES=core,docker

# Enable all categories
export MCP_TOOL_CATEGORIES=core,docker,monitoring,memory,agents,tasks,skills,media,git,networking,dev,learning,productivity
```

## Tool Count in Documentation

**When referencing tool counts in documentation**, use one of these approaches:

1. **Reference this document**: "See `agents/apps/agent-mcp/MCP_TOOLS_REFERENCE.md` for current tool count"
2. **Use dynamic reference**: "Use `list_tool_categories()` MCP tool to get current tool count"
3. **Note it's dynamic**: "Tool count varies based on enabled categories (use `list_tool_categories()` to check)"

**Do NOT hardcode tool counts** in documentation - they change as tools are added/removed.

## Complete Tool List

For the complete list of all available tools, see:
- `agents/apps/agent-mcp/README.md` - Complete tool catalog
- Use `list_tool_categories()` MCP tool - Returns all tools with descriptions

---

**Last Updated**: 2025-01-13  
**Status**: Active Reference

