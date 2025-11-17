# MCP Server Troubleshooting Guide

## Current Status

✅ **MCP Server is Working**
- Server initializes correctly
- 102 tools registered
- Responds to MCP protocol requests
- Config file is valid

❌ **Cursor Not Connecting**
- No MCP output/logs visible
- No MCP settings in Cursor UI
- Restarting doesn't help

## Possible Causes

### 1. Cursor Version Too Old

**MCP support requires Cursor 0.40+**

**Check your version:**
- Open Cursor
- Go to `Cursor > About Cursor` (menu bar)
- Or check `Help > About`

**If version < 0.40:**
- Update Cursor to the latest version
- Download from: https://cursor.sh

### 2. MCP Not Enabled in Cursor

**Try accessing MCP settings:**
1. Press `Cmd + Shift + J` (opens Cursor settings directly)
2. Or go to `Cursor > Settings` (⌘,)
3. Search for "MCP" or "Model Context Protocol"
4. Look for `Settings > Features > MCP Servers`

**If you don't see MCP settings:**
- Your Cursor version may not support MCP
- MCP might be a paid/premium feature
- Try updating Cursor

### 3. Config File Location Issue

**We've tried both locations:**
- ✅ `~/Library/Application Support/Cursor/User/globalStorage/mcp.json` (current)
- ✅ `~/.cursor/mcp.json` (alternative)

**Current config:**
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
        "PYTHONPATH": "/Users/joshuajenquist/repos/personal/home-server"
      }
    }
  }
}
```

### 4. Cursor MCP Extension Issue

**Check if MCP extension is installed:**
- Open Extensions view (⌘⇧X)
- Search for "MCP" or "Model Context Protocol"
- Check if it's installed and enabled

## Alternative: Use Claude Desktop

**Claude Desktop has native MCP support and is well-documented.**

### Setup for Claude Desktop

1. **Install Claude Desktop** (if not already installed)
   - Download from: https://claude.ai/download

2. **Configure MCP Server**

   Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`

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
           "PYTHONPATH": "/Users/joshuajenquist/repos/personal/home-server"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop**

4. **Verify Tools Are Available**
   - Ask Claude: "Check agent infrastructure status"
   - Or: "List all Docker containers"

### Why Claude Desktop?

- ✅ Native MCP support (designed by Anthropic)
- ✅ Well-documented and stable
- ✅ Free to use
- ✅ Works with the same MCP server

## Testing the MCP Server

**The server itself works perfectly. Test it:**

```bash
cd /Users/joshuajenquist/repos/personal/home-server/agents/apps/agent-mcp
python3 test_mcp_connection.py
```

**Expected output:**
```
✅ Initialization response received
✅ List tools response received: 102 tools
```

## Next Steps

### Option A: Fix Cursor MCP
1. Check Cursor version (must be 0.40+)
2. Update Cursor if needed
3. Try `Cmd + Shift + J` to access MCP settings
4. Check Cursor documentation/forums for MCP setup

### Option B: Use Claude Desktop (Recommended)
1. Install Claude Desktop
2. Configure `claude_desktop_config.json`
3. Restart Claude Desktop
4. Start using MCP tools immediately

### Option C: Use MCP Tools Directly
The tools can be called directly from Python scripts if needed, though this loses the AI integration benefits.

## Verification Commands

**Test server:**
```bash
cd /Users/joshuajenquist/repos/personal/home-server/agents/apps/agent-mcp
python3 test_mcp_connection.py
```

**Check config:**
```bash
cat ~/Library/Application\ Support/Cursor/User/globalStorage/mcp.json | python3 -m json.tool
cat ~/.cursor/mcp.json | python3 -m json.tool
```

**Check Cursor version:**
- `Cursor > About Cursor` in menu

