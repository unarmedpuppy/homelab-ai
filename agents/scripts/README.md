# Agent Scripts

Utility scripts for managing agent infrastructure and workflows.

## Available Scripts

### `start-agent-infrastructure.sh`

**Purpose**: Start all agent infrastructure services locally.

**Usage**:
```bash
# Start infrastructure
./agents/scripts/start-agent-infrastructure.sh

# Check if running (don't start)
./agents/scripts/start-agent-infrastructure.sh --check-only
```

**What it does**:
1. Checks if agent monitoring services are running
2. Starts Docker Compose services if not running
3. Waits for services to be healthy
4. Reports service URLs

**Services started**:
- Backend API: `http://localhost:3001`
- Frontend Dashboard: `http://localhost:3012`
- Grafana: `http://localhost:3011`
- InfluxDB: `http://localhost:8087`

**Requirements**:
- Docker and docker-compose (or docker compose v2)
- Agent monitoring docker-compose.yml at `agents/apps/agent-monitoring/`

**Exit codes**:
- `0` - Success (services running)
- `1` - Error (failed to start or check failed)

## Integration with Agent Workflow

### In Agent Prompts

The base agent prompt (`agents/prompts/base.md`) includes infrastructure startup as step 0:

```python
# Check if infrastructure is running
infra_status = await check_agent_infrastructure()

# If not running, start it
if not infra_status.get("all_running"):
    await start_agent_infrastructure()
```

### MCP Tools

Three MCP tools are available:
- `start_agent_infrastructure()` - Start all services
- `check_agent_infrastructure()` - Check service status
- `stop_agent_infrastructure()` - Stop all services

### Fallback (No MCP)

If MCP tools are unavailable, run the script directly:
```bash
cd /Users/joshuajenquist/repos/personal/home-server
./agents/scripts/start-agent-infrastructure.sh
```

## When to Use

**Always run before starting agent work:**
- Ensures monitoring is available
- Ensures dashboard is accessible
- Prevents "service unavailable" errors

**Run at session start:**
- First step in agent workflow (step 0)
- Before starting monitoring session (step 0.5)

## Troubleshooting

### Services won't start
```bash
# Check Docker is running
docker ps

# Check logs
cd agents/apps/agent-monitoring
docker-compose logs

# Check ports are available
lsof -i :3001
lsof -i :3012
lsof -i :3011
```

### Port conflicts
If ports are in use, modify `agents/apps/agent-monitoring/docker-compose.yml` to use different ports.

### Script not found
Ensure you're running from the project root:
```bash
cd /Users/joshuajenquist/repos/personal/home-server
./agents/scripts/start-agent-infrastructure.sh
```

---

**Last Updated**: 2025-01-13

