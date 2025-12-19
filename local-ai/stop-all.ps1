# Stop script for Local AI infrastructure
# Stops the web dashboard and optionally the manager service

param(
    [switch]$StopManager = $false  # Also stop the manager service
)

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "Stopping Local AI infrastructure..." -ForegroundColor Yellow

# Stop web dashboard (find Python processes running gaming-mode-web.py)
$dashboardProcesses = Get-Process | Where-Object {
    $_.CommandLine -like "*gaming-mode-web.py*" -or
    ($_.ProcessName -eq "python" -or $_.ProcessName -eq "pythonw") -and
    (Get-WmiObject Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine -like "*gaming-mode-web.py*"
}

if ($dashboardProcesses) {
    Write-Host "Stopping web dashboard..." -ForegroundColor Yellow
    foreach ($proc in $dashboardProcesses) {
        try {
            Stop-Process -Id $proc.Id -Force
            Write-Host "  Stopped process: $($proc.Id)" -ForegroundColor Green
        } catch {
            Write-Host "  Could not stop process: $($proc.Id)" -ForegroundColor Red
        }
    }
} else {
    Write-Host "Web dashboard is not running." -ForegroundColor Gray
}

# Stop manager service if requested
if ($StopManager) {
    Write-Host "Stopping manager service..." -ForegroundColor Yellow
    docker compose down
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Manager service stopped." -ForegroundColor Green
    } else {
        Write-Host "Error stopping manager service." -ForegroundColor Red
    }
} else {
    Write-Host "Manager service left running. Use -StopManager to stop it." -ForegroundColor Gray
}

Write-Host ""
Write-Host "Stopped." -ForegroundColor Green

