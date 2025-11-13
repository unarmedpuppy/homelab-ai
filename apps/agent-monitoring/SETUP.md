# Agent Monitoring Setup Guide

Complete setup guide for the self-contained agent monitoring system.

## Prerequisites

- Docker and Docker Compose installed
- Ports available: 3001, 3011, 3012, 8087

## Quick Start

1. **Navigate to the directory**:
   ```bash
   cd apps/agent-monitoring
   ```

2. **Copy environment file** (optional):
   ```bash
   cp .env.example .env
   ```
   Edit `.env` if you need custom configuration.

3. **Start all services**:
   ```bash
   docker-compose up -d
   ```

4. **Wait for services to be healthy** (about 30 seconds):
   ```bash
   docker-compose ps
   ```

5. **Access the services**:
   - **Frontend Dashboard**: http://localhost:3012
   - **Backend API**: http://localhost:3001
   - **Grafana**: http://localhost:3011 (admin/admin123)
   - **InfluxDB**: http://localhost:8087 (admin/admin123)

## First Time Setup

### Grafana

1. Open http://localhost:3011
2. Login with:
   - Username: `admin`
   - Password: `admin123`
3. The InfluxDB data source is automatically configured
4. Go to **Dashboards → Browse**
5. You should see "Agent Monitoring Dashboard"
6. Open it to view metrics (will populate as agents log activity)

### InfluxDB (if needed)

1. Open http://localhost:8087
2. Login with:
   - Username: `admin`
   - Password: `admin123`
3. Organization: `home-server`
4. Bucket: `agent_metrics`

## Verifying Setup

### Check Backend
```bash
curl http://localhost:3001/health
# Should return: {"status":"ok",...}
```

### Check Frontend
Open http://localhost:3012 in your browser

### Check Grafana
Open http://localhost:3011 and login

### Check InfluxDB
```bash
curl http://localhost:8087/api/v2/health
# Should return: {"status":"pass",...}
```

## Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f grafana
docker-compose logs -f influxdb
```

## Stopping Services

```bash
docker-compose down
```

## Data Persistence

All data is persisted in Docker volumes:
- `influxdb-data` - InfluxDB data
- `grafana-data` - Grafana dashboards and settings
- `./data/` - SQLite database (mounted from host)

## Troubleshooting

### Services won't start
- Check if ports are already in use
- Check Docker logs: `docker-compose logs`
- Verify Docker and Docker Compose are running

### No metrics in Grafana
- Wait a few minutes for agents to log activity
- Check backend logs for export errors
- Verify InfluxDB is healthy: `docker-compose ps`

### Backend can't connect to InfluxDB
- Check InfluxDB is running: `docker-compose ps influxdb`
- Verify environment variables in `docker-compose.yml`
- Check backend logs: `docker-compose logs backend`

## Customization

### Change Ports
Edit `docker-compose.yml` and change the port mappings:
```yaml
ports:
  - "YOUR_PORT:3001"  # Backend
  - "YOUR_PORT:3011"  # Grafana
  - "YOUR_PORT:3012"  # Frontend
```

### Change Credentials
1. Edit `docker-compose.yml` environment variables
2. Update `grafana/provisioning/datasources/influxdb.yml` with new token
3. Restart services: `docker-compose restart`

### Add Custom Dashboards
1. Create dashboard in Grafana UI
2. Export as JSON
3. Save to `grafana/dashboards/`
4. Restart Grafana: `docker-compose restart grafana`

---

For more details, see the main [README.md](README.md).

