# Agent Monitoring Dashboard

Real-time monitoring and activity tracking for all AI agents in the home server system.

## Overview

This service provides:
- **Real-time Agent Status**: See which agents are active, what they're working on
- **Activity Tracking**: Log all MCP tool calls, memory operations, and task updates
- **Visual Dashboard**: Next.js dashboard with live updates
- **Grafana Integration**: Time-series metrics exported to InfluxDB

## Architecture

- **Backend**: Node.js + Express + TypeScript (REST API)
- **Frontend**: Next.js 14+ + TypeScript (Dashboard UI)
- **Database**: SQLite (primary) + InfluxDB (metrics export)
- **Logging**: Python activity logger (integrated with MCP tools)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Access to InfluxDB (for Grafana integration)

### Setup

1. **Copy environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Configure environment variables** (see `.env.example`)

3. **Start services**:
   ```bash
   docker-compose up -d
   ```

4. **Access dashboard**:
   - Frontend: http://localhost:3012
   - Backend API: http://localhost:3011
   - Or via Traefik: http://agent-dashboard.server.unarmedpuppy.com

## Development

See individual README files in:
- `backend/README.md` - Backend development
- `frontend/README.md` - Frontend development
- `activity_logger/README.md` - MCP tool integration

## Status

**Phase 1**: ✅ Database + Logging (Complete)
- ✅ SQLite database schema created
- ✅ Activity logger Python module implemented
- ✅ MCP tools for agent status updates
- ✅ Database operations tested and working

**Phase 2**: ✅ Backend API (Complete)
- ✅ Node.js + Express + TypeScript backend
- ✅ REST API endpoints (agents, actions, stats, tasks, influxdb)
- ✅ SQLite database service
- ✅ InfluxDB export service
- ✅ Dockerfile and build configuration
- ✅ All endpoints tested and working

**Phase 3**: ✅ Frontend Dashboard (Complete)
- ✅ Next.js 14+ with TypeScript and Tailwind CSS
- ✅ Main dashboard with agent overview and activity feed
- ✅ Agent detail pages with stats and history
- ✅ Real-time auto-refresh (5s intervals)
- ✅ Responsive design
- ✅ Server-side rendering
**Phase 4**: ⏳ Grafana Integration
**Phase 5**: ⏳ Integration & Polish

---

**Last Updated**: 2025-01-13

