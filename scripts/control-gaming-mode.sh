#!/bin/bash
# Control script for Local AI Gaming Mode
# Usage:
#   ./control-gaming-mode.sh status          # Check current status
#   ./control-gaming-mode.sh enable          # Enable gaming mode (block new models)
#   ./control-gaming-mode.sh disable         # Disable gaming mode (allow new models)
#   ./control-gaming-mode.sh stop-all         # Force stop all running models
#   ./control-gaming-mode.sh safe            # Check if safe to game

MANAGER_URL="http://localhost:8000"
ACTION="${1:-status}"

get_status() {
    curl -s "$MANAGER_URL/status" 2>/dev/null || {
        echo "Error: Could not connect to manager at $MANAGER_URL" >&2
        echo "Make sure the manager is running: docker ps | grep vllm-manager" >&2
        exit 1
    }
}

set_gaming_mode() {
    local enable="$1"
    curl -s -X POST "$MANAGER_URL/gaming-mode" \
        -H "Content-Type: application/json" \
        -d "{\"enable\": $enable}" 2>/dev/null || {
        echo "Error: Could not set gaming mode" >&2
        exit 1
    }
}

stop_all_models() {
    curl -s -X POST "$MANAGER_URL/stop-all" 2>/dev/null || {
        echo "Error: Could not stop models" >&2
        exit 1
    }
}

format_status() {
    local status_json="$1"
    
    echo ""
    echo "=== Local AI Manager Status ==="
    
    local gaming_mode=$(echo "$status_json" | grep -o '"gaming_mode":[^,]*' | cut -d: -f2)
    local safe_to_game=$(echo "$status_json" | grep -o '"safe_to_game":[^,]*' | cut -d: -f2)
    
    echo -n "Gaming Mode: "
    if [ "$gaming_mode" = "true" ]; then
        echo "ENABLED (new models blocked)"
    else
        echo "DISABLED (new models allowed)"
    fi
    
    echo -n "Safe to Game: "
    if [ "$safe_to_game" = "true" ]; then
        echo "YES ✓"
    else
        echo "NO ✗"
    fi
    
    echo ""
    echo "Running Models:"
    echo "$status_json" | grep -o '"running_models":\[[^]]*\]' | grep -o '"[^"]*"' | sed 's/"//g' || echo "  (none)"
    
    echo ""
    echo "Use 'jq' for better formatting: curl -s $MANAGER_URL/status | jq"
}

case "$ACTION" in
    status)
        status=$(get_status)
        format_status "$status"
        ;;
    
    enable)
        echo "Enabling gaming mode..."
        set_gaming_mode true
        echo "Gaming mode ENABLED"
        echo "  New model requests will be blocked."
        echo "  Use './control-gaming-mode.sh disable' to allow models again."
        ;;
    
    disable)
        echo "Disabling gaming mode..."
        set_gaming_mode false
        echo "Gaming mode DISABLED"
        echo "  New model requests will be allowed."
        ;;
    
    stop-all)
        echo "Stopping all running models..."
        stop_all_models
        echo "Models stopped."
        ;;
    
    safe)
        status=$(get_status)
        safe_to_game=$(echo "$status" | grep -o '"safe_to_game":[^,]*' | cut -d: -f2)
        if [ "$safe_to_game" = "true" ]; then
            echo ""
            echo "✓ SAFE TO GAME"
            echo "  No models are running and gaming mode is disabled."
            exit 0
        else
            echo ""
            echo "✗ NOT SAFE TO GAME"
            echo "  Some models may still be running."
            echo "  Run './control-gaming-mode.sh stop-all' to stop them."
            exit 1
        fi
        ;;
    
    *)
        echo "Usage: $0 {status|enable|disable|stop-all|safe}" >&2
        exit 1
        ;;
esac

