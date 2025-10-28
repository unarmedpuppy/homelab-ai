#!/bin/bash

# Define the directory to traverse
dir=~/server/apps

# Traverse each subdirectory
for subdir in "$dir"/*; do
  # Check if it's a directory
  if [ -d "$subdir" ]; then
    # Skip jellyfin directory - it requires manual ZFS unlock
    if [[ "$subdir" == *"jellyfin"* ]]; then
      echo "Skipping jellyfin (requires manual ZFS unlock)"
      continue
    fi
    
    # Change to the subdirectory
    cd "$subdir"
    # Check if a docker-compose.yml file exists
    if [ -f docker-compose.yml ]; then
      # Run docker-compose up -d
      docker-compose up -d
    fi
    # Change back to the original directory
    cd -
  fi
done

# Start only the unlock service for jellyfin (not jellyfin itself)
cd "$dir/jellyfin"
if [ -f docker-compose-unlock.yml ]; then
  echo "Starting jellyfin unlock service..."
  docker-compose -f docker-compose-unlock.yml up -d
fi
cd -