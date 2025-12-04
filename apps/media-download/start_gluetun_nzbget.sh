#!/bin/bash
# Quick script to start gluetun and nzbget containers

echo "Starting gluetun and nzbget containers..."
cd "$(dirname "$0")"
docker-compose up -d gluetun nzbget

echo ""
echo "Waiting for containers to start..."
sleep 5

echo ""
echo "Container status:"
docker-compose ps gluetun nzbget

echo ""
echo "Testing NZBGet connection..."
sleep 2
curl -s -u nzbget:nzbget "http://localhost:6789/jsonrpc?version=1.1&method=status&id=1" | head -c 200
echo ""

