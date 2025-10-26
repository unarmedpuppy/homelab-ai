# WireGuard Setup Helper Script for Windows
# This script helps configure WireGuard with DNS leak prevention

Write-Host "🔐 WireGuard Setup Helper" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host ""

# Check if docker-compose is available
$dockerCompose = Get-Command docker-compose -ErrorAction SilentlyContinue
if (-not $dockerCompose) {
    Write-Host "❌ docker-compose not found. Please install Docker Compose." -ForegroundColor Red
    exit 1
}

# Create directories
Write-Host "📁 Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path wireguard\config | Out-Null
New-Item -ItemType Directory -Force -Path downloads\nzb, downloads\torrents, downloads\completed | Out-Null
New-Item -ItemType Directory -Force -Path media\tv, media\movies, media\music, media\books | Out-Null

Write-Host "✅ Directories created" -ForegroundColor Green
Write-Host ""

# Start WireGuard to generate config
Write-Host "🚀 Starting WireGuard container to generate configuration..." -ForegroundColor Yellow
docker-compose up -d wireguard

Start-Sleep -Seconds 5

# Get the generated peer config
if (Test-Path "wireguard\config\peer1\peer1.conf") {
    Write-Host "📱 Config generated for mobile device:" -ForegroundColor Cyan
    Get-Content "wireguard\config\peer1\peer1.conf"
    Write-Host ""
    Write-Host "📋 Config location: wireguard\config\peer1\peer1.conf" -ForegroundColor Green
    Write-Host ""
    Write-Host "To add VPN provider config:" -ForegroundColor Yellow
    Write-Host "1. Get config from your VPN provider" -ForegroundColor White
    Write-Host "2. Edit wireguard\config\wg0.conf" -ForegroundColor White
    Write-Host "3. Add DNS servers to prevent leaks: DNS = 1.1.1.1, 9.9.9.9" -ForegroundColor White
    Write-Host ""
    Write-Host "🔒 DNS Leak Prevention:" -ForegroundColor Cyan
    Write-Host "   Make sure to set DNS servers in wireguard\config\wg0.conf" -ForegroundColor White
    Write-Host "   Recommended DNS: 1.1.1.1 (Cloudflare) or 9.9.9.9 (Quad9)" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "⚠️  No peer config found. You may need to:" -ForegroundColor Yellow
    Write-Host "1. Check logs: docker-compose logs wireguard" -ForegroundColor White
    Write-Host "2. Manually configure: wireguard\config\wg0.conf" -ForegroundColor White
}

Write-Host ""
Write-Host "✅ Setup complete! Next steps:" -ForegroundColor Green
Write-Host "1. Configure your VPN provider in wireguard\config\wg0.conf" -ForegroundColor White
Write-Host "2. Ensure DNS servers are set for leak prevention" -ForegroundColor White
Write-Host "3. Test VPN connection: docker exec media-download-wireguard wg show" -ForegroundColor White
Write-Host "4. Start other services: docker-compose up -d" -ForegroundColor White
Write-Host ""

