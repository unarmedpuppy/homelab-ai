# Local AI Manager Auto-Start Script
# Save as: start-local-ai-manager.ps1

Write-Host "🚀 Starting Local AI Manager..." -ForegroundColor Green

# Wait for Docker to be ready
$maxAttempts = 30
$attempt = 0

Write-Host "⏳ Waiting for Docker to be ready..." -ForegroundColor Yellow

do {
    try {
        $null = docker version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Docker is ready!" -ForegroundColor Green
            break
        }
    }
    catch {
        Write-Host "⏳ Waiting for Docker... (attempt $($attempt + 1)/$maxAttempts)" -ForegroundColor Yellow
        Start-Sleep -Seconds 2
        $attempt++
    }
} while ($attempt -lt $maxAttempts)

if ($attempt -eq $maxAttempts) {
    Write-Host "❌ Docker failed to start within timeout period" -ForegroundColor Red
    Write-Host "Please ensure Docker Desktop is running and try again" -ForegroundColor Red
    exit 1
}

# Navigate to local-ai directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Start the manager service
Write-Host "🔧 Starting Local AI Manager service..." -ForegroundColor Green
docker compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Local AI Manager started successfully!" -ForegroundColor Green
    Write-Host "🌐 Manager is running on port 8000" -ForegroundColor Cyan
    Write-Host "🤖 Available models: llama3-8b, qwen2.5-14b-awq, deepseek-coder, qwen-image-edit" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Test with: curl http://localhost:8000/healthz" -ForegroundColor White
} else {
    Write-Host "❌ Failed to start Local AI Manager" -ForegroundColor Red
    Write-Host "Check Docker Desktop is running and try again" -ForegroundColor Red
    exit 1
}
