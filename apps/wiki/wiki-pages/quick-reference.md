# Quick Reference

### Connection Information

- **SSH Access**: `ssh unarmedpuppy@192.168.86.47 -p 4242`
- **Local IP**: `192.168.86.47` (check with `hostname -I`)
- **MAC Address**: `74:56:3c:e1:8b:3a`
- **EdgeRouter Access**: `ssh unarmedpuppy@172.16.30.1` (password in 1Password)
- **Domain**: `server.unarmedpuppy.com`

### Custom Aliases

- `cycle` - Runs `~/server/docker-restart.sh` (stops and starts all Docker containers)
- `server` - Runs `connect-server.sh` (SSH connection wrapper)
- `sync` - Git pull, add, commit & push operations

### Quick Commands

```bash
# Get local IP
hostname -I

# Get MAC address (requires net-tools)
sudo apt-get install net-tools
/sbin/ifconfig

# Check disk usage
sudo ncdu /
sudo du -sh * | sort -hr | head -n10

# Check directory size
du -sh server/apps/bedrock-viz/
```

---