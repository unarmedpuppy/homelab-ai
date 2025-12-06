#!/bin/bash

# Validate Secrets Script
# Checks for missing or default secrets in environment files

set -euo pipefail

# Configuration
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APPS_DIR="${REPO_ROOT}/apps"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ISSUES=0
WARNINGS=0

log() {
    echo -e "${GREEN}[OK]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    ((WARNINGS++))
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    ((ISSUES++))
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

echo -e "${BLUE}=== Secrets Validation ===${NC}\n"

# Check 1: Look for hardcoded credentials in docker-compose.yml files
info "Checking for hardcoded credentials in docker-compose.yml files..."
HARDCODED=$(find "$APPS_DIR" -name "docker-compose.yml" -type f -exec grep -l "basicauth\.users=.*\$apr1" {} \; 2>/dev/null || true)

if [ -n "$HARDCODED" ]; then
    error "Found hardcoded basic auth credentials:"
    echo "$HARDCODED" | while read -r file; do
        echo "  - $file"
    done
    echo ""
    info "Fix: Run scripts/fix-hardcoded-credentials.sh"
else
    log "No hardcoded basic auth credentials found"
fi

# Check 2: Check for .env files with proper permissions
info "Checking .env file permissions..."
find "$APPS_DIR" -name ".env" -type f 2>/dev/null | while read -r env_file; do
    PERMS=$(stat -c "%a" "$env_file" 2>/dev/null || stat -f "%OLp" "$env_file" 2>/dev/null)
    if [ "$PERMS" != "600" ] && [ "$PERMS" != "400" ]; then
        warning ".env file has insecure permissions ($PERMS): $env_file"
        info "  Fix: chmod 600 $env_file"
    else
        log ".env file has secure permissions: $env_file"
    fi
done

# Check 3: Check for default passwords in env.template files
info "Checking for default passwords in templates..."
DEFAULT_PASSWORDS=$(find "$APPS_DIR" -name "env.template" -o -name "*.env.template" | xargs grep -l "password.*=.*password\|PASSWORD.*=.*password\|password.*=.*123\|PASSWORD.*=.*123" 2>/dev/null || true)

if [ -n "$DEFAULT_PASSWORDS" ]; then
    warning "Found potential default passwords in templates:"
    echo "$DEFAULT_PASSWORDS" | while read -r file; do
        echo "  - $file"
    done
fi

# Check 4: Check for empty password fields that should be set
info "Checking for empty required password fields..."
find "$APPS_DIR" -name "env.template" -o -name "*.env.template" | while read -r template; do
    EMPTY_PASSWORDS=$(grep -E "PASSWORD.*=$|password.*=$" "$template" 2>/dev/null | grep -v "^#" || true)
    if [ -n "$EMPTY_PASSWORDS" ]; then
        info "  Template has empty password fields (expected): $(basename $(dirname $template))"
    fi
done

# Check 5: Verify .env files are in .gitignore
info "Checking .gitignore for .env patterns..."
if grep -q "^apps/\*/\.env" "${REPO_ROOT}/.gitignore" 2>/dev/null || grep -q "^\.env" "${REPO_ROOT}/.gitignore" 2>/dev/null; then
    log ".env files are in .gitignore"
else
    error ".env files are NOT in .gitignore"
    info "  Fix: Add 'apps/*/.env' to .gitignore"
fi

# Check 6: Check for secrets in docker-compose.yml that should be in .env
info "Checking for secrets that should be in environment variables..."
find "$APPS_DIR" -name "docker-compose.yml" -type f -exec grep -l "password\|secret\|key\|token" {} \; 2>/dev/null | while read -r file; do
    # Check if file uses environment variables
    if grep -q "\${.*}" "$file"; then
        log "File uses environment variables: $(basename $(dirname $file))"
    else
        # Check for hardcoded secrets (basic check)
        if grep -qE "(password|secret|key|token).*[:=].*[^$]" "$file" | grep -v "^#" | grep -v "template" | grep -v "example"; then
            warning "Potential hardcoded secret in: $file"
            info "  Review and move to .env file if needed"
        fi
    fi
done

# Summary
echo ""
echo -e "${BLUE}=== Summary ===${NC}"
if [ $ISSUES -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    log "All checks passed! No security issues found."
    exit 0
elif [ $ISSUES -eq 0 ]; then
    warning "$WARNINGS warning(s) found. Review and address as needed."
    exit 0
else
    error "$ISSUES issue(s) and $WARNINGS warning(s) found. Please address critical issues."
    exit 1
fi

