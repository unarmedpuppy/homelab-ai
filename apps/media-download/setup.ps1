# Complete Media Download System Setup for Windows
# This script sets up the entire system with all dependencies

Write-Host "🎬 Media Download System Setup" -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "🔍 Checking prerequisites..." -ForegroundColor Yellow

$docker = Get-Command docker -ErrorAction SilentlyContinue
if (-not $docker) {
    Write-Host "❌ Docker not installed. Please install Docker first." -ForegroundColor Red
    exit 1
}

$dockerCompose = Get-Command docker-compose -ErrorAction SilentlyContinue
if (-not $dockerCompose) {
    Write-Host "❌ docker-compose not found. Please install Docker Compose." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Docker and docker-compose found" -ForegroundColor Green
Write-Host ""

# Create all required directories
Write-Host "📁 Creating directory structure..." -ForegroundColor Yellow

$dirs = @(
    "wireguard\config",
    "nzbhydra2\config", "nzbhydra2\data",
    "jackett\config",
    "nzbget\config",
    "qbittorrent\config",
    "sabnzbd\config",
    "sonarr\config",
    "radarr\config",
    "lidarr\config",
    "bazarr\config",
    "readarr\config",
    "downloads\nzb", "downloads\torrents", "downloads\completed", "downloads\sabnzbd",
    "media\tv", "media\movies", "media\music", "media\books"
)

foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

Write-Host "✅ Directories created" -ForegroundColor Green
Write-Host ""

# Copy environment template if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "📝 Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.template" ".env"
    Write-Host "✅ Please edit .env with your configuration" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "✅ .env already exists" -ForegroundColor Green
    Write-Host ""
}

# Pull images
Write-Host "📥 Pulling Docker images..." -ForegroundColor Yellow
docker-compose pull
Write-Host "✅ Images pulled" -ForegroundColor Green
Write-Host ""

# Start WireGuard first
Write-Host "🚀 Starting WireGuard (VPN Gateway)..." -ForegroundColor Yellow
docker-compose up -d wireguard
Start-Sleep -Seconds 5

Write-Host "⏳ Waiting for WireGuard to be ready..." -ForegroundColor Yellow

$timeout = 60
$counter = 0
$ready = $false

while (-not $ready -and $counter -lt $timeout) {
    try {
        $result = docker exec media-download-wireguard wg 2>&1
        if ($result -like "*interface*") {
            $ready = $true
        }
    } catch {
        # Continue waiting
    }
    Start-Sleep -Seconds 1
    $counter++
}

if (-not $ready) {
    Write-Host "⚠️  WireGuard may not be fully configured yet" -ForegroundColor Yellow
    Write-Host "   You may need to manually configure the VPN connection" -ForegroundColor Yellow
} else {
    Write-Host "✅ WireGuard is ready" -ForegroundColor Green
}
Write-Host ""

# Display next steps
Write-Host "🎉 Setup Complete!" -ForegroundColor Green
Write-Host "==================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Configure WireGuard with your VPN provider:" -ForegroundColor White
Write-Host "   - Edit wireguard\config\wg0.conf" -ForegroundColor Gray
Write-Host "   - Add DNS servers for leak prevention: DNS = 1.1.1.1, 9.9.9.9" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Test VPN connection:" -ForegroundColor White
Write-Host "   docker exec media-download-wireguard wg show" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Start all services:" -ForegroundColor White
Write-Host "   docker-compose up -d" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Access web UIs:" -ForegroundColor White
Write-Host "   - NZBHydra2: http://localhost:5076" -ForegroundColor Gray
Write-Host "   - Jackett: http://localhost:9117" -ForegroundColor Gray
Write-Host "   - Sonarr: http://localhost:8989" -ForegroundColor Gray
Write-Host "   - Radarr: http://localhost:7878" -ForegroundColor Gray
Write-Host "   - Lidarr: http://localhost:8686" -ForegroundColor Gray
Write-Host "   - Bazarr: http://localhost:6767" -ForegroundColor Gray
Write-Host "   - qBittorrent: http://localhost:8080" -ForegroundColor Gray
Write-Host ""
Write-Host "📚 See README.md for detailed configuration instructions" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔒 Security Reminders:" -ForegroundColor Yellow
Write-Host "   - Never expose ports to the internet" -ForegroundColor White
Write-Host "   - Use strong passwords for all services" -ForegroundColor White
Write-Host "   - Verify kill switch is working" -ForegroundColor White
Write-Host "   - Monitor for DNS leaks" -ForegroundColor White
Write-Host ""

