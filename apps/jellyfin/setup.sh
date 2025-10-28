#!/bin/bash
# Setup script for Jellyfin ZFS encryption unlock service

set -e

echo "🔒 Jellyfin ZFS Unlock Service Setup"
echo "===================================="
echo ""

# Check if .env exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists. Please backup or remove it first."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Copy template
echo "📝 Creating .env file from template..."
cp env.template .env

# Get ZFS path
read -p "Enter ZFS dataset path (e.g., /tank/media): " ZFS_PATH
if [ -z "$ZFS_PATH" ]; then
    ZFS_PATH="/tank/media"
fi
sed -i.bak "s|ZFS_PATH=.*|ZFS_PATH=$ZFS_PATH|" .env

# Get username
read -p "Enter username for unlock service (default: admin): " UNLOCK_USER
if [ -z "$UNLOCK_USER" ]; then
    UNLOCK_USER="admin"
fi
sed -i.bak "s|UNLOCK_USER=.*|UNLOCK_USER=$UNLOCK_USER|" .env

# Generate password hash
echo ""
echo "🔑 Setting up unlock service password..."
echo "Enter a password for the unlock service:"
PASSWORD=$(echo -n "$(read -s PASSWORD; echo $PASSWORD)")

if [ -z "$PASSWORD" ]; then
    echo "❌ Password cannot be empty"
    exit 1
fi

# Generate hash
HASH=$(python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('$PASSWORD'))")
sed -i.bak "s|UNLOCK_PASSWORD_HASH=.*|UNLOCK_PASSWORD_HASH=$HASH|" .env

# Clean up backup file
rm -f .env.bak

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Start the unlock service:"
echo "   docker-compose -f docker-compose-unlock.yml up -d"
echo ""
echo "2. Access the UI at: http://YOUR_SERVER_IP:8889"
echo ""
echo "3. Your credentials are:"
echo "   Username: $UNLOCK_USER"
echo "   Password: (the one you just entered)"
echo ""

