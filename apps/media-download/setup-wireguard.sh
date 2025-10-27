#!/bin/bash
# WireGuard Setup Helper Script
# This script helps configure WireGuard with DNS leak prevention

set -e

echo "🔐 WireGuard Setup Helper"
echo "========================="
echo ""

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install Docker Compose."
    exit 1
fi

# Create directories
echo "📁 Creating directories..."
mkdir -p wireguard/config
mkdir -p downloads/{nzb,torrents,completed}
mkdir -p media/{tv,movies,music,books}

echo "✅ Directories created"
echo ""

# Start WireGuard to generate config
echo "🚀 Starting WireGuard container to generate configuration..."
docker-compose up -d wireguard

sleep 5

# Get the generated peer config
if [ -f "wireguard/config/peer1/peer1.conf" ]; then
    echo "📱 QR Code generated for mobile device:"
    docker exec media-download-wireguard cat /config/peer1/peer1.conf | grep -A 10 "^#[=]*$" | head -20
    echo ""
    
    cat wireguard/config/peer1/peer1.conf
    echo ""
    
    echo "📋 Config location: wireguard/config/peer1/peer1.conf"
    echo ""
    echo "To add VPN provider config:"
    echo "1. Get config from your VPN provider"
    echo "2. Edit wireguard/config/wg0.conf"
    echo "3. Add DNS servers to prevent leaks: DNS = 1.1.1.1, 9.9.9.9"
    echo ""
    echo "🔒 DNS Leak Prevention:"
    echo "   Make sure to set DNS servers in wireguard/config/wg0.conf"
    echo "   Recommended DNS: 1.1.1.1 (Cloudflare) or 9.9.9.9 (Quad9)"
    echo ""
else
    echo "⚠️  No peer config found. You may need to:"
    echo "1. Check logs: docker-compose logs wireguard"
    echo "2. Manually configure: wireguard/config/wg0.conf"
fi

echo ""
echo "✅ Setup complete! Next steps:"
echo "1. Configure your VPN provider in wireguard/config/wg0.conf"
echo "2. Ensure DNS servers are set for leak prevention"
echo "3. Test VPN connection: docker exec media-download-wireguard wg show"
echo "4. Start other services: docker-compose up -d"
echo ""
echo "🔍 To test for DNS leaks:"
echo "   docker exec media-download-wireguard dig @1.1.1.1 example.com"
echo ""

