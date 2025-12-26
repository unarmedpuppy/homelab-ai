#!/bin/bash
# Extract an app from home-server into its own repository with git history preserved
#
# Usage: ./extract-app-to-repo.sh <app_name> [target_dir]
#
# Example: ./extract-app-to-repo.sh pokedex ~/repos/personal/pokedex

set -e

APP_NAME="${1:?Usage: $0 <app_name> [target_dir]}"
TARGET_DIR="${2:-$HOME/repos/personal/$APP_NAME}"
SOURCE_REPO="$(cd "$(dirname "$0")/.." && pwd)"
TEMP_DIR=$(mktemp -d)

echo "=== Extracting $APP_NAME from home-server ==="
echo "Source: $SOURCE_REPO"
echo "Target: $TARGET_DIR"
echo "Temp:   $TEMP_DIR"
echo ""

# Check if target already exists
if [ -d "$TARGET_DIR" ]; then
    echo "ERROR: Target directory already exists: $TARGET_DIR"
    echo "Please remove it first or specify a different target."
    exit 1
fi

# Check if app exists in source
if [ ! -d "$SOURCE_REPO/apps/$APP_NAME" ]; then
    echo "ERROR: App not found: $SOURCE_REPO/apps/$APP_NAME"
    exit 1
fi

# Clone the repo (fresh clone needed for filter-repo)
echo ">>> Cloning repository..."
git clone "$SOURCE_REPO" "$TEMP_DIR/repo"
cd "$TEMP_DIR/repo"

# Remove remote to prevent accidental pushes
git remote remove origin

echo ">>> Filtering to apps/$APP_NAME/..."
git filter-repo --subdirectory-filter "apps/$APP_NAME" --force

# The filter-repo --subdirectory-filter automatically moves files to root
# So we should have all files at the root now

echo ">>> Moving to target directory..."
mkdir -p "$(dirname "$TARGET_DIR")"
mv "$TEMP_DIR/repo" "$TARGET_DIR"

# Clean up
rm -rf "$TEMP_DIR"

echo ""
echo "=== Extraction complete! ==="
echo ""
echo "Next steps:"
echo "  cd $TARGET_DIR"
echo "  git log --oneline -10    # Verify history"
echo "  git remote add origin git@github.com:YOUR_USERNAME/$APP_NAME.git"
echo "  git push -u origin main"
echo ""
