#!/bin/bash

echo "attempting to mount ZFS..."
source .env
# Load the ZFS key and mount the dataset
echo "$ZFS_KEY" | zfs load-key -a
zfs mount -a

# Execute the CMD
exec "$@"