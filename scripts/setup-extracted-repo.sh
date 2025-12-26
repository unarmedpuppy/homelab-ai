#!/bin/bash
# Set up an extracted repo with GitHub Actions workflow
#
# Usage: ./setup-extracted-repo.sh <app_name>

set -e

APP_NAME="${1:?Usage: $0 <app_name>}"
REPO_DIR="$HOME/repos/personal/$APP_NAME"

if [ ! -d "$REPO_DIR" ]; then
    echo "ERROR: Repo not found: $REPO_DIR"
    exit 1
fi

echo "=== Setting up $APP_NAME ==="

cd "$REPO_DIR"

# Create .github/workflows directory
mkdir -p .github/workflows

# Create GitHub Actions workflow
cat > .github/workflows/build.yml << 'EOF'
name: Build and Push

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:
    inputs:
      tag:
        description: 'Tag to build (e.g., v1.0.0)'
        required: true
        default: 'latest'

env:
  REGISTRY: registry.server.unarmedpuppy.com
  IMAGE_NAME: APP_NAME_PLACEHOLDER

jobs:
  build:
    runs-on: ubuntu-latest
    environment: Homelab
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to private registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ secrets.REGISTRY_USERNAME }}
          password: ${{ secrets.REGISTRY_PASSWORD }}

      - name: Extract version
        id: version
        run: |
          if [ "${{ github.event_name }}" == "workflow_dispatch" ]; then
            echo "VERSION=${{ github.event.inputs.tag }}" >> $GITHUB_OUTPUT
          else
            echo "VERSION=${GITHUB_REF#refs/tags/}" >> $GITHUB_OUTPUT
          fi

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ steps.version.outputs.VERSION }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
EOF

# Replace placeholder with actual app name
sed -i '' "s/APP_NAME_PLACEHOLDER/$APP_NAME/g" .github/workflows/build.yml

# Create .gitignore if it doesn't exist
if [ ! -f .gitignore ]; then
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
venv/
.venv/
*.egg-info/

# Node
node_modules/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Environment
.env
.env.local
EOF
fi

# Simplify docker-compose.yml for local dev (if it has Traefik labels)
if grep -q "traefik" docker-compose.yml 2>/dev/null; then
    # Backup original
    cp docker-compose.yml docker-compose.yml.bak

    # Create simple local dev version
    cat > docker-compose.yml << EOF
# Local development docker-compose
# For production deployment, see the home-server repo

services:
  $APP_NAME:
    build: .
    container_name: $APP_NAME
    ports:
      - "8080:80"
EOF

    rm docker-compose.yml.bak
fi

# Stage and commit
git add .
git commit -m "chore: Set up standalone repo with GitHub Actions CI

- Add GitHub Actions workflow for building and pushing to private registry
- Add .gitignore

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>" || echo "Nothing to commit"

echo "=== $APP_NAME setup complete ==="
