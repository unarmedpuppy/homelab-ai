#!/bin/bash
# Homelab AI Dashboard Deployment Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Deploying Homelab AI Dashboard..."

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main

# Build if needed (for TypeScript/React apps)
echo "🔨 Building dashboard..."
if [ -f "dashboard/package.json" ]; then
    cd dashboard
    npm install
    npm run build
    cd ..
    echo "✅ Dashboard built successfully"
fi

# Copy built files if they exist
if [ -d "dashboard/dist" ]; then
    echo "📦 Copying built files..."
    cp -r dashboard/dist/* .
    rm -rf dashboard/dist
fi

echo "✅ Deployment complete!"
echo ""
echo "Dashboard is now available at:"
echo "  - Local: http://localhost:3000 (if running)"
echo "  - Server: https://dashboard.unarmedpuppy.com (if configured)"
echo ""
echo "View the cron jobs at: /cron-jobs"
