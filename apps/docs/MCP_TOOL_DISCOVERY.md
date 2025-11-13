# MCP Tool and Skills Discovery Guide

## Overview

This guide helps AI agents discover and use **Skills** and **MCP Tools** effectively. **Skills and MCP Tools are your PRIMARY method for gaining context and capabilities.**

**Discovery Priority**:
1. **Skills** (workflows) - Check `server-management-skills/README.md` first
2. **MCP Tools** (operations) - Check `server-management-mcp/README.md` second
3. Create new MCP tool (if operation is reusable)
4. Create new skill (if workflow is reusable)
5. Existing scripts (fallback)
6. SSH commands (last resort)

**Key Principles**:
- **Skills provide workflows**: Complete step-by-step guidance for common tasks
- **MCP Tools provide capabilities**: Individual operations you can use
- **Skills use MCP Tools**: Skills orchestrate tools into workflows
- **Always check Skills and Tools first** - don't start from scratch
- If no tool/skill exists, **test your approach first**, then create one if reusable

## Discovery Workflow

### Step 1: Identify What You Need

When you need to perform a server operation, first identify what you're trying to do:
- **Complete workflow?** (deployment, troubleshooting, setup) → Check **Skills**
- **Individual operation?** (check status, restart, view logs) → Check **MCP Tools**

Examples:
- "Deploy code changes" → Use `standard-deployment` **skill**
- "Troubleshoot container failure" → Use `troubleshoot-container-failure` **skill**
- "Check container status" → Use `docker_container_status` **MCP tool**
- "Restart service" → Use `docker_compose_restart` **MCP tool**

### Step 2: Check Skills First (For Workflows)

**Primary Resource**: `server-management-skills/README.md`
- Complete skills catalog
- Skills by category (deployment, troubleshooting, maintenance)
- When to use each skill
- MCP tools used by each skill

**Available Skills**:
- `standard-deployment` - Complete deployment workflow
- `troubleshoot-container-failure` - Container diagnostics
- `system-health-check` - Comprehensive system verification
- `troubleshoot-stuck-downloads` - Download queue issues
- `deploy-new-service` - New service setup
- And more...

**If a skill exists for your workflow**: Use it! Skills provide complete, tested workflows.

### Step 3: Check MCP Tools (For Operations)

**Primary Resources**:
1. **Tool Reference**: `server-management-mcp/README.md`
   - Complete list of available tools
   - Tool signatures and parameters
   - Usage examples

2. **Tool Modules**: `server-management-mcp/tools/`
   - `docker.py` - Docker container management
   - `media_download.py` - Sonarr/Radarr/NZBGet operations
   - `monitoring.py` - System monitoring
   - `git.py` - Git operations
   - And more...

3. **Architecture Plan**: `apps/docs/MCP_SERVER_PLAN.md`
   - Complete tool catalog
   - Tool categories
   - Implementation status

### Step 4: Use Skills or Tools

**If you have MCP access** (Claude Desktop, GPT-4 with MCP):
- Skills are automatically discovered and activated
- MCP tools are auto-discovered and documented
- Type-safe with clear parameters

**If you don't have MCP access**:
- Review skill documentation in `server-management-skills/README.md`
- Review tool documentation in `server-management-mcp/README.md`
- Understand parameters and return values
- Follow skill workflows step-by-step

### Step 5: Fallback to SSH (If Needed)

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

## Common Operations → Skills/Tools Mapping

### Workflows (Use Skills)

### "Deploy changes and restart services" (Most Common)
→ Use: **`standard-deployment` skill**
- Complete workflow: verify → deploy → restart → verify
- Uses: `git_deploy`, `docker_compose_restart`, `docker_container_status`

### "Troubleshoot a container that won't start"
→ Use: **`troubleshoot-container-failure` skill**
- Complete diagnostic workflow
- Uses: `docker_container_status`, `docker_view_logs`, `check_service_dependencies`

### "Check overall system health"
→ Use: **`system-health-check` skill**
- Comprehensive system verification
- Uses: `check_disk_space`, `check_system_resources`, `docker_list_containers`

### "Fix stuck downloads in Sonarr/Radarr"
→ Use: **`troubleshoot-stuck-downloads` skill**
- Complete diagnostic and fix workflow
- Uses: `sonarr_queue_status`, `troubleshoot_failed_downloads`, `remove_stuck_downloads`

### "Set up a new service"
→ Use: **`deploy-new-service` skill**
- Complete setup workflow
- Uses: `check_port_status`, `write_file`, `validate_docker_compose`, `git_deploy`

### Operations (Use MCP Tools)

### "Check if a container is running"
→ Use: `docker_container_status(container_name)`

### "Restart a service"
→ Use: `docker_restart_container(container_name)` or `docker_compose_restart(app_path, service)`

### "View container logs"
→ Use: `docker_view_logs(container_name, lines=50)`

### "List all containers"
→ Use: `docker_list_containers()`

### "Check Sonarr queue"
→ Use: `sonarr_queue_status()`

### "Check disk space"
→ Use: `check_disk_space()`

### "Deploy code changes to server"
→ Use: `git_deploy(commit_message, files)`
- Handles: add → commit → push → pull on server

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

