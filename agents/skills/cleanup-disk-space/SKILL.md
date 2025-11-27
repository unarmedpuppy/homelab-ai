# Cleanup Disk Space

Free up disk space on the server.

## When to Use

- Disk usage above 80%
- Downloads failing due to space
- Docker builds failing

## Steps

### 1. Check Current Usage

```bash
df -h
docker system df
```

### 2. Clean Docker Resources

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove build cache
docker builder prune

# Nuclear option - remove everything unused
docker system prune -a --volumes
```

### 3. Clean Download Directories

```bash
# Find large files
du -sh /path/to/downloads/*

# Remove completed/extracted archives
find /path/to/downloads -name "*.rar" -o -name "*.zip" | xargs rm -f
```

### 4. Clean Logs

```bash
# Truncate large log files
truncate -s 0 /var/log/*.log

# Or use Docker's log rotation
docker logs CONTAINER --tail 0
```

### 5. Verify

```bash
df -h
```

## Quick Commands

```bash
# See what's using space
du -sh /* 2>/dev/null | sort -hr | head -20

# Find files over 100MB
find / -size +100M -type f 2>/dev/null

# Docker disk usage breakdown
docker system df -v
```
