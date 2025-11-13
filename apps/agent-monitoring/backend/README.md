# Agent Monitoring Backend

Node.js + Express + TypeScript backend API for agent monitoring dashboard.

## Features

- REST API for agent status, actions, and statistics
- SQLite database operations
- InfluxDB export for Grafana integration
- Task coordination system integration

## API Endpoints

### Agents
- `GET /api/agents` - List all agents (optional `?status=active`)
- `GET /api/agents/:id` - Get agent details with recent actions and stats

### Actions
- `GET /api/actions` - Get actions with filters
  - Query params: `limit`, `offset`, `agentId`, `actionType`, `toolName`, `startTime`, `endTime`
- `GET /api/actions/recent` - Get actions from last 24 hours

### Statistics
- `GET /api/stats` - Get system-wide statistics
- `GET /api/stats/tool-usage` - Get tool usage statistics (optional `?agentId=...&limit=20`)

### Tasks
- `GET /api/tasks` - Get task overview from task coordination system

### InfluxDB Export
- `POST /api/influxdb/export` - Export all metrics to InfluxDB
- `POST /api/influxdb/export/actions` - Export agent actions (body: `{hours: 1}`)
- `POST /api/influxdb/export/status` - Export agent status

### Health
- `GET /health` - Health check endpoint

## Development

### Setup

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
```

### Run

```bash
# Development (with hot reload)
npm run dev

# Production build
npm run build
npm start
```

### Environment Variables

- `PORT` - Server port (default: 3001)
- `DATABASE_PATH` - Path to SQLite database
- `INFLUXDB_URL` - InfluxDB URL (optional)
- `INFLUXDB_TOKEN` - InfluxDB token (optional)
- `INFLUXDB_ORG` - InfluxDB organization (optional)
- `INFLUXDB_DATABASE` - InfluxDB database name (optional)

## Docker

```bash
# Build
docker build -t agent-monitoring-backend .

# Run
docker run -p 3001:3001 \
  -v $(pwd)/../../data:/data \
  -e DATABASE_PATH=/data/agent_activity.db \
  agent-monitoring-backend
```

## Testing

See `API_TESTING.md` for comprehensive test results and validation.

### Quick Test

```bash
# Start server
npm run dev

# Test endpoints
curl http://localhost:3001/health
curl http://localhost:3001/api/agents
curl http://localhost:3001/api/stats
```

## Improvements Made

- ✅ Input validation for all query parameters
- ✅ Error handling with try-catch for JSON parsing
- ✅ Pagination limits (max 1000 items)
- ✅ Task route filters placeholder rows
- ✅ Request logging for development
- ✅ Comprehensive error messages

---

**Status**: Phase 2 Complete ✅

