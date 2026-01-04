#!/bin/bash
# Fix inotify limits for slskd
# Run with: sudo bash scripts/fix-slskd-inotify.sh

set -e

echo "=== Fixing inotify limits for slskd ==="

# Check current limits
echo "Current limits:"
echo "  max_user_instances: $(cat /proc/sys/fs/inotify/max_user_instances)"
echo "  max_user_watches: $(cat /proc/sys/fs/inotify/max_user_watches)"

# Increase limits temporarily
echo ""
echo "Increasing limits temporarily..."
sysctl -w fs.inotify.max_user_instances=512
sysctl -w fs.inotify.max_user_watches=524288

# Make permanent
echo ""
echo "Making changes permanent..."
if ! grep -q "fs.inotify.max_user_instances" /etc/sysctl.conf; then
    echo "fs.inotify.max_user_instances=512" >> /etc/sysctl.conf
    echo "Added max_user_instances to sysctl.conf"
else
    sed -i 's/fs.inotify.max_user_instances=.*/fs.inotify.max_user_instances=512/' /etc/sysctl.conf
    echo "Updated max_user_instances in sysctl.conf"
fi

if ! grep -q "fs.inotify.max_user_watches" /etc/sysctl.conf; then
    echo "fs.inotify.max_user_watches=524288" >> /etc/sysctl.conf
    echo "Added max_user_watches to sysctl.conf"
else
    sed -i 's/fs.inotify.max_user_watches=.*/fs.inotify.max_user_watches=524288/' /etc/sysctl.conf
    echo "Updated max_user_watches in sysctl.conf"
fi

# Verify new limits
echo ""
echo "New limits:"
echo "  max_user_instances: $(cat /proc/sys/fs/inotify/max_user_instances)"
echo "  max_user_watches: $(cat /proc/sys/fs/inotify/max_user_watches)"

# Restart slskd
echo ""
echo "Restarting slskd..."
cd ~/server/apps/media-download
docker compose restart slskd

echo ""
echo "Waiting for slskd to start..."
sleep 10

# Check if slskd is running
if docker ps | grep -q media-download-slskd; then
    echo "✅ slskd is running!"
    docker logs media-download-slskd --tail 5
else
    echo "❌ slskd failed to start. Check logs:"
    docker logs media-download-slskd --tail 20
fi

echo ""
echo "=== Done ==="
