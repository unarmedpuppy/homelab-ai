# Automatic Startup Guide

This guide explains how to set up the Local AI infrastructure to start automatically when Windows boots.

## What Starts Automatically

When configured, the following will start on boot:

1. **Docker Desktop** - If not already running
2. **Manager Service** - Docker container (`vllm-manager`) on port 8000
3. **Web Dashboard** - Docker container (`local-ai-dashboard`) on port 8080
4. **Model Containers** - Start on-demand when models are requested

## Quick Setup

### Option A: Simple Setup (No Admin Required) ⭐ Recommended

**Run this script (no admin needed):**
```powershell
cd local-ai
.\setup-startup-simple.ps1
```

This creates a shortcut in your Startup folder. Services will start automatically when you log in.

**See [MANUAL_STARTUP_SETUP.md](MANUAL_STARTUP_SETUP.md) for more options.**

### Option B: Task Scheduler (Requires Admin)

### 1. Enable Docker Desktop Auto-Start

1. Open Docker Desktop
2. Go to **Settings** → **General**
3. Check **"Start Docker Desktop when you log in"**
4. Click **Apply & Restart**

### 2. Configure Windows Task Scheduler

Run the setup script as Administrator:

```powershell
# Run PowerShell as Administrator
cd local-ai
.\setup-startup.ps1
```

This will:
- Create a scheduled task that runs on login
- Start Docker Desktop (if needed)
- Start the manager and web dashboard via `docker compose up -d`

**Note:** If you can't run as admin, use Option A instead.

### 3. Verify Setup

After setup, test it:

```powershell
# Test the startup script manually
.\start-all.ps1

# Check if services are running
docker ps

# Test the manager
curl http://localhost:8000/healthz

# Test the dashboard
curl http://localhost:8080
```

## Manual Startup

If you prefer to start manually:

```powershell
cd local-ai
docker compose up -d
```

This starts both the manager and web dashboard automatically.

## Access Points

Once started, you can access:

- **Manager API**: http://localhost:8000
- **Web Dashboard**: http://localhost:8080
- **Health Check**: http://localhost:8000/healthz

## Stopping Services

To stop everything:

```powershell
cd local-ai
docker compose down
```

Or use the stop script:

```powershell
.\stop-all.ps1
```

## Troubleshooting

### Services Don't Start on Boot

1. **Check Task Scheduler:**
   - Press `Win + R`, type `taskschd.msc`
   - Look for task: `LocalAI-Startup`
   - Check if it's enabled and ran successfully

2. **Check Startup Log:**
   ```powershell
   cat local-ai/startup.log
   ```

3. **Check Docker:**
   ```powershell
   docker ps
   docker logs vllm-manager
   docker logs local-ai-dashboard
   ```

### Docker Desktop Not Starting

- Ensure Docker Desktop is set to auto-start (Settings → General)
- Check if Docker Desktop service is running: `Get-Service *docker*`
- Try starting Docker Desktop manually first

### Port Already in Use

If ports 8000 or 8080 are already in use:

```powershell
# Find what's using the port
netstat -ano | findstr :8000
netstat -ano | findstr :8080

# Stop the conflicting service or change ports in docker-compose.yml
```

### Manager Not Responding

```powershell
# Check manager logs
docker logs vllm-manager --tail 50

# Restart manager
docker compose restart manager
```

### Web Dashboard Not Accessible

```powershell
# Check dashboard logs
docker logs local-ai-dashboard --tail 50

# Restart dashboard
docker compose restart web-dashboard

# Verify it can reach the manager
docker exec local-ai-dashboard curl http://vllm-manager:8000/healthz
```

## Removing Auto-Start

To remove the automatic startup:

```powershell
# Remove the scheduled task
Unregister-ScheduledTask -TaskName "LocalAI-Startup" -Confirm:$false
```

## Files Reference

- `start-all.ps1` - Main startup script
- `setup-startup.ps1` - Configures Windows Task Scheduler
- `stop-all.ps1` - Stops all services
- `docker-compose.yml` - Defines manager and web dashboard services
- `startup.log` - Log file created by startup script

## Next Steps

1. **Set up auto-start** using `setup-startup.ps1`
2. **Test the setup** by restarting your computer
3. **Bookmark** http://localhost:8080 for easy access
4. **Monitor** using the web dashboard

## See Also

- [README.md](README.md) - Main documentation
- [GAMING_MODE.md](GAMING_MODE.md) - Gaming mode documentation
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide

