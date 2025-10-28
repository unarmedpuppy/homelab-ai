#!/bin/bash

echo "Checking if ZFS dataset is mounted..."

# The ZFS dataset should be mounted at /media in the container
if ! mountpoint -q "/media"; then
  echo "ERROR: ZFS dataset is not mounted at /media."
  echo "Please use the unlock service to mount it first."
  exit 1
fi

echo "ZFS dataset is mounted. Starting Jellyfin..."

# Execute the CMD
exec "$@"