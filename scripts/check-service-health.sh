#!/bin/bash

# Service Health Check Script
# Provides quick overview of all Docker services status

set -euo pipefail

# Configuration
SERVER_USER="${SERVER_USER:-unarmedpuppy}"
SERVER_HOST="${SERVER_HOST:-192.168.86.47}"
SERVER_PORT="${SERVER_PORT:-4242}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check if running locally or remotely
if [ -f "/etc/debian_version" ]; then
    # Running on server
    IS_REMOTE=false
else
    # Running from local machine
    IS_REMOTE=true
fi

# Function to run commands
run_cmd() {
    if [ "$IS_REMOTE" = true ]; then
        ssh -p "$SERVER_PORT" "${SERVER_USER}@${SERVER_HOST}" "$@"
    else
        eval "$@"
    fi
}

# Get container status
echo -e "${CYAN}=== Docker Service Health Check ===${NC}\n"

# Check if Docker is running
if ! run_cmd "docker ps >/dev/null 2>&1"; then
    echo -e "${RED}Error: Docker is not running or not accessible${NC}"
    exit 1
fi

# Get all containers with status
echo -e "${BLUE}Container Status:${NC}\n"
run_cmd "docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

echo ""

# Count by status
echo -e "${BLUE}Summary:${NC}"
TOTAL=$(run_cmd "docker ps -a --format '{{.Names}}' | wc -l")
RUNNING=$(run_cmd "docker ps --format '{{.Names}}' | wc -l")
STOPPED=$(run_cmd "docker ps -a --filter 'status=exited' --format '{{.Names}}' | wc -l")
RESTARTING=$(run_cmd "docker ps -a --filter 'status=restarting' --format '{{.Names}}' | wc -l")

echo -e "  Total containers: ${CYAN}${TOTAL}${NC}"
echo -e "  ${GREEN}Running:${NC} ${RUNNING}"
echo -e "  ${YELLOW}Stopped:${NC} ${STOPPED}"

if [ "$RESTARTING" -gt 0 ]; then
    echo -e "  ${RED}Restarting:${NC} ${RESTARTING}"
    echo ""
    echo -e "${YELLOW}Containers in restart loop:${NC}"
    run_cmd "docker ps -a --filter 'status=restarting' --format '  - {{.Names}} ({{.Status}})'"
fi

echo ""

# Check for unhealthy containers
UNHEALTHY=$(run_cmd "docker ps --filter 'health=unhealthy' --format '{{.Names}}' | wc -l")
if [ "$UNHEALTHY" -gt 0 ]; then
    echo -e "${RED}Unhealthy containers:${NC}"
    run_cmd "docker ps --filter 'health=unhealthy' --format '  - {{.Names}} ({{.Status}})'"
    echo ""
fi

# Show recently restarted containers (last hour)
echo -e "${BLUE}Recent activity (last hour):${NC}"
RECENT=$(run_cmd "docker ps -a --filter 'since=1h' --format '{{.Names}}' | wc -l")
if [ "$RECENT" -gt 0 ]; then
    run_cmd "docker ps -a --filter 'since=1h' --format '  - {{.Names}} ({{.Status}})'"
else
    echo "  No recent activity"
fi

echo ""

# Disk usage
echo -e "${BLUE}Docker disk usage:${NC}"
run_cmd "docker system df"

echo ""
echo -e "${CYAN}=== End of Health Check ===${NC}"

