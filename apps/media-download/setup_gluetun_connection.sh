#!/bin/bash
# Complete setup script for gluetun and nzbget connection
# This script starts containers, verifies connections, and fixes configuration

set -e

echo "============================================================"
echo "Gluetun & NZBGet Connection Setup"
echo "============================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Server connection details
SERVER_USER="unarmedpuppy"
SERVER_HOST="192.168.86.47"
SERVER_PORT="4242"
SERVER_PATH="~/server/apps/media-download"

# Function to run command on server
run_on_server() {
    ssh -p "$SERVER_PORT" "$SERVER_USER@$SERVER_HOST" "$1"
}

# Step 1: Start containers
echo "[1/5] Starting gluetun and nzbget containers..."
run_on_server "cd $SERVER_PATH && docker-compose up -d gluetun nzbget"

# Wait for containers to start
echo "Waiting 10 seconds for containers to initialize..."
sleep 10

# Step 2: Check container status
echo ""
echo "[2/5] Checking container status..."
CONTAINER_STATUS=$(run_on_server "cd $SERVER_PATH && docker-compose ps gluetun nzbget | grep -E '(gluetun|nzbget)' | grep -c 'Up' || echo '0'")

if [ "$CONTAINER_STATUS" -ge "2" ]; then
    echo -e "${GREEN}✓ Both containers are running${NC}"
else
    echo -e "${RED}✗ Containers may not be running properly${NC}"
    echo "Checking detailed status..."
    run_on_server "cd $SERVER_PATH && docker-compose ps gluetun nzbget"
    exit 1
fi

# Step 3: Test NZBGet connection
echo ""
echo "[3/5] Testing NZBGet connection via gluetun..."
NZBGET_TEST=$(run_on_server "curl -s -u nzbget:nzbget 'http://localhost:6789/jsonrpc?version=1.1&method=status&id=1' | head -c 100" || echo "FAILED")

if [[ "$NZBGET_TEST" == *"result"* ]] || [[ "$NZBGET_TEST" == *"version"* ]]; then
    echo -e "${GREEN}✓ NZBGet is accessible via gluetun${NC}"
else
    echo -e "${YELLOW}⚠ NZBGet connection test inconclusive (may need more time to start)${NC}"
fi

# Step 4: Fix Sonarr and Radarr configuration
echo ""
echo "[4/5] Verifying Sonarr and Radarr configuration..."
echo "Running configuration fix script..."

# Run the Python fix script on the server
run_on_server "cd $SERVER_PATH && python3 check_and_fix_gluetun_connection.py" || {
    echo -e "${YELLOW}⚠ Could not run fix script automatically${NC}"
    echo "You may need to run it manually or fix via web UI"
}

# Step 5: Verify Docker auto-start
echo ""
echo "[5/5] Verifying Docker auto-start configuration..."
DOCKER_ENABLED=$(run_on_server "systemctl is-enabled docker 2>/dev/null || echo 'unknown'")

if [ "$DOCKER_ENABLED" == "enabled" ]; then
    echo -e "${GREEN}✓ Docker is enabled to start on boot${NC}"
else
    echo -e "${YELLOW}⚠ Docker may not start automatically on boot${NC}"
    echo "To enable: sudo systemctl enable docker"
fi

# Final summary
echo ""
echo "============================================================"
echo "Setup Complete!"
echo "============================================================"
echo ""
echo "Container Status:"
run_on_server "cd $SERVER_PATH && docker-compose ps gluetun nzbget | grep -E '(gluetun|nzbget|NAME)'"
echo ""
echo "Next steps:"
echo "1. Check Sonarr: http://192.168.86.47:8989"
echo "2. Check Radarr: http://192.168.86.47:7878"
echo "3. Verify download clients show 'Connected' status"
echo ""
echo "If issues persist, check logs:"
echo "  docker logs media-download-gluetun"
echo "  docker logs media-download-nzbget"

