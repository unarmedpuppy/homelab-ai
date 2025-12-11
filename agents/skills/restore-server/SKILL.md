---
name: restore-server
description: Restore from backups created by backup-server.sh
when_to_use: Disaster recovery, system restoration, reverting to previous state, data recovery
script: scripts/restore-server.sh
---

# Restore Server

Restores from backups created by `backup-server.sh`.

## When to Use

- Disaster recovery
- System restoration
- Reverting to previous state
- Data recovery
- Testing restore procedures

## ⚠️ Warning

**This will overwrite existing data. Requires confirmation.**

## Usage

```bash
# On server
RESTORE_SOURCE=/mnt/server-cloud/backups/daily/latest ~/server/scripts/restore-server.sh

# From local machine
bash scripts/connect-server.sh "RESTORE_SOURCE=/mnt/server-cloud/backups/daily/latest ~/server/scripts/restore-server.sh"
```

## Restore Source

Set `RESTORE_SOURCE` environment variable:

```bash
# Latest daily backup
RESTORE_SOURCE=/mnt/server-cloud/backups/daily/latest

# Specific backup
RESTORE_SOURCE=/mnt/server-cloud/backups/daily/2024-12-05

# Weekly backup
RESTORE_SOURCE=/mnt/server-cloud/backups/weekly/latest
```

## What Gets Restored

- Docker volumes
- Service configurations
- System configurations
- User configurations
- Cron jobs

## Process

1. **Confirmation prompt** - Script asks for confirmation
2. **Backup verification** - Checks backup integrity
3. **Stops services** - Stops Docker containers
4. **Restores data** - Copies files from backup
5. **Restarts services** - Starts Docker containers

## Before Restoring

1. **Verify backup source** - Ensure backup is valid
2. **Check backup health** - Run `check-backup-health` tool
3. **Backup current state** - Create backup before restoring
4. **Plan downtime** - Services will be stopped during restore

## After Restoring

1. **Verify services** - Check all containers are running
2. **Check logs** - Look for errors
3. **Test functionality** - Verify services work correctly
4. **Update documentation** - Note restore date and reason

## Related Tools

- `backup-server` - Create backups
- `check-backup-health` - Validate backup integrity

## Related Documentation

- `scripts/BACKUP_QUICKSTART.md` - Backup/restore guide
- `scripts/backup-strategy.md` - Backup strategy

