#!/bin/bash
#
# Safe deployment script for polymarket-bot
#
# This script checks for active trades before deploying to prevent
# interrupting trades that are awaiting market resolution.
#
# Usage:
#   ./agents/skills/deploy-polymarket-bot/deploy.sh          # Normal deploy
#   ./agents/skills/deploy-polymarket-bot/deploy.sh --force  # Skip safety check
#
# Exit codes:
#   0 - Deployment successful
#   1 - Blocked by active trades (use --force to override)
#   2 - Deployment failed

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
FORCE=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --force|-f)
            FORCE=true
            shift
            ;;
    esac
done

echo "═══════════════════════════════════════════════════════════════"
echo "  POLYMARKET BOT DEPLOYMENT"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Step 1: Check for active trades (unless --force)
if [ "$FORCE" = false ]; then
    echo "🔍 Checking for active trades..."
    echo ""

    # Run the check via SSH
    if ! "$REPO_ROOT/scripts/connect-server.sh" "docker exec polymarket-bot python3 /app/scripts/check_active_trades.py 2>/dev/null"; then
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 1 ]; then
            echo ""
            echo "═══════════════════════════════════════════════════════════════"
            echo "  ⛔ DEPLOYMENT BLOCKED - ACTIVE TRADES DETECTED"
            echo "═══════════════════════════════════════════════════════════════"
            echo ""
            echo "Wait for trades to resolve or use --force to override:"
            echo "  $SCRIPT_DIR/deploy.sh --force"
            echo ""
            exit 1
        elif [ $EXIT_CODE -eq 2 ]; then
            echo "⚠️  Could not check for active trades (container may not be running)"
            echo "   Proceeding with deployment..."
        fi
    fi
    echo ""
else
    echo "⚠️  FORCE MODE - Skipping active trade check!"
    echo ""
fi

# Step 2: Push local changes
echo "📤 Pushing local changes..."
cd "$REPO_ROOT"
git push origin main 2>/dev/null || true

# Step 3: Pull changes on server
echo "📥 Pulling changes on server..."
"$REPO_ROOT/scripts/connect-server.sh" "cd ~/server && git pull origin main"
echo ""

# Step 4: Rebuild and restart
echo "🔄 Rebuilding and restarting container..."
"$REPO_ROOT/scripts/connect-server.sh" "cd ~/server/apps/polymarket-bot && docker compose up -d --build"
echo ""

# Step 5: Wait for startup and verify
echo "⏳ Waiting for bot to start..."
sleep 3

echo "📋 Checking bot status..."
"$REPO_ROOT/scripts/connect-server.sh" "docker logs polymarket-bot --tail 15 2>&1" || true
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "  ✅ DEPLOYMENT COMPLETE"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Dashboard: http://192.168.86.47:8501/dashboard"
echo ""
