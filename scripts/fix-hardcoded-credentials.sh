#!/bin/bash

# Fix Hardcoded Credentials Script
# Moves hardcoded credentials from docker-compose.yml to environment variables

set -euo pipefail

# Configuration
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOMEPAGE_DIR="${REPO_ROOT}/apps/homepage"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if running on server or locally
if [ -f "/etc/debian_version" ]; then
    IS_SERVER=true
    SERVER_HOME="$HOME"
else
    IS_SERVER=false
    SERVER_HOME="/home/unarmedpuppy"
fi

log "Fixing hardcoded credentials in homepage..."

# Step 1: Check if .env file exists
ENV_FILE="${HOMEPAGE_DIR}/.env"
if [ -f "$ENV_FILE" ]; then
    warning ".env file already exists. Backing up..."
    cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Step 2: Extract current password hash from docker-compose.yml
CURRENT_HASH=$(grep -oP 'basicauth\.users=\K[^"]+' "${HOMEPAGE_DIR}/docker-compose.yml" | head -1)

if [ -z "$CURRENT_HASH" ]; then
    error "Could not find basic auth hash in docker-compose.yml"
fi

info "Found existing hash: ${CURRENT_HASH:0:20}..."

# Step 3: Prompt for new password or use existing
echo ""
read -p "Generate new password? (y/n) [n]: " -r GENERATE_NEW
GENERATE_NEW=${GENERATE_NEW:-n}

if [ "$GENERATE_NEW" = "y" ] || [ "$GENERATE_NEW" = "Y" ]; then
    read -sp "Enter new password for 'unarmedpuppy': " NEW_PASSWORD
    echo ""
    read -sp "Confirm password: " CONFIRM_PASSWORD
    echo ""
    
    if [ "$NEW_PASSWORD" != "$CONFIRM_PASSWORD" ]; then
        error "Passwords do not match"
    fi
    
    # Generate new hash
    NEW_HASH=$(htpasswd -nb unarmedpuppy "$NEW_PASSWORD" | cut -d: -f2)
    info "Generated new password hash"
else
    NEW_HASH="$CURRENT_HASH"
    info "Using existing password hash"
fi

# Step 4: Create .env file
log "Creating .env file..."
cat > "$ENV_FILE" << EOF
# Homepage Basic Auth
# Generated: $(date)
# Username: unarmedpuppy
HOMEPAGE_BASIC_AUTH=unarmedpuppy:${NEW_HASH}
EOF

chmod 600 "$ENV_FILE"
log "✓ Created .env file with restricted permissions"

# Step 5: Update docker-compose.yml
log "Updating docker-compose.yml..."
sed -i.bak "s|basicauth\.users=.*|basicauth.users=\${HOMEPAGE_BASIC_AUTH}|g" "${HOMEPAGE_DIR}/docker-compose.yml"
log "✓ Updated docker-compose.yml"

# Step 6: Ensure .env is in .gitignore
log "Ensuring .env files are in .gitignore..."
if ! grep -q "^apps/\*/\.env$" "${REPO_ROOT}/.gitignore" 2>/dev/null; then
    echo "" >> "${REPO_ROOT}/.gitignore"
    echo "# Environment files with secrets" >> "${REPO_ROOT}/.gitignore"
    echo "apps/*/.env" >> "${REPO_ROOT}/.gitignore"
    echo "apps/*/.env.*" >> "${REPO_ROOT}/.gitignore"
    log "✓ Added .env patterns to .gitignore"
else
    info ".env patterns already in .gitignore"
fi

# Step 7: Create env.template if it doesn't exist
TEMPLATE_FILE="${HOMEPAGE_DIR}/env.template"
if [ ! -f "$TEMPLATE_FILE" ]; then
    log "Creating env.template..."
    cat > "$TEMPLATE_FILE" << 'EOF'
# Homepage Environment Variables
# Copy this file to .env and fill in the values

# Basic Auth for Traefik
# Generate with: htpasswd -nb unarmedpuppy your_password
# Format: username:password_hash
HOMEPAGE_BASIC_AUTH=unarmedpuppy:$apr1$...
EOF
    log "✓ Created env.template"
fi

# Step 8: Summary
echo ""
log "✓ Hardcoded credentials fixed!"
echo ""
info "Next steps:"
echo "  1. Review ${ENV_FILE} to ensure it's correct"
echo "  2. If deploying to server, copy .env file:"
echo "     scp -P 4242 ${ENV_FILE} unarmedpuppy@192.168.86.47:${SERVER_HOME}/server/apps/homepage/.env"
echo "  3. Restart homepage service:"
if [ "$IS_SERVER" = true ]; then
    echo "     cd ~/server/apps/homepage && docker compose restart"
else
    echo "     ssh -p 4242 unarmedpuppy@192.168.86.47 'cd ~/server/apps/homepage && docker compose restart'"
fi
echo ""
warning "⚠️  Make sure .env file is NOT committed to git!"
echo ""


