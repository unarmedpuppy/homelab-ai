#!/bin/bash
# Final check - what's actually on the server
# Run: bash check-jobin-final.sh

echo "=== Checking Jobin SSH Setup ==="
echo ""

echo "1. User exists?"
if id jobin &>/dev/null; then
    echo "   ✅ Yes"
    id jobin
else
    echo "   ❌ No"
fi

echo ""
echo "2. SSH directory exists?"
if [ -d /home/jobin/.ssh ]; then
    echo "   ✅ Yes"
    sudo ls -la /home/jobin/.ssh/ 2>/dev/null || echo "   (Need sudo to view)"
else
    echo "   ❌ No"
fi

echo ""
echo "3. Authorized keys file exists?"
if [ -f /home/jobin/.ssh/authorized_keys ]; then
    echo "   ✅ Yes"
    echo "   Content:"
    sudo cat /home/jobin/.ssh/authorized_keys 2>/dev/null || echo "   (Need sudo to view)"
else
    echo "   ❌ No"
fi

echo ""
echo "4. Expected public key (NEW):"
echo "   ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIIonWDlOjiAaz0DAASv2gVrvKkx3w1ei1/vWIkUt3Yv n8n-automation-jobin"

echo ""
echo "=== To Fix ==="
echo "Run this command on the server:"
echo "  bash ~/setup-jobin-ssh-complete.sh 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIIonWDlOjiAaz0DAASv2gVrvKkx3w1ei1/vWIkUt3Yv n8n-automation-jobin'"


