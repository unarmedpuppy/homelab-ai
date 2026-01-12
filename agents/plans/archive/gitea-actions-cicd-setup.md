# Gitea Actions & CI/CD Setup

**Created**: 2026-01-03
**Status**: WORKING - Need to configure repo secrets
**Last Session**: Runner creating containers and executing steps successfully

## Current State

✅ **WORKING:**
- act_runner registered and picking up jobs
- Job containers created on `my-network`
- Workflow steps executing (checkout, git operations work)
- Docker CLI available in job containers

❌ **Remaining:**
- Configure secrets in Gitea for `homelab/pokedex` repo
- Test full build → push → deploy flow

## Key Fixes Applied

1. **Runner container must be `privileged: true`** - Required for Docker-in-Docker
2. **Job containers must be on `my-network`** - So they can resolve `gitea` hostname
3. **Use Harbor image path in labels** - `docker://harbor.server.unarmedpuppy.com/ghcr/catthehacker/ubuntu:act-latest`
4. **Remove duplicate docker socket mount** - Was causing issues with duplicate binds

## Summary

Set up Gitea Actions CI/CD on the self-hosted Gitea instance and added GitHub Actions workflows to personal repos for automated Docker builds and deployments.

## What Was Completed

### 1. Gitea Actions Setup (DONE)

Successfully configured Gitea Actions with act_runner:

**Configuration Files:**
- `apps/gitea/docker-compose.yml` - Added `act-runner` service
- `apps/gitea/config/runner-config.yaml` - Runner config with network settings
- `apps/gitea/env.template` - Added `GITEA_RUNNER_TOKEN`

**Key Settings:**
```yaml
# docker-compose.yml - act-runner service
environment:
  - GITEA_INSTANCE_URL=http://gitea:3000
  - GITEA_RUNNER_LABELS=ubuntu-latest:docker://node:20-bookworm,ubuntu-22.04:docker://node:20-bookworm
volumes:
  - ./config/runner-config.yaml:/config/config.yaml:ro
  - /var/run/docker.sock:/var/run/docker.sock

# runner-config.yaml - Critical for DNS resolution
container:
  network: my-network  # Job containers join this network to resolve 'gitea' hostname
```

**Issue Resolved:** Job containers couldn't resolve `gitea` hostname. Fixed by:
1. Setting `container.network: my-network` in runner config
2. Redeploying with fresh volume: `docker volume rm gitea_act-runner-data`

**Verification:** Test workflow ran successfully on pokedex repo.

### 2. GitHub Actions Workflows Added

Added CI/CD workflows for Docker build + push to Harbor registry:

| Repo | Workflow | Status |
|------|----------|--------|
| beads-viewer | `.github/workflows/build.yml` | Added, needs GitHub secrets |
| pokedex | `.github/workflows/build.yml` | Added, needs GitHub secrets |
| polyjuiced | `.github/workflows/build.yml` | Added (builds `polymarket-bot`), needs GitHub secrets |
| maptapdat | `.github/workflows/build.yml` | Added, needs GitHub secrets |

**Workflow Pattern:**
- Triggers on version tags (`v*`) and `workflow_dispatch`
- Builds Docker image with buildx
- Pushes to `harbor.server.unarmedpuppy.com/library/<image>`
- Auto-deploys to server via SSH on tag push

### 3. Gitea Workflow Added

Added Gitea Actions workflow to pokedex for testing:
- `.gitea/workflows/test.yml` - Now contains full build/deploy workflow

## What's Not Done

### Gitea Secrets Configuration (PRIORITY)

Configure these secrets in Gitea for `homelab/pokedex`:
1. Go to: https://gitea.server.unarmedpuppy.com/homelab/pokedex/settings/actions/secrets
2. Add these secrets:

| Secret | Value |
|--------|-------|
| `REGISTRY_USERNAME` | Harbor username (e.g., `admin`) |
| `REGISTRY_PASSWORD` | Harbor password |
| `DEPLOY_HOST` | `192.168.86.47` (internal IP) |
| `DEPLOY_PORT` | `4242` |
| `DEPLOY_USER` | `github-deploy` |
| `DEPLOY_SSH_KEY` | Contents of `~/.ssh/github-deploy-key` |

### GitHub Secrets Configuration

Each repo needs these secrets configured in GitHub:

| Secret | Value |
|--------|-------|
| `DEPLOY_HOST` | `73.94.229.18` (external IP) |
| `DEPLOY_PORT` | `4242` |
| `DEPLOY_USER` | `github-deploy` |
| `DEPLOY_SSH_KEY` | Contents of `~/.ssh/github-deploy-key` |

**To configure:** GitHub repo > Settings > Secrets and variables > Actions > New repository secret

### Repos Not on GitHub

These repos exist locally but aren't on GitHub yet:

| Repo | Has Dockerfile | Has Workflow | Notes |
|------|----------------|--------------|-------|
| opencode-terminal | Yes | Yes (local) | Simple ttyd container |
| smart-home-3d | Yes | Yes (local) | React + Express app |
| trading-bot | Yes | Yes (local, updated) | Updated registry to Harbor |
| trading-journal | Yes (2) | Yes (local) | Backend + Frontend Dockerfiles |

**To push to GitHub:**
1. Create repo on GitHub
2. `git remote add origin git@github.com:unarmedpuppy/<repo>.git`
3. `git push -u origin main`
4. Configure secrets
5. Add to Gitea mirrors

## File Locations

```
apps/gitea/
├── docker-compose.yml      # Gitea + PostgreSQL + act-runner
├── config/
│   └── runner-config.yaml  # Runner config (network: my-network)
├── env.template            # Environment variables template
└── README.md               # Updated with Actions documentation

# Workflow files in each repo:
<repo>/.github/workflows/build.yml   # GitHub Actions
<repo>/.gitea/workflows/*.yml        # Gitea Actions (optional)
```

## Commands Reference

```bash
# Check runner status
ssh -p 4242 unarmedpuppy@192.168.86.47 "docker logs gitea-act-runner 2>&1 | tail -50"

# Restart runner with fresh config
ssh -p 4242 unarmedpuppy@192.168.86.47 "cd ~/server/apps/gitea && docker compose down act-runner && docker volume rm gitea_act-runner-data && docker compose up -d act-runner"

# Trigger mirror sync (to pull GitHub changes to Gitea)
curl -X POST "https://gitea.server.unarmedpuppy.com/api/v1/repos/unarmedpuppy/<REPO>/mirror-sync" \
  -H "Authorization: token bae92395084591de4d32e8deefe780e9b4123ba1"

# Check workflow runs
# Via Gitea web UI: https://gitea.server.unarmedpuppy.com/<owner>/<repo>/actions
```

## Next Steps

### Priority 1: Configure GitHub Secrets
For repos already on GitHub with workflows (beads-viewer, pokedex, polyjuiced, maptapdat):
1. Go to each repo's Settings > Secrets
2. Add the 4 deployment secrets listed above
3. Test by pushing a version tag: `git tag v0.1.0 && git push origin v0.1.0`

### Priority 2: Push Remaining Repos to GitHub
For opencode-terminal, smart-home-3d, trading-bot, trading-journal:
1. Create GitHub repos (can be private)
2. Push code with `git remote add origin ... && git push -u origin main`
3. Configure secrets
4. Add as Gitea mirrors via `scripts/setup-gitea-mirrors.sh` or manually

### Priority 3: Create Gitea-Only Workflows (Optional)
For repos that should only build on Gitea (not GitHub):
- Create `.gitea/workflows/build.yml` with Harbor registry config
- Useful for private repos that shouldn't be on GitHub

## Troubleshooting

### Runner Not Picking Up Jobs
```bash
# Check runner is registered
docker logs gitea-act-runner 2>&1 | grep "registered"

# Verify runner appears in Gitea UI
# Site Administration > Actions > Runners
```

### Job Container DNS Fails
```bash
# Ensure runner config has network set
docker exec gitea-act-runner cat /config/config.yaml | grep network

# Should show: network: my-network
# If not, redeploy with fresh volume
```

### Workflow Not Triggering
- Check branch name matches workflow trigger (main vs master)
- Verify workflow file is in correct location (`.gitea/workflows/` or `.github/workflows/`)
- For mirrors: trigger sync first, then check if workflow runs
