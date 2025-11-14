#!/bin/bash
#
# Start Agent Infrastructure
#
# This script starts all agent infrastructure components locally:
# - Agent Monitoring (backend, frontend, InfluxDB, Grafana)
#
# Usage:
#   ./start-agent-infrastructure.sh [--check-only]
#
# Options:
#   --check-only    Only check if services are running, don't start them
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MONITORING_DIR="$PROJECT_ROOT/agents/apps/agent-monitoring"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: docker-compose or docker is not installed${NC}"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${YELLOW}Docker daemon is not running${NC}"
    echo ""
    
    # Try to start Docker Desktop on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Attempting to start Docker Desktop..."
        if open -a Docker &> /dev/null; then
            echo -e "${GREEN}✓ Docker Desktop launch command sent${NC}"
            echo ""
            echo "Waiting for Docker to start (this may take 30-60 seconds)..."
            
            # Wait for Docker to become available (max 60 seconds)
            local max_wait=60
            local waited=0
            while [ $waited -lt $max_wait ]; do
                if docker info &> /dev/null; then
                    echo -e "${GREEN}✓ Docker is now running!${NC}"
                    echo ""
                    break
                fi
                sleep 2
                waited=$((waited + 2))
                echo -n "."
            done
            echo ""
            
            if ! docker info &> /dev/null; then
                echo -e "${RED}Error: Docker did not start within $max_wait seconds${NC}"
                echo ""
                echo "Please:"
                echo "  1. Check if Docker Desktop is starting (look for whale icon in menu bar)"
                echo "  2. Wait for Docker to fully start"
                echo "  3. Run this script again"
                echo ""
                exit 1
            fi
        else
            echo -e "${RED}Could not start Docker Desktop automatically${NC}"
            echo ""
            echo "Please start Docker Desktop manually:"
            echo "  1. Open Docker Desktop application"
            echo "  2. Wait for Docker to start (whale icon in menu bar)"
            echo "  3. Run this script again"
            echo ""
            exit 1
        fi
    else
        echo -e "${RED}Error: Docker daemon is not running${NC}"
        echo ""
        echo "Please start Docker service:"
        echo "  sudo systemctl start docker"
        echo ""
        exit 1
    fi
fi

# Use docker compose (v2) if available, otherwise docker-compose (v1)
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

check_service() {
    local service_name=$1
    local port=$2
    
    if curl -s "http://localhost:${port}/health" > /dev/null 2>&1; then
        return 0
    fi
    return 1
}

check_monitoring() {
    echo "Checking agent monitoring services..."
    
    local backend_running=false
    local frontend_running=false
    
    # Check backend
    if check_service "backend" 3001; then
        echo -e "${GREEN}✓ Backend is running on localhost:3001${NC}"
        backend_running=true
    else
        echo -e "${YELLOW}✗ Backend is not running${NC}"
    fi
    
    # Check frontend
    if curl -s "http://localhost:3012" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend is running on localhost:3012${NC}"
        frontend_running=true
    else
        echo -e "${YELLOW}✗ Frontend is not running${NC}"
    fi
    
    if [ "$backend_running" = true ] && [ "$frontend_running" = true ]; then
        return 0
    fi
    return 1
}

start_monitoring() {
    echo "Starting agent monitoring infrastructure..."
    
    cd "$MONITORING_DIR"
    
    if [ ! -f "docker-compose.yml" ]; then
        echo -e "${RED}Error: docker-compose.yml not found in $MONITORING_DIR${NC}"
        exit 1
    fi
    
    echo "Starting Docker Compose services..."
    $DOCKER_COMPOSE up -d
    
    echo "Waiting for services to be healthy..."
    sleep 5
    
    # Wait for backend to be ready
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if check_service "backend" 3001; then
            echo -e "${GREEN}✓ Backend is ready${NC}"
            break
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    
    if [ $attempt -eq $max_attempts ]; then
        echo -e "${RED}Error: Backend did not become ready in time${NC}"
        echo "Check logs with: cd $MONITORING_DIR && $DOCKER_COMPOSE logs"
        exit 1
    fi
    
    # Wait for frontend to be ready
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "http://localhost:3012" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Frontend is ready${NC}"
            break
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    
    if [ $attempt -eq $max_attempts ]; then
        echo -e "${YELLOW}Warning: Frontend did not become ready in time${NC}"
        echo "It may still be starting. Check logs with: cd $MONITORING_DIR && $DOCKER_COMPOSE logs frontend"
    fi
    
    echo ""
    echo -e "${GREEN}Agent infrastructure is running!${NC}"
    echo ""
    echo "Services:"
    echo "  - Backend API: http://localhost:3001"
    echo "  - Frontend Dashboard: http://localhost:3012"
    echo "  - Grafana: http://localhost:3011 (admin/admin123)"
    echo ""
    echo "To stop services:"
    echo "  cd $MONITORING_DIR && $DOCKER_COMPOSE down"
    echo ""
}

# Main execution
CHECK_ONLY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --check-only)
            CHECK_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

if check_monitoring; then
    echo -e "${GREEN}All agent infrastructure services are running!${NC}"
    exit 0
fi

if [ "$CHECK_ONLY" = true ]; then
    echo -e "${YELLOW}Some services are not running${NC}"
    exit 1
fi

start_monitoring

