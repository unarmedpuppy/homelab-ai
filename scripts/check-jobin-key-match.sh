#!/bin/bash
# Check if the public key on server matches the private key
# Run this on the server: bash check-jobin-key-match.sh

echo "=== Checking Key Match ==="
echo ""

# Expected public key (from the private key)
EXPECTED_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINnV3BW4DAkFfCFBVWC1wcmnhzu1oaQYskfFNSdf5qmL n8n-automation-jobin"

echo "Expected public key (from private key):"
echo "$EXPECTED_KEY"
echo ""

echo "Actual public key on server (in authorized_keys):"
if [ -f /home/jobin/.ssh/authorized_keys ]; then
    ACTUAL_KEY=$(sudo cat /home/jobin/.ssh/authorized_keys | head -1)
    echo "$ACTUAL_KEY"
    echo ""
    
    if [ "$EXPECTED_KEY" = "$ACTUAL_KEY" ]; then
        echo "✅ Keys MATCH!"
    else
        echo "❌ Keys DO NOT MATCH!"
        echo ""
        echo "This is the problem! The public key on the server doesn't match the private key."
        echo ""
        echo "Fix it by running:"
        echo "  echo '$EXPECTED_KEY' | sudo tee /home/jobin/.ssh/authorized_keys"
        echo "  sudo chmod 600 /home/jobin/.ssh/authorized_keys"
        echo "  sudo chown jobin:jobin /home/jobin/.ssh/authorized_keys"
    fi
else
    echo "❌ authorized_keys file does not exist!"
    echo "Run the fix script: bash ~/fix-jobin-ssh.sh"
fi

echo ""
echo "=== Checking Permissions ==="
if [ -d /home/jobin/.ssh ]; then
    echo "SSH directory:"
    sudo ls -la /home/jobin/.ssh/
else
    echo "❌ .ssh directory does not exist!"
fi

