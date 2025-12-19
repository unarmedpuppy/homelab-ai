# Startup Configuration Status

## Current Setup

**Date Configured:** 2025-12-16

**Method:** Startup Folder (Simple - No Admin Required)

**Status:** ✅ Configured

The Local AI infrastructure is configured to start automatically when you log in.

## What Was Set Up

A shortcut was created in the Windows Startup folder:
- **Location:** `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Local AI Startup.lnk`
- **Runs:** `start-all.ps1` on login
- **Starts:**
  - Docker Desktop (if not running)
  - Manager service (vllm-manager on port 8000)
  - Web dashboard (local-ai-dashboard on port 8080)

## To Remove Auto-Start Later

If you want to stop the automatic startup, run:

```powershell
Remove-Item "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\Local AI Startup.lnk"
```

Or manually:
1. Press `Win + R`
2. Type: `shell:startup`
3. Delete the "Local AI Startup" shortcut

## Manual Start/Stop

**Start manually:**
```powershell
cd local-ai
.\start-all.ps1
```

**Stop services:**
```powershell
cd local-ai
docker compose down
```

**Or use the stop script:**
```powershell
.\stop-all.ps1
```

## Verification

To verify services are running:
```powershell
docker ps
```

Should show:
- `vllm-manager` (port 8000)
- `local-ai-dashboard` (port 8080)

## Access Points

- **Manager API:** http://localhost:8000
- **Web Dashboard:** http://localhost:8080
- **Health Check:** http://localhost:8000/healthz

