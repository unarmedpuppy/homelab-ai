---
name: enable-rsnapshot
description: Enable and configure rsnapshot local backups
when_to_use: When rsnapshot cron jobs are disabled or backups aren't running
---

# Enable rsnapshot

rsnapshot provides local file-level backups of server configurations to the ZFS pool.

## Current Status

**Issue (as of Dec 2024)**: The cron jobs in `/etc/cron.d/rsnapshot` are commented out.

## Check If Running

```bash
# Check last backup time
scripts/connect-server.sh "ls -la /jenquist-cloud/backups/rsnapshot/"

# Check cron file
scripts/connect-server.sh "cat /etc/cron.d/rsnapshot"

# Check if rsnapshot is installed
scripts/connect-server.sh "which rsnapshot"
```

## Enable Cron Jobs

The cron file has the schedules commented out. To enable:

```bash
# View current cron file
scripts/connect-server.sh "cat /etc/cron.d/rsnapshot"

# Uncomment the schedule lines (requires sudo)
# The file should have these lines UNCOMMENTED:
# 0 */4    * * *    root    /usr/bin/rsnapshot alpha
# 30 3     * * *    root    /usr/bin/rsnapshot beta
# 0  3     * * 1    root    /usr/bin/rsnapshot gamma
# 30 2     1 * *    root    /usr/bin/rsnapshot delta
```

**Manual edit required** (SSH to server):
```bash
sudo nano /etc/cron.d/rsnapshot
# Remove the # from the schedule lines
# Save and exit
```

## Verify Configuration

```bash
# Test rsnapshot config
scripts/connect-server.sh "sudo rsnapshot configtest"

# Should output: Syntax OK
```

## What's Backed Up

From `/etc/rsnapshot.conf`:

| Source | Description |
|--------|-------------|
| `/home/` | All home directories |
| `/etc/` | System configuration |
| `/usr/local/` | Local installations |
| `/var/lib/docker/volumes/` | Docker persistent data |

## Schedule

| Level | Frequency | Retention | Cron |
|-------|-----------|-----------|------|
| alpha | Every 4 hours | 3 copies | `0 */4 * * *` |
| beta | Daily 3:30 AM | 2 copies | `30 3 * * *` |
| gamma | Weekly Monday 3 AM | 1 copy | `0 3 * * 1` |
| delta | Monthly 1st 2:30 AM | 1 copy | `30 2 1 * *` |

## Run Manual Backup

```bash
# Run alpha backup now
scripts/connect-server.sh "sudo rsnapshot alpha"

# Check it worked
scripts/connect-server.sh "ls -la /jenquist-cloud/backups/rsnapshot/"
```

## Troubleshooting

### Config Errors

```bash
# Test config
scripts/connect-server.sh "sudo rsnapshot configtest"

# Common issue: tabs vs spaces
# rsnapshot.conf REQUIRES tabs between fields
```

### Backup Not Running

```bash
# Check if cron daemon is running
scripts/connect-server.sh "systemctl status cron"

# Check cron logs
scripts/connect-server.sh "grep rsnapshot /var/log/syslog | tail -20"
```

### Lock File Issues

```bash
# Check for stale lock file
scripts/connect-server.sh "ls -la /var/run/rsnapshot.pid"

# Remove if stale (no rsnapshot process running)
scripts/connect-server.sh "sudo rm /var/run/rsnapshot.pid"
```

## Backup Location

All backups stored in `/jenquist-cloud/backups/rsnapshot/`:

```
rsnapshot/
├── alpha.0/    # Most recent (every 4 hours)
├── alpha.1/
├── alpha.2/
├── beta.0/     # Daily
├── beta.1/
├── gamma.0/    # Weekly
└── delta.0/    # Monthly
```

## Restore Files

```bash
# Find file in backup
scripts/connect-server.sh "ls /jenquist-cloud/backups/rsnapshot/alpha.0/localhost/home/"

# Copy file back
scripts/connect-server.sh "cp /jenquist-cloud/backups/rsnapshot/alpha.0/localhost/etc/some-file /etc/"
```

## Related

- `agents/reference/backups.md` - Complete backup documentation
- `agents/skills/manage-b2-backup/` - Cloud backup management
