#!/bin/bash
# Helper script to install mutagen on macOS (handles externally-managed-environment)

echo "Installing mutagen for music organization..."

# Try different installation methods
if pip3 install --user --break-system-packages mutagen 2>&1 | grep -q "Successfully installed"; then
    echo "✓ Installed mutagen successfully"
    exit 0
elif pip3 install --user mutagen 2>&1 | grep -q "Successfully installed"; then
    echo "✓ Installed mutagen successfully (without --break-system-packages)"
    exit 0
else
    echo "✗ Automatic installation failed"
    echo ""
    echo "Please install manually:"
    echo "  pip3 install --user --break-system-packages mutagen"
    echo ""
    echo "Or use a virtual environment:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install mutagen"
    exit 1
fi

