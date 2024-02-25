#!/bin/bash

# Define the directory to traverse
dir=~/server/apps

# Traverse each subdirectory
for subdir in "$dir"/*; do
  # Check if it's a directory
  if [ -d "$subdir" ]; then
    # Change to the subdirectory
    cd "$subdir"
    # Check if a docker-compose.yml file exists
    if [ -f docker-compose.yml ]; then
      # Run docker-compose up -d
      docker-compose down
    fi
    # Change back to the original directory
    cd -
  fi
done