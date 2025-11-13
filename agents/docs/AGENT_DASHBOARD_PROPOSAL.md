# Agent Activity Dashboard - Proposal

## Overview

Create a centralized, persistent dashboard to observe all agent activity, status, and actions in real-time.

## Current Infrastructure

**What You Already Have:**
- ✅ **Grafana** (port 3010) - Monitoring dashboard
- ✅ **Homepage** (port 3000) - Service dashboard
- ✅ **SQLite** - Already used for memory system (`agents/memory/memory.db`)
- ✅ **InfluxDB** - Time-series database (if we want metrics)
- ✅ **n8n** - Workflow automation

## Proposed Solution: SQLite + Next.js/TypeScript Dashboard + Grafana Integration

### Why This Approach?

1. **Efficient Storage**: SQLite (like memory system)
   - Fast queries
   - No server needed
   - Already in use
   - Easy to backup
   - Export to InfluxDB for Grafana

2. **Modern Dashboard**: Next.js + TypeScript + Node.js
   - Type-safe full-stack application
   - Server-side rendering for performance
   - Real-time updates via polling or WebSocket
   - Professional UI with Tailwind CSS
   - Follows framework preferences (see `FRAMEWORK_PREFERENCES.md`)

3. **Grafana Integration**: Time-series visualizations
   - Export metrics to InfluxDB
   - Professional dashboards
   - Historical analysis
   - Alerting capabilities

4. **Action Logging**: Automatic via MCP tools
   - Log all tool calls
   - Log memory operations
   - Log task updates
   - Store in SQLite + export to InfluxDB

### Architecture

```
agents/
├── monitoring/
│   ├── agent_activity.db          # SQLite database (primary)
│   │
│   ├── backend/                    # Node.js + Express + TypeScript
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── src/
│   │   │   ├── index.ts            # Express app
│   │   │   ├── routes/             # API routes
│   │   │   │   ├── agents.ts       # Agent endpoints
│   │   │   │   ├── actions.ts      # Action endpoints
│   │   │   │   ├── stats.ts        # Stats endpoints
│   │   │   │   └── influxdb.ts     # InfluxDB export
│   │   │   ├── services/           # Business logic
│   │   │   │   ├── database.ts     # SQLite operations
│   │   │   │   ├── influxdb.ts     # InfluxDB operations
│   │   │   │   └── activity.ts     # Activity tracking
│   │   │   └── types/              # TypeScript types
│   │   └── Dockerfile
│   │
│   ├── frontend/                    # Next.js + TypeScript
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── next.config.js
│   │   ├── tailwind.config.js
│   │   ├── src/
│   │   │   ├── app/                # Next.js App Router
│   │   │   │   ├── layout.tsx
│   │   │   │   ├── page.tsx        # Main dashboard
│   │   │   │   ├── agents/         # Agent detail pages
│   │   │   │   └── api/            # API routes (if needed)
│   │   │   ├── components/          # React components
│   │   │   │   ├── AgentCard.tsx
│   │   │   │   ├── ActivityFeed.tsx
│   │   │   │   ├── TaskOverview.tsx
│   │   │   │   └── ToolUsageChart.tsx
│   │   │   ├── lib/                 # Utilities
│   │   │   │   └── api.ts           # API client
│   │   │   └── types/               # TypeScript types
│   │   └── Dockerfile
│   │
│   ├── activity_logger.py           # Python MCP tool logging
│   │
│   └── docker-compose.yml            # Service orchestration
```

### Database Schema

```sql
-- Agent Status
CREATE TABLE agent_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    status TEXT NOT NULL,  -- active, idle, blocked, completed
    current_task_id TEXT,
    progress TEXT,
    blockers TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(agent_id)
);

-- Agent Actions (Tool Calls)
CREATE TABLE agent_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    action_type TEXT NOT NULL,  -- mcp_tool, memory_query, memory_record, task_update
    tool_name TEXT,
    parameters TEXT,  -- JSON
    result_status TEXT,  -- success, error
    duration_ms INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent Sessions
CREATE TABLE agent_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_end TIMESTAMP,
    tasks_completed INTEGER DEFAULT 0,
    tools_called INTEGER DEFAULT 0
);
```

### Dashboard Features

**Main View:**
- **Active Agents** - List of all active agents with status
- **Recent Activity** - Live feed of all actions (tool calls, memory ops, task updates)
- **Task Overview** - Tasks by status, assignee
- **Agent Details** - Click agent to see:
  - Current task
  - Recent actions
  - Tool usage stats
  - Memory operations
  - Task history

**Visualizations:**
- Agent status cards (color-coded)
- Activity timeline
- Tool usage charts
- Task completion rates
- Agent activity heatmap

### Technology Stack

**Backend:**
- **Node.js** + **Express** + **TypeScript**
- **SQLite** (primary database)
- **InfluxDB** client (for metrics export)
- **Prisma** or **better-sqlite3** (SQLite ORM/driver)

**Frontend:**
- **Next.js 14+** (App Router)
- **TypeScript**
- **Tailwind CSS** (styling)
- **shadcn/ui** (UI components)
- **Recharts** or **Chart.js** (visualizations)

**Infrastructure:**
- **Docker Compose** (orchestration)
- **Traefik** (reverse proxy, already configured)
- **Grafana** (time-series dashboards)
- **InfluxDB** (time-series database, already running)

### Action Logging Strategy

**Automatic Logging via MCP Tools:**

1. **MCP Tool Wrapper** - Wrap all MCP tools to log calls:
   ```python
   @server.tool()
   async def docker_list_containers(...):
       start_time = time.time()
       try:
           result = await actual_docker_list_containers(...)
           log_action(agent_id, "mcp_tool", "docker_list_containers", success=True, duration=...)
           return result
       except Exception as e:
           log_action(agent_id, "mcp_tool", "docker_list_containers", success=False, error=str(e))
           raise
   ```

2. **Agent Status Updates** - New MCP tool:
   ```python
   update_agent_status(
       agent_id="agent-001",
       status="active",
       current_task_id="T1.3",
       progress="Setting up database schema",
       blockers=None
   )
   ```

3. **Memory Operations** - Already logged via memory tools, just need to track

4. **Task Updates** - Already logged via task coordination tools

### Integration Points

1. **Task Coordination System** - Link agent status to tasks
2. **Memory System** - Show memory operations per agent
3. **Agent Registry** - Link to agent definitions
4. **Homepage** - Add dashboard link to Homepage
5. **Grafana** - Export metrics to InfluxDB for time-series analysis
6. **InfluxDB** - Store time-series metrics (tool calls, agent activity, task completion rates)

### Dashboard UI Mockup

```
┌─────────────────────────────────────────────────────────┐
│  Agent Activity Dashboard                    [Refresh]  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Active Agents (3)                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ agent-001│  │ agent-002│  │ agent-003│             │
│  │ 🟢 Active│  │ 🟡 Idle  │  │ 🔴 Blocked│            │
│  │ Task: T1.3│ │ Task: -  │  │ Task: T2.1│            │
│  └──────────┘  └──────────┘  └──────────┘             │
│                                                          │
│  Recent Activity (Live Feed)                            │
│  ┌──────────────────────────────────────────────────┐ │
│  │ 10:23:45 agent-001 → docker_list_containers() ✅ │ │
│  │ 10:23:42 agent-001 → memory_query_decisions() ✅ │ │
│  │ 10:23:38 agent-003 → update_task_status(T2.1) ✅ │ │
│  │ 10:23:35 agent-001 → claim_task(T1.3) ✅         │ │
│  └──────────────────────────────────────────────────┘ │
│                                                          │
│  Task Overview                                          │
│  ┌──────────────────────────────────────────────────┐ │
│  │ In Progress: 5  │ Pending: 12  │ Completed: 23  │ │
│  └──────────────────────────────────────────────────┘ │
│                                                          │
│  Tool Usage (Last 24h)                                 │
│  ┌──────────────────────────────────────────────────┐ │
│  │ docker_list_containers: 45                        │ │
│  │ memory_query_decisions: 32                       │ │
│  │ update_task_status: 18                           │ │
│  └──────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Implementation Phases

#### Phase 1: Database + Logging (Day 1-2)
- Create SQLite database schema
- Implement Python action logger (`activity_logger.py`)
- Add logging wrapper to MCP tools
- Create `update_agent_status()` MCP tool
- Set up InfluxDB client and export functions

#### Phase 2: Backend API (Day 2-3)
- Set up Node.js + Express + TypeScript backend
- Create REST API endpoints:
  - `GET /api/agents` - List all agents with status
  - `GET /api/agents/:id` - Agent details
  - `GET /api/actions` - Recent actions (with pagination)
  - `GET /api/stats` - System statistics
  - `GET /api/tasks` - Task overview (integrate with task coordination)
  - `POST /api/influxdb/export` - Manual InfluxDB export
- SQLite database operations (Prisma or better-sqlite3)
- TypeScript types for all data structures

#### Phase 3: Frontend Dashboard (Day 3-4)
- Set up Next.js 14+ project with TypeScript
- Install Tailwind CSS and shadcn/ui
- Create main dashboard page:
  - Agent status cards
  - Activity feed component
  - Task overview component
  - Tool usage charts
- Create agent detail pages
- API client with TypeScript types
- Auto-refresh via polling (every 5-10 seconds)

#### Phase 4: Grafana Integration (Day 4-5)
- Set up InfluxDB export service
- Export metrics:
  - Agent activity (tool calls per agent)
  - Task completion rates
  - Memory operations
  - System-wide statistics
- Create Grafana dashboard:
  - Agent activity over time
  - Tool usage trends
  - Task completion metrics
  - System health indicators
- Configure automatic export (every 1-5 minutes)

#### Phase 5: Integration & Polish (Day 5)
- Integrate with Homepage (add link)
- Add to Traefik routing
- Update agent workflow docs
- Add Docker Compose configuration
- Create README with setup instructions

### Implementation Details

**Backend API Endpoints:**

```typescript
// GET /api/agents
interface Agent {
  id: string;
  status: 'active' | 'idle' | 'blocked' | 'completed';
  currentTaskId?: string;
  progress?: string;
  blockers?: string;
  lastUpdated: string;
}

// GET /api/agents/:id
interface AgentDetails extends Agent {
  recentActions: Action[];
  toolUsage: ToolUsage[];
  taskHistory: Task[];
  sessionStats: SessionStats;
}

// GET /api/actions?limit=50&agentId=...
interface Action {
  id: number;
  agentId: string;
  actionType: 'mcp_tool' | 'memory_query' | 'memory_record' | 'task_update';
  toolName?: string;
  parameters?: Record<string, any>;
  resultStatus: 'success' | 'error';
  durationMs?: number;
  timestamp: string;
}

// GET /api/stats
interface SystemStats {
  totalAgents: number;
  activeAgents: number;
  totalActions: number;
  actionsLast24h: number;
  toolUsage: Record<string, number>;
  taskStats: {
    pending: number;
    inProgress: number;
    completed: number;
  };
}
```

**InfluxDB Metrics Export:**

```typescript
// Metrics to export to InfluxDB
interface InfluxMetric {
  measurement: string;  // e.g., 'agent_actions', 'tool_usage', 'task_completion'
  tags: Record<string, string>;  // agent_id, tool_name, etc.
  fields: Record<string, number>;  // count, duration_ms, etc.
  timestamp: number;
}

// Example metrics:
// - agent_actions (count per agent per hour)
// - tool_usage (count per tool per hour)
// - task_completion_rate (tasks completed per hour)
// - agent_uptime (active time per agent)
```

**Docker Compose Configuration:**

```yaml
version: "3.8"
services:
  agent-monitoring-backend:
    build: ./backend
    environment:
      - DATABASE_PATH=/data/agent_activity.db
      - INFLUXDB_URL=http://influxdb:8086
      - INFLUXDB_DATABASE=agent_metrics
    volumes:
      - ./data:/data
    ports:
      - "3011:3001"
    networks:
      - my-network
    restart: unless-stopped

  agent-monitoring-frontend:
    build: ./frontend
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:3011
    ports:
      - "3012:3000"
    depends_on:
      - agent-monitoring-backend
    networks:
      - my-network
    restart: unless-stopped
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.agent-dashboard.rule=Host(`agent-dashboard.server.unarmedpuppy.com`)"
      - "traefik.http.routers.agent-dashboard.entrypoints=websecure"
      - "traefik.http.routers.agent-dashboard.tls.certresolver=myresolver"

networks:
  my-network:
    external: true
```

### Grafana Dashboard Panels

**Recommended Panels:**

1. **Agent Activity Over Time**
   - Line chart: Actions per agent per hour
   - Shows agent activity patterns

2. **Tool Usage Trends**
   - Bar chart: Most used tools (last 24h)
   - Line chart: Tool usage over time

3. **Task Completion Metrics**
   - Gauge: Tasks completed today
   - Line chart: Task completion rate over time

4. **Agent Status Distribution**
   - Pie chart: Active vs Idle vs Blocked agents

5. **System Health**
   - Single stat: Total active agents
   - Single stat: Actions in last hour
   - Single stat: Tasks in progress

### Next Steps

1. **Review and approve** this proposal
2. **Create project structure** following framework preferences
3. **Implement Phase 1** (Database + Logging)
4. **Iterate through phases** with testing at each step

### References

- **Framework Preferences**: `agents/docs/FRAMEWORK_PREFERENCES.md`
- **Next.js Docs**: https://nextjs.org/docs
- **InfluxDB Client**: https://github.com/influxdata/influxdb-client-js
- **Grafana Dashboard**: Use existing Grafana at port 3010

---

**Status**: Proposal (Revised)
**Technology Stack**: Next.js/TypeScript + Node.js + Grafana
**Effort**: 5 days
**Impact**: High (complete visibility into agent system with time-series analysis)

