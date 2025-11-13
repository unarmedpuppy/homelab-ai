# Home Server Management MCP Server

MCP (Model Context Protocol) server providing tools for managing the entire home server infrastructure.

## Installation

```bash
cd server-management-mcp
pip install -r requirements.txt
```

## Configuration

Create `config.json` (optional) to override defaults:

```json
{
  "server": {
    "host": "192.168.86.47",
    "port": 4242,
    "user": "unarmedpuppy"
  },
  "sonarr": {
    "api_key": "your-api-key"
  }
}
```

Or use environment variables:
- `SONARR_API_KEY`
- `RADARR_API_KEY`
- `NZBGET_USERNAME`
- `NZBGET_PASSWORD`
- `QBITTORRENT_USERNAME`
- `QBITTORRENT_PASSWORD`

## Running the Server

### Standalone (for testing)

```bash
python server.py
```

### With Claude Desktop

Add to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "home-server": {
      "command": "python",
      "args": ["/absolute/path/to/server-management-mcp/server.py"],
      "env": {
        "SONARR_API_KEY": "...",
        "RADARR_API_KEY": "..."
      }
    }
  }
}
```

## Available Tools

### Docker Management ✅
- `docker_list_containers` - List all containers with filters
- `docker_container_status` - Get detailed container status
- `docker_restart_container` - Restart a container (with health check option)
- `docker_stop_container` - Stop a container
- `docker_start_container` - Start a container
- `docker_view_logs` - View container logs
- `docker_compose_ps` - List docker-compose services
- `docker_compose_restart` - Restart docker-compose services

### Media Download ✅
**Sonarr Tools:**
- `sonarr_clear_queue` - Clear all items from Sonarr queue
- `sonarr_queue_status` - Get queue summary (total, by status, stuck items)
- `sonarr_trigger_import_scan` - Trigger manual import scan
- `sonarr_check_download_clients` - Check download client configuration
- `sonarr_list_series` - List all series in library

**Radarr Tools:**
- `radarr_clear_queue` - Clear all items from Radarr queue
- `radarr_queue_status` - Get queue summary
- `radarr_trigger_import_scan` - Trigger manual import scan
- `radarr_list_root_folders` - List all root folders
- `radarr_add_root_folder` - Add a new root folder
- `radarr_list_movies` - List all movies in library
- `radarr_check_missing_root_folders` - Find movies using unconfigured paths

**Download Clients:**
- `nzbget_status` - Get NZBGet download status and speeds
- `qbittorrent_status` - Get qBittorrent status and active torrents

### System Monitoring ✅
- `check_disk_space` - Check disk usage (with status: ok/warning/critical)
- `check_system_resources` - Check CPU, memory, and load average
- `get_recent_errors` - Get recent errors from service logs
- `service_health_check` - Comprehensive health check for a service
- `find_service_by_port` - Find which service is using a port

### Troubleshooting ✅
- `troubleshoot_failed_downloads` - Comprehensive diagnostic for Sonarr/Radarr
- `diagnose_download_client_unavailable` - Specific diagnostic for stuck downloads
- `check_service_dependencies` - Check if service dependencies are running

### Networking ✅
- `check_port_status` - Check if a port is listening
- `get_available_port` - Find available ports for new Docker containers (checks running containers, docker-compose files, and system ports)
- `vpn_status` - Check VPN services (Gluetun, Tailscale)
- `check_dns_status` - Check DNS service (AdGuard) status

### Agent Communication ✅
- `send_agent_message()` - Send message to another agent
- `get_agent_messages()` - Get messages for agent (with filters)
- `acknowledge_message()` - Acknowledge receipt of message
- `mark_message_resolved()` - Mark message as resolved
- `query_messages()` - Query messages with multiple filters

### System Utilities ✅
- `cleanup_archive_files` - Remove unpacked archive files (.rar, .par2, .nzb)
- `check_unmapped_folders` - Find folders not mapped to series/movies
- `list_completed_downloads` - List completed downloads in download directories

### Git Operations & Deployment ✅
- `git_status` - Check git repository status (branch, changes, ahead/behind)
- `git_deploy` - Complete deployment workflow (add → commit → push → pull on server)
- `deploy_and_restart` - Full workflow (deploy changes → restart affected services)
- `restart_affected_services` - Auto-detect and restart services based on git changes

### Memory Management ✅
- `memory_query_decisions` - Query decisions from memory (by project, task, tags, importance, or full-text search)
- `memory_query_patterns` - Query patterns from memory (by severity, tags, frequency, or full-text search)
- `memory_search` - Full-text search across all memories (decisions and patterns)
- `memory_record_decision` - Record a decision in memory
- `memory_record_pattern` - Record or update a pattern in memory
- `memory_save_context` - Save or update current work context
- `memory_get_recent_context` - Get recent work context (by agent or all)
- `memory_get_context_by_task` - Get context for a specific task
- `memory_export_to_markdown` - Export all memories to markdown files for human review

**Fallback**: If MCP tools unavailable, use `agents/memory/query_memory.sh` helper script. See `agents/memory/QUERY_MEMORY_README.md` for usage.

### Agent Management ✅
- `create_agent_definition` - Create a new specialized agent definition (with tasks and registry entry)
- `query_agent_registry` - Query the agent registry for existing agents (by specialization or status)
- `assign_task_to_agent` - Assign a new task to an existing agent
- `archive_agent` - Archive an agent (move to archive state)
- `reactivate_agent` - Reactivate an archived agent
- `sync_agent_registry` - Sync agent registry markdown from monitoring DB and definition files

### Skill Management ✅
- `propose_skill` - Propose a new skill for the skills library (creates proposal for review)
- `list_skill_proposals` - List skill proposals (by category or status)
- `query_skills` - Query existing skills (by category or search text)
- `analyze_patterns_for_skills` - Analyze patterns in memory and identify candidates for skill creation
- `auto_propose_skill_from_pattern` - Automatically create a skill proposal from a pattern

### Skill Activation ✅
- `suggest_relevant_skills` - Suggest relevant skills based on context (prompt, files, task) - **CRITICAL: Use this before starting work!**
- `get_skill_activation_reminder` - Get formatted reminder of which skills to check

### Dev Docs (Context Preservation) ✅
- `create_dev_docs` - Create dev docs (plan, context, tasks) for a major task
- `update_dev_docs` - Update dev docs with current progress (use before compaction)
- `list_active_dev_docs` - List all active dev docs for an agent
- `read_dev_docs` - Read all dev docs for a specific task (use at session start)

### Quality Checks ✅
- `check_code_quality` - Comprehensive quality check (errors, security, error handling) - **Use after every edit!**
- `check_build_errors` - Check for build errors in a project

### Code Review ✅
- `request_code_review` - Request systematic code review for modified files
- `self_review_checklist` - Get self-review checklist before marking tasks complete

### Task Coordination ✅
- `register_task` - Register a new task in the central task registry
- `query_tasks` - Query tasks with filters (status, assignee, project, priority, search)
- `get_task` - Get details for a single task by task ID
- `claim_task` - Claim a task (assign it to an agent) - validates dependencies
- `update_task_status` - Update the status of a task - auto-updates dependents
- `check_task_dependencies` - Check dependency status for a task

## Development

### Adding New Tools

1. Create a new module in `tools/` (e.g., `tools/monitoring.py`)
2. Implement tool functions with `@server.tool()` decorator
3. Register the module in `server.py`:
   ```python
   from tools.monitoring import register_monitoring_tools
   register_monitoring_tools(server)
   ```

### Testing

Test tools directly:
```python
from tools.docker import register_docker_tools
from mcp.server import Server

server = Server("test")
register_docker_tools(server)

# Tools are now available
```

## Project Structure

```
server-management-mcp/
├── server.py              # Main MCP server
├── config/
│   ├── __init__.py
│   └── settings.py        # Configuration management
├── clients/
│   ├── __init__.py
│   └── remote_exec.py     # Remote command execution
├── tools/
│   ├── __init__.py
│   ├── docker.py          # Docker tools
│   └── ...                # Other tool modules
└── README.md
```

## Status

- ✅ Core infrastructure
- ✅ Docker management tools (8 tools)
- ✅ Media download tools (11 tools)
- ✅ System monitoring tools (5 tools)
- ✅ Troubleshooting tools (3 tools)
- ✅ Git operations & deployment (4 tools)
- ✅ Networking tools (3 tools)
- ✅ System utilities (3 tools)
- ⏳ File operations (planned)
- ⏳ Database operations (planned)
- ⏳ Application-specific tools (planned)
- ⏳ Backup/restore tools (planned)

**Total Tools**: 76 tools implemented

**Breakdown**:
- Activity Monitoring: 4 tools
- Agent Communication: 5 tools
- Memory Management: 9 tools
- Task Coordination: 6 tools
- Agent Management: 6 tools
- Skill Management: 5 tools
- Skill Activation: 2 tools
- Dev Docs: 4 tools
- Quality Checks: 2 tools ⭐ NEW
- Code Review: 2 tools ⭐ NEW
- Docker Management: 8 tools
- Media Download: 13 tools
- System Monitoring: 5 tools
- Troubleshooting: 3 tools
- Git Operations: 4 tools
- Networking: 4 tools
- System Utilities: 3 tools

