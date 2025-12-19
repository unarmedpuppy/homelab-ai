# Gaming Mode & Resource Management

This document explains how to manage GPU resources when using your PC for gaming or other GPU-intensive tasks.

## Overview

The Local AI Manager includes several features to help you manage GPU memory:

1. **Automatic Idle Timeout**: Models automatically stop after 10 minutes of inactivity (configurable via `IDLE_TIMEOUT`)
2. **Gaming Mode**: Prevents new models from starting while enabled
3. **Status Monitoring**: Check what's loaded and if it's safe to game
4. **Force Stop**: Manually stop all running models

## Quick Start

### Web Dashboard (Recommended)

The easiest way to manage gaming mode is with the web dashboard:

```powershell
# Windows PowerShell
.\gaming-mode-web.ps1

# Linux/WSL Bash
./gaming-mode-web.sh
```

Then open your browser to: **http://localhost:8080**

The web dashboard provides:
- **Real-time status** - Auto-refreshes every 2 seconds
- **Visual indicators** - Color-coded status (green = safe, red = not safe)
- **One-click controls** - Toggle gaming mode, stop all models
- **Running models list** - See what's loaded with idle times
- **Connection status** - Shows if manager is reachable
- **Network access** - Access from any device on your network

**Features:**
- Modern, responsive design
- Works on desktop, tablet, and mobile
- No installation required (just Python + Flask)
- Accessible from any browser

### Desktop GUI (Alternative)

If you prefer a desktop application:

```powershell
# Windows PowerShell
.\gaming-mode-gui.ps1

# Linux/WSL Bash
./gaming-mode-gui.sh
```

**Features:**
- Dark theme for easy viewing
- No installation required (uses built-in tkinter)
- Lightweight (~400x500 window)
- Auto-refreshes status

### Command Line

### Check if Safe to Game

```powershell
# PowerShell (Windows)
.\control-gaming-mode.ps1 safe

# Bash (Linux/WSL)
./control-gaming-mode.sh safe
```

This will tell you if any models are running and consuming GPU memory.

### Before Gaming

1. **Stop all models** (recommended):
   ```powershell
   .\control-gaming-mode.ps1 stop-all
   ```

2. **Enable gaming mode** (prevents new requests from starting models):
   ```powershell
   .\control-gaming-mode.ps1 enable
   ```

3. **Verify it's safe**:
   ```powershell
   .\control-gaming-mode.ps1 safe
   ```

### After Gaming

Disable gaming mode to allow models to start again:

```powershell
.\control-gaming-mode.ps1 disable
```

## API Endpoints

The manager exposes several endpoints for programmatic control:

### GET `/status`

Get detailed status of all models and gaming mode.

**Response:**
```json
{
  "gaming_mode": false,
  "safe_to_game": true,
  "running_models": [],
  "stopped_models": [
    {
      "name": "llama3-8b",
      "type": "text",
      "status": "stopped"
    }
  ],
  "idle_timeout_seconds": 600,
  "summary": {
    "total_models": 4,
    "running": 0,
    "stopped": 4
  }
}
```

### POST `/gaming-mode`

Enable or disable gaming mode.

**Request:**
```json
{
  "enable": true
}
```

**Response:**
```json
{
  "gaming_mode": true,
  "previous_mode": false,
  "message": "Gaming mode enabled. New model requests will be blocked."
}
```

**Query Parameter Alternative:**
```
POST /gaming-mode?enable=true
POST /gaming-mode?enable=false
```

### POST `/stop-all`

Force stop all running model containers.

**Response:**
```json
{
  "stopped": ["llama3-8b", "qwen2.5-14b-awq"],
  "failed": [],
  "message": "Stopped 2 model(s). All models stopped successfully."
}
```

## GUI Application

### Launching the GUI

**Windows:**
```powershell
.\gaming-mode-gui.ps1
```

**Linux/WSL:**
```bash
./gaming-mode-gui.sh
```

**Direct Python:**
```bash
python gaming-mode-gui.py
# or
python3 gaming-mode-gui.py
```

### GUI Requirements

- Python 3.7+ (usually pre-installed on Windows/Linux)
- `requests` library (auto-installed by launcher scripts)
- `tkinter` (usually included with Python)

If `tkinter` is missing:
- **Windows**: Usually included, but if missing, reinstall Python with "tcl/tk" option
- **Linux**: `sudo apt-get install python3-tk` (Ubuntu/Debian)

### GUI Features

1. **Status Panel**
   - Gaming mode state (enabled/disabled)
   - Safe to game indicator
   - Connection status

2. **Running Models List**
   - Shows all currently loaded models
   - Displays model type and idle time
   - Updates automatically

3. **Control Buttons**
   - **Enable/Disable Gaming Mode** - Toggle to block/allow new models
   - **Stop All Models** - Force stop all running models
   - **Refresh Status** - Manual refresh (auto-refreshes every 2 seconds)

4. **Visual Feedback**
   - Green = Safe/Enabled/Good
   - Red = Not Safe/Error
   - Blue = Gaming mode enabled
   - Auto-refreshes every 2 seconds

## Control Scripts

### PowerShell (`control-gaming-mode.ps1`)

```powershell
# Check status
.\control-gaming-mode.ps1 status

# Enable gaming mode
.\control-gaming-mode.ps1 enable

# Disable gaming mode
.\control-gaming-mode.ps1 disable

# Stop all models
.\control-gaming-mode.ps1 stop-all

# Check if safe to game
.\control-gaming-mode.ps1 safe
```

### Bash (`control-gaming-mode.sh`)

```bash
# Check status
./control-gaming-mode.sh status

# Enable gaming mode
./control-gaming-mode.sh enable

# Disable gaming mode
./control-gaming-mode.sh disable

# Stop all models
./control-gaming-mode.sh stop-all

# Check if safe to game
./control-gaming-mode.sh safe
```

## How It Works

### Automatic Idle Timeout

The manager runs a background task that checks every 10 seconds for idle models. If a model hasn't been used for `IDLE_TIMEOUT` seconds (default: 600 = 10 minutes), it automatically stops the container.

**Configuration:**
- Set `IDLE_TIMEOUT` environment variable in `docker-compose.yml`
- Default: 600 seconds (10 minutes)
- Set to 0 to disable automatic stopping

### Gaming Mode

When gaming mode is enabled:
- **New model requests are blocked** - If someone tries to use a model that isn't already running, they'll get a 503 error
- **Already running models continue** - Models that are already loaded will continue to work
- **No automatic stopping** - Gaming mode doesn't stop existing models, it just prevents new ones

**Use Cases:**
- You're about to start gaming and want to prevent models from auto-starting
- You're doing GPU-intensive work and want to reserve GPU memory
- You want to ensure no new models start while you're away

### Status Monitoring

The `/status` endpoint provides:
- Current gaming mode state
- List of running models with idle time
- List of stopped models
- Whether it's safe to game (no models running + gaming mode disabled)

## Example Workflow

### Scenario: You want to game

```powershell
# 1. Check current status
.\control-gaming-mode.ps1 status

# 2. Stop all running models
.\control-gaming-mode.ps1 stop-all

# 3. Enable gaming mode (prevents new requests)
.\control-gaming-mode.ps1 enable

# 4. Verify it's safe
.\control-gaming-mode.ps1 safe
# Output: ✓ SAFE TO GAME

# 5. Start your game...

# 6. After gaming, disable gaming mode
.\control-gaming-mode.ps1 disable
```

### Scenario: Quick check before gaming

```powershell
# One command to check if safe
.\control-gaming-mode.ps1 safe

# If not safe, it will tell you what's running
# Then you can stop them:
.\control-gaming-mode.ps1 stop-all
.\control-gaming-mode.ps1 enable
```

## Integration with Other Tools

### Monitor Status Continuously

```powershell
# PowerShell
while ($true) {
    Clear-Host
    .\control-gaming-mode.ps1 status
    Start-Sleep -Seconds 5
}
```

### Check Before Running GPU-Intensive App

```powershell
# In your script
$status = Invoke-RestMethod http://localhost:8000/status
if (-not $status.safe_to_game) {
    Write-Host "Models are running! Stopping..."
    Invoke-RestMethod -Method Post http://localhost:8000/stop-all
    Invoke-RestMethod -Method Post http://localhost:8000/gaming-mode -Body '{"enable":true}' -ContentType "application/json"
}
```

## Troubleshooting

### Models Still Starting Despite Gaming Mode

- Check gaming mode is actually enabled: `.\control-gaming-mode.ps1 status`
- Verify the manager is running: `docker ps | grep vllm-manager`
- Check manager logs: `docker logs vllm-manager --tail 50`

### Can't Connect to Manager

- Ensure manager is running: `docker ps | grep vllm-manager`
- Check manager is accessible: `curl http://localhost:8000/healthz`
- Verify port 8000 is not blocked by firewall

### Models Not Stopping

- Check idle timeout setting: `docker exec vllm-manager env | grep IDLE_TIMEOUT`
- Verify models are actually idle (check `last_used` in status)
- Manually stop: `.\control-gaming-mode.ps1 stop-all`

## Configuration

### Adjust Idle Timeout

Edit `local-ai/docker-compose.yml`:

```yaml
environment:
  - IDLE_TIMEOUT=300  # 5 minutes instead of 10
```

Then restart the manager:
```bash
docker compose restart manager
```

### Disable Automatic Stopping

Set `IDLE_TIMEOUT=0` to disable automatic stopping (models will stay loaded until manually stopped).

## Best Practices

1. **Before Gaming**: Always run `stop-all` and `enable` gaming mode
2. **After Gaming**: Disable gaming mode to allow normal operation
3. **Monitor Regularly**: Use `status` to see what's loaded
4. **Set Reasonable Timeout**: 10 minutes is usually good, adjust based on your usage
5. **Use Safe Check**: The `safe` command is your friend - use it before gaming

## See Also

- [README.md](README.md) - Main documentation
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
- [TESTING.md](TESTING.md) - Testing guide

