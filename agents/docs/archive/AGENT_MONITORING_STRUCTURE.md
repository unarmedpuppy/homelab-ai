# Agent Monitoring Dashboard - Project Structure

## Recommended Structure

Based on the existing project patterns, the agent monitoring dashboard should be located in **`agents/apps/agent-monitoring/`** to follow the convention that all Docker Compose services live in `apps/`.

### Complete Project Structure

```
home-server/
├── apps/
│   └── agent-monitoring/              # Agent monitoring service
│       ├── docker-compose.yml         # Service orchestration
│       ├── README.md                  # Setup and usage guide
│       ├── .env.example               # Environment variables template
│       │
│       ├── data/                      # Persistent data (mounted volume)
│       │   └── agent_activity.db      # SQLite database
│       │
│       ├── backend/                   # Node.js + Express + TypeScript
│       │   ├── Dockerfile
│       │   ├── package.json
│       │   ├── tsconfig.json
│       │   ├── .dockerignore
│       │   ├── src/
│       │   │   ├── index.ts           # Express app entry point
│       │   │   ├── routes/
│       │   │   │   ├── index.ts
│       │   │   │   ├── agents.ts       # GET /api/agents, GET /api/agents/:id
│       │   │   │   ├── actions.ts      # GET /api/actions
│       │   │   │   ├── stats.ts        # GET /api/stats
│       │   │   │   ├── tasks.ts        # GET /api/tasks (task coordination integration)
│       │   │   │   └── influxdb.ts     # POST /api/influxdb/export
│       │   │   ├── services/
│       │   │   │   ├── database.ts     # SQLite operations
│       │   │   │   ├── influxdb.ts     # InfluxDB export operations
│       │   │   │   └── activity.ts      # Activity tracking logic
│       │   │   ├── types/
│       │   │   │   ├── index.ts
│       │   │   │   ├── agent.ts
│       │   │   │   ├── action.ts
│       │   │   │   └── stats.ts
│       │   │   └── utils/
│       │   │       └── logger.ts
│       │   └── .env.example
│       │
│       ├── frontend/                  # Next.js 14+ + TypeScript
│       │   ├── Dockerfile
│       │   ├── package.json
│       │   ├── tsconfig.json
│       │   ├── next.config.js
│       │   ├── tailwind.config.js
│       │   ├── .dockerignore
│       │   ├── src/
│       │   │   ├── app/                # Next.js App Router
│       │   │   │   ├── layout.tsx      # Root layout
│       │   │   │   ├── page.tsx        # Main dashboard page
│       │   │   │   ├── agents/
│       │   │   │   │   └── [id]/
│       │   │   │   │       └── page.tsx  # Agent detail page
│       │   │   │   └── api/            # Next.js API routes (if needed)
│       │   │   ├── components/
│       │   │   │   ├── ui/             # shadcn/ui components
│       │   │   │   ├── AgentCard.tsx
│       │   │   │   ├── AgentList.tsx
│       │   │   │   ├── ActivityFeed.tsx
│       │   │   │   ├── TaskOverview.tsx
│       │   │   │   ├── ToolUsageChart.tsx
│       │   │   │   └── StatsCards.tsx
│       │   │   ├── lib/
│       │   │   │   ├── api.ts          # API client
│       │   │   │   └── utils.ts
│       │   │   └── types/              # TypeScript types (shared with backend)
│       │   │       ├── agent.ts
│       │   │       ├── action.ts
│       │   │       └── stats.ts
│       │   └── .env.example
│       │
│       └── activity_logger/           # Python MCP tool logging
│           ├── activity_logger.py     # Main logging module
│           ├── requirements.txt
│           └── README.md              # Integration guide for MCP tools
│
├── agents/                             # Agent system (documentation, tools)
│   ├── docs/
│   │   ├── AGENT_DASHBOARD_PROPOSAL.md
│   │   ├── AGENT_MONITORING_STRUCTURE.md  # This file
│   │   └── ...
│   ├── memory/                        # Memory system (Python)
│   ├── registry/                       # Agent registry (markdown)
│   ├── tasks/                         # Task coordination (markdown)
│   └── ...
│
└── agents/apps/agent-mcp/              # MCP server (Python)
    └── tools/
        └── activity_monitoring.py      # MCP tools for activity logging
```

## Why `agents/apps/agent-monitoring/`?

### Follows Established Pattern
- ✅ All Docker Compose services are in `apps/`
- ✅ Consistent with `apps/trading-journal/`, `apps/homepage/`, etc.
- ✅ Discoverable via `scripts/docker-start.sh` pattern
- ✅ Follows the convention: `apps/` = running services

### Separation of Concerns
- **`agents/apps/agent-monitoring/`**: The running service (Docker Compose)
- **`agents/`**: Agent system documentation, memory, registry, tasks
- **`agents/apps/agent-mcp/`**: MCP server and tools

### Benefits
1. **Clear Ownership**: Service code lives with the service
2. **Easy Discovery**: All services in one place
3. **Docker Scripts**: Works with existing `docker-start.sh` pattern
4. **Homepage Integration**: Easy to add to Homepage config
5. **Traefik Routing**: Follows same pattern as other services

## Integration Points

### Links from `agents/` Directory

The `agents/` directory can reference the monitoring service:

```markdown
# agents/docs/README.md
## Agent Monitoring
- **Dashboard**: `agents/apps/agent-monitoring/` - Real-time agent activity dashboard
- **Documentation**: `agents/apps/agent-monitoring/README.md`
- **Access**: http://agent-dashboard.server.unarmedpuppy.com
```

### MCP Tool Integration

The Python activity logger can be imported by MCP tools:

```python
# agents/apps/agent-mcp/tools/activity_monitoring.py
from agents.monitoring.activity_logger import log_action

@server.tool()
async def docker_list_containers(...):
    # Log the action
    log_action(agent_id, "mcp_tool", "docker_list_containers", ...)
    # ... rest of tool logic
```

**Note**: The activity logger Python module can be:
- Option A: In `agents/apps/agent-monitoring/activity_logger/` (as shown above)
- Option B: In `agents/monitoring/activity_logger/` (if we want it in agents/)
- Option C: In `agents/apps/agent-mcp/tools/activity_logger/` (if it's MCP-specific)

**Recommendation**: Option A - Keep it with the service, but make it importable from MCP tools via Python path or package installation.

## Docker Compose Structure

```yaml
version: "3.8"

services:
  backend:
    build: ./backend
    container_name: agent-monitoring-backend
    restart: unless-stopped
    environment:
      - DATABASE_PATH=/data/agent_activity.db
      - INFLUXDB_URL=http://influxdb:8086
      - INFLUXDB_DATABASE=agent_metrics
      - PORT=3001
    volumes:
      - ./data:/data
    ports:
      - "3011:3001"
    networks:
      - my-network

  frontend:
    build: ./frontend
    container_name: agent-monitoring-frontend
    restart: unless-stopped
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:3011
    ports:
      - "3012:3000"
    depends_on:
      - backend
    networks:
      - my-network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.agent-dashboard.rule=Host(`agent-dashboard.server.unarmedpuppy.com`)"
      - "traefik.http.routers.agent-dashboard.entrypoints=websecure"
      - "traefik.http.routers.agent-dashboard.tls.certresolver=myresolver"
      - "homepage.group=Infrastructure"
      - "homepage.name=Agent Dashboard"
      - "homepage.href=http://agent-dashboard.server.unarmedpuppy.com"
      - "homepage.icon=activity.svg"

networks:
  my-network:
    external: true
```

## Alternative: If You Prefer `agents/monitoring/`

If you want it in `agents/` instead, the structure would be:

```
agents/
├── monitoring/                        # Agent monitoring service
│   ├── docker-compose.yml
│   ├── backend/
│   ├── frontend/
│   └── activity_logger/
```

**Pros:**
- ✅ Keeps all agent-related code together
- ✅ Clear that it's part of the agent system

**Cons:**
- ❌ Breaks the pattern that `apps/` = services
- ❌ Won't be discovered by `docker-start.sh` (unless we update it)
- ❌ Less consistent with other services

## Recommendation

**Use `agents/apps/agent-monitoring/`** because:
1. Follows established project patterns
2. Works with existing Docker scripts
3. Consistent with other services
4. Easy to discover and manage
5. Can still be referenced from `agents/` docs

The `agents/` directory remains focused on:
- Documentation
- Memory system (Python library)
- Registry (markdown files)
- Tasks (markdown files)
- Agent definitions

While `agents/apps/agent-monitoring/` is the running service that monitors all of the above.

---

**Status**: Structure Proposal
**Location**: `agents/apps/agent-monitoring/` (recommended)
**Alternative**: `agents/monitoring/` (if preferred)

