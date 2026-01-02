#!/bin/bash
# Launcher script for Gaming Mode Web Dashboard
# Usage: ./gaming-mode-web.sh
# Then open: http://localhost:8080

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_SCRIPT="$SCRIPT_DIR/gaming-mode-web.py"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "Error: Python not found. Please install Python 3.7+ and ensure it's in your PATH." >&2
        exit 1
    else
        PYTHON=python
    fi
else
    PYTHON=python3
fi

# Check if Flask library is available
if ! $PYTHON -c "import flask" 2>/dev/null; then
    echo "Installing required 'flask' library..."
    $PYTHON -m pip install flask requests --quiet
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install 'flask' library." >&2
        echo "Try running: pip install flask requests" >&2
        exit 1
    fi
fi

# Run the web server
echo "Starting Gaming Mode Web Dashboard..."
echo "Open your browser to: http://localhost:8080"
echo "Press Ctrl+C to stop"
echo ""
$PYTHON "$WEB_SCRIPT"

