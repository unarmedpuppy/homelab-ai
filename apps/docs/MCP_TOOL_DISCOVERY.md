# MCP Tool Discovery Guide

## Overview

This guide helps AI agents discover and use the Server Management MCP Server tools effectively. **Always check for MCP tools before writing custom scripts or SSH commands.**

**Key Principle**: If no tool exists for your operation, **test your approach first**, then **create an MCP tool** if the operation is reusable and should be shared with future agents.

## Tool Discovery Workflow

### Step 1: Identify the Operation

When you need to perform a server operation, first identify what you're trying to do:
- Manage Docker containers?
- Check service status?
- View logs?
- Troubleshoot issues?
- Manage media download queues?
- Check disk space?

### Step 2: Check MCP Server Tools

**Primary Resources**:
1. **Tool Reference**: `server-management-mcp/README.md`
   - Complete list of available tools
   - Tool signatures and parameters
   - Usage examples
   - Common workflows

2. **Tool Modules**: `server-management-mcp/tools/`
   - `docker.py` - Docker container management
   - `media_download.py` - Sonarr/Radarr/NZBGet operations (when implemented)
   - `monitoring.py` - System monitoring (when implemented)
   - And more...

3. **Architecture Plan**: `apps/docs/MCP_SERVER_PLAN.md`
   - Complete tool catalog
   - Tool categories
   - Implementation status

### Step 3: Use the Tool

**If you have MCP access** (Claude Desktop, GPT-4 with MCP):
- Use tools directly via MCP interface
- Tools are auto-discovered and documented
- Type-safe with clear parameters

**If you don't have MCP access**:
- Review tool documentation in `server-management-mcp/README.md`
- Understand tool parameters and return values
- Note that tools can be called programmatically or via CLI

### Step 4: Fallback to SSH (If Needed)

**Only if**:
- No MCP tool exists for the operation
- MCP server is unavailable
- One-off operation not worth adding to MCP

Use SSH commands via `scripts/connect-server.sh` as documented in `apps/docs/SERVER_AGENT_PROMPT.md`.

## Tool Categories

### Docker Management ✅ (Available)

**Location**: `server-management-mcp/tools/docker.py`

**Available Tools**:
- `docker_list_containers` - List all containers with filters
- `docker_container_status` - Get detailed container status
- `docker_restart_container` - Restart with health check option
- `docker_stop_container` - Stop containers
- `docker_start_container` - Start containers
- `docker_view_logs` - View container logs
- `docker_compose_ps` - List docker-compose services
- `docker_compose_restart` - Restart docker-compose services

**Use Cases**:
- Checking container status
- Restarting services
- Viewing logs
- Managing docker-compose applications

### Media Download 🚧 (In Progress)

**Location**: `server-management-mcp/tools/media_download.py` (to be implemented)

**Planned Tools**:
- `sonarr_clear_queue` - Clear Sonarr download queue
- `sonarr_queue_status` - Get queue status and stuck items
- `sonarr_trigger_import_scan` - Trigger manual import scan
- `sonarr_check_download_clients` - Verify download client configuration
- `radarr_clear_queue` - Clear Radarr download queue
- `radarr_add_root_folder` - Add root folder to Radarr
- `radarr_list_root_folders` - List all root folders
- `nzbget_status` - Get NZBGet download status
- `qbittorrent_status` - Get qBittorrent status

**Use Cases**:
- Troubleshooting stuck queues
- Managing download clients
- Triggering import scans
- Checking root folder configuration

### System Monitoring ✅ (Available)

**Available Tools**:
- `check_disk_space` - Check disk usage
- `check_system_resources` - CPU, memory, network
- `service_health_check` - Comprehensive health check
- `get_recent_errors` - Recent error logs
- `find_service_by_port` - Find service by port

**Planned Tools**:
- `check_disk_usage_by_service` - Disk usage breakdown
- `check_resource_limits` - Resource limit detection

### Troubleshooting ✅ (Available)

**Available Tools**:
- `troubleshoot_failed_downloads` - Sonarr/Radarr diagnostics
- `diagnose_download_client_unavailable` - Download client diagnostics
- `check_service_dependencies` - Dependency verification

**Planned Tools**:
- `troubleshoot_service` - Comprehensive diagnostics
- `diagnose_connection_issue` - Network diagnostics
- `diagnose_startup_failure` - Startup failure analysis
- `detect_port_conflicts` - Port conflict detection
- `validate_service_config` - Configuration validation

### Git Operations ⏳ (Planned - High Priority)

**Planned Tools**:
- `git_status` - Check repository status
- `git_pull` - Pull latest changes
- `git_sync` - Full sync workflow
- `git_log` - View commit history
- `git_diff` - Show differences
- `git_checkout` - Checkout branch/commit
- **`git_deploy`** - **Complete deployment workflow** (add → commit → push → pull on server)
- **`deploy_and_restart`** - **Full workflow** (deploy changes → restart affected services)

**Use Cases**:
- **Most Common**: `deploy_and_restart` - Standard agent workflow for deploying code and restarting services
- Deployment workflow automation
- Repository status checking
- Conflict detection
- Change tracking

**Workflow Tools** (High Priority):
- `git_deploy`: Combines git add, commit, push, and server pull into one operation
- `deploy_and_restart`: Complete workflow from code changes to service restart
- `restart_affected_services`: Auto-detect and restart services based on git changes

### File Operations ⏳ (Planned - High Priority)

**Planned Tools**:
- `read_file` - Read file contents
- `write_file` - Write file contents
- `search_files` - Search for files
- `read_env_file` - Parse .env files
- `validate_env_file` - Validate .env files
- `update_env_variable` - Update env variable
- `read_docker_compose` - Parse docker-compose.yml
- `validate_docker_compose` - Validate docker-compose.yml

**Use Cases**:
- Configuration file management
- Environment variable updates
- File searching and reading
- Configuration validation

### Database Operations ⏳ (Planned - High Priority)

**Planned Tools**:
- `database_backup` - Create database backup
- `database_restore` - Restore database
- `database_query` - Execute read-only query
- `database_health_check` - Check database health
- `database_list_tables` - List all tables
- `database_table_info` - Get table details

**Use Cases**:
- Database backup/restore
- Health monitoring
- Data inspection
- Troubleshooting

### Log Management ⏳ (Planned - Medium Priority)

**Planned Tools**:
- `search_logs` - Search across service logs
- `aggregate_errors` - Aggregate error logs
- `tail_logs` - Tail multiple service logs
- `export_logs` - Export logs to file

**Use Cases**:
- Cross-service troubleshooting
- Error pattern detection
- Log analysis
- Debugging

### Docker Advanced ⏳ (Planned - Medium Priority)

**Planned Tools**:
- `docker_list_images` - List Docker images
- `docker_prune_images` - Remove unused images
- `docker_update_image` - Update image
- `docker_list_volumes` - List volumes
- `docker_prune_volumes` - Remove unused volumes
- `docker_container_stats` - Get container stats
- `docker_compose_up` - Start services
- `docker_compose_down` - Stop services

**Use Cases**:
- Image management
- Volume cleanup
- Resource monitoring
- Service lifecycle management

## Common Operations → Tool Mapping

### "Check if a container is running"
→ Use: `docker_container_status(container_name)`

### "Restart a service"
→ Use: `docker_restart_container(container_name)`

### "View container logs"
→ Use: `docker_view_logs(container_name, lines=50)`

### "List all containers"
→ Use: `docker_list_containers()`

### "Check Sonarr queue"
→ Use: `sonarr_queue_status()` (when implemented)

### "Clear stuck downloads"
→ Use: `sonarr_clear_queue()` or `radarr_clear_queue()` (when implemented)

### "Check disk space"
→ Use: `check_disk_space()` (when implemented)

### "Troubleshoot a service"
→ Use: `troubleshoot_service(service_name)` (when implemented)

### "Deploy changes and restart services" (Most Common Workflow)
→ Use: `deploy_and_restart(commit_message, app_path, service)` (when implemented)
- This is the standard agent workflow: make changes → deploy → restart

### "Deploy code changes to server"
→ Use: `git_deploy(commit_message, files)` (when implemented)
- Handles: add → commit → push → pull on server

### "Restart services affected by changes"
→ Use: `restart_affected_services(app_path, check_changes=True)` (when implemented)
- Auto-detects which services need restarting based on git changes

## Tool Implementation Status

| Category | Status | Tools Available |
|----------|--------|----------------|
| Docker Management | ✅ Complete | 8 tools (planned: 16 total) |
| Media Download | ✅ Complete | 13 tools |
| System Monitoring | ✅ Complete | 5 tools |
| Troubleshooting | ✅ Complete | 3 tools (planned: 10 total) |
| Networking | ✅ Complete | 3 tools (planned: 8 total) |
| System Utilities | ✅ Complete | 3 tools |
| Git Operations | ⏳ Planned | 0 tools (planned: 6) |
| File Operations | ⏳ Planned | 0 tools (planned: 8) |
| Database Operations | ⏳ Planned | 0 tools (planned: 6) |
| Log Management | ⏳ Planned | 0 tools (planned: 4) |
| Docker Advanced | ⏳ Planned | 0 tools (planned: 8) |
| Networking Advanced | ⏳ Planned | 0 tools (planned: 5) |
| Application-Specific | ⏳ Planned | 0 tools (planned: 12) |
| Backup & Restore | ⏳ Planned | 0 tools (planned: 4) |

**Total**: 35 tools implemented, 60+ tools planned = 95+ total tools

## Adding New Tools

If you need an operation that doesn't exist:

### Step 1: Test Your Approach First

**Before creating a tool**, verify your approach works:
- Test the operation using SSH commands or direct execution
- Verify it produces expected results
- Confirm the approach is correct and safe

### Step 2: Determine if It Should Be an MCP Tool

**Create an MCP tool if**:
- ✅ Operation will be used multiple times
- ✅ Operation benefits from type safety and error handling
- ✅ Operation should be standardized across agents
- ✅ Operation is part of a common workflow
- ✅ Other agents will likely need the same operation

**Don't create an MCP tool if**:
- ❌ One-off operation that won't be repeated
- ❌ Experimental/test operation that may change
- ❌ Operation is too specific to a single use case

### Step 3: Implement the Tool

**If it should be an MCP tool**:

1. **Choose the right module**:
   - `tools/docker.py` - Docker operations
   - `tools/media_download.py` - Sonarr/Radarr/NZBGet (create if needed)
   - `tools/monitoring.py` - System monitoring (create if needed)
   - `tools/system.py` - System-level operations (create if needed)
   - Or create a new module if it's a new category

2. **Follow the pattern**:
   ```python
   @server.tool()
   async def your_tool_name(
       param1: str,
       param2: Optional[int] = None
   ) -> Dict[str, Any]:
       """
       Clear description of what the tool does.
       
       Args:
           param1: Description of parameter
           param2: Optional parameter description
           
       Returns:
           Dictionary with status and results
       """
       try:
           # Implementation here
           return {
               "status": "success",
               "data": {...}
           }
       except Exception as e:
           return {
               "status": "error",
               "error_type": type(e).__name__,
               "message": str(e)
           }
   ```

3. **Register the tool**:
   - Add import in `server.py`: `from tools.your_module import register_your_tools`
   - Register: `register_your_tools(server)`

4. **Update documentation**:
   - Add tool to `server-management-mcp/README.md`
   - Include usage examples
   - Document parameters and return values

5. **Test the tool**:
   - Verify it works as expected
   - Test error cases
   - Confirm return format is correct

6. **Use your new tool**:
   - Now use the tool for your operation
   - Other agents can discover and use it too

### Step 4: Fallback (If Not an MCP Tool)

**If it's a one-off operation**:
- Use SSH commands via `scripts/connect-server.sh`
- Document why it's not an MCP tool
- Note in your work that a tool could be created if needed in the future

## Best Practices

1. **Always check MCP tools first** - Don't write custom scripts without checking
2. **Test before creating** - Verify your approach works before implementing as a tool
3. **Create reusable tools** - If an operation will be used again, create an MCP tool
4. **Use type-safe tools** - MCP tools provide better error handling
5. **Document tool usage** - Note which tools you used in your work
6. **Follow patterns** - Use existing tools as examples for new implementations
7. **Update documentation** - Always update README.md when adding new tools
8. **Share knowledge** - Creating tools helps future agents

## Tool Creation Workflow

**Complete workflow when no tool exists**:

1. ✅ **Check for existing tool** - Review MCP server tools
2. ✅ **Test approach** - Verify operation works with SSH/direct execution
3. ✅ **Confirm it's reusable** - Determine if it should be an MCP tool
4. ✅ **Create the tool** - Implement following existing patterns
5. ✅ **Register and document** - Add to server.py and README.md
6. ✅ **Test the tool** - Verify it works correctly
7. ✅ **Use your tool** - Now use it for your operation
8. ✅ **Share with others** - Future agents can discover and use it

## Quick Reference

**Tool Documentation**: `server-management-mcp/README.md`
**Tool Source Code**: `server-management-mcp/tools/`
**Architecture Plan**: `apps/docs/MCP_SERVER_PLAN.md`
**Docker Setup**: `server-management-mcp/DOCKER_SETUP.md`
**Server Agent Prompt**: `apps/docs/SERVER_AGENT_PROMPT.md`

---

**Remember**: MCP tools are the preferred method for all server operations. Always check for available tools before writing custom commands.

