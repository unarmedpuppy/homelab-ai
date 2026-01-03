# Gitea as Source of Truth - Migration Plan

**Status**: PLANNING  
**Created**: 2026-01-03  
**Author**: Agent-assisted planning

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

- [ ] Verify Gitea stability (uptime, backups working)
- [ ] Set up Gitea Actions runner
- [ ] Create GitHub PAT with push access for mirrors
- [ ] Document current GitHub Actions workflows
- [ ] Inventory all repos (GitHub, local-only, private)
- [ ] Set up monitoring/alerting for Gitea

**Deliverables**:
- Gitea Actions runner operational
- Repo inventory spreadsheet
- Backup verification

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

### Phase 3: Migrate CI/CD to Gitea Actions (2-3 days)

**Objective**: Build pipelines run in Gitea, not GitHub

**Prerequisites**:
- Gitea Actions runner with Docker access
- Runner can push to Harbor registry
- Runner has necessary secrets

**Tasks**:
- [ ] Set up Gitea Actions runner (Docker-based)
- [ ] Migrate workflows repo-by-repo
- [ ] Add Harbor registry credentials to Gitea secrets
- [ ] Test builds on Gitea before disabling GitHub Actions
- [ ] Disable GitHub Actions workflows after verification

**Workflow Migration Checklist**:

| Repo | Has CI/CD | Workflow Type | Migration Status |
|------|-----------|---------------|------------------|
| homelab-ai | Yes | Build + push to Harbor | Pending |
| agent-gateway | Yes | Build + push to Harbor | Pending |
| trading-bot | Yes | Build + push to Harbor | Pending |
| trading-journal | Yes | Build + push to Harbor | Pending |
| (others) | TBD | TBD | TBD |

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

### Phase 4: Update Developer Workflows (1 day)

**Objective**: All development points to Gitea

**Tasks**:
- [ ] Update git remotes on all local clones
- [ ] Update SSH config for Gitea
- [ ] Update documentation
- [ ] Update any scripts that reference GitHub URLs

**Git Remote Update**:
```bash
# For each local repo:
git remote set-url origin git@gitea.server.unarmedpuppy.com:unarmedpuppy/REPO.git

# Or add Gitea as new remote, keep GitHub:
git remote rename origin github
git remote add origin git@gitea.server.unarmedpuppy.com:unarmedpuppy/REPO.git
```

**SSH Config** (`~/.ssh/config`):
```
Host gitea.server.unarmedpuppy.com
    HostName gitea.server.unarmedpuppy.com
    Port 2223
    User git
    IdentityFile ~/.ssh/id_ed25519
```

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

## Open Questions

1. **Runner infrastructure**: Use Docker-based runner or dedicated VM?
2. **Secrets management**: How to securely store Harbor credentials in Gitea?
3. **Backup frequency**: How often should Gitea data be backed up?
4. **External collaborators**: If any repos need external contributors, GitHub might still be better
5. **Mobile/web editing**: GitHub web UI is more polished - is this needed?

## Related Files

- `apps/gitea/docker-compose.yml` - Gitea service
- `agents/personas/gitea-agent.md` - Management persona
- `agents/skills/add-gitea-mirror/SKILL.md` - Mirror management
- `agents/reference/gitea/README.md` - API reference

## Next Steps

1. Review this plan
2. Answer open questions
3. Begin Phase 0 when ready
