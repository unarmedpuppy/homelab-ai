---
name: manage-b2-backup
description: Manage Backblaze B2 cloud backups - check status, prioritize folders, monitor progress, troubleshoot
when_to_use: When user asks about cloud backup status, wants to prioritize backup folders, or troubleshoot B2 issues
---

# Manage B2 Backup

Operations for managing encrypted Backblaze B2 cloud backups.

## Check Backup Status

```bash
# Is backup currently running?
scripts/connect-server.sh "ps aux | grep rclone | grep -v grep"

# Check B2 bucket size (how much uploaded)
scripts/connect-server.sh "rclone size b2-encrypted:"

# View latest backup log
scripts/connect-server.sh "ls -lt ~/server/logs/backups/backup-*.log | head -1 | xargs tail -20"

# Check cron execution log
scripts/connect-server.sh "tail -50 ~/server/logs/backups/cron.log"
```

## Start Manual Backup

```bash
# Start full backup in background
scripts/connect-server.sh "cd ~/server && git pull && nohup bash ~/server/scripts/backup-to-b2.sh > ~/server/logs/backups/manual-backup.log 2>&1 & echo 'Backup started'"

# Dry-run (preview only)
scripts/connect-server.sh "bash ~/server/scripts/backup-to-b2.sh --dry-run"
```

## Prioritize Specific Folder

To back up a high-priority folder before everything else:

```bash
# 1. Stop current backup
scripts/connect-server.sh "pkill -f 'rclone sync /jenquist-cloud'"

# 2. Back up priority folder first (example: personal-media)
scripts/connect-server.sh "nohup rclone sync /jenquist-cloud/archive/personal-media b2-encrypted:archive/personal-media --transfers 4 --checkers 8 --progress --log-file ~/server/logs/backups/priority-backup.log --log-level INFO --stats 1m > /dev/null 2>&1 & echo 'Priority backup started'"

# 3. Monitor progress
scripts/connect-server.sh "tail -10 ~/server/logs/backups/priority-backup.log"

# 4. Once complete, run full backup (skips already-uploaded files)
scripts/connect-server.sh "nohup bash ~/server/scripts/backup-to-b2.sh > ~/server/logs/backups/full-backup.log 2>&1 &"
```

## Monitor Progress

```bash
# Live progress (transfers, speed, ETA)
scripts/connect-server.sh "tail -5 ~/server/logs/backups/*.log | grep -E 'GiB|MiB|ETA'"

# Total uploaded to B2
scripts/connect-server.sh "rclone size b2-encrypted:"

# Count files in B2
scripts/connect-server.sh "rclone size b2-encrypted: 2>&1 | head -2"
```

## Stop Backup

```bash
# Stop all rclone processes
scripts/connect-server.sh "pkill -f 'rclone sync'"

# Verify stopped
scripts/connect-server.sh "ps aux | grep rclone | grep -v grep"
```

## Troubleshoot

### Backup Not Running
```bash
# Check if process exists
scripts/connect-server.sh "ps aux | grep rclone | grep -v grep"

# Check cron is scheduled
scripts/connect-server.sh "crontab -l | grep backup"

# Check last cron run
scripts/connect-server.sh "tail -20 ~/server/logs/backups/cron.log"
```

### Hit Daily Cap
1. Increase cap in Backblaze B2 console
2. Restart backup:
   ```bash
   scripts/connect-server.sh "nohup bash ~/server/scripts/backup-to-b2.sh > ~/server/logs/backups/resumed-backup.log 2>&1 &"
   ```

### Check Credentials
```bash
scripts/connect-server.sh "rclone config show b2"
scripts/connect-server.sh "rclone lsd b2:"  # Should list bucket
```

## Restore Files

```bash
# Single file
scripts/connect-server.sh "rclone copy b2-encrypted:path/to/file.txt /local/destination/"

# Directory
scripts/connect-server.sh "rclone copy b2-encrypted:some-folder /local/destination/"

# List files in B2 (decrypted view)
scripts/connect-server.sh "rclone ls b2-encrypted: | head -50"
```

## Configuration

| Item | Location |
|------|----------|
| Backup script | `scripts/backup-to-b2.sh` |
| rclone config | `~/.config/rclone/rclone.conf` (on server) |
| Logs | `~/server/logs/backups/` |
| Cron schedule | `crontab -l` (daily at 3 AM) |

## Reference

See `agents/reference/backups.md` for complete backup system documentation.
