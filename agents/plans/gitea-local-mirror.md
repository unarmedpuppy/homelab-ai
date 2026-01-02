# Gitea Local Mirror - GitHub Fallback Strategy

## Goal

Create a local Git server (Gitea) that mirrors all personal GitHub repositories, providing:
- **Offline access** to all repos when internet is unavailable
- **Redundancy** in case GitHub goes down or account issues
- **Local speed** for large repo operations
- **Privacy** for sensitive repos (optional - keep some local-only)

## Architecture Options

### Option A: Automatic Mirror (Pull-based) - RECOMMENDED

```
GitHub ──────────────────────────────────────────────────────┐
   │                                                         │
   │  Gitea mirrors every X hours                           │
   ▼                                                         │
┌─────────────────────────────────────────────────────────┐  │
│                    Gitea Server                          │  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │  │
│  │ home-server │  │ homelab-ai  │  │ other repos │     │  │
│  │   (mirror)  │  │   (mirror)  │  │  (mirrors)  │     │  │
│  └─────────────┘  └─────────────┘  └─────────────┘     │  │
└─────────────────────────────────────────────────────────┘  │
                                                             │
Developer workflow unchanged:                                │
   git push origin main ─────────────────────────────────────┘
   (pushes to GitHub, Gitea syncs automatically)
```

**Pros**:
- Zero workflow change
- Automatic sync (configurable interval)
- Gitea handles all the complexity

**Cons**:
- Slight delay before mirror updates
- Read-only mirrors (can't push to Gitea directly)

### Option B: Dual Remotes (Push to both)

```
┌──────────────────┐
│  Local Machine   │
│                  │
│  git push all    │───┬───▶ GitHub (origin)
│                  │   │
└──────────────────┘   └───▶ Gitea (local)
```

**Setup**:
```bash
git remote add local git@gitea.server:user/repo.git
git remote add all origin
git remote set-url --add --push all git@github.com:user/repo.git
git remote set-url --add --push all git@gitea.server:user/repo.git

# Now: git push all main → pushes to both
```

**Pros**:
- Real-time sync
- Can push to either

**Cons**:
- Workflow change required
- Manual setup per repo
- More complex conflict handling

### Option C: Post-receive Hook (GitHub Actions → Gitea)

```
Push to GitHub → GitHub Action triggers → Pushes to Gitea
```

**Cons**: Requires internet (defeats offline purpose), more complex

## Recommendation: Option A (Automatic Mirror)

Gitea's built-in mirror feature is purpose-built for this. Zero workflow change.

## Implementation Plan

### Phase 1: Deploy Gitea

**Create docker-compose** (`apps/gitea/docker-compose.yml`):
```yaml
services:
  gitea:
    image: harbor.server.unarmedpuppy.com/docker-hub/gitea/gitea:latest
    container_name: gitea
    environment:
      - USER_UID=1000
      - USER_GID=1000
      - GITEA__database__DB_TYPE=sqlite3
      - GITEA__server__ROOT_URL=https://git.server.unarmedpuppy.com
      - GITEA__server__SSH_DOMAIN=git.server.unarmedpuppy.com
      - GITEA__server__SSH_PORT=2222
      - GITEA__mirror__ENABLED=true
      - GITEA__mirror__DEFAULT_INTERVAL=1h
    volumes:
      - gitea-data:/data
      - /etc/timezone:/etc/timezone:ro
      - /etc/localtime:/etc/localtime:ro
    ports:
      - "3000:3000"   # Web UI
      - "2222:22"     # Git SSH (if not using Traefik)
    restart: unless-stopped
    networks:
      - traefik-net
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.gitea.rule=Host(`git.server.unarmedpuppy.com`)"
      - "traefik.http.routers.gitea.tls=true"
      - "traefik.http.services.gitea.loadbalancer.server.port=3000"
      # Homepage integration
      - "homepage.group=Development"
      - "homepage.name=Gitea"
      - "homepage.icon=gitea"
      - "homepage.href=https://git.server.unarmedpuppy.com"
      - "homepage.description=Local Git Mirror"

volumes:
  gitea-data:

networks:
  traefik-net:
    external: true
```

### Phase 2: Initial Setup

1. Access `https://git.server.unarmedpuppy.com`
2. Complete initial setup wizard
3. Create admin account
4. Generate GitHub personal access token (read-only for mirroring)

### Phase 3: Configure Mirrors

**For each GitHub repo**:
1. Gitea UI → New Migration → GitHub
2. Enter: `https://github.com/unarmedpuppy/home-server.git`
3. Enable: "This repository will be a mirror"
4. Set sync interval (1 hour recommended)
5. Add GitHub token for private repos

**Or use Gitea API** (scriptable):
```bash
curl -X POST "https://git.server.unarmedpuppy.com/api/v1/repos/migrate" \
  -H "Authorization: token $GITEA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clone_addr": "https://github.com/unarmedpuppy/home-server.git",
    "mirror": true,
    "private": true,
    "repo_name": "home-server",
    "auth_token": "'$GITHUB_TOKEN'"
  }'
```

### Phase 4: Automate Mirror Creation

**Create script** (`scripts/sync-github-to-gitea.sh`):
```bash
#!/bin/bash
# Sync all GitHub repos to Gitea as mirrors

GITHUB_USER="unarmedpuppy"
GITEA_URL="https://git.server.unarmedpuppy.com"
GITEA_TOKEN="..."
GITHUB_TOKEN="..."

# Get all GitHub repos
repos=$(gh repo list $GITHUB_USER --json name -q '.[].name')

for repo in $repos; do
    echo "Mirroring: $repo"
    curl -X POST "$GITEA_URL/api/v1/repos/migrate" \
      -H "Authorization: token $GITEA_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "clone_addr": "https://github.com/'$GITHUB_USER'/'$repo'.git",
        "mirror": true,
        "private": true,
        "repo_name": "'$repo'",
        "auth_token": "'$GITHUB_TOKEN'"
      }'
done
```

### Phase 5: DNS Setup

Add to Cloudflare/AdGuard:
- `git.server.unarmedpuppy.com` → server IP

### Phase 6: Backup Gitea Data

Add to backup script:
```bash
# Gitea data
rsync -av /var/lib/docker/volumes/gitea-data/ $BACKUP_DIR/gitea/
```

## Storage Estimate

| Repos | Avg Size | Total |
|-------|----------|-------|
| ~20 repos | ~100MB each | ~2GB |

With git history compression, likely less.

## Offline Usage

When internet is down:
```bash
# Clone from local Gitea
git clone git@git.server.unarmedpuppy.com:unarmedpuppy/home-server.git

# Or add as remote to existing repo
git remote add local git@git.server.unarmedpuppy.com:unarmedpuppy/home-server.git
git fetch local
```

## Advanced: Two-Way Sync (Optional)

If you want to push to Gitea and have it sync to GitHub:

1. In Gitea, disable "Mirror" mode
2. Add GitHub as a push mirror
3. Gitea pushes changes to GitHub

This is more complex and requires careful conflict handling.

## Security Considerations

1. **Gitea token** - Store securely, needed for API access
2. **GitHub token** - Read-only PAT for mirroring private repos
3. **SSH access** - Use SSH keys, not passwords
4. **Firewall** - Keep port 2222 internal only (or use Tailscale)

## Files to Create

| File | Purpose |
|------|---------|
| `apps/gitea/docker-compose.yml` | Gitea service definition |
| `apps/gitea/.env.example` | Environment template |
| `scripts/sync-github-to-gitea.sh` | Bulk mirror creation |

## Next Steps

1. [ ] Approve this plan
2. [ ] Create Gitea docker-compose
3. [ ] Deploy and configure
4. [ ] Set up mirrors for all repos
5. [ ] Add DNS entry
6. [ ] Add to backup rotation
7. [ ] Create skill for managing mirrors

## Questions to Consider

1. **Which repos to mirror?** All personal? Or just critical ones (home-server, homelab-ai)?
2. **Sync interval?** 1 hour is good balance. More frequent = more API calls.
3. **Private repos?** Need GitHub PAT with `repo` scope for private repos.
4. **Local-only repos?** Any repos you want ONLY on Gitea (not GitHub)?
