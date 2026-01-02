# PowerShell script to build image inference server
# Builds the Docker image for the image model inference server

Write-Host "Building image inference server..." -ForegroundColor Cyan

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$imageServerPath = Join-Path $scriptPath "image-inference-server"

# Check if Dockerfile exists
if (-not (Test-Path (Join-Path $imageServerPath "Dockerfile"))) {
    Write-Host "Error: Dockerfile not found in image-inference-server/" -ForegroundColor Red
    exit 1
}

# Change to image-inference-server directory
Push-Location $imageServerPath

# Build the image
Write-Host "Building Docker image: image-inference-server:latest" -ForegroundColor Yellow
docker build -t image-inference-server:latest .

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[OK] Image built successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Run setup.sh to create the container"
    Write-Host "2. Or manually create container (see README.md)"
} else {
    Write-Host "Error: Build failed" -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location

