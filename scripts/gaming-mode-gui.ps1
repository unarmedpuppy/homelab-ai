# Launcher script for Gaming Mode GUI
# Usage: .\gaming-mode-gui.ps1

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$guiScript = Join-Path $scriptPath "gaming-mode-gui.py"

# Check if Python is available
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command python3 -ErrorAction SilentlyContinue
}

if (-not $python) {
    Write-Host "Error: Python not found. Please install Python 3.7+ and ensure it's in your PATH." -ForegroundColor Red
    exit 1
}

# Check if requests library is available
$requestsCheck = & $python.Source -c "import requests" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing required 'requests' library..." -ForegroundColor Yellow
    & $python.Source -m pip install requests --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to install 'requests' library." -ForegroundColor Red
        Write-Host "Try running: pip install requests" -ForegroundColor Yellow
        exit 1
    }
}

# Run the GUI
Write-Host "Starting Gaming Mode GUI..." -ForegroundColor Green
& $python.Source $guiScript

