# VPN Verification Script for Windows
# Checks VPN connection, DNS leaks, and kill switch functionality

Write-Host "🔍 VPN Verification Script" -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor Cyan
Write-Host ""

# Check if WireGuard container is running
$wgRunning = docker ps --format "{{.Names}}" | Select-String "media-download-wireguard"

if (-not $wgRunning) {
    Write-Host "❌ WireGuard container is not running" -ForegroundColor Red
    Write-Host "   Start it with: docker-compose up -d wireguard" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ WireGuard container is running" -ForegroundColor Green
Write-Host ""

# Check VPN connection
Write-Host "🔌 Checking VPN connection..." -ForegroundColor Yellow
try {
    $wgStatus = docker exec media-download-wireguard wg show 2>&1
    if ($wgStatus -like "*interface*") {
        Write-Host "✅ VPN interface is active" -ForegroundColor Green
        Write-Host $wgStatus
    } else {
        Write-Host "⚠️  VPN interface not configured properly" -ForegroundColor Yellow
        Write-Host "   Check: docker-compose logs wireguard" -ForegroundColor Gray
    }
} catch {
    Write-Host "⚠️  Could not check VPN status" -ForegroundColor Yellow
}
Write-Host ""

# Test DNS servers
Write-Host "🌐 Checking DNS configuration..." -ForegroundColor Yellow
docker exec media-download-wireguard cat /etc/resolv.conf
Write-Host ""

# Test DNS leak
Write-Host "🔍 Testing for DNS leaks..." -ForegroundColor Yellow
Write-Host "Your public IP (should be VPN IP):" -ForegroundColor Gray
try {
    $ip = docker exec media-download-wireguard curl -s ifconfig.me 2>&1
    Write-Host $ip -ForegroundColor Cyan
} catch {
    Write-Host "Failed to get IP" -ForegroundColor Red
}
Write-Host ""

Write-Host "DNS servers visible from VPN container:" -ForegroundColor Gray
try {
    docker exec media-download-wireguard dig google.com 2>&1 | Select-String "SERVER:"
} catch {
    Write-Host "Could not check DNS" -ForegroundColor Yellow
}
Write-Host ""

# Test network isolation (kill switch)
Write-Host "🛡️ Testing Kill Switch..." -ForegroundColor Yellow
Write-Host "Attempting to ping from download container (should fail if kill switch works)..." -ForegroundColor Gray
$killSwitchTest = docker exec media-download-nzbget ping -c 1 -W 2 8.8.8.8 2>&1
if ($LASTEXITCODE -eq 0 -or $killSwitchTest -like "*success*" -or $killSwitchTest -like "*packet*") {
    Write-Host "⚠️  WARNING: Kill switch may not be working properly" -ForegroundColor Yellow
    Write-Host "   Containers can still access internet directly" -ForegroundColor Yellow
} else {
    Write-Host "✅ Kill switch is working - containers isolated from direct internet" -ForegroundColor Green
}
Write-Host ""

# Check download containers can reach internet through VPN
Write-Host "🔗 Testing VPN tunnel..." -ForegroundColor Yellow
try {
    docker exec media-download-wireguard ping -c 1 -W 2 1.1.1.1 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ VPN tunnel is working" -ForegroundColor Green
    } else {
        Write-Host "❌ VPN tunnel is not working" -ForegroundColor Red
        Write-Host "   Check your VPN provider configuration" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ VPN tunnel is not working" -ForegroundColor Red
}
Write-Host ""

# Summary
Write-Host "📊 Summary" -ForegroundColor Cyan
Write-Host "==========" -ForegroundColor Cyan
if ($wgStatus -like "*interface*") {
    Write-Host "✅ VPN: Connected" -ForegroundColor Green
} else {
    Write-Host "❌ VPN: Not connected" -ForegroundColor Red
}

$internetTest = docker exec media-download-wireguard ping -c 1 -W 2 1.1.1.1 2>&1
if ($LASTEXITCODE -eq 0 -or $internetTest -like "*success*") {
    Write-Host "✅ Internet: Accessible through VPN" -ForegroundColor Green
} else {
    Write-Host "❌ Internet: Not accessible" -ForegroundColor Red
}

if ($killSwitchTest -and ($LASTEXITCODE -eq 0 -or $killSwitchTest -like "*success*")) {
    Write-Host "⚠️  Kill Switch: May not be working" -ForegroundColor Yellow
} else {
    Write-Host "✅ Kill Switch: Working" -ForegroundColor Green
}

Write-Host ""
Write-Host "💡 Tips:" -ForegroundColor Cyan
Write-Host "   - If VPN is not connected, check wireguard\config\wg0.conf" -ForegroundColor White
Write-Host "   - If DNS is leaking, add DNS servers to WireGuard config" -ForegroundColor White
Write-Host "   - Run: docker-compose logs wireguard for more details" -ForegroundColor White
Write-Host ""

