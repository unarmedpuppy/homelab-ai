#!/bin/bash
# Complete SSH setup for jobin - run this on the server
# Usage: bash setup-jobin-ssh-complete.sh '<public_key_here>'

set -e

if [ -z "$1" ]; then
    echo "Usage: bash setup-jobin-ssh-complete.sh '<public_key>'"
    exit 1
fi

PUBLIC_KEY="$1"

echo "=== Complete Jobin SSH Setup ==="
echo ""

# Ensure user exists
if ! id jobin &>/dev/null; then
    echo "Creating user jobin..."
    sudo adduser --disabled-password --gecos 'n8n automation user' jobin
fi

# Add to groups
echo "Adding to groups..."
sudo usermod -aG docker jobin 2>/dev/null || true
sudo usermod -aG sudo jobin 2>/dev/null || true

# Create .ssh directory
echo "Creating SSH directory..."
sudo mkdir -p /home/jobin/.ssh
sudo chmod 700 /home/jobin/.ssh
sudo chown jobin:jobin /home/jobin/.ssh

# Add public key (overwrite if exists)
echo "Adding public key..."
echo "$PUBLIC_KEY" | sudo tee /home/jobin/.ssh/authorized_keys > /dev/null

# Set permissions
echo "Setting permissions..."
sudo chmod 600 /home/jobin/.ssh/authorized_keys
sudo chown jobin:jobin /home/jobin/.ssh/authorized_keys

# Verify
echo ""
echo "=== Verification ==="
echo "Directory:"
sudo ls -ld /home/jobin/.ssh
echo ""
echo "Authorized keys:"
sudo ls -l /home/jobin/.ssh/authorized_keys
echo ""
echo "Key content:"
sudo cat /home/jobin/.ssh/authorized_keys
echo ""
echo "✅ Setup complete!"
echo ""
echo "Test with:"
echo "  ssh -i <private_key> jobin@192.168.86.47 -p 4242"

