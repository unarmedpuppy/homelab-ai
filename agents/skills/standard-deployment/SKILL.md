# Standard Deployment

Deploy code changes to the home server.

## When to Use

- Deploying code changes
- Updating service configurations
- Restarting services after config changes

## Steps

### 1. Check Current State

```bash
git status
git diff
```

### 2. Commit and Push

```bash
git add .
git commit -m "Description of changes"
git push
```

### 3. Pull on Server and Restart

```bash
# SSH to server and pull
ssh homeserver "cd /home/shua/home-server && git pull"

# Restart affected service
ssh homeserver "cd /home/shua/home-server/apps/SERVICE_NAME && docker compose restart"
```

### 4. Verify

```bash
# Check container is running
ssh homeserver "docker ps | grep SERVICE_NAME"

# Check logs for errors
ssh homeserver "docker logs SERVICE_NAME --tail 50"
```

## If Something Goes Wrong

1. Check logs: `docker logs SERVICE_NAME --tail 100`
2. Check container status: `docker inspect SERVICE_NAME`
3. Rollback if needed: `git revert HEAD && git push`
