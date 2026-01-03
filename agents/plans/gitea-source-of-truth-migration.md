# Gitea as Source of Truth - Migration Plan

**Status**: IN PROGRESS (Phase 4 - Developer Workflow)  
**Created**: 2026-01-03  
**Last Updated**: 2026-01-03  
**Author**: Agent-assisted planning

## Progress Summary

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 0: Preparation | COMPLETE | Runner deployed, tested on pokedex |
| Phase 1: Import Repos | COMPLETE | All 20 repos in Gitea |
| Phase 2: Push Mirrors | COMPLETE | 8 repos with push mirrors to GitHub |
| Phase 3: CI/CD Migration | COMPLETE | Workflows created for 7 repos, deploy secrets configured |
| Phase 4: Developer Workflow | IN PROGRESS | Script created, docs updated |
| Phase 5: Cutover | PENDING | |

**USER ACTION REQUIRED**: Add `HARBOR_USERNAME` and `HARBOR_PASSWORD` secrets to repos in Gitea (Settings → Actions → Secrets)

## Overview

Migrate from GitHub-centric to Gitea-centric Git workflow:

| Aspect | Current | Target |
|--------|---------|--------|
| Source of Truth | GitHub | Gitea |
| Backup/Mirror | Gitea (pull) | GitHub (push) |
| CI/CD | GitHub Actions | Gitea Actions |
| Developer Push | → GitHub | → Gitea |

## Benefits

1. **Full ownership** - No third-party dependency for primary operations
2. **All repos unified** - Including private repos not on GitHub
3. **Faster CI/CD** - Local runners, no network latency to GitHub
4. **No rate limits** - GitHub API limits don't affect primary workflow
5. **Offline capable** - Core operations work without internet

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Single point of failure** | High - server down = no code | UPS, ZFS snapshots, frequent push mirrors to GitHub |
| **Push mirror failures** | Medium - GitHub backup stale | Monitoring, alerting, manual sync fallback |
| **Gitea Actions immaturity** | Medium - workflow compat issues | Test workflows before migration, keep GitHub as fallback |
| **Developer workflow change** | Low - SSH/remote changes | Clear documentation, gradual transition |
| **Existing GitHub PRs/Issues** | Low - orphaned data | Close/migrate before cutover |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Developer Workstation                     │
│                                                             │
│   git push origin main ──────────────────┐                  │
│                                          │                  │
└──────────────────────────────────────────┼──────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     Home Server (Primary)                    │
│                                                             │
│  ┌─────────────┐    push     ┌─────────────┐               │
│  │   Gitea     │────mirror───▶│   GitHub    │               │
│  │  (source)   │◀────────────│  (backup)   │               │
│  └──────┬──────┘             └─────────────┘               │
│         │                                                   │
│         │ webhook                                           │
│         ▼                                                   │
│  ┌─────────────┐    push     ┌─────────────┐               │
│  │   Gitea     │────image────▶│   Harbor    │               │
│  │   Actions   │             │  Registry   │               │
│  └─────────────┘             └─────────────┘               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Migration Phases

### Phase 0: Preparation (1-2 days)

**Objective**: Ensure infrastructure is ready

- [x] Verify Gitea stability (uptime, backups working)
- [x] Set up Gitea Actions runner (Docker-based)
- [x] Test Gitea Actions on a repo (pokedex - confirmed working)
- [ ] Create GitHub PAT with push access for mirrors
- [ ] Document current GitHub Actions workflows
- [ ] Inventory all repos (GitHub, local-only, private)
- [ ] Add Gitea to rclone/Backblaze backup schedule
- [ ] Set up monitoring/alerting for Gitea

**Gitea Actions Runner Setup** (Docker-based):

```yaml
# Add to apps/gitea/docker-compose.yml
  gitea-runner:
    image: harbor.server.unarmedpuppy.com/docker-hub/gitea/act_runner:latest
    container_name: gitea-runner
    restart: unless-stopped
    depends_on:
      - gitea
    environment:
      - GITEA_INSTANCE_URL=https://gitea.server.unarmedpuppy.com
      - GITEA_RUNNER_REGISTRATION_TOKEN=${GITEA_RUNNER_TOKEN}
      - GITEA_RUNNER_NAME=home-server-runner
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - gitea-runner-data:/data
    networks:
      - my-network
```

**Get Runner Token**:
1. Gitea Admin → Actions → Runners → Create new runner
2. Copy registration token to `.env` as `GITEA_RUNNER_TOKEN`

**Deliverables**:
- Gitea Actions runner operational
- Repo inventory complete
- Backup verification
- Runner can build Docker images

### Phase 1: Import All Repos to Gitea (1 day)

**Objective**: All repos exist in Gitea as primary copies

**Tasks**:
- [ ] Import local-only repos to Gitea (12 repos not on GitHub)
- [ ] Convert existing pull mirrors to regular repos
- [ ] Verify all repo data intact (branches, tags, history)

**Repos to import** (currently local-only):
| Repo | Action |
|------|--------|
| agents | Import from local |
| agents-mono | Import from local |
| budget | Import from local |
| chatterbox-tts-service | Import from local |
| life-os | Import from local (keep private) |
| media-downs-dockerized | Import from local |
| opencode-terminal | Import from local |
| shared-agent-skills | Import from local |
| smart-home-3d | Import from local |
| tcg-scraper | Import from local |
| trading-bot | Import from local |
| trading-journal | Import from local |

**Repos to convert** (pull mirror → regular):
| Repo | Action |
|------|--------|
| agent-gateway | Disable pull mirror, keep as regular |
| beads-viewer | Disable pull mirror, keep as regular |
| home-server | Disable pull mirror, keep as regular |
| homelab-ai | Disable pull mirror, keep as regular |
| maptapdat | Disable pull mirror, keep as regular |
| pokedex | Disable pull mirror, keep as regular |
| polyjuiced | Disable pull mirror, keep as regular |
| workflow-agents | Disable pull mirror, keep as regular |

### Phase 2: Set Up Push Mirrors to GitHub (1 day)

**Objective**: Gitea automatically pushes to GitHub as backup

**Tasks**:
- [ ] Configure push mirrors for each public repo
- [ ] Set mirror interval (recommend: 1 hour or on-push)
- [ ] Test push mirror functionality
- [ ] Verify GitHub repos receive updates

**Push Mirror Configuration**:
```
Gitea Repo Settings → Mirror Settings:
- Mirror Direction: Push
- Remote URL: https://github.com/unarmedpuppy/REPO.git
- Authorization: GitHub PAT
- Sync On Push: Yes (immediate backup)
- Sync Interval: 1h (fallback)
```

**Repos to push-mirror** (public repos):
- agent-gateway
- beads-viewer
- home-server
- homelab-ai
- maptapdat
- pokedex
- polyjuiced
- workflow-agents

**Private repos** (no GitHub mirror):
- life-os
- Others as needed

### Phase 3: Migrate CI/CD to Gitea Actions (2-3 days) - COMPLETE

**Objective**: Build pipelines run in Gitea, not GitHub

**Prerequisites**:
- [x] Gitea Actions runner with Docker access
- [x] Runner can push to Harbor registry
- [ ] Runner has necessary secrets (HARBOR creds need user input)

**Tasks**:
- [x] Set up Gitea Actions runner (Docker-based)
- [x] Migrate workflows repo-by-repo
- [ ] Add Harbor registry credentials to Gitea secrets (USER ACTION)
- [ ] Test builds on Gitea before disabling GitHub Actions
- [ ] Disable GitHub Actions workflows after verification

**Workflow Migration Checklist**:

| Repo | Has CI/CD | Workflow Type | Migration Status |
|------|-----------|---------------|------------------|
| homelab-ai | Yes | Build + push to Harbor (6 images) | `.gitea/workflows/build.yml` created |
| beads-viewer | Yes | Build + push + deploy | `.gitea/workflows/build.yml` created |
| trading-bot | Yes | Build + push to Harbor | `.gitea/workflows/build.yml` created |
| trading-journal | Yes | Build + push (2 images) | `.gitea/workflows/build.yml` created |
| maptapdat | Yes | Build + push to Harbor | `.gitea/workflows/build.yml` created |
| smart-home-3d | Yes | Build + push to Harbor | `.gitea/workflows/build.yml` created |
| opencode-terminal | Yes | Build + push to Harbor | `.gitea/workflows/build.yml` created |
| pokedex | Yes | Build + push + deploy | `.gitea/workflows/test.yml` (existing) |

**Secrets Configured**:
- DEPLOY_HOST, DEPLOY_PORT, DEPLOY_USER, DEPLOY_SSH_KEY: Added to beads-viewer, homelab-ai, pokedex
- HARBOR_USERNAME, HARBOR_PASSWORD: USER ACTION REQUIRED

**Gitea Actions vs GitHub Actions**:
- Gitea Actions is ~95% compatible with GitHub Actions syntax
- Use `runs-on: ubuntu-latest` or custom runner labels
- Secrets stored in Gitea repo/org settings
- Some GitHub-specific actions need alternatives

**Example Workflow Conversion**:
```yaml
# .gitea/workflows/build.yml (same syntax as GitHub)
name: Build and Push
on:
  push:
    tags: ['v*']

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build and push
        run: |
          docker build -t harbor.server.unarmedpuppy.com/library/${{ github.repository }}:${{ github.ref_name }} .
          docker push harbor.server.unarmedpuppy.com/library/${{ github.repository }}:${{ github.ref_name }}
```

### Phase 4: Update Developer Workflows (1 day) - IN PROGRESS

**Objective**: All development points to Gitea

**Tasks**:
- [ ] Update git remotes on all local clones
- [x] Update SSH config for Gitea (documented)
- [x] Update documentation (Gitea reference updated)
- [ ] Update any scripts that reference GitHub URLs

**Automated Script**:
```bash
# Use the switch script for each repo:
./scripts/switch-to-gitea.sh /path/to/repo

# Or from within a repo:
cd /path/to/repo && ~/repos/personal/home-server/scripts/switch-to-gitea.sh
```

**Manual Git Remote Update**:
```bash
# For each local repo:
git remote set-url origin ssh://git@gitea.server.unarmedpuppy.com:2223/unarmedpuppy/REPO.git

# Or add Gitea as new remote, keep GitHub:
git remote rename origin github
git remote add origin ssh://git@gitea.server.unarmedpuppy.com:2223/unarmedpuppy/REPO.git
```

**SSH Config** (`~/.ssh/config`):
```
Host gitea.server.unarmedpuppy.com
    HostName gitea.server.unarmedpuppy.com
    Port 2223
    User git
    IdentityFile ~/.ssh/id_ed25519
```

**Repos to Switch**:
| Repo | Status |
|------|--------|
| home-server | Pending |
| homelab-ai | Pending |
| beads-viewer | Pending |
| maptapdat | Pending |
| smart-home-3d | Pending |
| opencode-terminal | Pending |
| trading-bot | Pending |
| trading-journal | Pending |
| pokedex | Pending |
| polyjuiced | Pending |
| workflow-agents | Pending |
| agent-gateway | Pending |

### Phase 5: Cutover & Cleanup (1 day)

**Objective**: Gitea is definitively the source of truth

**Tasks**:
- [ ] Final sync all repos to Gitea
- [ ] Verify push mirrors working
- [ ] Archive/close GitHub Issues/PRs (if any)
- [ ] Update GitHub repo descriptions: "Mirror of gitea.server.unarmedpuppy.com"
- [ ] Disable GitHub Actions on all repos
- [ ] Update AGENTS.md and documentation
- [ ] Announce migration complete

**GitHub Repo Description Update**:
```
⚠️ MIRROR - Primary repo at https://gitea.server.unarmedpuppy.com/unarmedpuppy/REPO
```

## Rollback Plan

If critical issues arise:

1. **Re-enable GitHub as primary**:
   - Update git remotes back to GitHub
   - Convert Gitea push mirrors to pull mirrors
   - Re-enable GitHub Actions

2. **Keep Gitea as secondary** until issues resolved

## Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 0: Preparation | 1-2 days | None |
| Phase 1: Import Repos | 1 day | Phase 0 |
| Phase 2: Push Mirrors | 1 day | Phase 1 |
| Phase 3: CI/CD Migration | 2-3 days | Phase 2 |
| Phase 4: Developer Workflow | 1 day | Phase 3 |
| Phase 5: Cutover | 1 day | Phase 4 |

**Total: ~7-9 days**

## Success Criteria

- [ ] All 20 repos in Gitea with full history
- [ ] Push mirrors updating GitHub within 1 hour
- [ ] CI/CD builds running in Gitea Actions
- [ ] All developer machines pointing to Gitea
- [ ] Documentation updated
- [ ] Monitoring/alerting in place

## Decisions

| Question | Decision |
|----------|----------|
| Runner infrastructure | Docker-based runner |
| Backup frequency | Nightly via rclone + Backblaze B2 |
| External collaborators | None - Gitea private by default |
| Mobile/web editing | Not needed |
| GitHub visibility | Public mirrors (backup), Gitea is private |

## Edge Case: GitHub Contributions

If someone contributes to a public GitHub mirror (PR, issue, direct push):

**Scenario**: Gitea pushes to GitHub, but someone submits a PR on GitHub.

**Handling Options**:

### Option A: Manual Pull (Recommended for rare cases)
```bash
# On local machine, add GitHub as secondary remote
git remote add github https://github.com/unarmedpuppy/REPO.git
git fetch github
git merge github/main  # or cherry-pick specific commits
git push origin main   # Push to Gitea, which mirrors back to GitHub
```

### Option B: Gitea Scheduled Pull (If contributions are frequent)
Set up a cron job or Gitea Action to periodically check GitHub for new commits:
```yaml
# .gitea/workflows/sync-from-github.yml
name: Sync from GitHub
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:  # Manual trigger

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Fetch and merge from GitHub
        run: |
          git remote add github https://github.com/unarmedpuppy/${{ github.repository }}.git || true
          git fetch github
          if git rev-list HEAD..github/main --count | grep -q '^0$'; then
            echo "No new commits on GitHub"
          else
            git merge github/main --no-edit
            git push origin main
          fi
```

### Option C: Webhook-based (Most complex)
GitHub webhook triggers Gitea to pull on any push to GitHub. Requires:
- GitHub webhook pointing to Gitea
- Gitea endpoint to handle webhook
- More infrastructure, probably overkill

**Recommendation**: Start with Option A (manual). If GitHub contributions become frequent, implement Option B.

## Edge Case: Web/Mobile Editing

If you ever need to make quick edits without a full dev environment:

**Gitea Web Editor**:
- Gitea has built-in web editor (click file → Edit)
- Less polished than GitHub but functional
- Accessible at https://gitea.server.unarmedpuppy.com

**VS Code Server (Alternative)**:
- Could deploy code-server or VS Code tunnel for full IDE in browser
- More setup but much better editing experience
- Consider if web editing becomes frequent

**Current Setup**:
- OpenCode Terminal at https://terminal.server.unarmedpuppy.com provides CLI access
- Can use `vim`/`nano` for quick edits via terminal

**Recommendation**: Gitea web editor is sufficient for rare quick fixes. No additional infrastructure needed.

## Related Files

- `apps/gitea/docker-compose.yml` - Gitea service
- `agents/personas/gitea-agent.md` - Management persona
- `agents/skills/add-gitea-mirror/SKILL.md` - Mirror management
- `agents/reference/gitea/README.md` - API reference

## Next Steps

1. Review this plan
2. Answer open questions
3. Begin Phase 0 when ready
