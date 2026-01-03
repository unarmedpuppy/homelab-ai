---
name: add-gitea-mirror
description: Add a new GitHub repository as a pull mirror in Gitea
when_to_use: Adding new repos to Gitea, setting up GitHub mirrors, backing up repositories
---

# Add Gitea Mirror

Add a GitHub repository as a pull mirror to the self-hosted Gitea instance.

## When to Use

- Adding a new repository to Gitea mirrors
- Setting up backup for a new GitHub repo
- Migrating repositories to local Gitea

## Prerequisites

1. Gitea must be running at `https://gitea.server.unarmedpuppy.com`
2. `GITEA_API_TOKEN` must be set in `apps/gitea/.env`
3. `GITHUB_PAT` must be set in `apps/gitea/.env`

## Steps

### 1. Get Required Credentials

```bash
source apps/gitea/.env
echo "Gitea Token: ${GITEA_API_TOKEN:-NOT SET}"
echo "GitHub PAT: ${GITHUB_PAT:-NOT SET}"
```

If `GITEA_API_TOKEN` is not set:
1. Go to https://gitea.server.unarmedpuppy.com/user/settings/applications
2. Generate new token with `repo` scope
3. Add to `apps/gitea/.env` as `GITEA_API_TOKEN=your_token`

### 2. Create Mirror via API

```bash
REPO_NAME="your-repo-name"
GITHUB_USERNAME="unarmedpuppy"

curl -X POST "https://gitea.server.unarmedpuppy.com/api/v1/repos/migrate" \
  -H "Authorization: token ${GITEA_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"clone_addr\": \"https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git\",
    \"uid\": 1,
    \"repo_name\": \"${REPO_NAME}\",
    \"mirror\": true,
    \"private\": false,
    \"auth_username\": \"${GITHUB_USERNAME}\",
    \"auth_password\": \"${GITHUB_PAT}\",
    \"mirror_interval\": \"8h\"
  }"
```

### 3. Verify Mirror

```bash
curl -s "https://gitea.server.unarmedpuppy.com/api/v1/repos/unarmedpuppy/${REPO_NAME}" \
  -H "Authorization: token ${GITEA_API_TOKEN}" | jq '.mirror'
```

### 4. Trigger Manual Sync (Optional)

```bash
curl -X POST "https://gitea.server.unarmedpuppy.com/api/v1/repos/unarmedpuppy/${REPO_NAME}/mirror-sync" \
  -H "Authorization: token ${GITEA_API_TOKEN}"
```

## Quick Reference

### API Endpoints

| Action | Method | Endpoint |
|--------|--------|----------|
| Create mirror | POST | `/api/v1/repos/migrate` |
| Get repo info | GET | `/api/v1/repos/{owner}/{repo}` |
| Trigger sync | POST | `/api/v1/repos/{owner}/{repo}/mirror-sync` |
| List repos | GET | `/api/v1/user/repos` |

### Mirror Configuration

- **Sync interval**: 8 hours (default)
- **Auth**: GitHub username + PAT
- **Type**: Pull mirror (GitHub → Gitea)

## Bulk Setup

For multiple repositories, use the bulk setup script:

```bash
bash scripts/setup-gitea-mirrors.sh
```

Edit the `REPOS` array in the script to add/remove repositories.

## Troubleshooting

### 401 Unauthorized
- Verify `GITEA_API_TOKEN` is valid
- Regenerate token if expired

### 409 Conflict
- Repository already exists in Gitea
- Delete existing repo first or skip

### Mirror Not Syncing
1. Check mirror status in Gitea UI
2. Verify GitHub PAT has `repo` scope
3. Check Gitea logs: `docker logs gitea --tail 100`

## Update README

After adding a new mirror, update `apps/gitea/README.md`:

```markdown
| new-repo-name | GitHub | Pull Mirror |
```
