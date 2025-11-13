# MCP Server Quick Start

## What We've Built

A working MCP (Model Context Protocol) server with Docker management tools that can be used by AI agents to manage your home server.

## Current Status

✅ **Implemented:**
- Core MCP server infrastructure
- Configuration management
- Remote execution client (SSH)
- 8 Docker management tools:
  - `docker_list_containers` - List all containers
  - `docker_container_status` - Get detailed container status
  - `docker_restart_container` - Restart a container
  - `docker_stop_container` - Stop a container
  - `docker_start_container` - Start a container
  - `docker_view_logs` - View container logs
  - `docker_compose_ps` - List docker-compose services
  - `docker_compose_restart` - Restart docker-compose services

## Installation

```bash
cd server-management-mcp
pip install -r requirements.txt
```

## Test the Setup

```bash
python test_setup.py
```

This will verify:
- Configuration loading
- Remote SSH execution
- Docker access

## Running the Server

### For Testing (stdio transport)

```bash
python server.py
```

The server will communicate via stdin/stdout (for MCP clients).

### With Claude Desktop

1. Find your Claude Desktop config file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add the MCP server:

```json
{
  "mcpServers": {
    "home-server": {
      "command": "python",
      "args": ["/absolute/path/to/home-server/server-management-mcp/server.py"],
      "env": {
        "SONARR_API_KEY": "dd7148e5a3dd4f7aa0c579194f45edff",
        "RADARR_API_KEY": "afb58cf1eaee44208099b403b666e29c"
      }
    }
  }
}
```

3. Restart Claude Desktop

4. The tools will be available in Claude Desktop conversations!

## Example Usage (Once Connected)

You can now ask Claude:

- "List all Docker containers"
- "What's the status of media-download-sonarr?"
- "Restart the trading-bot container"
- "Show me logs from media-download-radarr"

## Next Steps

1. **Add Media Download Tools** - Sonarr/Radarr queue management
2. **Add Monitoring Tools** - Disk space, system resources
3. **Add Application-Specific Tools** - Trading bot, Jellyfin, etc.
4. **Add Troubleshooting Tools** - Automated diagnostics

## Project Structure

```
server-management-mcp/
├── server.py              # Main MCP server entry point
├── config/
│   └── settings.py        # Configuration management
├── clients/
│   └── remote_exec.py     # Remote SSH execution
├── tools/
│   └── docker.py          # Docker management tools
├── test_setup.py          # Setup verification
└── README.md              # Full documentation
```

## Troubleshooting

### "Command not found" errors
- Make sure `scripts/connect-server.sh` exists and is executable
- Verify SSH access to server works: `bash scripts/connect-server.sh "echo test"`

### "Module not found" errors
- Install dependencies: `pip install -r requirements.txt`
- Make sure you're running from the `server-management-mcp` directory

### MCP connection issues
- Verify the Python path in Claude Desktop config is absolute
- Check that Python has the `mcp` package installed
- Look for error messages in Claude Desktop logs

## Development

To add new tools:

1. Create a new file in `tools/` (e.g., `tools/media_download.py`)
2. Import and register in `server.py`:
   ```python
   from tools.media_download import register_media_tools
   register_media_tools(server)
   ```
3. Follow the pattern in `tools/docker.py` for tool definitions

