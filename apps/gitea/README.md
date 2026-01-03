# Gitea

Self-hosted Git service with pull mirrors from GitHub for backup and offline access.

## Access

- **URL**: https://gitea.server.unarmedpuppy.com
- **SSH**: `ssh://git@gitea.server.unarmedpuppy.com:2223`
- **Ports**: 
  - `3007` - Web interface
  - `2223` - SSH (git operations)
- **Status**: Active

## Configuration

### Initial Setup

After first deployment, create admin user via CLI:

```bash
docker exec -it gitea gitea admin user create \
  --username unarmedpuppy \
  --password "YOUR_PASSWORD" \
  --email gitea@jenquist.com \
  --admin
```

### Mirror Configuration

Mirrors sync every 8 hours from GitHub. To set up mirrors:

1. **Bulk setup**: Run `bash scripts/setup-gitea-mirrors.sh`
2. **Single repo**: Use the agent skill `agents/skills/add-gitea-mirror`
3. **Manual**: New Migration > GitHub > Enter repo URL with PAT auth

### Environment Variables

Copy `env.template` to `.env` and fill in:
- `GITEA_DB_*` - PostgreSQL credentials
- `GITEA_SECRET_KEY` - Generate with `openssl rand -hex 32`
- `GITEA_INTERNAL_TOKEN` - Generate with `openssl rand -hex 64`
- `GITEA_JWT_SECRET` - Generate with `openssl rand -base64 32`
- `GITHUB_PAT` - Personal Access Token for mirror authentication
- `GITEA_RUNNER_TOKEN` - Runner registration token (get from Gitea UI)

## Gitea Actions (CI/CD)

Gitea Actions provides GitHub Actions-compatible CI/CD pipelines.

### Setup

1. **Get runner token**: Site Administration > Actions > Runners > Create new Runner
2. **Add to `.env`**: `GITEA_RUNNER_TOKEN=<token>`
3. **Restart services**: `docker compose up -d`

### Creating Workflows

Workflows go in `.gitea/workflows/` (or `.github/workflows/`):

```yaml
name: Build and Test

on:
  push:
    branches: [main]
  pull_request:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: echo "Building..."
```

### Runner Labels

The act_runner supports:
- `ubuntu-latest` - Node 20 on Debian Bookworm
- `ubuntu-22.04` - Node 20 on Debian Bookworm

### Troubleshooting

```bash
docker logs gitea-act-runner
docker exec gitea-act-runner act_runner list
```

## Mirrored Repositories

### Active Mirrors (GitHub → Gitea)

| Repository | Status |
|------------|--------|
| agent-gateway | ✅ Mirrored |
| beads-viewer | ✅ Mirrored |
| home-server | ✅ Mirrored |
| homelab-ai | ✅ Mirrored |
| maptapdat | ✅ Mirrored |
| pokedex | ✅ Mirrored |
| polyjuiced | ✅ Mirrored |
| workflow-agents | ✅ Mirrored |

### Not on GitHub (Local Only / Private)

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

### Manual Mirror Sync

```bash
curl -X POST "https://gitea.server.unarmedpuppy.com/api/v1/repos/unarmedpuppy/REPO_NAME/mirror-sync" \
  -H "Authorization: token YOUR_GITEA_TOKEN"
```

### Backup

```bash
docker exec gitea-db pg_dump -U gitea gitea > gitea_backup.sql
docker cp gitea:/var/lib/gitea ./gitea-data-backup
```

## References

- [Gitea Documentation](https://docs.gitea.com/)
- [Gitea Docker Installation](https://docs.gitea.com/installation/install-with-docker)
