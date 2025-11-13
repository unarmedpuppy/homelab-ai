#!/bin/bash
# Pre-Submission Check Script
# Run this before marking a task as [REVIEW]
# Usage: ./pre-submit-check.sh [backend|frontend|all]

set -e  # Exit on error

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CHECK_TYPE="${1:-all}"

echo "=========================================="
echo "Pre-Submission Check"
echo "=========================================="
echo "Project Root: $PROJECT_ROOT"
echo "Check Type: $CHECK_TYPE"
echo ""

ERRORS=0
WARNINGS=0

# Function to check command exists
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "⚠️  WARNING: $1 not found. Skipping $1 checks."
        return 1
    fi
    return 0
}

# Function to count errors
count_errors() {
    if [ $? -ne 0 ]; then
        ((ERRORS++))
        return 1
    fi
    return 0
}

# Function to count warnings
count_warnings() {
    ((WARNINGS++))
    return 0
}

# Backend Checks
if [ "$CHECK_TYPE" = "backend" ] || [ "$CHECK_TYPE" = "all" ]; then
    echo "----------------------------------------"
    echo "Backend Checks"
    echo "----------------------------------------"
    
    if [ -d "$PROJECT_ROOT/backend" ]; then
        cd "$PROJECT_ROOT/backend"
        
        # Python syntax check
        echo "✓ Checking Python syntax..."
        python3 -m py_compile app/*.py 2>/dev/null || {
            echo "❌ Python syntax errors found"
            count_errors
        }
        
        # Type checking (mypy)
        if check_command mypy; then
            echo "✓ Running mypy type checks..."
            mypy . --ignore-missing-imports 2>&1 | head -20 || {
                echo "⚠️  Type checking issues found (see output above)"
                count_warnings
            }
        fi
        
        # Linting (flake8)
        if check_command flake8; then
            echo "✓ Running flake8 linting..."
            flake8 . --max-line-length=120 --exclude=__pycache__,*.pyc 2>&1 | head -20 || {
                echo "⚠️  Linting issues found (see output above)"
                count_warnings
            }
        fi
        
        # Code formatting (black)
        if check_command black; then
            echo "✓ Checking code formatting (black)..."
            black --check . --line-length=120 2>&1 || {
                echo "⚠️  Code formatting issues found. Run: black ."
                count_warnings
            }
        fi
        
        # Check for common issues
        echo "✓ Checking for common issues..."
        
        # Check for print statements (should use logging)
        if grep -r "print(" --include="*.py" . 2>/dev/null | grep -v "# OK" | head -5; then
            echo "⚠️  Found print() statements (consider using logging)"
            count_warnings
        fi
        
        # Check for TODO/FIXME
        if grep -ri "TODO\|FIXME" --include="*.py" . 2>/dev/null | head -5; then
            echo "⚠️  Found TODO/FIXME comments"
            count_warnings
        fi
        
        # Check for hardcoded secrets
        if grep -ri "password\s*=\s*['\"].*['\"]\|secret\s*=\s*['\"].*['\"]\|api_key\s*=\s*['\"].*['\"]" --include="*.py" . 2>/dev/null | grep -v "# OK" | head -3; then
            echo "❌ Potential hardcoded secrets found!"
            count_errors
        fi
        
        echo "✓ Backend checks complete"
    else
        echo "⚠️  Backend directory not found, skipping backend checks"
    fi
    echo ""
fi

# Frontend Checks
if [ "$CHECK_TYPE" = "frontend" ] || [ "$CHECK_TYPE" = "all" ]; then
    echo "----------------------------------------"
    echo "Frontend Checks"
    echo "----------------------------------------"
    
    if [ -d "$PROJECT_ROOT/frontend" ]; then
        cd "$PROJECT_ROOT/frontend"
        
        # Check if node_modules exists
        if [ ! -d "node_modules" ]; then
            echo "⚠️  node_modules not found. Run: npm install"
            count_warnings
        else
            # Type checking (TypeScript)
            if [ -f "package.json" ] && grep -q "typescript" package.json; then
                echo "✓ Running TypeScript type checks..."
                npm run type-check 2>&1 || {
                    echo "❌ TypeScript errors found"
                    count_errors
                }
            fi
            
            # Linting
            if [ -f "package.json" ] && grep -q "\"lint\"" package.json; then
                echo "✓ Running ESLint..."
                npm run lint 2>&1 || {
                    echo "⚠️  Linting issues found"
                    count_warnings
                }
            fi
            
            # Build check
            if [ -f "package.json" ] && grep -q "\"build\"" package.json; then
                echo "✓ Checking build..."
                npm run build 2>&1 || {
                    echo "❌ Build failed"
                    count_errors
                }
            fi
            
            # Check for console.log
            echo "✓ Checking for console.log statements..."
            if find src -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" 2>/dev/null | xargs grep -l "console\.log" 2>/dev/null | head -5; then
                echo "⚠️  Found console.log statements (remove before submission)"
                count_warnings
            fi
            
            # Check for any types
            echo "✓ Checking for 'any' types..."
            if find src -name "*.ts" -o -name "*.tsx" 2>/dev/null | xargs grep -n ": any" 2>/dev/null | grep -v "// OK" | head -5; then
                echo "⚠️  Found 'any' types (use specific types)"
                count_warnings
            fi
        fi
        
        echo "✓ Frontend checks complete"
    else
        echo "⚠️  Frontend directory not found, skipping frontend checks"
    fi
    echo ""
fi

# Docker Checks
if [ "$CHECK_TYPE" = "all" ]; then
    echo "----------------------------------------"
    echo "Docker Checks"
    echo "----------------------------------------"
    
    if [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        echo "✓ Checking docker-compose.yml syntax..."
        docker compose config > /dev/null 2>&1 || {
            echo "❌ docker-compose.yml has syntax errors"
            count_errors
        }
        echo "✓ Docker checks complete"
    fi
    echo ""
fi

# Summary
echo "=========================================="
echo "Summary"
echo "=========================================="
echo "Errors: $ERRORS"
echo "Warnings: $WARNINGS"
echo ""

if [ $ERRORS -gt 0 ]; then
    echo "❌ FAILED: $ERRORS error(s) found. Please fix before submitting for review."
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo "⚠️  PASSED with warnings: $WARNINGS warning(s) found. Consider fixing before review."
    exit 0
else
    echo "✅ PASSED: All checks passed! Ready for review."
    exit 0
fi

