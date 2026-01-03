# Gitea

Self-hosted Git service with pull mirrors from GitHub for backup and offline access.

## Access

- **URL**: https://gitea.server.unarmedpuppy.com
- **SSH**: `ssh://git@gitea.server.unarmedpuppy.com:2222`
- **Ports**: 
  - `3005` - Web interface
  - `2222` - SSH (git operations)
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

## Mirrored Repositories

| Repository | Source | Type |
|------------|--------|------|
| agent-gateway | GitHub | Pull Mirror |
| agents | GitHub | Pull Mirror |
| agents-mono | GitHub | Pull Mirror |
| beads-viewer | GitHub | Pull Mirror |
| budget | GitHub | Pull Mirror |
| chatterbox-tts-service | GitHub | Pull Mirror |
| home-server | GitHub | Pull Mirror |
| homelab-ai | GitHub | Pull Mirror |
| maptapdat | GitHub | Pull Mirror |
| media-downs-dockerized | GitHub | Pull Mirror |
| opencode-terminal | GitHub | Pull Mirror |
| pokedex | GitHub | Pull Mirror |
| polyjuiced | GitHub | Pull Mirror |
| shared-agent-skills | GitHub | Pull Mirror |
| smart-home-3d | GitHub | Pull Mirror |
| tcg-scraper | GitHub | Pull Mirror |
| trading-bot | GitHub | Pull Mirror |
| trading-journal | GitHub | Pull Mirror |
| workflow-agents | GitHub | Pull Mirror |
| life-os | - | Local Only |

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
