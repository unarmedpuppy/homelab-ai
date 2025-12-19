# Launcher script for Gaming Mode Web Dashboard
# Usage: .\gaming-mode-web.ps1
# Then open: http://localhost:8080

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$webScript = Join-Path $scriptPath "gaming-mode-web.py"

# Check if Python is available
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command python3 -ErrorAction SilentlyContinue
}

if (-not $python) {
    Write-Host "Error: Python not found. Please install Python 3.7+ and ensure it's in your PATH." -ForegroundColor Red
    exit 1
}

# Check if Flask library is available
$flaskCheck = & $python.Source -c "import flask" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing required 'flask' library..." -ForegroundColor Yellow
    & $python.Source -m pip install flask requests --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to install 'flask' library." -ForegroundColor Red
        Write-Host "Try running: pip install flask requests" -ForegroundColor Yellow
        exit 1
    }
}

# Run the web server
Write-Host "Starting Gaming Mode Web Dashboard..." -ForegroundColor Green
Write-Host "Open your browser to: http://localhost:8080" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""
& $python.Source $webScript

