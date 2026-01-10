# Backup System Reference

This document covers all backup systems, their configuration, schedules, and management.

## Overview

The server uses a **3-2-1 backup strategy**:
- **3** copies of data (original + 2 backups)
- **2** different storage types (ZFS + cloud)
- **1** offsite copy (Backblaze B2)

| System | What | Where | Schedule | Retention |
|--------|------|-------|----------|-----------|
| **ZFS RAID-Z1** | All data | 4x 7.3TB drives | Real-time | N/A (primary) |
| **rsnapshot** | Server configs | `/jenquist-cloud/backups/` | Every 4 hours | 3 alpha, 2 beta, 1 gamma, 1 delta |
| **Backblaze B2** | Entire ZFS pool | Cloud (encrypted) | Daily 3 AM | Indefinite |

## Backblaze B2 Cloud Backup

### Configuration

| Component | Value |
|-----------|-------|
| **Provider** | Backblaze B2 Cloud Storage |
| **Bucket** | `jenquist-cloud` |
| **Source** | `/jenquist-cloud` (entire ZFS pool) |
| **Tool** | rclone with crypt encryption |
| **Encryption** | AES-256 (files) + EME (filenames) |
| **Schedule** | Daily at 3:00 AM (cron) |
| **Cost** | ~$6/TB/month storage, $0.01/GB download |

### Encryption

All data is encrypted **client-side** before upload using rclone crypt:
- **Algorithm**: AES-256 in CTR mode with HMAC-SHA256 authentication
- **Filename encryption**: EME wide-block (filenames unreadable in B2)
- **Directory encryption**: Enabled
- **Password**: Stored in 1Password - **REQUIRED FOR RECOVERY**

**WARNING**: Losing the encryption password = permanent data loss. Backblaze only sees encrypted blobs.

### Files & Configuration

| File | Location | Purpose |
|------|----------|---------|
| Backup script | `scripts/backup-to-b2.sh` | Main backup script |
| rclone config | `~/.config/rclone/rclone.conf` | B2 credentials + encryption |
| Logs | `~/server/logs/backups/backup-*.log` | Per-run logs |
| Cron log | `~/server/logs/backups/cron.log` | Scheduled run output |

### rclone Configuration

```ini
[b2]
type = b2
account = <keyID>
key = <applicationKey>

[b2-encrypted]
type = crypt
remote = b2:jenquist-cloud
password = <obscured-password>
filename_encryption = standard
directory_name_encryption = true
```

### Cron Schedule

```
# User crontab (crontab -e)
30 5 * * * /home/unarmedpuppy/server/scripts/backup-to-b2.sh >> /home/unarmedpuppy/server/logs/backups/cron.log 2>&1
```

> **TEMPORARY (Jan 2026)**: Schedule changed from 1:00 AM to 5:30 AM to allow initial B2 sync to complete. The server restarts at 5:00 AM daily, which was terminating backups after only 4 hours. Running at 5:30 AM gives ~23.5 hours per day. **Revert to `0 1 * * *` once initial sync completes.**

### Common Operations

#### Check Backup Status
```bash
# Is backup running?
ps aux | grep rclone | grep -v grep

# Check B2 bucket size
rclone size b2-encrypted:

# View latest log
ls -lt ~/server/logs/backups/backup-*.log | head -1 | xargs tail -20

# Check cron log
tail -100 ~/server/logs/backups/cron.log
```

#### Run Manual Backup
```bash
# Full backup
bash ~/server/scripts/backup-to-b2.sh

# Dry-run (preview only)
bash ~/server/scripts/backup-to-b2.sh --dry-run

# Background with logging
nohup bash ~/server/scripts/backup-to-b2.sh > ~/server/logs/backups/manual-backup.log 2>&1 &
```

#### Prioritize Specific Folder
To back up a specific folder first (e.g., personal-media before everything else):

```bash
# 1. Stop current backup
pkill -f 'rclone sync /jenquist-cloud'

# 2. Back up priority folder first
nohup rclone sync /jenquist-cloud/archive/personal-media b2-encrypted:archive/personal-media \
  --transfers 4 --checkers 8 --progress \
  --log-file ~/server/logs/backups/priority-backup.log \
  --log-level INFO --stats 1m > /dev/null 2>&1 &

# 3. Once complete, run full backup (will skip already-uploaded files)
bash ~/server/scripts/backup-to-b2.sh
```

#### Restore Files
```bash
# Single file
rclone copy b2-encrypted:path/to/file.txt /local/destination/

# Directory
rclone copy b2-encrypted:some-folder /local/destination/

# Full restore (disaster recovery)
rclone sync b2-encrypted: /jenquist-cloud --progress
```

#### View What Backblaze Sees
```bash
# Encrypted filenames (what B2 stores)
rclone ls b2:jenquist-cloud

# Decrypted view (what you see)
rclone ls b2-encrypted:
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Backup not running | Check `ps aux \| grep rclone`, verify cron with `crontab -l` |
| Hit daily cap | Increase cap in Backblaze console, restart backup |
| Authentication error | `rclone config show b2`, regenerate key if needed |
| Slow uploads | Check bandwidth, adjust `--transfers` in script |
| No space on device | rclone needs temp space; check `df -h /` |

---

## rsnapshot Local Backup

### What's Backed Up

| Source | Description |
|--------|-------------|
| `/home/` | All home directories |
| `/etc/` | System configuration |
| `/usr/local/` | Local installations |
| `/var/lib/docker/volumes/` | Docker persistent data |

### Destination

All backups stored in `/jenquist-cloud/backups/rsnapshot/`

### Retention Schedule

| Level | Keeps | Frequency | Cron Schedule |
|-------|-------|-----------|---------------|
| alpha | 3 | Every 4 hours | `0 */4 * * *` |
| beta | 2 | Daily | `30 3 * * *` |
| gamma | 1 | Weekly (Saturday) | `0 3 * * 1` |
| delta | 1 | Monthly (1st) | `30 2 1 * *` |

### Configuration

| File | Purpose |
|------|---------|
| `/etc/rsnapshot.conf` | Main configuration |
| `/etc/cron.d/rsnapshot` | Cron schedule (may need uncommenting) |
| `/var/run/rsnapshot.pid` | Lock file |

### Common Operations

```bash
# Test configuration
sudo rsnapshot configtest

# Run manual backup
sudo rsnapshot alpha

# Check backup sizes
du -sh /jenquist-cloud/backups/rsnapshot/*/

# View backup contents
ls -la /jenquist-cloud/backups/rsnapshot/alpha.0/localhost/
```

### Current Status (as of Dec 2024)

**Issue**: Cron entries in `/etc/cron.d/rsnapshot` are commented out.
**Action needed**: Uncomment the cron lines to re-enable automated backups.

```bash
# Edit and uncomment the schedule lines
sudo nano /etc/cron.d/rsnapshot
```

---

## ZFS RAID-Z1 Pool

### Configuration

| Setting | Value |
|---------|-------|
| Pool name | `jenquist-cloud` |
| Configuration | RAID-Z1 (4 drives) |
| Drive size | 7.3TB each |
| Usable capacity | ~21TB |
| Fault tolerance | 1 drive failure |

### Health Check

```bash
# Pool status
zpool status jenquist-cloud

# Pool usage
zpool list jenquist-cloud

# Disk space
df -h /jenquist-cloud
```

### What's Stored

| Directory | Contents |
|-----------|----------|
| `/jenquist-cloud/archive/` | Media files (movies, TV, music, personal-media) |
| `/jenquist-cloud/backups/` | rsnapshot local backups |
| `/jenquist-cloud/vault/` | Secure storage |

---

## Disaster Recovery

### Scenario: Total Server Loss

1. **Set up new server** with Ubuntu
2. **Create ZFS pool** (or use ext4)
3. **Install rclone**: `sudo apt install rclone`
4. **Get credentials from 1Password**:
   - B2 keyID and applicationKey
   - Encryption password
5. **Configure rclone**:
   ```bash
   mkdir -p ~/.config/rclone
   rclone obscure "YOUR-PASSWORD"  # Get obscured version
   # Create rclone.conf with credentials
   ```
6. **Restore data**:
   ```bash
   rclone sync b2-encrypted: /jenquist-cloud --progress
   ```
7. **Restore server configs** from `/jenquist-cloud/backups/rsnapshot/`
8. **Rebuild Docker services** using git repo

### Scenario: Single Drive Failure

1. ZFS will continue operating in degraded mode
2. Replace failed drive
3. `zpool replace jenquist-cloud <old-device> <new-device>`
4. Wait for resilver to complete

### Scenario: Accidental File Deletion

1. Check rsnapshot backups first (fastest):
   ```bash
   ls /jenquist-cloud/backups/rsnapshot/alpha.0/localhost/home/
   ```
2. If not in rsnapshot, restore from B2:
   ```bash
   rclone copy b2-encrypted:path/to/file /destination/
   ```

---

## Future Plans

### Planned Improvements

1. **[ ] Enable rsnapshot cron** - Uncomment `/etc/cron.d/rsnapshot`
2. **[ ] Bare metal recovery (Rear)** - Create bootable recovery image
3. **[ ] Backup monitoring** - Alert on backup failures
4. **[ ] Test restore on dev server** - Verify disaster recovery works

### Bare Metal Recovery with Rear

**Status**: Planned (task `home-server-rn2`)

Rear (Relax-and-Recover) creates a bootable ISO that can restore the entire server including:
- Operating system
- All packages and configurations
- Docker setup

This is the "gold standard" for disaster recovery but requires additional setup.

---

## Cost Summary

### Backblaze B2 (Current)

| Data Size | Monthly Cost | Full Restore Cost |
|-----------|--------------|-------------------|
| 1 TB | $6 | $10 |
| 5 TB | $30 | $50 |
| 10 TB | $60 | $100 |

- Uploads: Free
- First 1GB download/day: Free
- Storage: $0.006/GB/month
- Download: $0.01/GB

### Local Storage (One-time)

- 4x 8TB drives: ~$600-800
- Power consumption: ~40W continuous

---

## Selective Backup with backup-configurator

### Overview

The backup-configurator tool enables **surgical backup selection** to reduce B2 storage costs by only backing up essential directories instead of the entire ~21TB pool.

| Component | Value |
|-----------|-------|
| **Tool** | `scripts/backup-configurator.py` |
| **Agent** | `agents/personas/backup-agent.md` |
| **Skill** | `agents/skills/backup-configurator/SKILL.md` |
| **Config Storage** | `~/.backup-configs.json` |

### Why Use Selective Backup

| Approach | Data Size | Monthly Cost |
|----------|-----------|--------------|
| Full pool backup | ~21 TB | ~$126/month |
| Personal media only | ~2 TB | ~$12/month |
| Critical data only | ~500 GB | ~$3/month |

### Quick Start

```bash
# Run interactively on server
scripts/connect-server.sh "python3 ~/server/scripts/backup-configurator.py"

# List saved configurations
scripts/connect-server.sh "python3 ~/server/scripts/backup-configurator.py list"

# Show configuration details
scripts/connect-server.sh "python3 ~/server/scripts/backup-configurator.py show CONFIG_NAME"

# Test with dry-run
scripts/connect-server.sh "python3 ~/server/scripts/backup-configurator.py run CONFIG_NAME --dry-run"
```

### Recommended Backup Priorities

| Priority | Directories | Why |
|----------|-------------|-----|
| **Critical** | `vault/`, `backups/` | Irreplaceable personal data |
| **High** | `archive/personal-media/` | Photos, documents, memories |
| **Medium** | `archive/entertainment-media/Music/` | Music collection |
| **Low/Skip** | `harbor/`, `archive/entertainment-media/Movies/` | Can be re-downloaded |

### Default Exclude Patterns

The tool excludes these by default:
- `*.tmp`, `*.temp` - Temporary files
- `.DS_Store`, `Thumbs.db` - OS metadata
- `.cache/`, `tmp/`, `temp/` - Cache directories
- `.Trash/` - Trash folders

### Configuration File Format

Configs stored in `~/.backup-configs.json`:

```json
{
  "configs": [
    {
      "name": "personal-essentials",
      "source_paths": ["vault/", "backups/", "archive/personal-media/"],
      "exclude_patterns": ["*.tmp", ".cache/"],
      "priority": "high",
      "enabled": true,
      "rclone_remote": "b2-encrypted:"
    }
  ]
}
```

---

## Quick Reference

### Check All Backup Systems

```bash
# B2 backup status
ps aux | grep rclone | grep -v grep
rclone size b2-encrypted:

# rsnapshot status
ls -la /jenquist-cloud/backups/rsnapshot/

# ZFS health
zpool status jenquist-cloud
```

### Key Locations

| What | Where |
|------|-------|
| B2 backup script | `scripts/backup-to-b2.sh` |
| Backup configurator | `scripts/backup-configurator.py` |
| Backup configs | `~/.backup-configs.json` |
| B2 logs | `~/server/logs/backups/` |
| rclone config | `~/.config/rclone/rclone.conf` |
| rsnapshot config | `/etc/rsnapshot.conf` |
| rsnapshot backups | `/jenquist-cloud/backups/rsnapshot/` |
| ZFS pool | `/jenquist-cloud/` |

### Emergency Contacts

- **Backblaze Support**: https://www.backblaze.com/help.html
- **Encryption Password**: 1Password (search "B2" or "rclone")
