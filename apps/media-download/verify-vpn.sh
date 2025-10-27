#!/bin/bash
# VPN Verification Script
# Checks VPN connection, DNS leaks, and kill switch functionality

set -e

echo "🔍 VPN Verification Script"
echo "=========================="
echo ""

# Check if WireGuard container is running
if ! docker ps | grep -q media-download-wireguard; then
    echo "❌ WireGuard container is not running"
    echo "   Start it with: docker-compose up -d wireguard"
    exit 1
fi

echo "✅ WireGuard container is running"
echo ""

# Check VPN connection
echo "🔌 Checking VPN connection..."
wg_status=$(docker exec media-download-wireguard wg show 2>/dev/null || echo "not running")

if echo "$wg_status" | grep -q "interface"; then
    echo "✅ VPN interface is active"
    echo "$wg_status"
else
    echo "⚠️  VPN interface not configured properly"
    echo "   Check: docker-compose logs wireguard"
fi
echo ""

# Test DNS servers
echo "🌐 Checking DNS configuration..."
docker exec media-download-wireguard cat /etc/resolv.conf
echo ""

# Test DNS leak
echo "🔍 Testing for DNS leaks..."
echo "Your public IP (should be VPN IP):"
docker exec media-download-wireguard curl -s ifconfig.me 2>/dev/null || echo "Failed to get IP"
echo ""

echo "DNS servers visible from VPN container:"
docker exec media-download-wireguard dig google.com | grep "SERVER:"
echo ""

# Test network isolation (kill switch)
echo "🛡️ Testing Kill Switch..."
echo "Attempting to ping from download container (should fail if kill switch works)..."
if docker exec media-download-nzbget ping -c 1 -W 2 8.8.8.8 &> /dev/null; then
    echo "⚠️  WARNING: Kill switch may not be working properly"
    echo "   Containers can still access internet directly"
else
    echo "✅ Kill switch is working - containers isolated from direct internet"
fi
echo ""

# Check download containers can reach internet through VPN
echo "🔗 Testing VPN tunnel..."
if docker exec media-download-wireguard ping -c 1 -W 2 1.1.1.1 &> /dev/null; then
    echo "✅ VPN tunnel is working"
else
    echo "❌ VPN tunnel is not working"
    echo "   Check your VPN provider configuration"
fi
echo ""

# Summary
echo "📊 Summary"
echo "=========="
if echo "$wg_status" | grep -q "interface"; then
    echo "✅ VPN: Connected"
else
    echo "❌ VPN: Not connected"
fi

if docker exec media-download-wireguard ping -c 1 -W 2 1.1.1.1 &> /dev/null; then
    echo "✅ Internet: Accessible through VPN"
else
    echo "❌ Internet: Not accessible"
fi

if docker exec media-download-nzbget ping -c 1 -W 2 8.8.8.8 &> /dev/null 2>&1; then
    echo "⚠️  Kill Switch: May not be working"
else
    echo "✅ Kill Switch: Working"
fi

echo ""
echo "💡 Tips:"
echo "   - If VPN is not connected, check wireguard/config/wg0.conf"
echo "   - If DNS is leaking, add DNS servers to WireGuard config"
echo "   - Run: docker-compose logs wireguard for more details"
echo ""

