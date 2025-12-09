#!/bin/bash
# Fix permissions for jobin SSH - run with sudo
# Usage: sudo bash fix-jobin-permissions.sh

set -e

echo "=== Fixing jobin SSH Permissions ==="

# Ensure directory exists
mkdir -p /home/jobin/.ssh

# Set directory permissions
chmod 700 /home/jobin/.ssh
chown jobin:jobin /home/jobin/.ssh

# Ensure authorized_keys exists with correct key
if [ ! -f /home/jobin/.ssh/authorized_keys ]; then
    echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINnV3BW4DAkFfCFBVWC1wcmnhzu1oaQYskfFNSdf5qmL n8n-automation-jobin' > /home/jobin/.ssh/authorized_keys
fi

# Set file permissions
chmod 600 /home/jobin/.ssh/authorized_keys
chown jobin:jobin /home/jobin/.ssh/authorized_keys

# Verify
echo ""
echo "✅ Permissions fixed!"
echo ""
echo "Directory:"
ls -ld /home/jobin/.ssh
echo ""
echo "Authorized keys:"
ls -l /home/jobin/.ssh/authorized_keys
echo ""
echo "Content:"
cat /home/jobin/.ssh/authorized_keys

