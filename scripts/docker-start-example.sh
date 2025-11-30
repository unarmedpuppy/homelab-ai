#!/bin/bash
# Example: Test the docker-start script logic without actually starting containers
# Usage: ./docker-start-example.sh

dir=~/server/apps

# Function to check if a docker-compose file is enabled
is_enabled() {
  local compose_file="$1"
  
  if [ ! -f "$compose_file" ]; then
    return 1
  fi
  
  if grep -qE "^\s*x-enabled:\s*true" "$compose_file" 2>/dev/null; then
    return 0
  fi
  
  if grep -qE "^\s*x-enabled:\s*false" "$compose_file" 2>/dev/null; then
    return 1
  fi
  
  return 0
}

echo "Checking docker-compose files for x-enabled status..."
echo ""

for subdir in "$dir"/*; do
  if [ -d "$subdir" ]; then
    cd "$subdir" || continue
    
    if [ -f docker-compose.yml ]; then
      app_name=$(basename "$subdir")
      if is_enabled "docker-compose.yml"; then
        status=$(grep -E "^\s*x-enabled:" docker-compose.yml 2>/dev/null | head -1 || echo "  (not specified - default: enabled)")
        echo "✅ $app_name - ENABLED $status"
      else
        echo "❌ $app_name - DISABLED (x-enabled: false)"
      fi
    fi
    
    cd - > /dev/null
  fi
done

echo ""
echo "Done! Use this to verify which apps will start automatically."

