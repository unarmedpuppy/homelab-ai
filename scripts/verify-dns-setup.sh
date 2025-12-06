#!/bin/bash

# Verify DNS Setup Script
# Checks if AdGuard Home DNS is properly configured and accessible

set -euo pipefail

# Configuration
SERVER_IP="${SERVER_IP:-192.168.86.47}"
ADGUARD_PORT="${ADGUARD_PORT:-53}"
ADGUARD_WEB="${ADGUARD_WEB:-8083}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

ISSUES=0
WARNINGS=0

log() {
    echo -e "${GREEN}[✓]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[!]${NC} $1"
    ((WARNINGS++))
}

error() {
    echo -e "${RED}[✗]${NC} $1"
    ((ISSUES++))
}

info() {
    echo -e "${BLUE}[i]${NC} $1"
}

section() {
    echo ""
    echo -e "${CYAN}=== $1 ===${NC}"
}

echo -e "${CYAN}"
echo "╔════════════════════════════════════════╗"
echo "║     DNS Setup Verification             ║"
echo "║     $(date +"%Y-%m-%d %H:%M:%S")                    ║"
echo "╚════════════════════════════════════════╝"
echo -e "${NC}"

# Check 1: AdGuard Home Container
section "AdGuard Home Service"
if command -v docker &> /dev/null; then
    if docker ps --format "{{.Names}}" | grep -q "^adguard$"; then
        CONTAINER_STATUS=$(docker ps --filter "name=adguard" --format "{{.Status}}")
        log "AdGuard Home container is running"
        info "Status: $CONTAINER_STATUS"
    else
        error "AdGuard Home container is not running"
        info "Start with: cd apps/adguard-home && docker compose up -d"
    fi
else
    warning "Docker not found (running from remote?)"
    info "Check server: ssh -p 4242 unarmedpuppy@${SERVER_IP} 'docker ps | grep adguard'"
fi

# Check 2: Port 53 Accessibility
section "DNS Port (53) Accessibility"
if command -v nc &> /dev/null || command -v telnet &> /dev/null; then
    if timeout 2 bash -c "echo > /dev/tcp/${SERVER_IP}/${ADGUARD_PORT}" 2>/dev/null; then
        log "Port 53 is accessible on ${SERVER_IP}"
    else
        error "Cannot connect to ${SERVER_IP}:${ADGUARD_PORT}"
        warning "Check firewall: sudo ufw status | grep 53"
        warning "Verify AdGuard Home is listening on all interfaces"
    fi
else
    info "Skipping port check (nc/telnet not available)"
fi

# Check 3: DNS Resolution Test
section "DNS Resolution Test"
if command -v nslookup &> /dev/null || command -v dig &> /dev/null; then
    TEST_DOMAIN="google.com"
    
    if command -v dig &> /dev/null; then
        RESULT=$(dig @${SERVER_IP} ${TEST_DOMAIN} +short +timeout=2 2>&1)
        if echo "$RESULT" | grep -qE "^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+"; then
            log "DNS resolution working"
            info "Resolved ${TEST_DOMAIN} to: $(echo "$RESULT" | head -1)"
        else
            error "DNS resolution failed"
            info "Response: $RESULT"
        fi
    elif command -v nslookup &> /dev/null; then
        RESULT=$(nslookup ${TEST_DOMAIN} ${SERVER_IP} 2>&1 | grep -A 1 "Name:" | tail -1)
        if echo "$RESULT" | grep -qE "[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+"; then
            log "DNS resolution working"
            info "Resolved ${TEST_DOMAIN}"
        else
            error "DNS resolution failed"
        fi
    fi
else
    warning "nslookup/dig not available for DNS test"
fi

# Check 4: Current DNS Configuration
section "Current DNS Configuration"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CURRENT_DNS=$(scutil --dns | grep "nameserver\[0\]" | head -1 | awk '{print $3}' || echo "unknown")
    info "Current DNS: $CURRENT_DNS"
    if [ "$CURRENT_DNS" = "${SERVER_IP}" ]; then
        log "Device is using AdGuard Home DNS"
    else
        warning "Device is NOT using AdGuard Home DNS"
        info "Current DNS: $CURRENT_DNS (should be ${SERVER_IP})"
        info "Configure DNS to: ${SERVER_IP}"
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if [ -f /etc/resolv.conf ]; then
        CURRENT_DNS=$(grep "^nameserver" /etc/resolv.conf | head -1 | awk '{print $2}' || echo "unknown")
        info "Current DNS: $CURRENT_DNS"
        if [ "$CURRENT_DNS" = "${SERVER_IP}" ]; then
            log "Device is using AdGuard Home DNS"
        else
            warning "Device is NOT using AdGuard Home DNS"
            info "Current DNS: $CURRENT_DNS (should be ${SERVER_IP})"
        fi
    fi
else
    info "DNS configuration check not supported on this OS"
fi

# Check 5: AdGuard Home Web Interface
section "AdGuard Home Web Interface"
if command -v curl &> /dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 "http://${SERVER_IP}:${ADGUARD_WEB}" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
        log "AdGuard Home web interface is accessible"
        info "Access at: http://${SERVER_IP}:${ADGUARD_WEB}"
    else
        warning "Cannot access AdGuard Home web interface"
        info "Expected: http://${SERVER_IP}:${ADGUARD_WEB}"
        info "HTTP Code: $HTTP_CODE"
    fi
else
    info "curl not available (skipping web interface check)"
fi

# Check 6: Firewall Rules (if on server)
section "Firewall Configuration"
if [ -f "/etc/debian_version" ]; then
    if command -v ufw &> /dev/null; then
        if ufw status | grep -q "53/tcp.*ALLOW" && ufw status | grep -q "53/udp.*ALLOW"; then
            log "Firewall allows DNS (port 53)"
        else
            warning "Firewall may be blocking DNS"
            info "Run: sudo ufw allow 53/tcp && sudo ufw allow 53/udp"
        fi
    else
        info "UFW not installed (check iptables manually)"
    fi
else
    info "Not on server (skipping firewall check)"
fi

# Summary
echo ""
echo -e "${CYAN}╔════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║           Summary                     ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════╝${NC}"
echo ""

if [ $ISSUES -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    log "All checks passed! DNS is properly configured."
    echo ""
    info "Next steps:"
    echo "  1. Configure AdGuard Home filters"
    echo "  2. Set up custom DNS rewrites for local services"
    echo "  3. Check AdGuard Home dashboard for query statistics"
    exit 0
elif [ $ISSUES -eq 0 ]; then
    warning "$WARNINGS warning(s) found. Review above."
    exit 0
else
    error "$ISSUES issue(s) and $WARNINGS warning(s) found."
    echo ""
    info "Troubleshooting:"
    echo "  1. Ensure AdGuard Home is running: docker ps | grep adguard"
    echo "  2. Check firewall: sudo ufw status"
    echo "  3. Verify DNS on device points to: ${SERVER_IP}"
    echo "  4. See: docs/GOOGLE_HOME_DNS_SETUP.md"
    exit 1
fi

