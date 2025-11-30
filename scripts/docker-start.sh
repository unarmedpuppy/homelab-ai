#!/bin/bash

# Define the directory to traverse
dir=~/server/apps

# Function to check if a docker-compose file is enabled
is_enabled() {
  local compose_file="$1"
  
  # Check if file exists
  if [ ! -f "$compose_file" ]; then
    return 1
  fi
  
  # Check for x-enabled: true in the compose file
  # This uses Docker Compose's x- extension fields for metadata
  if grep -qE "^\s*x-enabled:\s*true" "$compose_file" 2>/dev/null; then
    return 0
  fi
  
  # If x-enabled is not found, default to enabled (backward compatibility)
  # Only skip if explicitly set to false
  if grep -qE "^\s*x-enabled:\s*false" "$compose_file" 2>/dev/null; then
    return 1
  fi
  
  # Default to enabled if x-enabled is not specified
  return 0
}

# Traverse each subdirectory
for subdir in "$dir"/*; do
  # Check if it's a directory
  if [ -d "$subdir" ]; then
    # Change to the subdirectory
    cd "$subdir" || continue
    
    # Check if a docker-compose.yml file exists
    if [ -f docker-compose.yml ]; then
      # Check if the compose file is enabled
      if is_enabled "docker-compose.yml"; then
        echo "Starting services in $(basename "$subdir")..."
        docker-compose up -d
      else
        echo "Skipping $(basename "$subdir") (x-enabled: false or not set)"
      fi
    fi
    
    # Change back to the original directory
    cd - > /dev/null
  fi
done

# Handle jellyfin unlock service separately
if [ -d "$dir/jellyfin" ]; then
  cd "$dir/jellyfin" || exit
  if [ -f docker-compose-unlock.yml ]; then
    if is_enabled "docker-compose-unlock.yml"; then
      echo "Starting jellyfin unlock service..."
      docker-compose -f docker-compose-unlock.yml up -d
    else
      echo "Skipping jellyfin unlock service (x-enabled: false)"
    fi
  fi
  cd - > /dev/null
fi