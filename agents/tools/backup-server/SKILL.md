---
name: backup-server
description: Comprehensive backup script for the entire server
when_to_use: Before major changes, regular backups, system maintenance, disaster recovery preparation
script: scripts/backup-server.sh
---

# Backup Server

Comprehensive backup script for the entire server.

## When to Use

- Before major system changes
- Regular backups (automated via cron)
- System maintenance
- Disaster recovery preparation
- Before upgrades

## Usage

```bash
# On server
BACKUP_DEST=/mnt/server-cloud/backups/daily ~/server/scripts/backup-server.sh

# From local machine
bash scripts/connect-server.sh "BACKUP_DEST=/mnt/server-cloud/backups/daily ~/server/scripts/backup-server.sh"
```

## What It Backs Up

- **All Docker volumes** - Application data
- **All docker-compose.yml files** - Service configurations
- **System configurations** - /etc directory
- **User home directory configurations** - ~/.config, ~/.ssh, etc.
- **Cron jobs** - Scheduled tasks
- **Mount point information** - Storage configuration
- **System package lists** - Installed packages

## Backup Destination

Set `BACKUP_DEST` environment variable:

```bash
# Daily backups
BACKUP_DEST=/mnt/server-cloud/backups/daily

# Weekly backups
BACKUP_DEST=/mnt/server-cloud/backups/weekly

# Monthly backups
BACKUP_DEST=/mnt/server-cloud/backups/monthly
```

## Automated Backups

Backups are automated via cron jobs (set up with `setup-backup-cron.sh`):
- **Daily**: 2 AM (kept 7 days)
- **Weekly**: Sunday 1 AM (kept 4 weeks)
- **Monthly**: 1st at midnight (kept 6 months)

## Verification

After backup, verify integrity:

```bash
# Check backup health
bash scripts/connect-server.sh "~/server/scripts/check-backup-health.sh"
```

## Related Tools

- `restore-server` - Restore from backups
- `check-backup-health` - Validate backup integrity
- `cleanup-old-backups` - Remove old backups (automated)

## Related Documentation

- `scripts/BACKUP_QUICKSTART.md` - Quick start guide
- `scripts/backup-strategy.md` - Backup strategy details

