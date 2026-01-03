---
name: github-actions-auto-deploy
description: Set up GitHub Actions to auto-deploy to server on tag push
when_to_use: When you want CI/CD to automatically deploy Docker containers after building images
---

# GitHub Actions Auto-Deploy

Automatically deploy Docker containers to the home server when pushing version tags.

## Quick Start

### 1. Copy Workflow Template

Add this to `.github/workflows/deploy.yml` in your repo:

```yaml
name: Build and Deploy

on:
  push:
    branches:
      - main
    tags:
      - 'v*'
  workflow_dispatch:
    inputs:
      deploy:
        description: 'Deploy after build'
        type: boolean
        default: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Harbor
        uses: docker/login-action@v3
        with:
          registry: ${{ secrets.HARBOR_REGISTRY }}
          username: ${{ secrets.HARBOR_USERNAME }}
          password: ${{ secrets.HARBOR_PASSWORD }}

      - name: Extract version
        id: version
        run: |
          if [[ "${{ github.ref }}" == refs/tags/v* ]]; then
            echo "tag=${GITHUB_REF#refs/tags/}" >> $GITHUB_OUTPUT
          else
            echo "tag=latest" >> $GITHUB_OUTPUT
          fi

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: |
            ${{ secrets.HARBOR_REGISTRY }}/library/YOUR_APP:latest
            ${{ secrets.HARBOR_REGISTRY }}/library/YOUR_APP:${{ steps.version.outputs.tag }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    needs: build
    if: startsWith(github.ref, 'refs/tags/') || inputs.deploy == true
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.DEPLOY_HOST }}
          username: ${{ secrets.DEPLOY_USER }}
          key: ${{ secrets.DEPLOY_SSH_KEY }}
          port: ${{ secrets.DEPLOY_PORT }}
          script: |
            cd ~/server
            git pull origin main
            cd apps/YOUR_APP
            sudo docker compose pull
            sudo docker compose up -d --remove-orphans
            sudo docker image prune -f
```

### 2. Configure GitHub Secrets

Add these secrets to your repo (Settings → Secrets → Actions):

| Secret | Value |
|--------|-------|
| `HARBOR_REGISTRY` | `harbor.server.unarmedpuppy.com` |
| `HARBOR_USERNAME` | Harbor username |
| `HARBOR_PASSWORD` | Harbor password |
| `DEPLOY_HOST` | `192.168.86.47` |
| `DEPLOY_PORT` | `4242` |
| `DEPLOY_USER` | `github-deploy` |
| `DEPLOY_SSH_KEY` | Private key (see below) |

### 3. Set Up Deploy User (One-Time on Server)

```bash
# Generate SSH key locally
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github-deploy-key -N ""

# On server: Create user and add key
ssh -p 4242 unarmedpuppy@192.168.86.47 << 'EOF'
sudo useradd -m -s /bin/bash github-deploy
sudo mkdir -p /home/github-deploy/.ssh
sudo chmod 700 /home/github-deploy/.ssh
# Add your public key here:
echo 'ssh-ed25519 YOUR_PUBLIC_KEY github-actions-deploy' | sudo tee /home/github-deploy/.ssh/authorized_keys
sudo chmod 600 /home/github-deploy/.ssh/authorized_keys
sudo chown -R github-deploy:github-deploy /home/github-deploy/.ssh
sudo usermod -p '*' github-deploy

# Grant sudo for docker
sudo tee /etc/sudoers.d/github-deploy << 'SUDOERS'
github-deploy ALL=(ALL) NOPASSWD: /usr/bin/docker compose *
github-deploy ALL=(ALL) NOPASSWD: /usr/bin/docker pull *
github-deploy ALL=(ALL) NOPASSWD: /usr/bin/docker image prune -f
github-deploy ALL=(ALL) NOPASSWD: /usr/bin/git -C /home/unarmedpuppy/server *
SUDOERS

sudo usermod -aG unarmedpuppy github-deploy
EOF
```

### 4. Deploy

```bash
# Tag and push to trigger deployment
git tag v1.0.0
git push origin v1.0.0
```

## Workflow Triggers

| Trigger | Builds | Deploys |
|---------|--------|---------|
| Push to main | ✅ | ❌ |
| Push tag `v*` | ✅ | ✅ |
| Manual + deploy | ✅ | ✅ |

## Example Repos Using This Pattern

- `agent-gateway` - Agent Core + Gateway services
- `homelab-ai` - LLM Router + Dashboard

## Troubleshooting

**SSH fails**: Ensure private key in GitHub includes `-----BEGIN/END-----` lines

**Docker permission denied**: Check `/etc/sudoers.d/github-deploy` syntax with `visudo -cf`

**Deploy skipped**: Only runs on `v*` tags or manual with deploy=true