# Simple startup setup - NO ADMIN REQUIRED
# Uses Windows Startup Folder (runs when you log in)

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$startupFolder = [Environment]::GetFolderPath("Startup")
$startupScript = Join-Path $scriptPath "start-all.ps1"

Write-Host "Setting up Local AI automatic startup (Simple Method)..." -ForegroundColor Green
Write-Host ""

# Verify startup script exists
if (-not (Test-Path $startupScript)) {
    Write-Host "ERROR: Startup script not found at: $startupScript" -ForegroundColor Red
    exit 1
}

# Create a shortcut in the Startup folder
$shortcutPath = Join-Path $startupFolder "Local AI Startup.lnk"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$startupScript`""
$shortcut.WorkingDirectory = $scriptPath
$shortcut.Description = "Starts Local AI infrastructure on login"
$shortcut.Save()

# Create status file
$statusFile = Join-Path $scriptPath "STARTUP_STATUS.md"
$statusContent = @"
# Startup Configuration Status

## Current Setup

**Date Configured:** $(Get-Date -Format "yyyy-MM-dd")

**Method:** Startup Folder (Simple - No Admin Required)

**Status:** ✅ Configured

The Local AI infrastructure is configured to start automatically when you log in.

## What Was Set Up

A shortcut was created in the Windows Startup folder:
- **Location:** `$shortcutPath`
- **Runs:** `start-all.ps1` on login
- **Starts:**
  - Docker Desktop (if not running)
  - Manager service (vllm-manager on port 8000)
  - Web dashboard (local-ai-dashboard on port 8080)

## To Remove Auto-Start Later

If you want to stop the automatic startup, run:

\`\`\`powershell
Remove-Item `"$shortcutPath`"
\`\`\`

Or manually:
1. Press `Win + R`
2. Type: `shell:startup`
3. Delete the "Local AI Startup" shortcut

## Manual Start/Stop

**Start manually:**
\`\`\`powershell
cd local-ai
.\start-all.ps1
\`\`\`

**Stop services:**
\`\`\`powershell
cd local-ai
docker compose down
\`\`\`

**Or use the stop script:**
\`\`\`powershell
.\stop-all.ps1
\`\`\`

## Verification

To verify services are running:
\`\`\`powershell
docker ps
\`\`\`

Should show:
- `vllm-manager` (port 8000)
- `local-ai-dashboard` (port 8080)

## Access Points

- **Manager API:** http://localhost:8000
- **Web Dashboard:** http://localhost:8080
- **Health Check:** http://localhost:8000/healthz
"@
Set-Content -Path $statusFile -Value $statusContent

Write-Host "✓ Startup shortcut created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Location: $shortcutPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "The Local AI infrastructure will now start automatically when you log in." -ForegroundColor Green
Write-Host ""
Write-Host "To test the startup script manually:" -ForegroundColor Yellow
Write-Host "  .\start-all.ps1" -ForegroundColor White
Write-Host ""
Write-Host "To remove the startup:" -ForegroundColor Yellow
Write-Host "  Remove-Item `"$shortcutPath`"" -ForegroundColor White
Write-Host ""
Write-Host "📝 Status saved to: STARTUP_STATUS.md" -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: This method requires you to be logged in." -ForegroundColor Gray
Write-Host "For startup without login, use Task Scheduler (requires admin)." -ForegroundColor Gray

