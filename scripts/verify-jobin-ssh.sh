#!/bin/bash
# Verification script for jobin SSH setup
# Run this on the server: bash verify-jobin-ssh.sh

echo "=== Verifying jobin SSH Setup ==="
echo ""

# Check if user exists
echo "1. Checking if user exists..."
if id jobin &>/dev/null; then
    echo "   ✅ User 'jobin' exists"
    id jobin
else
    echo "   ❌ User 'jobin' does not exist"
    exit 1
fi

echo ""
echo "2. Checking SSH directory..."
if [ -d /home/jobin/.ssh ]; then
    echo "   ✅ SSH directory exists"
    sudo ls -la /home/jobin/.ssh/
else
    echo "   ❌ SSH directory does not exist"
    echo "   Run: sudo mkdir -p /home/jobin/.ssh && sudo chmod 700 /home/jobin/.ssh"
    exit 1
fi

echo ""
echo "3. Checking authorized_keys file..."
if [ -f /home/jobin/.ssh/authorized_keys ]; then
    echo "   ✅ authorized_keys exists"
    echo "   Content:"
    sudo cat /home/jobin/.ssh/authorized_keys
    echo ""
    echo "   Expected key fingerprint: SHA256:P7vUNoEnt3r1P6DASNOBcM8zGsgZtD/U0tWECkIVDXU"
else
    echo "   ❌ authorized_keys does not exist"
    exit 1
fi

echo ""
echo "4. Checking permissions..."
SSH_DIR_PERMS=$(stat -c "%a" /home/jobin/.ssh)
AUTH_KEY_PERMS=$(stat -c "%a" /home/jobin/.ssh/authorized_keys)
SSH_DIR_OWNER=$(stat -c "%U:%G" /home/jobin/.ssh)
AUTH_KEY_OWNER=$(stat -c "%U:%G" /home/jobin/.ssh/authorized_keys)

echo "   SSH directory: $SSH_DIR_PERMS (should be 700), owner: $SSH_DIR_OWNER (should be jobin:jobin)"
echo "   authorized_keys: $AUTH_KEY_PERMS (should be 600), owner: $AUTH_KEY_OWNER (should be jobin:jobin)"

if [ "$SSH_DIR_PERMS" != "700" ] || [ "$AUTH_KEY_PERMS" != "600" ]; then
    echo "   ⚠️  Permissions are incorrect!"
    echo "   Run:"
    echo "   sudo chmod 700 /home/jobin/.ssh"
    echo "   sudo chmod 600 /home/jobin/.ssh/authorized_keys"
    echo "   sudo chown -R jobin:jobin /home/jobin/.ssh"
fi

if [ "$SSH_DIR_OWNER" != "jobin:jobin" ] || [ "$AUTH_KEY_OWNER" != "jobin:jobin" ]; then
    echo "   ⚠️  Ownership is incorrect!"
    echo "   Run: sudo chown -R jobin:jobin /home/jobin/.ssh"
fi

echo ""
echo "5. Checking SSH server configuration..."
if sudo grep -q "^PubkeyAuthentication yes" /etc/ssh/sshd_config 2>/dev/null; then
    echo "   ✅ PubkeyAuthentication is enabled"
elif sudo grep -q "^#PubkeyAuthentication" /etc/ssh/sshd_config 2>/dev/null; then
    echo "   ⚠️  PubkeyAuthentication is commented (defaults to yes, should be fine)"
else
    echo "   ⚠️  Could not verify PubkeyAuthentication setting"
fi

echo ""
echo "=== Summary ==="
echo "If all checks passed, try testing the connection from your local machine:"
echo "  ssh -i agents/plans-local/jobin_server_key -v jobin@192.168.86.47 -p 4242"
echo ""
echo "The -v flag will show detailed connection information for troubleshooting."

