#!/bin/bash
# Launcher script for Gaming Mode GUI
# Usage: ./gaming-mode-gui.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GUI_SCRIPT="$SCRIPT_DIR/gaming-mode-gui.py"

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

# Check if requests library is available
if ! $PYTHON -c "import requests" 2>/dev/null; then
    echo "Installing required 'requests' library..."
    $PYTHON -m pip install requests --quiet
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install 'requests' library." >&2
        echo "Try running: pip install requests" >&2
        exit 1
    fi
fi

# Run the GUI
echo "Starting Gaming Mode GUI..."
$PYTHON "$GUI_SCRIPT"

