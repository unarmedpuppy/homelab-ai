#!/bin/bash

# Security Audit Script
# Automated security checks for the home server

set -euo pipefail

# Configuration
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APPS_DIR="${REPO_ROOT}/apps"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

CRITICAL=0
HIGH=0
MEDIUM=0
LOW=0

log() {
    echo -e "${GREEN}[✓]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[!]${NC} $1"
    ((MEDIUM++))
}

error_critical() {
    echo -e "${RED}[CRITICAL]${NC} $1"
    ((CRITICAL++))
}

error_high() {
    echo -e "${RED}[HIGH]${NC} $1"
    ((HIGH++))
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

section() {
    echo ""
    echo -e "${CYAN}=== $1 ===${NC}"
}

# Check if running on server
if [ -f "/etc/debian_version" ]; then
    IS_SERVER=true
else
    IS_SERVER=false
fi

echo -e "${CYAN}"
echo "╔════════════════════════════════════════╗"
echo "║     Security Audit Report             ║"
echo "║     $(date +"%Y-%m-%d %H:%M:%S")                    ║"
echo "╚════════════════════════════════════════╝"
echo -e "${NC}"

# 1. Hardcoded Credentials Check
section "Hardcoded Credentials"
TMPFILE=$(mktemp)
find "$APPS_DIR" -name "docker-compose.yml" -type f -exec grep -l "basicauth\.users=.*\$apr1" {} \; > "$TMPFILE" 2>/dev/null
if [ -s "$TMPFILE" ]; then
    error_critical "Hardcoded basic auth credentials found"
    FILE_COUNT=0
    while IFS= read -r file; do
        [ -n "$file" ] || continue
        RELATIVE_FILE="${file#$REPO_ROOT/}"
        [ "$RELATIVE_FILE" = "$file" ] && RELATIVE_FILE="$file"  # Fallback if no match
        echo "  → $RELATIVE_FILE"
        FILE_COUNT=$((FILE_COUNT + 1))
    done < "$TMPFILE"
    CRITICAL=$((CRITICAL + FILE_COUNT))
    rm -f "$TMPFILE"
else
    log "No hardcoded basic auth credentials"
    rm -f "$TMPFILE"
fi

# 2. Root Containers Check
section "Container Security"
TMPFILE=$(mktemp)
find "$APPS_DIR" -name "docker-compose.yml" -type f -exec grep -l "user: root" {} \; > "$TMPFILE" 2>/dev/null
if [ -s "$TMPFILE" ]; then
    error_critical "Containers running as root"
    FILE_COUNT=0
    while IFS= read -r file; do
        RELATIVE_FILE="${file#$REPO_ROOT/}"
        echo "  → $RELATIVE_FILE"
        FILE_COUNT=$((FILE_COUNT + 1))
    done < "$TMPFILE"
    CRITICAL=$((CRITICAL + FILE_COUNT))
    rm -f "$TMPFILE"
else
    log "No containers running as root"
    rm -f "$TMPFILE"
fi

TMPFILE=$(mktemp)
find "$APPS_DIR" -name "*.yml" -type f -exec grep -l "privileged: true" {} \; > "$TMPFILE" 2>/dev/null
if [ -s "$TMPFILE" ]; then
    warning "Privileged containers found (review if necessary)"
    while IFS= read -r file; do
        RELATIVE_FILE="${file#$REPO_ROOT/}"
        echo "  → $RELATIVE_FILE"
    done < "$TMPFILE"
    rm -f "$TMPFILE"
fi

# 3. .env File Security
section "Secrets Management"
ENV_FILES=$(find "$APPS_DIR" -name ".env" -type f 2>/dev/null | wc -l)
if [ "$ENV_FILES" -gt 0 ]; then
    INSECURE_PERMS=$(find "$APPS_DIR" -name ".env" -type f ! -perm 600 2>/dev/null | wc -l)
    if [ "$INSECURE_PERMS" -gt 0 ]; then
        error_high "$INSECURE_PERMS .env file(s) with insecure permissions"
    else
        log "All .env files have secure permissions (600)"
    fi
else
    info "No .env files found (may be expected)"
fi

# 4. .gitignore Check
section "Git Security"
if grep -q "^apps/\*/\.env" "${REPO_ROOT}/.gitignore" 2>/dev/null; then
    log ".env files are in .gitignore"
else
    error_high ".env files not in .gitignore"
fi

# 5. fail2ban Check (server only)
if [ "$IS_SERVER" = true ]; then
    section "Intrusion Prevention"
    if command -v fail2ban-client &> /dev/null; then
        if systemctl is-active --quiet fail2ban; then
            log "fail2ban is installed and running"
        else
            error_high "fail2ban is installed but not running"
        fi
    else
        error_high "fail2ban is not installed"
    fi
fi

# 6. Resource Limits Check
section "Container Resource Limits"
NO_LIMITS=$(find "$APPS_DIR" -name "docker-compose.yml" -type f -exec grep -L "deploy:" {} \; 2>/dev/null | wc -l)
if [ "$NO_LIMITS" -gt 0 ]; then
    warning "$NO_LIMITS docker-compose file(s) without resource limits"
else
    log "All containers have resource limits"
fi

# 7. Network Security Check
section "Network Security"
EXPOSED_PORTS=$(find "$APPS_DIR" -name "docker-compose.yml" -type f -exec grep -h "ports:" -A 10 {} \; 2>/dev/null | grep -E "^\s+-.*:" | wc -l)
if [ "$EXPOSED_PORTS" -gt 0 ]; then
    info "$EXPOSED_PORTS port mapping(s) found (review if all are necessary)"
fi

# 8. Docker Socket Access
section "Docker Socket Access"
SOCKET_ACCESS=$(find "$APPS_DIR" -name "docker-compose.yml" -type f -exec grep -l "docker.sock" {} \; 2>/dev/null || true)
if [ -n "$SOCKET_ACCESS" ]; then
    warning "Containers with Docker socket access"
    for file in $SOCKET_ACCESS; do
        if grep -q "docker.sock.*:ro" "$file"; then
            echo "  → $file (read-only - acceptable)"
        else
            error_high "$file (read-write - security risk!)"
        fi
    done
else
    log "No containers accessing Docker socket"
fi

# 9. Default Credentials Check
section "Default Credentials"
DEFAULT_CREDS=$(find "$APPS_DIR" -name "*.template" -o -name "env.template" | xargs grep -l "password.*=.*password\|PASSWORD.*=.*password" 2>/dev/null || true)
if [ -n "$DEFAULT_CREDS" ]; then
    warning "Potential default passwords in templates"
else
    log "No obvious default passwords in templates"
fi

# Summary
echo ""
echo -e "${CYAN}╔════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║           Audit Summary                ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════╝${NC}"
echo ""

if [ $CRITICAL -gt 0 ]; then
    echo -e "${RED}CRITICAL: $CRITICAL issue(s)${NC}"
fi
if [ $HIGH -gt 0 ]; then
    echo -e "${RED}HIGH: $HIGH issue(s)${NC}"
fi
if [ $MEDIUM -gt 0 ]; then
    echo -e "${YELLOW}MEDIUM: $MEDIUM issue(s)${NC}"
fi
if [ $LOW -gt 0 ]; then
    echo -e "${BLUE}LOW: $LOW issue(s)${NC}"
fi

echo ""
if [ $CRITICAL -eq 0 ] && [ $HIGH -eq 0 ] && [ $MEDIUM -eq 0 ]; then
    log "No security issues found! System appears secure."
    exit 0
elif [ $CRITICAL -gt 0 ]; then
    error_critical "Critical issues found! Immediate action required."
    echo ""
    info "Run: bash scripts/validate-secrets.sh"
    info "See: agents/reference/security/SECURITY_AUDIT.md"
    exit 1
else
    warning "Some issues found. Review and address as needed."
    exit 0
fi

