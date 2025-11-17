# Dynamic MCP Tool Discovery

## Problem

The MCP server had 102 tools, which exceeded Cursor's recommended limit of 80 tools. This caused performance issues and warnings.

## Solution: Category-Based Tool Loading

Tools are now organized into **categories** and only enabled categories are loaded. This reduces the initial tool count significantly.

### Default Configuration

By default, only **essential categories** are enabled:
- `core` - Infrastructure, activity monitoring, communication (3 tool modules)
- `docker` - Docker management (1 tool module)
- `monitoring` - System monitoring, troubleshooting (4 tool modules)
- `memory` - Memory management (1 tool module)
- `agents` - Agent management (2 tool modules)
- `tasks` - Task coordination (1 tool module)
- `skills` - Skill management (2 tool modules)

**Total: ~50-60 tools** (down from 102)

### Disabled by Default

These categories are disabled by default but can be enabled when needed:
- `media` - Media download tools (Sonarr, Radarr, etc.)
- `git` - Git operations
- `networking` - Network, VPN, DNS tools
- `dev` - Development tools (dev docs, quality checks, code review)
- `learning` - Learning, critiquing, evaluation tools

## Configuration

### Environment Variable

Set `MCP_TOOL_CATEGORIES` to enable specific categories:

```bash
# Enable only core tools
MCP_TOOL_CATEGORIES=core,docker

# Enable core + media tools
MCP_TOOL_CATEGORIES=core,docker,monitoring,media

# Enable everything
MCP_TOOL_CATEGORIES=core,docker,monitoring,memory,agents,tasks,skills,media,git,networking,dev,learning
```

### Cursor Configuration

Update your Cursor `mcp.json` to include the environment variable:

```json
{
  "mcpServers": {
    "home-server": {
      "command": "/opt/homebrew/bin/python3",
      "args": [
        "/Users/joshuajenquist/repos/personal/home-server/agents/apps/agent-mcp/server.py"
      ],
      "env": {
        "AGENT_MONITORING_API_URL": "http://localhost:3001",
        "PYTHONPATH": "/Users/joshuajenquist/repos/personal/home-server",
        "MCP_TOOL_CATEGORIES": "core,docker,monitoring,memory,agents,tasks,skills"
      }
    }
  }
}
```

### Available Categories

| Category | Description | Tool Modules | Default |
|----------|-------------|--------------|---------|
| `core` | Essential tools | infrastructure, activity_monitoring, communication | ✅ |
| `docker` | Docker management | docker | ✅ |
| `monitoring` | System monitoring | monitoring, system, troubleshooting, service_debugging | ✅ |
| `memory` | Memory management | memory | ✅ |
| `agents` | Agent management | agent_management, agent_documentation | ✅ |
| `tasks` | Task coordination | task_coordination | ✅ |
| `skills` | Skill management | skill_management, skill_activation | ✅ |
| `media` | Media download | media_download | ❌ |
| `git` | Git operations | git | ❌ |
| `networking` | Networking tools | networking | ❌ |
| `dev` | Development tools | dev_docs, quality_checks, code_review | ❌ |
| `learning` | Learning & evaluation | learning, critiquing, evaluation | ❌ |

## Discovering Available Tools

Use the `list_tool_categories` tool to see:
- Which categories are enabled
- How many tools each category contains
- How to configure categories

Example:
```
"List available tool categories"
```

## Benefits

1. **Reduced Tool Count**: Only load what you need
2. **Better Performance**: Fewer tools = faster tool discovery
3. **Flexible Configuration**: Enable categories as needed
4. **No Code Changes**: Just change environment variable

## Dynamic Discovery

The system is designed for dynamic discovery:
- Tools are organized by category
- Categories can be enabled/disabled via environment variable
- No need to modify code to add/remove tools
- Server restart required to apply category changes (MCP limitation)

## Future Improvements

Potential enhancements:
- Runtime category enable/disable (would require MCP protocol changes)
- Per-session category configuration
- Tool usage analytics to suggest optimal categories

