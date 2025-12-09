#!/bin/bash
# Fix script for jobin SSH setup - run this on the server with sudo
# Usage: bash fix-jobin-ssh.sh

set -e

PUBLIC_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINnV3BW4DAkFfCFBVWC1wcmnhzu1oaQYskfFNSdf5qmL n8n-automation-jobin"

echo "=== Fixing jobin SSH Setup ==="
echo ""

# Ensure SSH directory exists with correct permissions
echo "1. Setting up SSH directory..."
sudo mkdir -p /home/jobin/.ssh
sudo chmod 700 /home/jobin/.ssh
sudo chown jobin:jobin /home/jobin/.ssh

# Add the public key
echo "2. Adding public key to authorized_keys..."
echo "$PUBLIC_KEY" | sudo tee /home/jobin/.ssh/authorized_keys > /dev/null

# Set correct permissions on authorized_keys
echo "3. Setting correct permissions..."
sudo chmod 600 /home/jobin/.ssh/authorized_keys
sudo chown jobin:jobin /home/jobin/.ssh/authorized_keys

# Verify
echo ""
echo "4. Verifying setup..."
echo "   Directory permissions: $(stat -c "%a %U:%G" /home/jobin/.ssh)"
echo "   Key file permissions: $(stat -c "%a %U:%G" /home/jobin/.ssh/authorized_keys)"
echo ""
echo "   Public key in authorized_keys:"
sudo cat /home/jobin/.ssh/authorized_keys
echo ""
echo "   Expected fingerprint: SHA256:P7vUNoEnt3r1P6DASNOBcM8zGsgZtD/U0tWECkIVDXU"
echo ""

# Check SSH server config
echo "5. Checking SSH server allows public key auth..."
if sudo grep -q "^PubkeyAuthentication" /etc/ssh/sshd_config; then
    sudo grep "^PubkeyAuthentication" /etc/ssh/sshd_config
else
    echo "   (Using default: PubkeyAuthentication yes)"
fi

echo ""
echo "✅ Setup complete! Test connection with:"
echo "   ssh -i <private_key> jobin@192.168.86.47 -p 4242"

