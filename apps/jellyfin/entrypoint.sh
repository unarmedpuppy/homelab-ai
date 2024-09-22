#!/bin/bash

echo "attempting to mount ZFS..."
source .env

# Load the ZFS key and mount the dataset
echo "$ZFS_KEY" | zfs load-key -a
zfs mount -a

# Wait until the ZFS dataset is mounted
until mountpoint -q "$ZFS_PATH"; do
  echo "Waiting for ZFS dataset to be mounted..."
  sleep 1
done

echo "ZFS dataset mounted. Starting the application..."

# Execute the CMD
exec "$@"