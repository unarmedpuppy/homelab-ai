---
name: deploy-home-server
description: Deploy docker-compose changes to home-server via Gitea Actions
when_to_use: After making changes to any docker-compose.yml files in home-server
---

# Deploy Home Server Changes

Deploy docker-compose changes to the server automatically via Gitea Actions. No SSH required.

## When to Use

After making ANY changes to:
- `apps/*/docker-compose.yml`
- `apps/*/.env` (environment files)
- Any other config that requires container restart

## Workflow

```bash
# 1. Stage and commit changes
git add <changed-files>
git commit -m "feat/fix/chore: description"

# 2. Push to main
git push

# 3. Get latest tag and increment
git tag -l --sort=-v:refname | head -1
# Example output: v0.1.11

# 4. Create and push new tag
git tag v0.1.12
git push origin v0.1.12
```

## What Happens

1. Gitea Actions workflow triggers on tag push
2. Workflow SSHs to server as `github-deploy` user
3. Runs `git pull` in `~/server`
4. Detects which `apps/` directories changed
5. Runs `docker compose up -d` only for changed apps

## One-Liner

```bash
git add . && git commit -m "message" && git push && \
  git tag v$(git tag -l 'v*' --sort=-v:refname | head -1 | sed 's/v//' | awk -F. '{print $1"."$2"."$3+1}') && \
  git push origin $(git tag -l --sort=-v:refname | head -1)
```

## Important Notes

- **Never SSH to deploy** - Always use this workflow
- Workflow only restarts apps with changed files
- Tags must follow semver: `v0.1.x`
- Check Gitea Actions for deployment status

## Verification

After tagging, check deployment:
1. Gitea Actions: `https://gitea.server.unarmedpuppy.com/homelab/home-server/actions`
2. Or wait ~30 seconds and verify the service is running
