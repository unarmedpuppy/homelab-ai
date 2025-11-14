# MCP Server Setup for Cursor - Step-by-Step Guide

## Step 0.5: Configure MCP Server in Cursor

This guide walks you through setting up the Python MCP server so Cursor can use all 71+ agent tools.

---

## Prerequisites

- ✅ **Python 3.8+** installed
- ✅ **pip** installed
- ✅ **Cursor** installed
- ✅ **Agent infrastructure running** (Step 0 complete)

---

## Step 1: Install MCP Server Dependencies

The MCP server is a Python application. Install dependencies:

```bash
cd /Users/joshuajenquist/repos/personal/home-server/agents/apps/agent-mcp
python3 -m pip install -r requirements.txt --break-system-packages
```

Or use a virtual environment (recommended):

```bash
cd /Users/joshuajenquist/repos/personal/home-server/agents/apps/agent-mcp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

This will install:
- `mcp` - Model Context Protocol SDK
- `python-dotenv` - Environment variable management
- `aiohttp` - Async HTTP client
- `pydantic` - Data validation
- `docker` - Docker API client

---

## Step 2: Verify Installation

Test that the server can be imported:

```bash
cd /Users/joshuajenquist/repos/personal/home-server/agents/apps/agent-mcp
python3 -c "import mcp; print('MCP installed successfully')"
```

---

## Step 3: Create Cursor MCP Configuration

### Location

**macOS**: `~/Library/Application Support/Cursor/User/globalStorage/mcp.json`

### Create the Config File

1. **Open Terminal** and run:
   ```bash
   mkdir -p ~/Library/Application\ Support/Cursor/User/globalStorage
   ```

2. **Create/edit the config file**:
   ```bash
   nano ~/Library/Application\ Support/Cursor/User/globalStorage/mcp.json
   ```

   Or use your preferred editor (VS Code, Cursor, etc.)

### Configuration Content

**Python MCP Server Configuration**:

```json
{
  "mcpServers": {
    "home-server": {
      "command": "/opt/homebrew/bin/python3",
      "args": [
        "/Users/joshuajenquist/repos/personal/home-server/agents/apps/agent-mcp/server.py"
      ],
      "env": {
        "AGENT_MONITORING_API_URL": "http://localhost:3001"
      }
    }
  }
}
```

**Note**: Replace `/opt/homebrew/bin/python3` with the output of `which python3` if different.

### Optional: Add API Keys

If you need Sonarr/Radarr tools, add API keys to the `env` section:

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
        "SONARR_API_KEY": "your-sonarr-api-key-here",
        "RADARR_API_KEY": "your-radarr-api-key-here"
      }
    }
  }
}
```

### Using Virtual Environment

If you installed dependencies in a virtual environment, use the venv's Python:

```json
{
  "mcpServers": {
    "home-server": {
      "command": "/Users/joshuajenquist/repos/personal/home-server/agents/apps/agent-mcp/venv/bin/python",
      "args": [
        "/Users/joshuajenquist/repos/personal/home-server/agents/apps/agent-mcp/server.py"
      ],
      "env": {
        "AGENT_MONITORING_API_URL": "http://localhost:3001"
      }
    }
  }
}
```

---

## Step 4: Restart Cursor

**Important**: You must restart Cursor for the MCP configuration to take effect.

1. **Quit Cursor completely** (⌘Q on macOS)
2. **Reopen Cursor**
3. **Open a new chat/conversation**

---

## Step 5: Verify MCP Tools Are Available

Once Cursor restarts, the MCP tools should be available. You can test by:

1. **In a Cursor chat**, try asking:
   - "Check agent infrastructure status"
   - "List all Docker containers"

2. **Check Cursor's MCP status** (if available in settings)

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'mcp'"

**Problem**: Python can't find the MCP module.

**Solutions**:
1. Verify installation: `python3 -c "import mcp; print('OK')"`
2. Reinstall dependencies: `pip install -r requirements.txt --break-system-packages`
3. Check Python version: `python3 --version` (should be 3.8+)
4. Use virtual environment if system packages are protected

### "Command not found: python3"

**Problem**: Cursor can't find Python.

**Solutions**:
1. Find Python: `which python3`
2. Update config with full path to python3
3. Install Python if missing: `brew install python3`

### MCP Server Not Starting

**Problem**: Cursor shows MCP server errors.

**Solutions**:
1. Check config file syntax (must be valid JSON)
2. Verify server.py path is correct and file exists: `ls -la agents/apps/agent-mcp/server.py`
3. Test server manually: `python3 agents/apps/agent-mcp/server.py` (should start and wait for input)
4. Check Python dependencies: `python3 -c "import mcp, aiohttp, pydantic, docker; print('All dependencies OK')"`
5. Check Cursor logs for specific error messages

### Tools Not Appearing

**Problem**: MCP config looks correct but tools don't show up.

**Solutions**:
1. Restart Cursor again
2. Check Cursor settings for MCP server status
3. Verify agent infrastructure is running (Step 0)
4. Try a simple tool first: `check_agent_infrastructure()`
5. Check that Python can import all modules: `python3 -c "from tools.infrastructure import register_infrastructure_tools; print('OK')"`

---

## What You Get

Once configured, you'll have access to **71+ MCP tools**:

- ✅ **Activity Monitoring** (4 tools) - Start sessions, update status
- ✅ **Memory Management** (9 tools) - Query and record decisions/patterns
- ✅ **Task Coordination** (6 tools) - Register and manage tasks
- ✅ **Agent Management** (6 tools) - Create and manage agents
- ✅ **Agent Communication** (5 tools)
- ✅ **Docker Management** (8 tools)
- ✅ **Media Download** (13 tools)
- ✅ **System Monitoring** (5 tools)
- ✅ **Git Operations** (4 tools)
- ✅ **Troubleshooting** (3 tools)
- ✅ **Networking** (3 tools)
- ✅ **System Utilities** (3 tools)
- ✅ **Skill Management** (3 tools)
- ✅ **Skill Activation** (2 tools)
- ✅ **Dev Docs** (4 tools)
- ✅ **Agent Documentation** (5 tools)
- ✅ **Quality Checks** (2 tools)
- ✅ **Code Review** (2 tools)
- ✅ **Service Debugging** (4 tools)

---

## Next Steps

After completing Step 0.5, proceed to **Step 1: Check Memory First** as outlined in `base.md`.
