# Agent Monitoring Dashboard

Self-contained monitoring system for AI agents with Grafana integration.

## Overview

This service provides:
- **Real-time Agent Status**: See which agents are active, what they're working on
- **Activity Tracking**: Log all MCP tool calls, memory operations, and task updates
- **Visual Dashboard**: Next.js dashboard with live updates
- **Grafana Integration**: Time-series metrics and professional dashboards
- **Self-Contained**: Everything runs in Docker Compose

## Architecture

- **Backend**: Node.js + Express + TypeScript (REST API)
- **Frontend**: Next.js 14+ + TypeScript (Dashboard UI)
- **Database**: SQLite (primary) + InfluxDB (metrics export)
- **Visualization**: Grafana with pre-configured dashboards
- **Logging**: Python activity logger (integrated with MCP tools)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Ports available: 3001 (backend), 3010 (Grafana), 3012 (frontend), 8086 (InfluxDB)

### Setup

1. **Copy environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Configure environment variables** (optional, defaults work for local dev):
   - Edit `.env` if you need custom ports or credentials

3. **Start all services**:
   ```bash
   docker-compose up -d
   ```

4. **Access services**:
   - Frontend Dashboard: http://localhost:3012
   - Backend API: http://localhost:3001
   - Grafana: http://localhost:3010 (admin/admin123)
   - InfluxDB: http://localhost:8086

### First Time Setup

1. **Grafana Login**:
   - URL: http://localhost:3010
   - Username: `admin`
   - Password: `admin123`
   - The InfluxDB data source is automatically configured

2. **View Dashboards**:
   - Go to Dashboards → Browse
   - "Agent Monitoring Dashboard" should be available
   - Metrics will start appearing after agents log activity

3. **InfluxDB Setup** (if needed):
   - URL: http://localhost:8086
   - Username: `admin`
   - Password: `admin123`
   - Organization: `home-server`
   - Bucket: `agent_metrics`

## Services

### Backend API (`backend/`)
- REST API for agent status, actions, and statistics
- Automatic metric export to InfluxDB (every 30s)
- SQLite database operations
- See `backend/README.md` for details

### Frontend Dashboard (`frontend/`)
- Next.js dashboard with real-time updates
- Agent overview and detail pages
- Activity feed with auto-refresh
- See `frontend/README.md` for details

### Grafana (`grafana/`)
- Pre-configured InfluxDB data source
- Pre-built dashboards for agent monitoring
- Customizable visualizations
- Located in `grafana/` directory

### InfluxDB
- Time-series database for metrics
- Automatic data retention
- Pre-configured with organization and bucket

## Development

### Running Locally (without Docker)

```bash
# Backend
cd backend
npm install
npm run dev

# Frontend (in another terminal)
cd frontend
npm install
npm run dev

# Note: You'll need to set up InfluxDB and Grafana separately
```

### Building for Production

```bash
# Build all services
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Configuration

### Environment Variables

See `.env.example` for all available options:

- `BACKEND_PORT` - Backend API port (default: 3001)
- `FRONTEND_PORT` - Frontend port (default: 3012)
- `GRAFANA_PORT` - Grafana port (default: 3010)
- `INFLUXDB_URL` - InfluxDB connection URL
- `INFLUXDB_TOKEN` - InfluxDB authentication token
- `METRIC_EXPORT_INTERVAL` - How often to export metrics (ms, default: 30000)

### Grafana Dashboards

Dashboards are located in `grafana/dashboards/`:
- `agent-monitoring.json` - Main dashboard with agent metrics

To add custom dashboards:
1. Create dashboard in Grafana UI
2. Export as JSON
3. Save to `grafana/dashboards/`
4. Restart Grafana service

## Status

**Phase 1**: ✅ Database + Logging (Complete)
**Phase 2**: ✅ Backend API (Complete)
**Phase 3**: ✅ Frontend Dashboard (Complete)
**Phase 4**: ✅ Grafana Integration (Complete)
- ✅ Docker Compose setup with all services
- ✅ InfluxDB configuration
- ✅ Grafana with pre-configured data source
- ✅ Automatic metric export from backend
- ✅ Pre-built dashboards

**Phase 5**: ✅ Integration & Polish (Complete)
- ✅ Homepage integration (automatic service discovery)
- ✅ Traefik integration (reverse proxy with HTTPS)
- ✅ Performance optimizations (in-memory caching)
- ✅ UI improvements (loading states, Grafana links)
- ✅ Comprehensive documentation (integration guide)
- ✅ Production-ready configuration

---

**Last Updated**: 2025-01-13
