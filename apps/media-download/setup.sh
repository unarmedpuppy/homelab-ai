#!/bin/bash
# Complete Media Download System Setup
# This script sets up the entire system with all dependencies

set -e

echo "🎬 Media Download System Setup"
echo "==============================="
echo ""

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install Docker Compose."
    exit 1
fi

echo "✅ Docker and docker-compose found"
echo ""

# Create all required directories
echo "📁 Creating directory structure..."
mkdir -p wireguard/config
mkdir -p nzbhydra2/{config,data}
mkdir -p jackett/config
mkdir -p nzbget/config
mkdir -p qbittorrent/config
mkdir -p sabnzbd/config
mkdir -p sonarr/config
mkdir -p radarr/config
mkdir -p lidarr/config
mkdir -p bazarr/config
mkdir -p readarr/config
mkdir -p downloads/{nzb,torrents,completed,sabnzbd}
mkdir -p media/{tv,movies,music,books}

echo "✅ Directories created"
echo ""

# Copy environment template if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.template .env
    echo "✅ Please edit .env with your configuration"
    echo ""
else
    echo "✅ .env already exists"
    echo ""
fi

# Set permissions
echo "🔐 Setting permissions..."
chmod -R 755 ./
echo "✅ Permissions set"
echo ""

# Pull images
echo "📥 Pulling Docker images..."
docker-compose pull
echo "✅ Images pulled"
echo ""

# Start WireGuard first
echo "🚀 Starting WireGuard (VPN Gateway)..."
docker-compose up -d wireguard
sleep 5

# Wait for WireGuard to be healthy
echo "⏳ Waiting for WireGuard to be ready..."
timeout=60
counter=0
while ! docker exec media-download-wireguard wg &> /dev/null; do
    if [ $counter -ge $timeout ]; then
        echo "❌ WireGuard failed to start"
        exit 1
    fi
    sleep 1
    counter=$((counter+1))
done

echo "✅ WireGuard is ready"
echo ""

# Display next steps
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "Next steps:"
echo "1. Configure WireGuard with your VPN provider:"
echo "   - Edit wireguard/config/wg0.conf"
echo "   - Add DNS servers for leak prevention: DNS = 1.1.1.1, 9.9.9.9"
echo ""
echo "2. Test VPN connection:"
echo "   docker exec media-download-wireguard wg show"
echo ""
echo "3. Start all services:"
echo "   docker-compose up -d"
echo ""
echo "4. Access web UIs:"
echo "   - NZBHydra2: http://localhost:5076"
echo "   - Jackett: http://localhost:9117"
echo "   - Sonarr: http://localhost:8989"
echo "   - Radarr: http://localhost:7878"
echo "   - Lidarr: http://localhost:8686"
echo "   - Bazarr: http://localhost:6767"
echo "   - qBittorrent: http://localhost:8080"
echo ""
echo "5. Configure services:"
echo "   - Add Usenet provider to NZBGet"
echo "   - Add indexers to NZBHydra2 and Jackett"
echo "   - Configure Sonarr/Radarr/Lidarr with indexers"
echo ""
echo "📚 See README.md for detailed configuration instructions"
echo ""
echo "🔒 Security Reminders:"
echo "   - Never expose ports to the internet"
echo "   - Use strong passwords for all services"
echo "   - Verify kill switch is working"
echo "   - Monitor for DNS leaks"
echo ""

