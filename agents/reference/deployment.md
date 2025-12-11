# Deployment Workflows

Deployment patterns and workflows for the home server.

## Automated Deployment (Recommended)

Use the deployment script for a complete workflow:

```bash
# Deploy everything
bash scripts/deploy-to-server.sh "Your commit message"

# Deploy and restart specific app
bash scripts/deploy-to-server.sh "Update config" --app APP_NAME

# Deploy without restarting
bash scripts/deploy-to-server.sh "Docs update" --no-restart
```

## Manual Deployment Steps

1. **Make changes locally**
2. **Commit and push:**
   ```bash
   git add . && git commit -m "message" && git push
   ```
3. **Pull on server:**
   ```bash
   ssh -p 4242 unarmedpuppy@192.168.86.47 "cd ~/server && git pull"
   ```
4. **Restart services:**
   ```bash
   ssh -p 4242 unarmedpuppy@192.168.86.47 "cd ~/server/apps/APP_NAME && docker compose restart"
   ```

**Never make direct changes on the server without explicit permission.**

## Server Details

- **Server Path**: `~/server` (home dir of `unarmedpuppy` user)
- **Local Repo**: `/Users/joshuajenquist/repos/personal/home-server`
- **Local IP**: `192.168.86.47`
- **SSH**: `ssh -p 4242 unarmedpuppy@192.168.86.47`

## Connection

```bash
# SSH to server
ssh -p 4242 unarmedpuppy@192.168.86.47

# Or use helper script
bash scripts/connect-server.sh "command"
```

## Verification

After deployment, verify services:

```bash
# Check container is running
ssh -p 4242 unarmedpuppy@192.168.86.47 "docker ps | grep SERVICE_NAME"

# Check logs for errors
ssh -p 4242 unarmedpuppy@192.168.86.47 "docker logs SERVICE_NAME --tail 50"
```

## Rollback

If something goes wrong:

```bash
# Revert last commit
git revert HEAD && git push

# Or restore from backup
# (server-specific backup procedures)
```

## Related Tools

- `agents/skills/standard-deployment/` - Standard deployment workflow
- `agents/skills/deploy-new-service/` - Setting up new services
- `agents/personas/server-agent.md` - Server management specialist

