---
name: server-ssh
description: SSH access to the home server
when_to_use: When needing to run commands on the server
---

# Server SSH Access

## Connection Details

| Setting | Value |
|---------|-------|
| Host | `host.docker.internal` |
| Port | `4242` |
| User | `claude-deploy` |
| Key | `/home/appuser/.ssh/id_ed25519` |

## Basic SSH Command

```bash
ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal 'COMMAND'
```

## Multiple Commands

Use heredoc for multiple commands:

```bash
ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal << 'EOF'
command1
command2
command3
EOF
```

## Common Server Paths

| Path | Contents |
|------|----------|
| `/home/unarmedpuppy/server` | Main server git repo |
| `/home/unarmedpuppy/server/apps` | Docker compose apps |
| `/mnt/server-storage` | Media storage drive |
| `/mnt/server-cloud` | Cloud sync drive |

## User Permissions

The `claude-deploy` user has restricted sudo access:

### Allowed (with sudo)
- `sudo docker ps/logs/inspect/images/stats` - View containers
- `sudo docker start/stop/restart` - Manage containers
- `sudo docker compose -f /home/unarmedpuppy/server/apps/*/docker-compose.yml` - Compose operations
- `sudo git -C /home/unarmedpuppy/server` - Git operations in server repo

### Not Allowed
- `docker rm`, `docker rmi`, `docker volume rm` - Delete resources
- `docker system prune` - Cleanup operations
- Other sudo commands
- Direct docker access (must use sudo)

## Examples

### List Running Containers

```bash
ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal 'sudo docker ps'
```

### Check Container Logs

```bash
ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal 'sudo docker logs --tail 100 CONTAINER_NAME'
```

### Restart a Service

```bash
ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal 'sudo docker restart CONTAINER_NAME'
```

### Check Disk Space

```bash
ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal 'df -h'
```

### Pull Latest Server Code

```bash
ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal 'sudo git -C /home/unarmedpuppy/server pull'
```

### Docker Compose Operations

```bash
# Restart a service stack
ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal \
  'sudo docker compose -f /home/unarmedpuppy/server/apps/SERVICE/docker-compose.yml restart'

# View compose logs
ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal \
  'sudo docker compose -f /home/unarmedpuppy/server/apps/SERVICE/docker-compose.yml logs --tail 50'
```

## Troubleshooting

### Permission Denied (publickey)
- The container's SSH key may not be in claude-deploy's authorized_keys
- Ask user to add key: `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIH9qRw+hzNh8GVFv3Ec89mQh4n247nvSoJBhWkUpknob`

### Command Not Allowed
- Only whitelisted sudo commands work
- If you need a command that's blocked, ask the user to run it directly

### Connection Refused
- Server may be unreachable from container network
- Try: `host.docker.internal` should resolve to Docker host
