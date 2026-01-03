# Claude-Harness SSH to Server

## Overview

The claude-harness container can SSH to the home server as the restricted `claude-deploy` user to run whitelisted docker and git commands.

## Connection Details

| Setting | Value |
|---------|-------|
| Host | `host.docker.internal` |
| Port | `4242` |
| User | `claude-deploy` |
| Key | `/home/appuser/.ssh/id_ed25519` |

**Important**: Must use explicit key path - SSH doesn't find it automatically due to running as different user context.

## SSH Command Pattern

```bash
ssh -p 4242 -i /home/appuser/.ssh/id_ed25519 claude-deploy@host.docker.internal 'COMMAND'
```

## Allowed Commands (sudoers whitelist)

```
# View containers
sudo docker ps *
sudo docker logs *
sudo docker inspect *
sudo docker images
sudo docker stats *

# Manage containers
sudo docker restart *
sudo docker start *
sudo docker stop *

# Compose operations (only in server apps directory)
sudo docker compose -f /home/unarmedpuppy/server/apps/*/docker-compose.yml *

# Git operations (only in server repo)
sudo git -C /home/unarmedpuppy/server *
```

## Blocked Commands

- `docker rm`, `docker rmi`, `docker volume rm` - Cannot delete resources
- `docker system prune` - Cannot cleanup
- Any sudo commands not in whitelist

## Setup Requirements

### 1. claude-deploy user on server
```bash
sudo useradd -m -s /bin/bash claude-deploy
sudo usermod -p '*' claude-deploy  # Unlock account for SSH key auth
```

### 2. SSH authorized_keys
```bash
sudo mkdir -p /home/claude-deploy/.ssh
echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIH9qRw+hzNh8GVFv3Ec89mQh4n247nvSoJBhWkUpknob claude-harness@container' | sudo tee /home/claude-deploy/.ssh/authorized_keys
sudo chmod 700 /home/claude-deploy/.ssh
sudo chmod 600 /home/claude-deploy/.ssh/authorized_keys
sudo chown -R claude-deploy:claude-deploy /home/claude-deploy/.ssh
```

### 3. Sudoers file at /etc/sudoers.d/claude-deploy
```
claude-deploy ALL=(ALL) NOPASSWD: /usr/bin/docker ps *
claude-deploy ALL=(ALL) NOPASSWD: /usr/bin/docker logs *
claude-deploy ALL=(ALL) NOPASSWD: /usr/bin/docker inspect *
claude-deploy ALL=(ALL) NOPASSWD: /usr/bin/docker images
claude-deploy ALL=(ALL) NOPASSWD: /usr/bin/docker stats *
claude-deploy ALL=(ALL) NOPASSWD: /usr/bin/docker restart *
claude-deploy ALL=(ALL) NOPASSWD: /usr/bin/docker start *
claude-deploy ALL=(ALL) NOPASSWD: /usr/bin/docker stop *
claude-deploy ALL=(ALL) NOPASSWD: /usr/bin/docker compose -f /home/unarmedpuppy/server/apps/*/docker-compose.yml *
claude-deploy ALL=(ALL) NOPASSWD: /usr/bin/git -C /home/unarmedpuppy/server *
```

### 4. Git safe.directory (for sudo git)
```bash
sudo git -C /home/unarmedpuppy/server config --global --add safe.directory /home/unarmedpuppy/server
```

## Troubleshooting

### Permission denied (publickey)
- Check authorized_keys exists and has correct permissions
- Verify key matches: container's `/home/appuser/.ssh/id_ed25519.pub`

### Connection refused
- Use `host.docker.internal` not raw IP from inside container
- Container must be on a Docker network with host access

### sudo: command not allowed
- Only whitelisted commands work
- Check exact syntax matches sudoers patterns

### Git dubious ownership
- Run: `sudo git -C /home/unarmedpuppy/server config --global --add safe.directory /home/unarmedpuppy/server`

## Container SSH Key

The container generates a persistent SSH key at first run, stored in Docker volume `claude-harness-ssh`.

Public key: `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIH9qRw+hzNh8GVFv3Ec89mQh4n247nvSoJBhWkUpknob claude-harness@container`
