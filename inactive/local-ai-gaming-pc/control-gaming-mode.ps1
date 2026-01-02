# Control script for Local AI Gaming Mode
# Usage:
#   .\control-gaming-mode.ps1 status          # Check current status
#   .\control-gaming-mode.ps1 enable          # Enable gaming mode (block new models)
#   .\control-gaming-mode.ps1 disable          # Disable gaming mode (allow new models)
#   .\control-gaming-mode.ps1 stop-all         # Force stop all running models
#   .\control-gaming-mode.ps1 safe            # Check if safe to game

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("status", "enable", "disable", "stop-all", "safe")]
    [string]$Action
)

$MANAGER_URL = "http://localhost:8000"

function Get-Status {
    try {
        $response = Invoke-RestMethod -Uri "$MANAGER_URL/status" -Method Get
        return $response
    } catch {
        Write-Host "Error: Could not connect to manager at $MANAGER_URL" -ForegroundColor Red
        Write-Host "Make sure the manager is running: docker ps | grep vllm-manager" -ForegroundColor Yellow
        exit 1
    }
}

function Set-GamingMode {
    param([bool]$Enable)
    
    try {
        $body = @{ enable = $Enable } | ConvertTo-Json
        $response = Invoke-RestMethod -Uri "$MANAGER_URL/gaming-mode" -Method Post -Body $body -ContentType "application/json"
        return $response
    } catch {
        Write-Host "Error: Could not set gaming mode" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        exit 1
    }
}

function Stop-AllModels {
    try {
        $response = Invoke-RestMethod -Uri "$MANAGER_URL/stop-all" -Method Post
        return $response
    } catch {
        Write-Host "Error: Could not stop models" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        exit 1
    }
}

function Format-Status {
    param($status)
    
    Write-Host "`n=== Local AI Manager Status ===" -ForegroundColor Cyan
    Write-Host "Gaming Mode: " -NoNewline
    if ($status.gaming_mode) {
        Write-Host "ENABLED (new models blocked)" -ForegroundColor Yellow
    } else {
        Write-Host "DISABLED (new models allowed)" -ForegroundColor Green
    }
    
    Write-Host "`nSafe to Game: " -NoNewline
    if ($status.safe_to_game) {
        Write-Host "YES ✓" -ForegroundColor Green
    } else {
        Write-Host "NO ✗" -ForegroundColor Red
        if ($status.running_models.Count -gt 0) {
            Write-Host "  Reason: $($status.running_models.Count) model(s) still running" -ForegroundColor Yellow
        }
        if ($status.gaming_mode) {
            Write-Host "  Reason: Gaming mode is enabled (this is fine if you're gaming)" -ForegroundColor Yellow
        }
    }
    
    Write-Host "`nRunning Models: $($status.running_models.Count)" -ForegroundColor Cyan
    if ($status.running_models.Count -gt 0) {
        foreach ($model in $status.running_models) {
            $idle = if ($model.idle_seconds) { "$($model.idle_seconds)s idle" } else { "active" }
            Write-Host "  - $($model.name) ($($model.type)) - $idle" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  (none)" -ForegroundColor Gray
    }
    
    Write-Host "`nStopped Models: $($status.stopped_models.Count)" -ForegroundColor Cyan
    if ($status.stopped_models.Count -gt 0) {
        foreach ($model in $status.stopped_models) {
            Write-Host "  - $($model.name) ($($model.type))" -ForegroundColor Gray
        }
    }
    
    Write-Host "`nIdle Timeout: $($status.idle_timeout_seconds)s ($([math]::Round($status.idle_timeout_seconds / 60, 1)) minutes)" -ForegroundColor Cyan
    Write-Host ""
}

switch ($Action) {
    "status" {
        $status = Get-Status
        Format-Status $status
    }
    
    "enable" {
        Write-Host "Enabling gaming mode..." -ForegroundColor Yellow
        $result = Set-GamingMode -Enable $true
        Write-Host "Gaming mode ENABLED" -ForegroundColor Green
        Write-Host "  New model requests will be blocked." -ForegroundColor Yellow
        Write-Host "  Use '.\control-gaming-mode.ps1 disable' to allow models again." -ForegroundColor Gray
    }
    
    "disable" {
        Write-Host "Disabling gaming mode..." -ForegroundColor Yellow
        $result = Set-GamingMode -Enable $false
        Write-Host "Gaming mode DISABLED" -ForegroundColor Green
        Write-Host "  New model requests will be allowed." -ForegroundColor Yellow
    }
    
    "stop-all" {
        Write-Host "Stopping all running models..." -ForegroundColor Yellow
        $result = Stop-AllModels
        if ($result.stopped.Count -gt 0) {
            Write-Host "Stopped $($result.stopped.Count) model(s):" -ForegroundColor Green
            foreach ($model in $result.stopped) {
                Write-Host "  - $model" -ForegroundColor Gray
            }
        } else {
            Write-Host "No models were running." -ForegroundColor Gray
        }
        if ($result.failed.Count -gt 0) {
            Write-Host "`nFailed to stop:" -ForegroundColor Red
            foreach ($fail in $result.failed) {
                Write-Host "  - $($fail.model): $($fail.error)" -ForegroundColor Red
            }
        }
    }
    
    "safe" {
        $status = Get-Status
        if ($status.safe_to_game) {
            Write-Host "`n✓ SAFE TO GAME" -ForegroundColor Green
            Write-Host "  No models are running and gaming mode is disabled." -ForegroundColor Gray
            exit 0
        } else {
            Write-Host "`n✗ NOT SAFE TO GAME" -ForegroundColor Red
            if ($status.running_models.Count -gt 0) {
                Write-Host "  $($status.running_models.Count) model(s) are still running:" -ForegroundColor Yellow
                foreach ($model in $status.running_models) {
                    Write-Host "    - $($model.name)" -ForegroundColor Yellow
                }
                Write-Host "`n  Run '.\control-gaming-mode.ps1 stop-all' to stop them." -ForegroundColor Gray
            }
            if ($status.gaming_mode) {
                Write-Host "  Gaming mode is enabled (this is fine if you're already gaming)." -ForegroundColor Yellow
            }
            exit 1
        }
    }
}

