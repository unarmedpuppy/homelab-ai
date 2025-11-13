# Agent Tools Plan for Media Download Stack Management

## Overview

This document outlines a plan for creating reusable agent tools that abstract complex Sonarr/Radarr/NZBGet operations into simple, callable functions. These tools will enable other AI agents to troubleshoot and manage the media download stack without needing deep knowledge of API endpoints, authentication, or Docker container execution.

## ⚠️ Updated Recommendation

**See `apps/docs/MCP_SERVER_PLAN.md` for a broader approach**: Instead of standalone tools just for media download, consider implementing a comprehensive **MCP (Model Context Protocol) server** that provides tools for managing the entire home server (50+ applications). This provides:

- Single integration point for all server operations
- Type-safe tool definitions
- Automatic tool discovery
- Better composability across services
- Unified error handling

The tools defined in this document would become a subset of the broader MCP server's capabilities.

## Design Goals

1. **Simplicity**: Tools should have clear, descriptive names and minimal parameters
2. **Abstraction**: Hide complexity of API calls, authentication, and remote execution
3. **Reusability**: Tools should be composable and work together
4. **Error Handling**: Tools should provide clear error messages and diagnostics
5. **Context Preservation**: Tools should leverage existing context (API keys, paths, etc.)

## Tool Categories

### 1. Queue Management Tools

#### `clear_sonarr_queue`
**Purpose**: Remove all items from Sonarr's download queue
**Parameters**: 
- `blocklist` (optional, default: false) - Whether to add removed items to blocklist
- `remove_from_client` (optional, default: true) - Whether to remove from download client

**Returns**: 
- `removed_count`: Number of items removed
- `status`: Success/failure

**Example Usage**:
```python
result = clear_sonarr_queue(blocklist=False)
# Returns: {"removed_count": 147, "status": "success"}
```

#### `clear_radarr_queue`
**Purpose**: Remove all items from Radarr's download queue
**Parameters**: Same as `clear_sonarr_queue`

#### `get_sonarr_queue_status`
**Purpose**: Get summary of Sonarr queue
**Returns**:
- `total_items`: Total items in queue
- `by_status`: Count of items by status (e.g., {"downloading": 5, "completed": 10})
- `by_protocol`: Count by protocol (usenet vs torrent)
- `stuck_items`: Items with error/unavailable status

#### `get_radarr_queue_status`
**Purpose**: Get summary of Radarr queue
**Returns**: Same structure as Sonarr

#### `remove_stuck_downloads`
**Purpose**: Remove only items stuck with "downloadClientUnavailable" or error status
**Parameters**:
- `service`: "sonarr" or "radarr"
- `status_filter`: Optional list of statuses to filter (default: ["downloadClientUnavailable"])

### 2. Import & Scan Tools

#### `trigger_sonarr_import_scan`
**Purpose**: Manually trigger import scan for completed TV downloads
**Parameters**:
- `path` (optional): Specific path to scan (default: "/downloads/completed/tv")

**Returns**:
- `command_id`: ID of triggered command
- `status`: Command status

#### `trigger_radarr_import_scan`
**Purpose**: Manually trigger import scan for completed movie downloads
**Parameters**:
- `path` (optional): Specific path to scan (default: "/downloads/completed/movies")

#### `check_import_progress`
**Purpose**: Check status of import scan commands
**Parameters**:
- `service`: "sonarr" or "radarr"
- `command_id` (optional): Specific command ID, or latest if not provided

### 3. Download Client Management Tools

#### `check_download_clients`
**Purpose**: Verify download clients are configured and accessible
**Parameters**:
- `service`: "sonarr" or "radarr"

**Returns**:
- `clients`: List of configured clients with status
- `connection_status`: Test results for each client
- `issues`: List of any problems found

**Example Return**:
```json
{
  "clients": [
    {
      "name": "NZBGet",
      "protocol": "usenet",
      "enabled": true,
      "host": "media-download-gluetun:6789",
      "status": "connected"
    },
    {
      "name": "qBittorrent",
      "protocol": "torrent",
      "enabled": true,
      "host": "media-download-gluetun:8080",
      "status": "connected"
    }
  ],
  "issues": []
}
```

#### `configure_qbittorrent`
**Purpose**: Add or update qBittorrent configuration in Sonarr/Radarr
**Parameters**:
- `service`: "sonarr" or "radarr"
- `host` (optional): Override host (default: "media-download-gluetun")
- `port` (optional): Override port (default: 8080)
- `username` (optional): Override username (default: "admin")
- `password` (optional): Override password (default: "adminadmin")
- `category` (optional): Category for downloads (default: "tv" for Sonarr, "movies" for Radarr)

#### `set_qbittorrent_password`
**Purpose**: Set permanent password for qBittorrent WebUI
**Parameters**:
- `password`: New password to set
- `temp_password` (optional): Current temporary password if needed

**Returns**:
- `success`: Whether password was set
- `message`: Status message

### 4. Root Folder Management Tools

#### `list_root_folders`
**Purpose**: List all configured root folders
**Parameters**:
- `service`: "sonarr" or "radarr"

**Returns**:
- `folders`: List of root folders with paths, IDs, and accessibility status

#### `add_root_folder`
**Purpose**: Add a new root folder
**Parameters**:
- `service`: "sonarr" or "radarr"
- `path`: Path to add as root folder

**Returns**:
- `folder_id`: ID of newly created folder
- `accessible`: Whether folder is accessible
- `unmapped_folders`: List of existing folders that can now be mapped

#### `check_missing_root_folders`
**Purpose**: Identify movies/series using paths that aren't configured as root folders
**Parameters**:
- `service`: "sonarr" or "radarr"

**Returns**:
- `missing_paths`: List of paths in use but not configured
- `affected_items`: Count of items affected

### 5. Troubleshooting Tools

#### `troubleshoot_failed_downloads`
**Purpose**: Comprehensive diagnostic for failed downloads
**Parameters**:
- `service`: "sonarr" or "radarr"
- `include_logs` (optional, default: true): Include recent error logs

**Returns**:
- `queue_issues`: Problems found in queue
- `client_issues`: Download client connection problems
- `path_issues`: Root folder or path mapping problems
- `disk_space`: Disk space status
- `recommendations`: Suggested fixes
- `logs` (if include_logs): Recent error logs

**Example Return**:
```json
{
  "queue_issues": {
    "stuck_items": 10,
    "status": "downloadClientUnavailable"
  },
  "client_issues": [
    {
      "client": "qBittorrent",
      "problem": "Not configured",
      "fix": "Run configure_qbittorrent('sonarr')"
    }
  ],
  "path_issues": [
    {
      "path": "/movies/Kids/Films",
      "problem": "Not configured as root folder",
      "fix": "Run add_root_folder('radarr', '/movies/Kids/Films')"
    }
  ],
  "disk_space": {
    "usage_percent": 78,
    "status": "ok"
  },
  "recommendations": [
    "Configure qBittorrent download client",
    "Add /movies/Kids/Films as root folder"
  ]
}
```

#### `diagnose_download_client_unavailable`
**Purpose**: Specific diagnostic for "downloadClientUnavailable" errors
**Parameters**:
- `service`: "sonarr" or "radarr"

**Returns**:
- `root_cause`: Identified problem
- `affected_items`: Number of items affected
- `fix_steps`: Step-by-step fix instructions
- `can_auto_fix`: Whether tool can automatically fix

#### `check_service_health`
**Purpose**: Overall health check of a service
**Parameters**:
- `service`: "sonarr", "radarr", "nzbget", "qbittorrent", or "all"

**Returns**:
- `status`: "healthy", "degraded", or "unhealthy"
- `checks`: Results of individual health checks
- `issues`: List of problems found

### 6. Library Management Tools

#### `list_sonarr_series`
**Purpose**: List all series in Sonarr library
**Parameters**:
- `search` (optional): Filter by series name

**Returns**:
- `series`: List of series with paths and status

#### `list_radarr_movies`
**Purpose**: List all movies in Radarr library
**Parameters**:
- `search` (optional): Filter by movie name
- `root_folder` (optional): Filter by root folder path

**Returns**:
- `movies`: List of movies with paths and status

#### `check_unmapped_folders`
**Purpose**: Find folders in root directories that aren't mapped to series/movies
**Parameters**:
- `service`: "sonarr" or "radarr"
- `root_folder_id` (optional): Specific root folder to check

**Returns**:
- `unmapped_folders`: List of folders that could be imported

### 7. Log & Diagnostic Tools

#### `get_recent_errors`
**Purpose**: Get recent error logs from a service
**Parameters**:
- `service`: "sonarr", "radarr", "nzbget", or "qbittorrent"
- `lines` (optional, default: 50): Number of lines to retrieve
- `level` (optional): Filter by log level ("error", "warning", "info")

**Returns**:
- `logs`: List of log entries
- `error_count`: Count of errors found

#### `check_disk_space`
**Purpose**: Check disk space usage
**Parameters**:
- `path` (optional): Specific path to check (default: root)

**Returns**:
- `usage_percent`: Disk usage percentage
- `free_gb`: Free space in GB
- `status`: "ok", "warning", or "critical"
- `recommendations`: Suggestions if space is low

#### `cleanup_archive_files`
**Purpose**: Remove unpacked archive files (.rar, .par2, .nzb) from completed downloads
**Parameters**:
- `dry_run` (optional, default: false): Show what would be deleted without deleting
- `category` (optional): Specific category to clean ("tv", "movies", "all")

**Returns**:
- `files_removed`: Number of files removed
- `space_freed_gb`: Space freed in GB
- `files_removed_list`: List of removed files (if dry_run was false)

## Implementation Approaches

### Option 1: Python CLI Tool Suite (Recommended)

**Structure**:
```
apps/media-download/tools/
├── __init__.py
├── config.py              # Loads credentials from context or env
├── sonarr_client.py       # Sonarr API wrapper
├── radarr_client.py       # Radarr API wrapper
├── nzbget_client.py       # NZBGet API wrapper
├── qbittorrent_client.py  # qBittorrent API wrapper
├── queue.py               # Queue management tools
├── imports.py             # Import/scan tools
├── clients.py             # Download client management
├── folders.py             # Root folder management
├── troubleshoot.py        # Troubleshooting tools
└── cli.py                 # CLI entry point
```

**Example Tool Implementation**:
```python
# tools/queue.py
from .sonarr_client import SonarrClient
from .config import get_config

def clear_sonarr_queue(blocklist=False, remove_from_client=True):
    """Clear all items from Sonarr queue."""
    config = get_config()
    client = SonarrClient(config['sonarr_api_key'])
    
    # Get all queue items
    queue = client.get_queue()
    if not queue['records']:
        return {"removed_count": 0, "status": "success", "message": "Queue already empty"}
    
    # Remove each item
    removed = 0
    for item in queue['records']:
        try:
            client.remove_queue_item(
                item['id'],
                remove_from_client=remove_from_client,
                blocklist=blocklist
            )
            removed += 1
        except Exception as e:
            # Log error but continue
            pass
    
    return {
        "removed_count": removed,
        "status": "success",
        "message": f"Removed {removed} items from queue"
    }
```

**CLI Usage**:
```bash
# Direct execution
python -m tools.cli clear_sonarr_queue --blocklist=false

# Via connect-server script
bash scripts/connect-server.sh "cd ~/server/apps/media-download && python3 -m tools.cli clear_sonarr_queue"
```

### Option 2: Shell Script Wrappers

**Structure**:
```
apps/media-download/tools/
├── clear-sonarr-queue.sh
├── clear-radarr-queue.sh
├── troubleshoot-failed-downloads.sh
├── check-download-clients.sh
├── trigger-import-scan.sh
└── lib/
    ├── common.sh          # Common functions (API calls, auth)
    └── config.sh          # Load configuration
```

**Example Script**:
```bash
#!/bin/bash
# tools/clear-sonarr-queue.sh

source "$(dirname "$0")/lib/common.sh"
source "$(dirname "$0")/lib/config.sh"

SONARR_API_KEY=$(get_sonarr_api_key)
SONARR_URL="http://127.0.0.1:8989"

# Get queue items
QUEUE_ITEMS=$(docker exec media-download-sonarr curl -s \
  "http://127.0.0.1:8989/api/v3/queue?apikey=${SONARR_API_KEY}" \
  | python3 -c "import sys, json; data=json.load(sys.stdin); print(' '.join([str(r['id']) for r in data['records']]))")

# Remove items
REMOVED=0
for id in $QUEUE_ITEMS; do
  docker exec media-download-sonarr curl -s -X DELETE \
    "http://127.0.0.1:8989/api/v3/queue/${id}?apikey=${SONARR_API_KEY}&removeFromClient=true&blocklist=false" > /dev/null
  REMOVED=$((REMOVED + 1))
done

echo "{\"removed_count\": ${REMOVED}, \"status\": \"success\"}"
```

### Option 3: MCP (Model Context Protocol) Server

**Structure**:
```
apps/media-download/mcp-server/
├── server.py              # MCP server implementation
├── tools/
│   ├── queue_tools.py
│   ├── import_tools.py
│   ├── client_tools.py
│   └── troubleshoot_tools.py
└── config.py
```

**Example MCP Tool Definition**:
```python
# mcp-server/tools/queue_tools.py
from mcp.server import Server
from mcp.types import Tool

def register_queue_tools(server: Server):
    @server.tool()
    async def clear_sonarr_queue(
        blocklist: bool = False,
        remove_from_client: bool = True
    ) -> dict:
        """
        Clear all items from Sonarr's download queue.
        
        Args:
            blocklist: Whether to add removed items to blocklist
            remove_from_client: Whether to remove from download client
            
        Returns:
            Dictionary with removed_count and status
        """
        # Implementation here
        pass
```

### Option 4: Hybrid Approach (Recommended)

Combine Python tools with simple shell wrappers:

1. **Python library** for complex operations (API calls, data processing)
2. **Shell scripts** for simple, one-off commands
3. **CLI interface** that can be called from anywhere
4. **MCP server** (optional) for AI agent integration

## Configuration Management

### Centralized Config

**File**: `apps/media-download/tools/config.py` or `tools/config.json`

```python
# tools/config.py
import os
from pathlib import Path

def get_config():
    """Load configuration from environment or config file."""
    config_file = Path(__file__).parent.parent / "tools" / "config.json"
    
    # Default values from PIRATE_AGENT_CONTEXT.md
    defaults = {
        "sonarr": {
            "api_key": "dd7148e5a3dd4f7aa0c579194f45edff",
            "base_url": "http://127.0.0.1:8989",
            "container": "media-download-sonarr"
        },
        "radarr": {
            "api_key": "afb58cf1eaee44208099b403b666e29c",
            "base_url": "http://127.0.0.1:7878",
            "container": "media-download-radarr"
        },
        "nzbget": {
            "username": "nzbget",
            "password": "nzbget",
            "host": "media-download-gluetun",
            "port": 6789
        },
        "qbittorrent": {
            "username": "admin",
            "password": "adminadmin",
            "host": "media-download-gluetun",
            "port": 8080
        },
        "server": {
            "host": "192.168.86.47",
            "port": 4242,
            "user": "unarmedpuppy",
            "connect_script": "scripts/connect-server.sh"
        }
    }
    
    # Override with environment variables
    for service in ["sonarr", "radarr"]:
        key = f"{service.upper()}_API_KEY"
        if key in os.environ:
            defaults[service]["api_key"] = os.environ[key]
    
    return defaults
```

## Tool Execution Context

### Remote Execution

All tools must execute commands on the remote server. Two approaches:

**Option A: Tools run locally, execute remotely**
```python
def execute_remote(command):
    """Execute command on remote server."""
    connect_script = get_config()["server"]["connect_script"]
    result = subprocess.run(
        [connect_script, command],
        capture_output=True,
        text=True
    )
    return result.stdout, result.stderr, result.returncode
```

**Option B: Tools are deployed to server, run there**
- Tools are installed on the server
- Agents call tools via SSH or API
- More efficient but requires deployment

## Error Handling & Validation

### Standard Error Response Format

```python
{
    "status": "error",
    "error_type": "ConnectionError" | "ValidationError" | "NotFoundError",
    "message": "Human-readable error message",
    "details": {
        "service": "sonarr",
        "operation": "clear_queue",
        "suggestion": "Check if Sonarr container is running"
    }
}
```

### Validation

- **Parameter validation**: Check required parameters, types, ranges
- **Service availability**: Verify containers are running before operations
- **Authentication**: Verify API keys work before making requests
- **Path validation**: Check paths exist and are accessible

## Tool Documentation

Each tool should have:
1. **Docstring**: Clear description, parameters, returns
2. **Examples**: Usage examples in docstring
3. **Error cases**: Document what errors can occur
4. **Dependencies**: What other tools/services it depends on

## Testing Strategy

### Unit Tests
- Mock API responses
- Test error handling
- Test parameter validation

### Integration Tests
- Test against actual services (in test environment)
- Verify end-to-end workflows
- Test error recovery

### Example Test
```python
def test_clear_sonarr_queue_empty():
    """Test clearing empty queue."""
    result = clear_sonarr_queue()
    assert result["removed_count"] == 0
    assert result["status"] == "success"

def test_clear_sonarr_queue_with_items(mock_sonarr_api):
    """Test clearing queue with items."""
    mock_sonarr_api.queue.return_value = {
        "records": [{"id": 1}, {"id": 2}]
    }
    result = clear_sonarr_queue()
    assert result["removed_count"] == 2
```

## Agent Integration Examples

### Example 1: Simple Troubleshooting Agent

```python
# Agent receives: "Sonarr queue is stuck"
def handle_stuck_queue():
    # Check queue status
    status = get_sonarr_queue_status()
    
    if status["stuck_items"] > 0:
        # Diagnose the problem
        diagnosis = diagnose_download_client_unavailable("sonarr")
        
        # Auto-fix if possible
        if diagnosis["can_auto_fix"]:
            # Apply fixes
            if "qBittorrent not configured" in diagnosis["root_cause"]:
                configure_qbittorrent("sonarr")
            
            # Clear stuck items
            remove_stuck_downloads("sonarr")
        else:
            # Return recommendations
            return diagnosis["fix_steps"]
```

### Example 2: Proactive Health Check Agent

```python
# Agent runs periodic health checks
def periodic_health_check():
    health = check_service_health("all")
    
    if health["status"] != "healthy":
        # Run comprehensive troubleshooting
        for service in ["sonarr", "radarr"]:
            issues = troubleshoot_failed_downloads(service)
            
            # Auto-fix common issues
            for issue in issues["recommendations"]:
                if "configure qBittorrent" in issue.lower():
                    configure_qbittorrent(service)
                elif "add root folder" in issue.lower():
                    # Extract path from recommendation
                    path = extract_path_from_recommendation(issue)
                    add_root_folder(service, path)
```

## Implementation Priority

### Phase 1: Core Tools (Week 1)
1. Queue management tools
2. Basic troubleshooting (`troubleshoot_failed_downloads`)
3. Download client checking

### Phase 2: Management Tools (Week 2)
1. Root folder management
2. Import scan tools
3. Library listing tools

### Phase 3: Advanced Tools (Week 3)
1. Comprehensive diagnostics
2. Auto-fix capabilities
3. Health monitoring

### Phase 4: Integration (Week 4)
1. MCP server (if desired)
2. Agent prompt updates
3. Documentation

## Next Steps

1. **Choose implementation approach** (Python CLI recommended)
2. **Set up project structure** in `apps/media-download/tools/`
3. **Implement core client wrappers** (Sonarr, Radarr, etc.)
4. **Build first tool** (`clear_sonarr_queue`) as proof of concept
5. **Create tool documentation** template
6. **Set up testing framework**
7. **Iterate and expand** tool set

## Questions to Resolve

1. **Execution model**: Should tools run locally (via SSH) or be deployed to server?
2. **Authentication**: Store credentials in config file, environment variables, or both?
3. **Logging**: Where should tool execution logs be stored?
4. **Permissions**: Should tools have different permission levels?
5. **MCP integration**: Is MCP server desired, or just CLI tools?
6. **Error reporting**: How should tools report errors to calling agents?

---

**Created**: 2025-11-13
**Status**: Planning Phase
**Next Action**: Choose implementation approach and begin Phase 1

