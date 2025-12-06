---
name: check-backup-health
description: Validate backup integrity and check for recent backups
when_to_use: Regular backup verification, after backup operations, troubleshooting backup issues
script: scripts/check-backup-health.sh
---

# Check Backup Health

Validates backup integrity and checks for recent backups.

## When to Use

- Regular backup verification (weekly/monthly)
- After backup operations
- Troubleshooting backup issues
- Before restore operations
- Compliance checks

## Usage

```bash
# On server
~/server/scripts/check-backup-health.sh

# From local machine
bash scripts/connect-server.sh "~/server/scripts/check-backup-health.sh"
```

## What It Checks

- **Backup existence** - Are backups present?
- **Backup age** - How recent are backups?
- **Backup integrity** - Are backups valid?
- **Backup size** - Are backups complete?
- **Retention policy** - Are old backups cleaned up?

## Output

- ✓ **Green checkmarks** - Backups healthy
- ! **Yellow warnings** - Issues to review
- ✗ **Red errors** - Critical problems

## Common Issues

### No Recent Backups

**Problem**: No backups found in last 24 hours

**Solution**: Check cron jobs are running:
```bash
bash scripts/connect-server.sh "crontab -l"
```

### Backup Integrity Issues

**Problem**: Backup files corrupted or incomplete

**Solution**: 
1. Check disk space: `bash scripts/connect-server.sh "df -h"`
2. Check backup logs
3. Run backup manually to test

### Missing Backup Destinations

**Problem**: Backup directories don't exist

**Solution**: Create backup directories:
```bash
bash scripts/connect-server.sh "mkdir -p /mnt/server-cloud/backups/{daily,weekly,monthly}"
```

## Related Tools

- `backup-server` - Create backups
- `restore-server` - Restore from backups
- `cleanup-old-backups` - Remove old backups (automated)

