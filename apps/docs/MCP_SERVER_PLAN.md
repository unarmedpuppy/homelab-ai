# MCP Server Plan for Home Server Management

## Overview

Create a comprehensive Model Context Protocol (MCP) server that provides AI agents with tools to manage the entire home server infrastructure, not just individual services. This enables agents to perform complex multi-service operations, troubleshooting, and automation across all 50+ applications.

## Why MCP Server?

1. **Unified Interface**: Single entry point for all server operations
2. **Type Safety**: Structured tool definitions with clear parameters
3. **Agent Integration**: Works seamlessly with Claude, GPT-4, and other MCP-compatible agents
4. **Extensibility**: Easy to add new tools as services are added
5. **Composability**: Tools can call other tools to build complex workflows
6. **Discovery**: Agents can discover available capabilities automatically

## Architecture

### Server Structure

```
agents/apps/agent-mcp/
├── server.py                 # Main MCP server
├── config/
│   ├── __init__.py
│   ├── settings.py          # Load from env/config files
│   └── credentials.py       # Secure credential management
├── tools/
│   ├── __init__.py
│   ├── docker.py            # Docker container management
│   ├── media_download.py     # Sonarr/Radarr/NZBGet tools
│   ├── trading_bot.py        # Trading bot operations
│   ├── monitoring.py         # Grafana, health checks
│   ├── networking.py        # Traefik, DNS, VPN
│   ├── storage.py            # Disk space, backups
│   ├── services.py           # Service status, logs
│   └── system.py            # System-level operations
├── clients/
│   ├── __init__.py
│   ├── sonarr.py            # Sonarr API client
│   ├── radarr.py            # Radarr API client
│   ├── docker_api.py        # Docker API client
│   └── remote_exec.py       # Remote command execution
└── README.md
```

## Tool Categories

### 1. Docker & Container Management

#### `docker_list_containers`
List all Docker containers with status
- Parameters: `filter` (optional) - Filter by status/app
- Returns: List of containers with name, status, ports, health

#### `docker_container_status`
Get detailed status of a container
- Parameters: `container_name` - Name of container
- Returns: Status, logs, resource usage

#### `docker_restart_container`
Restart a Docker container
- Parameters: `container_name`, `wait` (optional) - Wait for healthy status
- Returns: Success status, new container status

#### `docker_stop_container`
Stop a Docker container
- Parameters: `container_name`
- Returns: Success status

#### `docker_start_container`
Start a Docker container
- Parameters: `container_name`
- Returns: Success status

#### `docker_view_logs`
View container logs
- Parameters: `container_name`, `lines` (default: 50), `follow` (default: false)
- Returns: Log lines

#### `docker_compose_ps`
List containers from docker-compose
- Parameters: `app_path` - Path to app directory (e.g., "apps/media-download")
- Returns: List of services and their status

#### `docker_compose_restart`
Restart services via docker-compose
- Parameters: `app_path`, `service` (optional) - Specific service or all
- Returns: Restart results

#### `docker_list_images`
List Docker images with sizes and tags
- Parameters: `filter` (optional) - Filter by name or tag
- Returns: List of images with name, tag, size, created date

#### `docker_prune_images`
Remove unused Docker images
- Parameters: `dry_run` (default: false), `filter` (optional) - Filter by age or label
- Returns: Space freed, images removed count

#### `docker_update_image`
Pull latest version of an image
- Parameters: `image_name`, `tag` (optional, default: "latest")
- Returns: New image ID, update status

#### `docker_list_volumes`
List Docker volumes with usage information
- Parameters: `filter` (optional) - Filter by name or label
- Returns: List of volumes with name, driver, mount point, size

#### `docker_prune_volumes`
Remove unused Docker volumes
- Parameters: `dry_run` (default: false), `filter` (optional)
- Returns: Space freed, volumes removed count

#### `docker_container_stats`
Get real-time container resource usage
- Parameters: `container_name`, `duration` (optional, default: 5 seconds)
- Returns: CPU, memory, network, disk I/O stats

#### `docker_compose_up`
Start services via docker-compose (with build option)
- Parameters: `app_path`, `service` (optional), `build` (default: false)
- Returns: Start results, container IDs

#### `docker_compose_down`
Stop and remove services via docker-compose
- Parameters: `app_path`, `volumes` (default: false), `remove_orphans` (default: false)
- Returns: Stop results

#### `restart_affected_services`
Restart services based on git changes or explicit app path
- Parameters: `app_path` (optional) - Auto-detect from git changes if not provided, `service` (optional) - Specific service or all, `check_changes` (default: true) - Analyze git changes to determine affected services
- Returns: Services restarted, restart results, detected changes summary
- **Use Case**: Restart only services affected by recent changes
- **Auto-detection**: Analyzes git diff to find modified docker-compose.yml files and restart those services

### 2. Git Operations & Repository Management

#### `git_status`
Check git repository status
- Parameters: `path` (optional) - Repository path, default: ~/server
- Returns: Branch, uncommitted changes, untracked files, ahead/behind status

#### `git_pull`
Pull latest changes from remote
- Parameters: `path` (optional), `branch` (optional, default: main)
- Returns: Pull results, updated files, conflicts if any

#### `git_checkout`
Checkout a branch or commit
- Parameters: `path` (optional), `branch_or_commit` - Branch name or commit hash
- Returns: Checkout status, current branch

#### `git_log`
Get git commit history
- Parameters: `path` (optional), `limit` (default: 10), `since` (optional) - Date filter
- Returns: List of commits with hash, author, date, message

#### `git_diff`
Show differences between commits or branches
- Parameters: `path` (optional), `base` (optional), `compare` (optional)
- Returns: Diff output, changed files

#### `git_sync`
Full sync workflow: pull, check status, report conflicts
- Parameters: `path` (optional), `branch` (optional)
- Returns: Sync status, conflicts, updated files count

#### `git_deploy`
Complete deployment workflow: add → commit → push → pull on server
- Parameters: `commit_message`, `files` (optional) - Specific files or "all", `path` (optional), `branch` (optional, default: main), `skip_pull` (default: false)
- Returns: Status of each step, commit hash, push status, pull status, conflicts if any, updated files on server
- **Use Case**: Standard deployment workflow that agents use constantly

#### `deploy_and_restart`
Complete deployment and restart workflow: deploy changes → restart affected services
- Parameters: `commit_message`, `app_path` (optional) - Auto-detect from changes if not provided, `service` (optional) - Specific service or all, `files` (optional), `branch` (optional)
- Returns: Deployment status, services restarted, restart results, any errors
- **Use Case**: Most common agent workflow - deploy code and restart services
- **Auto-detection**: Can analyze git changes to determine which services need restarting

### 3. File Operations & Configuration Management

#### `read_file`
Read file contents from server
- Parameters: `file_path` - Full path to file
- Returns: File contents, encoding, size

#### `write_file`
Write content to file on server
- Parameters: `file_path`, `content`, `backup` (default: true)
- Returns: Write status, backup location if created

#### `search_files`
Search for files by name or content
- Parameters: `pattern` - Filename pattern or content search, `path` (optional), `type` (optional) - "name" or "content"
- Returns: List of matching files with paths

#### `read_env_file`
Read and parse .env file
- Parameters: `file_path` - Path to .env file
- Returns: Parsed environment variables as dictionary

#### `validate_env_file`
Validate .env file against template
- Parameters: `env_path`, `template_path` (optional)
- Returns: Validation results, missing variables, invalid values

#### `update_env_variable`
Update a single environment variable in .env file
- Parameters: `file_path`, `key`, `value`, `backup` (default: true)
- Returns: Update status, backup location

#### `read_docker_compose`
Read and parse docker-compose.yml
- Parameters: `file_path` - Path to docker-compose.yml
- Returns: Parsed services, networks, volumes configuration

#### `validate_docker_compose`
Validate docker-compose.yml syntax and configuration
- Parameters: `file_path`
- Returns: Validation results, errors, warnings

### 4. Media Download Stack

#### `sonarr_clear_queue`
Clear Sonarr download queue
- Parameters: `blocklist` (default: false), `remove_from_client` (default: true)
- Returns: Removed count, status

#### `sonarr_queue_status`
Get Sonarr queue status
- Returns: Total items, by status, by protocol, stuck items

#### `sonarr_trigger_import_scan`
Trigger manual import scan
- Parameters: `path` (optional) - Specific path to scan
- Returns: Command ID, status

#### `sonarr_check_download_clients`
Check Sonarr download client configuration
- Returns: Clients list, connection status, issues

#### `radarr_clear_queue`
Clear Radarr download queue (same params as Sonarr)

#### `radarr_queue_status`
Get Radarr queue status

#### `radarr_add_root_folder`
Add root folder to Radarr
- Parameters: `path` - Path to add
- Returns: Folder ID, accessibility status

#### `radarr_list_root_folders`
List all Radarr root folders
- Returns: Folders with paths and IDs

#### `nzbget_status`
Get NZBGet download status
- Returns: Queue status, download speed, server status

#### `qbittorrent_status`
Get qBittorrent status
- Returns: Active torrents, download/upload speeds

### 5. Database Operations

#### `database_backup`
Create backup of a database
- Parameters: `database_type` - "postgresql", "mysql", "sqlite", `database_name`, `output_path` (optional)
- Returns: Backup file path, size, backup status

#### `database_restore`
Restore database from backup
- Parameters: `database_type`, `database_name`, `backup_path`, `drop_existing` (default: false)
- Returns: Restore status, verification results

#### `database_query`
Execute a read-only query on database
- Parameters: `database_type`, `database_name`, `query`, `limit` (default: 100)
- Returns: Query results, row count

#### `database_health_check`
Check database connectivity and health
- Parameters: `database_type`, `database_name` (optional) - Check all if not specified
- Returns: Connection status, version, size, active connections

#### `database_list_tables`
List all tables in a database
- Parameters: `database_type`, `database_name`
- Returns: List of tables with row counts

#### `database_table_info`
Get detailed information about a table
- Parameters: `database_type`, `database_name`, `table_name`
- Returns: Columns, indexes, constraints, row count

### 6. Log Management & Aggregation

#### `search_logs`
Search across multiple service logs
- Parameters: `pattern` - Search pattern, `services` (optional) - List of service names, `since` (optional) - Time filter, `limit` (default: 100)
- Returns: Matching log entries with service, timestamp, message

#### `aggregate_errors`
Aggregate error logs across services
- Parameters: `since` (optional) - Time filter, `group_by` (optional) - "service", "error_type", "time"
- Returns: Error summary, grouped errors, trends

#### `tail_logs`
Tail multiple service logs simultaneously
- Parameters: `services` - List of service names, `lines` (default: 50), `follow` (default: false)
- Returns: Recent log entries per service

#### `export_logs`
Export logs to file
- Parameters: `services`, `output_path`, `since` (optional), `format` (optional) - "json", "text", "csv"
- Returns: Export status, file path, size

### 7. Trading Bot Operations

#### `trading_bot_status`
Get trading bot status
- Returns: Running status, active strategies, positions

#### `trading_bot_restart`
Restart trading bot service
- Returns: Restart status

#### `trading_bot_view_logs`
View trading bot logs
- Parameters: `lines` (default: 50), `level` (optional) - Filter by log level
- Returns: Log entries

#### `trading_bot_check_health`
Comprehensive health check
- Returns: API status, database connectivity, broker connection

### 8. System & Monitoring

#### `check_disk_space`
Check disk space usage
- Parameters: `path` (optional) - Specific path, default: root
- Returns: Usage percent, free space, status

#### `check_system_resources`
Check CPU, memory, network usage
- Returns: Resource metrics

#### `service_health_check`
Comprehensive health check for a service
- Parameters: `service_name` - Name of service
- Returns: Health status, checks performed, issues found

#### `get_recent_errors`
Get recent errors from logs
- Parameters: `service` (optional), `lines` (default: 50)
- Returns: Error log entries

### 9. Networking & Infrastructure

#### `test_connectivity`
Test network connectivity to a host/port
- Parameters: `host`, `port` (optional), `timeout` (default: 5)
- Returns: Connection status, latency, error if failed

#### `resolve_dns`
Resolve DNS name to IP address
- Parameters: `hostname`, `record_type` (optional, default: "A")
- Returns: Resolved addresses, TTL

#### `check_network_route`
Check network routing to a destination
- Parameters: `destination`, `max_hops` (default: 30)
- Returns: Route path, latency per hop, issues

#### `list_listening_ports`
List all listening ports and their services
- Parameters: `filter_port` (optional), `filter_protocol` (optional) - "tcp", "udp"
- Returns: List of ports with service, process, container

#### `check_port_conflict`
Check if a port is already in use
- Parameters: `port`, `protocol` (optional, default: "tcp")
- Returns: Port status, conflicting service if any

#### `traefik_status`
Check Traefik reverse proxy status
- Returns: Active routes, SSL certificates, backend health

#### `check_dns_status`
Check DNS service status (AdGuard)
- Returns: DNS status, query stats

#### `vpn_status`
Check VPN services status (Gluetun, Tailscale)
- Returns: Connection status, active connections

#### `check_port_status`
Check if a port is listening
- Parameters: `port`, `host` (optional, default: localhost)
- Returns: Port status, process using port

### 10. Storage & Backups

#### `list_backup_files`
List all backup files with metadata
- Parameters: `service` (optional), `backup_type` (optional) - "full", "incremental"
- Returns: List of backups with date, size, location, status

#### `verify_backup`
Verify backup file integrity
- Parameters: `backup_path`, `backup_type`
- Returns: Verification status, checksum, file integrity

#### `backup_env_files`
Backup all .env files from applications
- Parameters: `output_path` (optional), `include_template` (default: false)
- Returns: Backup location, files backed up count

#### `restore_env_file`
Restore .env file from backup
- Parameters: `app_path`, `backup_path`, `backup` (default: true)
- Returns: Restore status, backup location if created

#### `list_backups`
List available backups
- Parameters: `service` (optional) - Filter by service
- Returns: Backup list with dates, sizes

#### `create_backup`
Create backup of a service
- Parameters: `service_name`, `type` (optional) - Full or incremental
- Returns: Backup ID, location

#### `restore_backup`
Restore from backup
- Parameters: `backup_id`, `service_name`
- Returns: Restore status

#### `cleanup_old_backups`
Remove old backups
- Parameters: `service` (optional), `keep_days` (default: 30)
- Returns: Cleanup results

### 11. Application-Specific Tools

#### `jellyfin_library_scan`
Trigger Jellyfin library scan
- Parameters: `library_id` (optional) - Specific library or all
- Returns: Scan status, task ID

#### `jellyfin_users_list`
List all Jellyfin users
- Returns: List of users with permissions, last activity

#### `immich_upload_status`
Check Immich upload queue status
- Returns: Pending uploads, failed uploads, sync status

#### `immich_trigger_sync`
Trigger Immich library sync
- Returns: Sync status, task ID

#### `homeassistant_config_check`
Validate Home Assistant configuration
- Returns: Validation results, errors, warnings

#### `homeassistant_reload_config`
Reload Home Assistant configuration
- Parameters: `domain` (optional) - Specific domain or all
- Returns: Reload status, errors if any

#### `paperless_document_count`
Get Paperless document statistics
- Returns: Total documents, by status, by tag, OCR queue

#### `n8n_workflow_list`
List all n8n workflows
- Returns: List of workflows with status, last run, trigger info

#### `n8n_workflow_execute`
Manually execute an n8n workflow
- Parameters: `workflow_id` or `workflow_name`
- Returns: Execution status, run ID

#### `vaultwarden_status`
Check Vaultwarden status and statistics
- Returns: User count, item count, sync status, health

#### `grafana_dashboard_list`
List Grafana dashboards
- Returns: List of dashboards with ID, name, tags

#### `grafana_datasource_status`
Check Grafana datasource connectivity
- Returns: Datasource status, last query time, errors

#### `jellyfin_library_status`
Check Jellyfin library status
- Returns: Library stats, scan status

#### `immich_sync_status`
Check Immich sync status
- Returns: Sync progress, pending items

#### `homeassistant_restart`
Restart Home Assistant
- Returns: Restart status

#### `paperless_ocr_status`
Check Paperless OCR processing
- Returns: Queue status, processing stats

### 12. Troubleshooting & Diagnostics

#### `detect_port_conflicts`
Scan for port conflicts across all services
- Returns: Conflicting ports, services using them, recommendations

#### `check_service_health_all`
Check health of all services
- Parameters: `filter_status` (optional) - Only check "unhealthy" or "unknown"
- Returns: Health status per service, summary statistics

#### `diagnose_startup_failure`
Diagnose why a service failed to start
- Parameters: `service_name`
- Returns: Root cause, logs, dependencies, suggested fixes

#### `check_resource_limits`
Check if services are hitting resource limits
- Parameters: `service` (optional) - Specific service or all
- Returns: Services near limits, current usage, recommendations

#### `find_orphaned_volumes`
Find Docker volumes not attached to any container
- Returns: List of orphaned volumes with size, last used

#### `check_disk_usage_by_service`
Break down disk usage by service/application
- Parameters: `path` (optional) - Specific path or root
- Returns: Disk usage per service, largest directories

#### `validate_service_config`
Validate service configuration files
- Parameters: `service_name` or `config_path`
- Returns: Validation results, errors, warnings, missing values

#### `troubleshoot_service`
Comprehensive troubleshooting for a service
- Parameters: `service_name`
- Returns: Issues found, recommendations, auto-fixable items

#### `diagnose_connection_issue`
Diagnose network/connection problems
- Parameters: `service_name`, `target` (optional)
- Returns: Diagnostic results, suggested fixes

#### `check_service_dependencies`
Check if service dependencies are running
- Parameters: `service_name`
- Returns: Dependency status, missing services

#### `find_service_by_port`
Find which service is using a port
- Parameters: `port`
- Returns: Service name, container, process

## Implementation

### MCP Server Setup

```python
# server.py
from mcp.server import Server
from mcp.types import Tool, TextContent
import asyncio

from tools.docker import register_docker_tools
from tools.media_download import register_media_tools
from tools.monitoring import register_monitoring_tools
# ... other tool modules

server = Server("home-server-management")

# Register all tool categories
register_docker_tools(server)
register_media_tools(server)
register_monitoring_tools(server)
# ... register others

async def main():
    async with server:
        await server.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Example Tool Implementation

```python
# tools/media_download.py
from mcp.server import Server
from mcp.types import Tool
from clients.sonarr import SonarrClient
from clients.remote_exec import RemoteExecutor

def register_media_tools(server: Server):
    
    @server.tool()
    async def sonarr_clear_queue(
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
        try:
            client = SonarrClient()
            queue = await client.get_queue()
            
            if not queue.get("records"):
                return {
                    "status": "success",
                    "removed_count": 0,
                    "message": "Queue is already empty"
                }
            
            removed = 0
            for item in queue["records"]:
                await client.remove_queue_item(
                    item["id"],
                    remove_from_client=remove_from_client,
                    blocklist=blocklist
                )
                removed += 1
            
            return {
                "status": "success",
                "removed_count": removed,
                "total_items": len(queue["records"])
            }
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    async def sonarr_queue_status() -> dict:
        """
        Get summary of Sonarr queue status.
        
        Returns:
            Dictionary with total_items, by_status, by_protocol, stuck_items
        """
        client = SonarrClient()
        queue = await client.get_queue()
        
        # Process queue data...
        return {
            "total_items": len(queue.get("records", [])),
            "by_status": {...},
            "by_protocol": {...},
            "stuck_items": [...]
        }
```

### Remote Execution Client

```python
# clients/remote_exec.py
import subprocess
import json
from typing import Tuple

class RemoteExecutor:
    """Execute commands on remote server via SSH."""
    
    def __init__(self):
        self.connect_script = "scripts/connect-server.sh"
    
    async def execute(self, command: str) -> Tuple[str, str, int]:
        """
        Execute command on remote server.
        
        Returns:
            (stdout, stderr, returncode)
        """
        process = await asyncio.create_subprocess_exec(
            self.connect_script,
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        return stdout.decode(), stderr.decode(), process.returncode
    
    async def docker_exec(self, container: str, command: str) -> str:
        """Execute command inside Docker container."""
        full_command = f"docker exec {container} {command}"
        stdout, stderr, returncode = await self.execute(full_command)
        
        if returncode != 0:
            raise Exception(f"Command failed: {stderr}")
        
        return stdout
```

## Configuration Management

### Settings File

```python
# config/settings.py
from pathlib import Path
import os
import json

class Settings:
    """Load settings from environment and config files."""
    
    def __init__(self):
        self.config_file = Path(__file__).parent.parent / "config.json"
        self.load_config()
    
    def load_config(self):
        """Load configuration from file or environment."""
        # Defaults from context documents
        self.defaults = {
            "server": {
                "host": "192.168.86.47",
                "port": 4242,
                "user": "unarmedpuppy",
                "connect_script": "scripts/connect-server.sh"
            },
            "sonarr": {
                "api_key": os.getenv("SONARR_API_KEY", "dd7148e5a3dd4f7aa0c579194f45edff"),
                "base_url": "http://127.0.0.1:8989",
                "container": "media-download-sonarr"
            },
            # ... other services
        }
        
        # Override with config file if exists
        if self.config_file.exists():
            with open(self.config_file) as f:
                file_config = json.load(f)
                self.defaults.update(file_config)
    
    def get(self, service: str, key: str, default=None):
        """Get configuration value."""
        return self.defaults.get(service, {}).get(key, default)

settings = Settings()
```

## Tool Discovery & Documentation

### Auto-Generated Tool List

The MCP server automatically exposes:
- Tool names and descriptions
- Parameter schemas
- Return type schemas
- Examples (via docstrings)

Agents can discover capabilities dynamically:

```python
# Agent can query available tools
tools = await server.list_tools()
# Returns all registered tools with schemas
```

## Usage Examples

### Example 1: Troubleshoot Stuck Sonarr Queue

```python
# Agent workflow
async def troubleshoot_sonarr():
    # 1. Check queue status
    status = await sonarr_queue_status()
    
    if status["stuck_items"] > 0:
        # 2. Check download clients
        clients = await sonarr_check_download_clients()
        
        # 3. Fix issues
        if "qBittorrent not configured" in clients["issues"]:
            await configure_qbittorrent("sonarr")
        
        # 4. Clear stuck items
        await sonarr_clear_queue()
```

### Example 2: System Health Check

```python
# Agent workflow
async def system_health_check():
    # 1. Check disk space
    disk = await check_disk_space()
    
    # 2. Check critical services
    services = ["sonarr", "radarr", "trading-bot", "jellyfin"]
    for service in services:
        health = await service_health_check(service)
        if health["status"] != "healthy":
            # Troubleshoot
            await troubleshoot_service(service)
    
    # 3. Check Docker
    containers = await docker_list_containers()
    unhealthy = [c for c in containers if c["health"] != "healthy"]
    
    return {
        "disk_space": disk,
        "services": services_health,
        "unhealthy_containers": unhealthy
    }
```

### Example 3: Multi-Service Operation

```python
# Agent workflow
async def restart_media_stack():
    # 1. Stop services gracefully
    await docker_compose_restart("apps/media-download", service="sonarr")
    await docker_compose_restart("apps/media-download", service="radarr")
    
    # 2. Wait for healthy status
    await asyncio.sleep(10)
    
    # 3. Verify services are up
    sonarr_status = await docker_container_status("media-download-sonarr")
    radarr_status = await docker_container_status("media-download-radarr")
    
    return {
        "sonarr": sonarr_status["status"],
        "radarr": radarr_status["status"]
    }
```

### Example 4: Standard Deployment Workflow (Most Common)

```python
# Agent workflow - This is what agents do constantly
async def deploy_changes():
    # Single tool call handles entire workflow
    result = await deploy_and_restart(
        commit_message="Update service configuration",
        # app_path auto-detected from git changes
        # service auto-detected or restarts all in app
    )
    
    # Result includes:
    # - Git add/commit/push status
    # - Server pull status
    # - Services restarted
    # - Any conflicts or errors
    
    if result["status"] == "success":
        print(f"Deployed and restarted {result['services_restarted']} services")
    else:
        # Handle errors
        print(f"Deployment failed: {result['error']}")
```

### Example 5: Git Deploy Only (Without Restart)

```python
# Agent workflow - When you just need to sync code
async def sync_code():
    result = await git_deploy(
        commit_message="Update documentation",
        files="all"  # or specific files
    )
    
    # Handles: add → commit → push → pull on server
    # Returns conflicts, updated files, etc.
```

## Deployment

### Running the MCP Server

```bash
# Install dependencies
pip install mcp python-dotenv

# Run server
python agents/apps/agent-mcp/server.py

# Or as a service
systemd service or docker container
```

### Agent Configuration

Agents connect to MCP server via:
- **Stdio transport**: Direct process communication
- **SSE transport**: HTTP Server-Sent Events
- **WebSocket**: Real-time bidirectional communication

Example Claude Desktop config:
```json
{
  "mcpServers": {
    "home-server": {
      "command": "python",
      "args": ["/path/to/agents/apps/agent-mcp/server.py"],
      "env": {
        "SONARR_API_KEY": "...",
        "RADARR_API_KEY": "..."
      }
    }
  }
}
```

## Benefits Over Individual Tools

1. **Single Integration Point**: Agents only need to connect to one MCP server
2. **Type Safety**: All tools have defined schemas
3. **Discovery**: Agents can discover new tools automatically
4. **Composability**: Tools can be combined into complex workflows
5. **Consistency**: Unified error handling and response formats
6. **Extensibility**: Easy to add new tools as services are added
7. **Documentation**: Auto-generated from tool definitions

## Implementation Phases

### Phase 1: Core Infrastructure ✅ (Complete)
- ✅ MCP server setup
- ✅ Remote execution client
- ✅ Configuration management
- ✅ Docker tools (list, status, restart, logs, compose)

### Phase 2: Media Download Tools ✅ (Complete)
- ✅ Sonarr/Radarr queue management
- ✅ Download client configuration
- ✅ Root folder management
- ✅ Import scan triggers

### Phase 3: System & Monitoring ✅ (Complete)
- ✅ Disk space checks
- ✅ Service health checks
- ✅ Log viewing
- ✅ Resource monitoring

### Phase 4: Git & File Operations ⏳ (High Priority)
- ⏳ Git operations (status, pull, sync)
- ⏳ File operations (read, write, search)
- ⏳ Configuration management (.env files, docker-compose validation)
- ⏳ Template validation

### Phase 5: Database Operations ⏳ (High Priority)
- ⏳ Database backup/restore
- ⏳ Database health checks
- ⏳ Query execution (read-only)
- ⏳ Table inspection

### Phase 6: Log Aggregation ⏳ (Medium Priority)
- ⏳ Cross-service log search
- ⏳ Error aggregation
- ⏳ Log export
- ⏳ Log tailing

### Phase 7: Docker Advanced ⏳ (Medium Priority)
- ⏳ Image management (list, prune, update)
- ⏳ Volume management (list, prune)
- ⏳ Container stats
- ⏳ Compose operations (up, down)

### Phase 8: Networking Advanced ⏳ (Medium Priority)
- ⏳ Connectivity testing
- ⏳ DNS resolution
- ⏳ Port conflict detection
- ⏳ Network route checking

### Phase 9: Application-Specific Tools ⏳ (Ongoing)
- ⏳ Trading bot tools
- ⏳ Jellyfin/Immich tools
- ⏳ Home Assistant tools
- ⏳ Paperless tools
- ⏳ n8n workflow management
- ⏳ Vaultwarden status
- ⏳ Grafana integration

### Phase 10: Advanced Troubleshooting ⏳ (Ongoing)
- ⏳ Automated diagnostics
- ⏳ Multi-service workflows
- ⏳ Startup failure diagnosis
- ⏳ Resource limit detection
- ⏳ Configuration validation

### Phase 11: Backup & Restore ⏳ (Planned)
- ⏳ Backup automation
- ⏳ Backup verification
- ⏳ .env file backup
- ⏳ Restore operations

## Next Steps

1. **Set up MCP server structure**
2. **Implement core Docker tools** (proof of concept)
3. **Add media download tools** (most requested)
4. **Test with Claude Desktop** or other MCP client
5. **Expand to other services** based on usage

---

## Tool Implementation Status

### ✅ Implemented (35 tools)
- Docker Management: 8 tools
- Media Download: 13 tools
- System Monitoring: 5 tools
- Troubleshooting: 3 tools
- Networking: 3 tools
- System Utilities: 3 tools

### ⏳ Planned (62+ tools)
- Git Operations: 8 tools (including workflow tools)
- File Operations: 8 tools
- Database Operations: 6 tools
- Log Management: 4 tools
- Docker Advanced: 8 tools
- Networking Advanced: 5 tools
- Application-Specific: 12 tools
- Advanced Troubleshooting: 7 tools
- Backup & Restore: 4 tools

**Total**: 35 implemented, 60+ planned = 95+ total tools

## Priority Recommendations

### Critical (Implement Next)
1. **Git Operations** - Required for deployment workflow
   - **Priority**: `git_deploy` and `deploy_and_restart` should be implemented first as they're the most common workflows
2. **File Operations** - Essential for configuration management
3. **Database Operations** - Critical for data management
4. **Docker Advanced** - Image/volume management needed

### High Priority
5. **Log Aggregation** - Cross-service troubleshooting
6. **Networking Advanced** - Port conflict detection
7. **Application-Specific** - Service-specific operations

### Medium Priority
8. **Advanced Troubleshooting** - Automated diagnostics
9. **Backup & Restore** - Data protection

---

**Created**: 2025-11-13
**Last Updated**: 2025-01-10
**Status**: Active Development
**Current Phase**: Phase 3 Complete, Phase 4 Starting
**Recommended Approach**: MCP Server for unified server management

