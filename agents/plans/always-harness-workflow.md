# Always Harness Workflow Plan

## Status: PLANNING

## Overview

Migrate to a "single source of truth" development workflow where the Claude Harness on the server is the primary development environment. Local machines become thin clients that connect to the harness.

## Goals

1. **Single environment** - No sync issues, one place for all work
2. **Multi-device access** - Laptop, PC, phone all connect to same workspace
3. **Unified context** - One AGENTS.md, one beads database, shared across all repos
4. **Simplified local** - Local machines are for reading/reference only

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Harness (Server)                   │
│                   "Single Source of Truth"                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  /workspace/                                                 │
│  ├── AGENTS.md              ← Cross-repo agent instructions │
│  ├── .beads/                ← Unified task database         │
│  │   └── issues.jsonl                                       │
│  ├── skills/                ← Shared skills (symlinked)     │
│  ├── personas/              ← Shared personas (symlinked)   │
│  │                                                          │
│  ├── home-server/           ← All homelab repos             │
│  ├── homelab-ai/                                            │
│  ├── pokedex/                                               │
│  ├── polyjuiced/                                            │
│  ├── agent-gateway/                                         │
│  ├── beads-viewer/                                          │
│  ├── maptapdat/                                             │
│  ├── trading-bot/                                           │
│  ├── trading-journal/                                       │
│  └── workflows/             ← Shared CI/CD workflows        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
         ▲              ▲              ▲
         │              │              │
    ┌────┴────┐    ┌────┴────┐    ┌────┴────┐
    │ Laptop  │    │   PC    │    │  Phone  │
    │  SSH    │    │  SSH    │    │  ttyd   │
    │ VS Code │    │ VS Code │    │ browser │
    └─────────┘    └─────────┘    └─────────┘
```

## Access Methods

| Device | Method | Use Case |
|--------|--------|----------|
| Laptop/PC | SSH terminal | Primary development |
| Laptop/PC | VS Code Remote SSH | When IDE features needed |
| Phone/Tablet | ttyd web terminal | Quick fixes, monitoring |
| Any browser | code-server (optional) | Full IDE from browser |

## Implementation Steps

### Phase 1: Update Claude Harness

**1.1 Update entrypoint.sh to clone all repos**

Current bootstrap only clones home-server and homelab-ai. Update to clone all homelab repos:

```bash
REPOS=(
  "home-server"
  "homelab-ai"
  "pokedex"
  "polyjuiced"
  "agent-gateway"
  "beads-viewer"
  "maptapdat"
  "trading-bot"
  "trading-journal"
  "workflows"
)

setup_workspace() {
  for repo in "${REPOS[@]}"; do
    if [ ! -d "$repo" ] && [ -n "${GITHUB_TOKEN:-}" ]; then
      gosu "$APPUSER" git clone "https://github.com/unarmedpuppy/${repo}.git"
    fi
  done
}
```

**1.2 Create /workspace/AGENTS.md**

Top-level agent instructions that:
- Explain the workspace structure
- Reference individual repo AGENTS.md files
- Define cross-repo workflows
- Point to shared beads database

**1.3 Install beads in container**

Add to Dockerfile:
```dockerfile
# Install Rust and beads
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
RUN /root/.cargo/bin/cargo install beads-cli
```

Or install pre-built binary if available.

**1.4 Initialize beads in /workspace**

Add to entrypoint.sh:
```bash
setup_beads() {
  if [ ! -d "/workspace/.beads" ]; then
    cd /workspace
    gosu "$APPUSER" bd init
  fi
}
```

**1.5 Add beads daemon to startup**

Run beads daemon alongside other services:
```bash
gosu "$APPUSER" bd daemon start &
```

### Phase 2: Create Workspace Structure

**2.1 /workspace/AGENTS.md content**

```markdown
# Homelab Workspace - Agent Instructions

This is the unified development workspace for all homelab projects.

## Workspace Structure

- `/workspace/` - Root workspace (you are here)
- `/workspace/.beads/` - Unified task database
- `/workspace/<repo>/` - Individual project repos

## Cross-Repo Workflows

### Task Management
All tasks tracked in /workspace/.beads/:
- `bd ready` - Find unblocked work
- `bd list` - View all tasks
- `bd create "title" -p 1` - Create task

### Deployment
- Code changes: Push tag → CI builds → Harbor Deployer auto-deploys
- Config changes: Push to home-server → Gitea Actions deploys

## Per-Repo Context

Each repo has its own AGENTS.md with specific instructions:
- `home-server/AGENTS.md` - Server infrastructure
- `homelab-ai/AGENTS.md` - AI services
- etc.

## Quick Commands

# SSH to server (if needed for debugging)
ssh -p 4242 unarmedpuppy@host.docker.internal

# Check all repo status
for d in */; do echo "=== $d ===" && git -C "$d" status -s; done

# Pull all repos
for d in */; do git -C "$d" pull; done
```

**2.2 Symlink shared resources (optional)**

If we want shared skills/personas at workspace level:
```bash
ln -s home-server/agents/skills /workspace/skills
ln -s home-server/agents/personas /workspace/personas
```

### Phase 3: Update Individual Repos

**3.1 Remove beads from home-server**

- Delete `.beads/` directory from home-server
- Update AGENTS.md to reference workspace-level beads
- Remove beads-related git hooks

**3.2 Update repo AGENTS.md files**

Add header to each repo's AGENTS.md:
```markdown
> **Note**: This repo is typically accessed via the Claude Harness.
> Cross-repo tasks are tracked in `/workspace/.beads/`.
> See `/workspace/AGENTS.md` for workspace-wide context.
```

### Phase 4: Improve Access

**4.1 Ensure ttyd is mobile-friendly**

- Test on phone browsers
- Adjust font size / touch handling if needed
- Consider adding viewport meta tag

**4.2 VS Code Remote SSH setup**

Document in README:
```bash
# Add to ~/.ssh/config on local machine
Host harness
  HostName server.unarmedpuppy.com
  Port 4242
  User appuser
  IdentityFile ~/.ssh/id_ed25519

# Then in VS Code: Remote-SSH: Connect to Host → harness
```

**4.3 (Optional) Add code-server**

For full VS Code in browser:
```dockerfile
# Add to Dockerfile
RUN curl -fsSL https://code-server.dev/install.sh | sh
```

Add to docker-compose:
```yaml
ports:
  - "8443:8443"  # code-server
```

### Phase 5: Documentation

**5.1 Update home-server README**

Add "Development Workflow" section explaining harness-first approach.

**5.2 Create reference doc**

`agents/reference/harness-workflow.md` with:
- How to connect
- Workspace structure
- Common workflows
- Troubleshooting

**5.3 Update AGENTS.md boundaries**

Local AGENTS.md should note:
- "For full development workflow, connect to Claude Harness"
- "Local is for reference only"

## Migration Checklist

- [ ] Update claude-harness/entrypoint.sh to clone all repos
- [ ] Add beads installation to Dockerfile
- [ ] Create /workspace/AGENTS.md template
- [ ] Add beads init/daemon to entrypoint.sh
- [ ] Remove .beads/ from home-server repo
- [ ] Update home-server/AGENTS.md
- [ ] Test SSH access from laptop/PC
- [ ] Test ttyd from phone
- [ ] Test VS Code Remote SSH
- [ ] Document in reference guide

## Rollback Plan

If this approach doesn't work:
1. Keep beads in home-server (restore from git)
2. Continue with repo-specific workflows
3. Accept sync limitations

## Open Questions

1. **Beads installation** - Build from source or pre-built binary?
2. **code-server** - Worth adding for browser IDE?
3. **Repo list** - Any other repos to include?
4. **Phone testing** - Need to verify ttyd works well on mobile

## Success Criteria

- [ ] Can connect from laptop, PC, and phone
- [ ] Single beads database works across all repos
- [ ] AGENTS.md provides useful cross-repo context
- [ ] No more sync conflicts
- [ ] Workflow feels natural and productive
