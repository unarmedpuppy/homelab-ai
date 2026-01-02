# Setup script to configure Local AI to start on Windows boot
# Run this script once to configure automatic startup
# Requires: Administrator privileges

param(
    [switch]$NoDashboard = $false  # Don't start web dashboard on boot
)

# Check for admin privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "This script requires Administrator privileges." -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    exit 1
}

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$startupScript = Join-Path $scriptPath "start-all.ps1"
$taskName = "LocalAI-Startup"

Write-Host "Setting up Local AI automatic startup..." -ForegroundColor Green
Write-Host ""

# Verify startup script exists
if (-not (Test-Path $startupScript)) {
    Write-Host "ERROR: Startup script not found at: $startupScript" -ForegroundColor Red
    exit 1
}

# Remove existing task if it exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Create the scheduled task
Write-Host "Creating scheduled task..." -ForegroundColor Yellow

$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$startupScript`"" -WorkingDirectory $scriptPath

$trigger = New-ScheduledTaskTrigger -AtLogOn

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable:$false

$description = "Starts Local AI infrastructure (Docker containers and web dashboard) on system boot"

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description $description | Out-Null

Write-Host ""
Write-Host "✓ Scheduled task created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Task Details:" -ForegroundColor Cyan
Write-Host "  Name: $taskName" -ForegroundColor White
Write-Host "  Trigger: At logon" -ForegroundColor White
Write-Host "  Script: $startupScript" -ForegroundColor White
Write-Host ""
Write-Host "The Local AI infrastructure will now start automatically when you log in." -ForegroundColor Green
Write-Host ""
Write-Host "To test the startup script manually:" -ForegroundColor Yellow
Write-Host "  .\start-all.ps1" -ForegroundColor White
Write-Host ""
Write-Host "To remove the startup task:" -ForegroundColor Yellow
Write-Host "  Unregister-ScheduledTask -TaskName `"$taskName`" -Confirm:`$false" -ForegroundColor White
Write-Host ""
Write-Host "To view/edit the task:" -ForegroundColor Yellow
Write-Host "  taskschd.msc" -ForegroundColor White
Write-Host "  (Then search for: $taskName)" -ForegroundColor White

