# Trading Bot Dashboard - Access Information

## 🌐 How to Access

### Main Dashboard
**URL**: `http://localhost:8021`  
**Alternative**: `http://192.168.86.47:8021` (from other devices on your network)

### Other Endpoints
- **Scheduler Dashboard**: `http://localhost:8021/scheduler`
- **API Documentation**: `http://localhost:8021/docs`
- **Health Check**: `http://localhost:8021/health`
- **API Base**: `http://localhost:8021/api`

### Monitoring Services
- **Grafana**: `http://localhost:3002` (metrics visualization)
- **Prometheus**: `http://localhost:9091` (metrics collection)
- **Alertmanager**: `http://localhost:9094` (alert management)

## 🔧 Port Mapping

The container runs on port 8000 internally and is exposed as port 8021 on your host:
- **Internal**: `0.0.0.0:8000` (inside container)
- **External**: `localhost:8021` (your machine)

This avoids conflicts with other services that might use ports 8000, 9090, 3000, etc.

## 📋 Quick Access Commands

```bash
# Open dashboard in default browser (Mac)
open http://localhost:8021

# Open dashboard in default browser (Linux)
xdg-open http://localhost:8021

# Check if service is running
curl http://localhost:8021/health

# Check container status
docker-compose ps
```

## 🚨 Troubleshooting

### Can't Access Dashboard?

1. **Check if container is running**:
   ```bash
   docker-compose ps
   ```
   Should show `Up` status for `bot` service

2. **Check container logs**:
   ```bash
   docker-compose logs bot --tail 50
   ```

3. **Verify port is accessible**:
   ```bash
   curl http://localhost:8021/health
   ```

4. **Check firewall** (if accessing from another device):
   - Port 8021 needs to be open
   - Use `http://192.168.86.47:8021` (your local IP)

### Container Not Starting?

If the container is restarting or crashed:
```bash
# Rebuild and restart
docker-compose build bot
docker-compose up -d bot

# Check logs for errors
docker-compose logs bot
```

## 📱 Homepage Integration

If you have a homepage service running, the trading bot should appear under the "Trading Bot" group with:
- **Name**: Trading Bot API
- **Icon**: TradingView icon
- **URL**: `http://192.168.86.47:8021`

