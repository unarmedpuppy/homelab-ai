# Gitea Reference Documentation

Self-hosted Git service with GitHub pull mirrors for backup and offline access.

## Quick Reference

| Property | Value |
|----------|-------|
| **URL** | https://gitea.server.unarmedpuppy.com |
| **SSH** | `ssh://git@gitea.server.unarmedpuppy.com:2223` |
| **Web Port** | 3007 |
| **SSH Port** | 2223 |
| **Admin User** | unarmedpuppy |
| **Database** | PostgreSQL 16 |
| **Mirror Interval** | 8 hours |

## API Reference

Base URL: `https://gitea.server.unarmedpuppy.com/api/v1`

### Authentication

All API calls require a token:
```bash
-H "Authorization: token YOUR_GITEA_TOKEN"
```

Generate token at: Settings → Applications → Generate New Token

### Common Endpoints

| Action | Method | Endpoint |
|--------|--------|----------|
| List repos | GET | `/user/repos` |
| Get repo | GET | `/repos/{owner}/{repo}` |
| Create mirror | POST | `/repos/migrate` |
| Trigger sync | POST | `/repos/{owner}/{repo}/mirror-sync` |
| List users | GET | `/admin/users` |

### Create Mirror Example

```bash
curl -X POST "https://gitea.server.unarmedpuppy.com/api/v1/repos/migrate" \
  -H "Authorization: token ${GITEA_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "clone_addr": "https://github.com/unarmedpuppy/repo-name.git",
    "uid": 1,
    "repo_name": "repo-name",
    "mirror": true,
    "private": false,
    "auth_username": "unarmedpuppy",
    "auth_password": "${GITHUB_PAT}",
    "mirror_interval": "8h"
  }'
```

### Trigger Mirror Sync

```bash
curl -X POST "https://gitea.server.unarmedpuppy.com/api/v1/repos/unarmedpuppy/repo-name/mirror-sync" \
  -H "Authorization: token ${GITEA_API_TOKEN}"
```

## Docker Configuration

### Containers

| Container | Image | Purpose |
|-----------|-------|---------|
| gitea | `harbor.../gitea/gitea:1.22-rootless` | Git server |
| gitea-db | `harbor.../postgres:16-alpine` | Database |

### Volumes

| Volume | Purpose |
|--------|---------|
| gitea-data | Repository data |
| gitea-config | Configuration |
| gitea-db-data | PostgreSQL data |

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `GITEA_DB_USER` | Database username |
| `GITEA_DB_PASSWORD` | Database password |
| `GITEA_SECRET_KEY` | Session encryption |
| `GITEA_INTERNAL_TOKEN` | Internal API auth |
| `GITEA_JWT_SECRET` | OAuth2 JWT signing |
| `GITHUB_PAT` | GitHub mirror auth |
| `GITEA_API_TOKEN` | Gitea API access |

## Gitea Actions

### Runner Status

Runner: `gitea-act-runner` (Docker-based)

Check status:
```bash
docker ps --filter name=gitea-act-runner
```

### Required Secrets

Configure at: **Gitea → Site Administration → Actions → Secrets** (for org-wide) or per-repo in Settings → Actions → Secrets.

| Secret | Value | Purpose |
|--------|-------|---------|
| `HARBOR_USERNAME` | Harbor robot account or admin | Registry auth |
| `HARBOR_PASSWORD` | Harbor password | Registry auth |
| `DEPLOY_HOST` | `192.168.86.47` | SSH deploy target |
| `DEPLOY_PORT` | `4242` | SSH port |
| `DEPLOY_USER` | `unarmedpuppy` | SSH username |
| `DEPLOY_SSH_KEY` | Contents of `~/.ssh/github-deploy-key` | SSH private key |

### Workflow Files Location

Workflows go in `.gitea/workflows/` (same syntax as GitHub Actions).

### Repos with Gitea Workflows

| Repository | Workflow | Status |
|------------|----------|--------|
| pokedex | `.gitea/workflows/test.yml` | Active |
| maptapdat | `.gitea/workflows/build.yml` | Ready |
| homelab-ai | `.gitea/workflows/build.yml` | Ready |
| beads-viewer | `.gitea/workflows/build.yml` | Ready |
| smart-home-3d | `.gitea/workflows/build.yml` | Ready |
| opencode-terminal | `.gitea/workflows/build.yml` | Ready |
| trading-journal | `.gitea/workflows/build.yml` | Ready |
| trading-bot | `.gitea/workflows/build.yml` | Ready |

## Push Mirrors (Gitea → GitHub)

### Active Push Mirrors (8 repos)

| Repository | Status |
|------------|--------|
| agent-gateway | ✅ Push Mirror to GitHub |
| beads-viewer | ✅ Push Mirror to GitHub |
| home-server | ✅ Push Mirror to GitHub |
| homelab-ai | ✅ Push Mirror to GitHub |
| maptapdat | ✅ Push Mirror to GitHub |
| pokedex | ✅ Push Mirror to GitHub |
| polyjuiced | ✅ Push Mirror to GitHub |
| workflow-agents | ✅ Push Mirror to GitHub |

### Local Only (12 repos - not on GitHub)

| Repository | Notes |
|------------|-------|
| agents | Not on GitHub |
| agents-mono | Not on GitHub |
| budget | Not on GitHub |
| chatterbox-tts-service | Not on GitHub |
| life-os | Private - Gitea only |
| media-downs-dockerized | Not on GitHub |
| opencode-terminal | Not on GitHub |
| shared-agent-skills | Not on GitHub |
| smart-home-3d | Not on GitHub |
| tcg-scraper | Not on GitHub |
| trading-bot | Not on GitHub |
| trading-journal | Not on GitHub |

## Maintenance

### Backup

```bash
# Database backup
docker exec gitea-db pg_dump -U gitea gitea > gitea_backup.sql

# Repository data backup
docker cp gitea:/var/lib/gitea ./gitea-data-backup
```

### Restore

```bash
# Restore database
cat gitea_backup.sql | docker exec -i gitea-db psql -U gitea gitea

# Restore repository data
docker cp ./gitea-data-backup/. gitea:/var/lib/gitea/
```

### Logs

```bash
docker logs gitea --tail 100
docker logs gitea-db --tail 100
```

## Troubleshooting

### Mirror Not Syncing

1. Check GitHub PAT is valid
2. Verify mirror status in UI (repo → Settings → Mirror)
3. Check Gitea logs: `docker logs gitea | grep mirror`
4. Trigger manual sync via API

### 502 Bad Gateway

1. Check container is running: `docker ps | grep gitea`
2. Check Traefik can reach it: `docker logs traefik | grep gitea`
3. Verify port 3000 inside container is listening

### Database Connection Failed

1. Check gitea-db is healthy: `docker ps | grep gitea-db`
2. Verify credentials in .env match docker-compose
3. Check PostgreSQL logs: `docker logs gitea-db`

## Related Files

| File | Purpose |
|------|---------|
| `apps/gitea/docker-compose.yml` | Service definition |
| `apps/gitea/.env` | Credentials (gitignored) |
| `apps/gitea/README.md` | App documentation |
| `scripts/setup-gitea-mirrors.sh` | Bulk mirror setup |
| `agents/skills/add-gitea-mirror/SKILL.md` | Add mirror skill |
| `agents/personas/gitea-agent.md` | Management persona |
