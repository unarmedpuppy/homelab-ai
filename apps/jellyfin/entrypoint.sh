#!/bin/bash

# Load the ZFS key and mount the dataset
echo "your-zfs-key" | zfs load-key pool/dataset
zfs mount pool/dataset

# Execute the CMD
exec "$@"