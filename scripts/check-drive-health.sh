#!/bin/bash

# Drive Health Check Script
# Checks SMART status for all drives and ZFS pool health

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if smartctl is installed
if ! command -v smartctl &> /dev/null; then
    error "smartctl not found. Install with: sudo apt install smartmontools"
    exit 1
fi

log "=== Drive Health Check ==="
echo

# Get all disk devices
DISKS=$(lsblk -d -n -o NAME | grep -E '^sd[a-z]$|^nvme')

if [ -z "$DISKS" ]; then
    error "No disk devices found"
    exit 1
fi

# Check each drive
HEALTHY=true
for disk in $DISKS; do
    device="/dev/$disk"
    
    echo "--- Checking $device ---"
    
    # Check if SMART is enabled
    if ! smartctl -i "$device" &>/dev/null; then
        warning "$device: SMART not available or device not found"
        continue
    fi
    
    # Get SMART overall health
    health=$(smartctl -H "$device" 2>/dev/null | grep -i "SMART overall-health self-assessment test result" | awk '{print $6}')
    
    if [ "$health" = "PASSED" ]; then
        log "$device: SMART health: PASSED"
    else
        error "$device: SMART health: $health"
        HEALTHY=false
    fi
    
    # Get critical SMART attributes
    echo "  Critical attributes:"
    smartctl -A "$device" 2>/dev/null | grep -E "Reallocated_Sector|Current_Pending|Offline_Uncorrectable|UDMA_CRC" | while read line; do
        attr=$(echo "$line" | awk '{print $2}')
        value=$(echo "$line" | awk '{print $10}')
        worst=$(echo "$line" | awk '{print $11}')
        thresh=$(echo "$line" | awk '{print $12}')
        
        if [ -n "$value" ] && [ "$value" != "0" ]; then
            if [ "$value" -gt "$thresh" ]; then
                error "    $attr: $value (Worst: $worst, Threshold: $thresh) - FAILING!"
                HEALTHY=false
            elif [ "$value" -gt 0 ]; then
                warning "    $attr: $value (Worst: $worst, Threshold: $thresh) - Warning"
            fi
        fi
    done
    
    # Get temperature
    temp=$(smartctl -A "$device" 2>/dev/null | grep -i "Temperature_Celsius" | awk '{print $10}')
    if [ -n "$temp" ]; then
        if [ "$temp" -gt 60 ]; then
            warning "  Temperature: ${temp}°C (High!)"
        else
            log "  Temperature: ${temp}°C"
        fi
    fi
    
    # Get power-on hours
    hours=$(smartctl -A "$device" 2>/dev/null | grep -i "Power_On_Hours" | awk '{print $10}')
    if [ -n "$hours" ]; then
        days=$((hours / 24))
        log "  Power-on hours: ${hours} (${days} days)"
    fi
    
    echo
done

# Check ZFS pool status
echo "=== ZFS Pool Status ==="
if command -v zpool &> /dev/null; then
    zpool_status=$(sudo zpool status 2>/dev/null || echo "")
    if [ -n "$zpool_status" ]; then
        echo "$zpool_status"
        
        # Check for errors
        if echo "$zpool_status" | grep -q "errors:"; then
            errors=$(echo "$zpool_status" | grep "errors:" | awk '{print $2}')
            if [ "$errors" != "No" ] && [ "$errors" != "0" ]; then
                error "ZFS pool has errors: $errors"
                HEALTHY=false
            fi
        fi
        
        # Check for degraded/faulted drives
        if echo "$zpool_status" | grep -qE "DEGRADED|FAULTED|OFFLINE"; then
            error "ZFS pool is DEGRADED or has FAULTED drives!"
            HEALTHY=false
        fi
    else
        warning "ZFS pool not found or not accessible"
    fi
else
    warning "zpool command not found"
fi

echo
echo "=== Summary ==="
if [ "$HEALTHY" = true ]; then
    log "All drives appear healthy"
    exit 0
else
    error "One or more drives have issues - investigate immediately!"
    exit 1
fi

