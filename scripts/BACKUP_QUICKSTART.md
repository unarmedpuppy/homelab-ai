# Backup Quick Start Guide

## Quick Setup (5 minutes)

### 1. Copy scripts to server

If running from your local machine:
```bash
cd ~/repos/personal/home-server
./scripts/connect-server.sh "mkdir -p ~/server/scripts"
scp -P 4242 scripts/backup-*.sh scripts/restore-*.sh scripts/setup-backup-cron.sh scripts/cleanup-old-backups.sh scripts/check-backup-health.sh unarmedpuppy@192.168.86.47:~/server/scripts/
./scripts/connect-server.sh "chmod +x ~/server/scripts/*.sh"
```

Or if you're already on the server:
```bash
# Scripts should already be in ~/server/scripts/ after git sync
chmod +x ~/server/scripts/*.sh
```

### 2. Create backup directories

```bash
# On the server
mkdir -p /mnt/server-cloud/backups/{daily,weekly,monthly}
```

### 3. Run first backup (test)

```bash
# On the server
BACKUP_DEST=/mnt/server-cloud/backups/daily ~/server/scripts/backup-server.sh
```

This will create your first backup. Check it:
```bash
ls -lh /mnt/server-cloud/backups/daily/
```

### 4. Setup automated backups

```bash
# On the server (or from local)
~/server/scripts/setup-backup-cron.sh
```

This sets up:
- Daily backups at 2 AM (kept 7 days)
- Weekly backups on Sunday 1 AM (kept 4 weeks)
- Monthly backups on 1st at midnight (kept 6 months)
- Automatic cleanup of old backups
- Backup health checks

### 5. Verify cron jobs are installed

```bash
sudo crontab -l | grep backup
```

You should see the backup cron jobs listed.

## Manual Backup

To run a backup manually:
```bash
# Daily backup
BACKUP_DEST=/mnt/server-cloud/backups/daily ~/server/scripts/backup-server.sh

# Weekly backup
BACKUP_DEST=/mnt/server-cloud/backups/weekly ~/server/scripts/backup-server.sh

# Monthly backup
BACKUP_DEST=/mnt/server-cloud/backups/monthly ~/server/scripts/backup-server.sh
```

## Restore from Backup

```bash
# Restore everything
RESTORE_SOURCE=/mnt/server-cloud/backups/daily/latest ~/server/scripts/restore-server.sh

# Restore specific backup
RESTORE_SOURCE=/mnt/server-cloud/backups/weekly/server-backup-20240101_010000 ~/server/scripts/restore-server.sh
```

## Check Backup Health

```bash
~/server/scripts/check-backup-health.sh
```

## View Backup Logs

```bash
# Daily backup log
tail -f /var/log/server-backup-daily.log

# Weekly backup log
tail -f /var/log/server-backup-weekly.log

# Monthly backup log
tail -f /var/log/server-backup-monthly.log

# Cleanup log
tail -f /var/log/backup-cleanup.log

# Health check log
tail -f /var/log/backup-health.log
```

## Next Steps

1. **Test restore**: Try restoring a single docker volume to verify backups work
2. **Setup cloud backup** (optional): See `backup-strategy.md` for cloud backup options
3. **Setup monitoring**: Configure alerts if backups fail (see backup-strategy.md)
4. **Regular testing**: Test full restore procedure quarterly

## Troubleshooting

### Backup fails with permission error
```bash
# Ensure backup directory is writable
sudo chown -R unarmedpuppy:unarmedpuppy /mnt/server-cloud/backups
```

### Can't find latest backup
```bash
# Check if symlink exists
ls -la /mnt/server-cloud/backups/daily/latest

# List all backups
ls -lh /mnt/server-cloud/backups/daily/
```

### Out of disk space
```bash
# Check disk usage
df -h /mnt/server-cloud

# Manually run cleanup
~/server/scripts/cleanup-old-backups.sh

# Or delete old backups manually
rm -rf /mnt/server-cloud/backups/daily/server-backup-20240101_*
```

## Cost-Effective Cloud Backup (Optional)

For additional protection, consider syncing monthly backups to cloud:

1. **Install rclone**:
   ```bash
   sudo apt install rclone
   rclone config
   ```

2. **Configure cloud storage** (Backblaze B2, Wasabi, etc.)

3. **Create sync script**:
   ```bash
   cat > ~/server/scripts/sync-to-cloud.sh <<'EOF'
   #!/bin/bash
   rclone sync /mnt/server-cloud/backups/monthly \
     b2:home-server-backups/monthly \
     --progress
   EOF
   chmod +x ~/server/scripts/sync-to-cloud.sh
   ```

4. **Add to cron** (runs day after monthly backup):
   ```bash
   sudo crontab -e
   # Add: 0 2 2 * * /home/unarmedpuppy/server/scripts/sync-to-cloud.sh
   ```

For more details, see `backup-strategy.md`.

