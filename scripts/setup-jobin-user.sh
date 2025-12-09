#!/bin/bash
# Setup script for jobin user - run this on the server
# Usage: bash setup-jobin-user.sh <public_key_content>

set -e

PUBLIC_KEY="$1"

if [ -z "$PUBLIC_KEY" ]; then
    echo "Usage: bash setup-jobin-user.sh '<public_key_content>'"
    exit 1
fi

echo "Creating jobin user..."
sudo adduser --disabled-password --gecos 'n8n automation user' jobin || echo "User may already exist"

echo "Adding jobin to docker group..."
sudo usermod -aG docker jobin

echo "Adding jobin to sudo group (for system admin tasks)..."
sudo usermod -aG sudo jobin

echo "Setting up SSH directory..."
sudo mkdir -p /home/jobin/.ssh
sudo chmod 700 /home/jobin/.ssh

echo "Adding SSH public key..."
echo "$PUBLIC_KEY" | sudo tee /home/jobin/.ssh/authorized_keys > /dev/null
sudo chmod 600 /home/jobin/.ssh/authorized_keys
sudo chown -R jobin:jobin /home/jobin/.ssh

echo "Setting up home directory permissions..."
sudo chmod 755 /home/jobin

echo "✅ User 'jobin' created and configured!"
echo ""
echo "User details:"
echo "  - Username: jobin"
echo "  - Groups: $(groups jobin)"
echo "  - Home: /home/jobin"
echo ""
echo "Test SSH connection:"
echo "  ssh -i <private_key> jobin@192.168.86.47 -p 4242"

