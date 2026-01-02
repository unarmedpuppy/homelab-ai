# Startup script for Local AI infrastructure
# This script starts:
# 1. Docker Desktop (if not running)
# 2. Manager service (docker compose)
# 3. Web dashboard (gaming-mode-web.py)
#
# To run on startup, add this script to Windows Task Scheduler

param(
    [switch]$NoDashboard = $false  # Skip starting the web dashboard
)

$ErrorActionPreference = "Continue"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$logFile = Join-Path $scriptPath "startup.log"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Add-Content -Path $logFile -Value $logMessage
    Write-Host $logMessage
}

Write-Log "=== Local AI Startup Script ==="

# Change to script directory
Set-Location $scriptPath
Write-Log "Working directory: $scriptPath"

# 1. Check and start Docker Desktop
Write-Log "Checking Docker Desktop..."
$dockerRunning = docker ps 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Log "Docker Desktop is not running. Attempting to start..."
    
    # Try to start Docker Desktop
    $dockerDesktopPath = "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dockerDesktopPath) {
        Start-Process -FilePath $dockerDesktopPath
        Write-Log "Docker Desktop start command issued. Waiting for it to start..."
        
        # Wait up to 60 seconds for Docker to be ready
        $maxWait = 60
        $waited = 0
        while ($waited -lt $maxWait) {
            Start-Sleep -Seconds 2
            $waited += 2
            $dockerCheck = docker ps 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Log "Docker Desktop is now running!"
                break
            }
        }
        
        if ($waited -ge $maxWait) {
            Write-Log "WARNING: Docker Desktop may not be fully started. Continuing anyway..."
        }
    } else {
        Write-Log "WARNING: Docker Desktop not found at expected path. Please start it manually."
    }
} else {
    Write-Log "Docker Desktop is already running."
}

# 2. Start manager service (docker compose)
Write-Log "Starting manager service..."
try {
    docker compose up -d
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Manager service started successfully."
        
        # Wait a moment for the service to initialize
        Start-Sleep -Seconds 3
        
        # Check if manager is responding
        $maxWait = 30
        $waited = 0
        while ($waited -lt $maxWait) {
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:8000/healthz" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
                if ($response.StatusCode -eq 200) {
                    Write-Log "Manager service is responding."
                    break
                }
            } catch {
                # Manager not ready yet
            }
            Start-Sleep -Seconds 2
            $waited += 2
        }
        
        if ($waited -ge $maxWait) {
            Write-Log "WARNING: Manager service may not be fully ready. Check logs with: docker logs vllm-manager"
        }
    } else {
        Write-Log "ERROR: Failed to start manager service. Check docker compose logs."
    }
} catch {
    Write-Log "ERROR starting manager service: $($_.Exception.Message)"
}

# 3. Web dashboard is now part of docker-compose, so it starts automatically with manager
# No manual start needed!

Write-Log "=== Startup Complete ==="
Write-Log "Manager: http://localhost:8000"
Write-Log "Dashboard: http://localhost:8080 (auto-started with docker-compose)"
Write-Log "Log file: $logFile"

