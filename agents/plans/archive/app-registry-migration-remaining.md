# App Registry Migration - Remaining Steps

**Status**: In Progress
**Created**: 2024-12-23
**Last Updated**: 2024-12-23

## Summary

Custom apps have been extracted from the home-server monorepo into separate repositories with GitHub Actions CI/CD configured to build and push Docker images to the private registry.

## Completed

- [x] Private Docker registry deployed at `registry.server.unarmedpuppy.com`
- [x] Registry UI deployed at `registry-ui.server.unarmedpuppy.com`
- [x] Extraction script created: `scripts/extract-app-to-repo.sh`
- [x] Setup script created: `scripts/setup-extracted-repo.sh`
- [x] All apps extracted to `~/repos/personal/<app-name>` with git history preserved
- [x] All docker-compose files updated to use registry images
- [x] Source code removed from home-server monorepo
- [x] Home-server changes pushed to GitHub

## Apps Status

| App | Extracted | GitHub Repo | Secrets | Image Built | Deployed |
|-----|-----------|-------------|---------|-------------|----------|
| pokedex | ✅ | ✅ | ✅ | ✅ | ✅ |
| trading-bot | ✅ | ⬜ | ⬜ | ⬜ | ⬜ |
| polymarket-bot | ✅ | ⬜ | ⬜ | ⬜ | ⬜ |
| trading-journal | ✅ | ⬜ | ⬜ | ⬜ | ⬜ |
| maptapdat | ✅ | ⬜ | ⬜ | ⬜ | ⬜ |
| smart-home-3d | ✅ | ⬜ | ⬜ | ⬜ | ⬜ |
| beads-viewer | ✅ | ⬜ | ⬜ | ⬜ | ⬜ |
| opencode-terminal | ✅ | ⬜ | ⬜ | ⬜ | ⬜ |

## Remaining Steps Per App

For each app (except pokedex), complete these steps:

### 1. Create GitHub Repository

Go to https://github.com/new and create a new repository:
- Name: `<app-name>` (e.g., `trading-bot`)
- Visibility: Private (recommended)
- Don't initialize with README (repo already has content)

### 2. Push Extracted Repository

```bash
cd ~/repos/personal/<app-name>
git remote add origin git@github.com:unarmedpuppy/<app-name>.git
git branch -M main
git push -u origin main
```

### 3. Configure GitHub Secrets

1. Go to repo Settings → Environments
2. Create environment named `Homelab` (if not exists)
3. Add secrets:
   - `REGISTRY_USERNAME`: Your registry username
   - `REGISTRY_PASSWORD`: Your registry password

### 4. Build Initial Image

```bash
cd ~/repos/personal/<app-name>
git tag v1.0.0
git push --tags
```

This triggers GitHub Actions to build and push the image.

### 5. Verify Image in Registry

Visit https://registry-ui.server.unarmedpuppy.com and confirm the image appears.

### 6. Deploy on Server

```bash
# From home-server directory
scripts/connect-server.sh "cd ~/server/apps/<app-name> && docker compose pull && docker compose up -d"
```

## Special Cases

### trading-journal

Has two images that need to be built:
- `trading-journal-backend`
- `trading-journal-frontend`

The workflow at `.github/workflows/build.yml` handles both.

## Quick Reference Commands

```bash
# List extracted repos
ls ~/repos/personal/{trading-bot,polymarket-bot,trading-journal,maptapdat,smart-home-3d,beads-viewer,opencode-terminal}

# Check if repo has remote configured
cd ~/repos/personal/<app-name> && git remote -v

# Check GitHub Actions status (after pushing)
gh run list --repo unarmedpuppy/<app-name>

# Deploy all updated apps at once (after images are built)
for app in trading-bot polymarket-bot trading-journal maptapdat smart-home-3d beads-viewer opencode-terminal; do
  scripts/connect-server.sh "cd ~/server/apps/$app && docker compose pull && docker compose up -d"
done
```

## Registry Credentials

Stored in `apps/registry/auth/htpasswd` on the server. Same credentials used for:
- Docker login to registry
- GitHub Actions secrets
- Registry UI login
