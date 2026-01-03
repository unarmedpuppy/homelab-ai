---
name: server-ssh
description: SSH access to the home server
when_to_use: When needing to run commands on the server
---

# Server SSH Access

## Connection Details

| Setting | Value |
|---------|-------|
| Host | `192.168.86.47` |
| Port | `4242` |
| User | `claude-deploy` |
| Auth | SSH key (auto-configured) |

## Basic SSH Command

```bash
ssh -p 4242 claude-deploy@192.168.86.47 'COMMAND'
```

## Multiple Commands

Use heredoc for multiple commands:

```bash
ssh -p 4242 claude-deploy@192.168.86.47 << 'EOF'
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

The `claude-deploy` user has restricted access:

### Allowed
- Read files in server directories
- Run `sudo docker` (view, restart, compose)
- Run `sudo git` in `/home/unarmedpuppy/server`

### Not Allowed
- `sudo` for other commands
- Delete docker resources (containers, images, volumes)
- Modify system files
- Access other users' home directories

## Examples

### Check Disk Space

```bash
ssh -p 4242 claude-deploy@192.168.86.47 'df -h'
```

### List Apps Directory

```bash
ssh -p 4242 claude-deploy@192.168.86.47 'ls -la /home/unarmedpuppy/server/apps/'
```

### Check Server Git Status

```bash
ssh -p 4242 claude-deploy@192.168.86.47 'sudo git -C /home/unarmedpuppy/server status'
```

### Pull Latest Server Code

```bash
ssh -p 4242 claude-deploy@192.168.86.47 'sudo git -C /home/unarmedpuppy/server pull'
```

## Troubleshooting

### Connection Refused
- Server SSH may be down
- Check if server is reachable: `ping 192.168.86.47`

### Permission Denied
- SSH key may not be authorized
- Check: `ssh -vvv -p 4242 claude-deploy@192.168.86.47`

### Command Not Allowed
- User has restricted sudo access
- Only specific commands are whitelisted
- Ask user to run command directly if needed
