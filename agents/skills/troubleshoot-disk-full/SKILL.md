---
name: troubleshoot-disk-full
description: Diagnose and resolve disk full issues - find large files, clean up Docker, clear logs
when_to_use: When server shows disk full errors, services fail to start, or df -h shows high usage
---

# Troubleshoot Disk Full

Steps to diagnose and resolve disk space issues on the server.

## Quick Diagnosis

```bash
# Check disk usage
scripts/connect-server.sh "df -h"

# Find which directory is using space
scripts/connect-server.sh "du -sh /* 2>/dev/null | sort -hr | head -20"

# Check Docker disk usage
scripts/connect-server.sh "docker system df"
```

## Common Culprits

### 1. AdGuard Query Log (KNOWN ISSUE)

AdGuard's `querylog.json` can grow to 100GB+. This has caused disk full before.

```bash
# Check AdGuard log size
scripts/connect-server.sh "docker exec adguard-home ls -lh /opt/adguardhome/work/data/querylog.json 2>/dev/null"

# Delete query log (safe - it regenerates)
scripts/connect-server.sh "docker exec adguard-home rm -f /opt/adguardhome/work/data/querylog.json"

# Restart AdGuard to apply
scripts/connect-server.sh "docker restart adguard-home"
```

**Prevention**: Configure AdGuard to limit query log size in Settings → General → Query Log.

### 2. Docker Images and Containers

```bash
# Check Docker disk usage
scripts/connect-server.sh "docker system df"

# Remove unused images, containers, networks
scripts/connect-server.sh "docker system prune -f"

# More aggressive: remove all unused images
scripts/connect-server.sh "docker image prune -a -f"

# Remove dangling volumes (CAREFUL - check first)
scripts/connect-server.sh "docker volume ls -f dangling=true"
scripts/connect-server.sh "docker volume prune -f"
```

### 3. Download Folder (Sonarr/Radarr)

Downloads can accumulate if import fails (e.g., ZFS not mounted).

```bash
# Check downloads size
scripts/connect-server.sh "du -sh ~/server/apps/media-download/downloads/"

# List large files
scripts/connect-server.sh "find ~/server/apps/media-download/downloads -type f -size +1G -exec ls -lh {} \;"

# Clear downloads (if ZFS was down and imports failed)
scripts/connect-server.sh "rm -rf ~/server/apps/media-download/downloads/*"
```

### 4. Log Files

```bash
# Find large log files
scripts/connect-server.sh "find /var/log -type f -size +100M -exec ls -lh {} \; 2>/dev/null"

# Check Docker logs
scripts/connect-server.sh "docker ps -q | xargs -I {} sh -c 'echo === {} === && docker logs {} 2>&1 | wc -l'"

# Truncate large Docker logs
scripts/connect-server.sh "docker ps -q | xargs -I {} sh -c 'truncate -s 0 \$(docker inspect {} --format=\"{{.LogPath}}\")'"
```

### 5. Journal Logs

```bash
# Check journal size
scripts/connect-server.sh "journalctl --disk-usage"

# Clear old journal entries
scripts/connect-server.sh "sudo journalctl --vacuum-size=100M"
```

## Find Largest Files

```bash
# Top 20 largest files on system
scripts/connect-server.sh "find / -type f -size +500M -exec ls -lh {} \; 2>/dev/null | sort -k5 -hr | head -20"

# Top 20 largest directories
scripts/connect-server.sh "du -h / 2>/dev/null | sort -hr | head -20"
```

## After Cleanup

```bash
# Verify space recovered
scripts/connect-server.sh "df -h"

# Restart any failed services
scripts/connect-server.sh "docker ps -a --filter 'status=exited' --format '{{.Names}}'"
```

## Prevention

1. **Set up log rotation** for Docker containers
2. **Configure AdGuard** to limit query log retention
3. **Monitor disk space** with alerts (Prometheus + Grafana)
4. **Scheduled cleanup** via cron for Docker prune

## Related

- See `agents/reference/backups.md` for backup systems
- See `agents/skills/cleanup-disk-space/` for routine maintenance
