#!/bin/bash

# Deploy to Server Script
# Automates the complete deployment workflow:
# 1. Stage all changes
# 2. Commit with message
# 3. Push to remote
# 4. Pull on server
# 5. Optionally restart services

set -euo pipefail

# Configuration
SERVER_USER="${SERVER_USER:-unarmedpuppy}"
SERVER_HOST="${SERVER_HOST:-192.168.86.47}"
SERVER_PORT="${SERVER_PORT:-4242}"
SERVER_REPO_PATH="${SERVER_REPO_PATH:-~/server}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
COMMIT_MESSAGE=""
APP_NAME=""
NO_RESTART=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --app)
            APP_NAME="$2"
            shift 2
            ;;
        --no-restart)
            NO_RESTART=true
            shift
            ;;
        *)
            if [ -z "$COMMIT_MESSAGE" ]; then
                COMMIT_MESSAGE="$1"
            else
                COMMIT_MESSAGE="$COMMIT_MESSAGE $1"
            fi
            shift
            ;;
    esac
done

# Validate commit message
if [ -z "$COMMIT_MESSAGE" ]; then
    echo -e "${RED}Error: Commit message is required${NC}"
    echo "Usage: $0 'commit message' [--app APP_NAME] [--no-restart]"
    echo ""
    echo "Examples:"
    echo "  $0 'Update plex configuration'"
    echo "  $0 'Fix docker network issue' --app traefik"
    echo "  $0 'Documentation update' --no-restart"
    exit 1
fi

# Helper functions
log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Step 1: Stage all changes
log "Staging all changes..."
if ! git add .; then
    error "Failed to stage changes"
fi

# Check if there are changes to commit
if git diff --staged --quiet; then
    warning "No changes to commit. Continuing with pull on server..."
else
    # Step 2: Commit
    log "Committing changes: '$COMMIT_MESSAGE'"
    if ! git commit -m "$COMMIT_MESSAGE"; then
        error "Failed to commit changes"
    fi

    # Step 3: Push to remote
    log "Pushing to remote repository..."
    if ! git push; then
        error "Failed to push to remote"
    fi
    log "✓ Changes pushed successfully"
fi

# Step 4: Pull on server
log "Pulling changes on server..."
if ! ssh -p "$SERVER_PORT" "${SERVER_USER}@${SERVER_HOST}" "cd ${SERVER_REPO_PATH} && git pull"; then
    error "Failed to pull changes on server"
fi
log "✓ Server updated successfully"

# Step 5: Restart services (if not disabled)
if [ "$NO_RESTART" = false ]; then
    if [ -n "$APP_NAME" ]; then
        log "Restarting app: $APP_NAME"
        if ! ssh -p "$SERVER_PORT" "${SERVER_USER}@${SERVER_HOST}" "cd ${SERVER_REPO_PATH}/apps/${APP_NAME} && docker compose restart"; then
            warning "Failed to restart $APP_NAME (container may not exist)"
        else
            log "✓ $APP_NAME restarted successfully"
        fi
    else
        info "Skipping service restart (use --app APP_NAME to restart specific app)"
        info "Or run manually: ssh -p $SERVER_PORT ${SERVER_USER}@${SERVER_HOST} 'cd ${SERVER_REPO_PATH}/apps/APP_NAME && docker compose restart'"
    fi
else
    info "Skipping service restart (--no-restart flag set)"
fi

log "✓ Deployment complete!"


