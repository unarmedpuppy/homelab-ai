---
name: zfs-pool-recovery
description: Recover ZFS pool from drive failures, import issues, or missing drives
when_to_use: When ZFS pool won't mount, drives are missing, or pool shows degraded status
---

# ZFS Pool Recovery

Steps to diagnose and recover from ZFS pool issues.

## Pool Info

| Setting | Value |
|---------|-------|
| Pool name | `jenquist-cloud` |
| Configuration | RAID-Z1 (4 drives) |
| Mount point | `/jenquist-cloud` |
| Fault tolerance | 1 drive failure |

## Quick Diagnosis

```bash
# Check pool status
scripts/connect-server.sh "zpool status jenquist-cloud"

# Check if pool is mounted
scripts/connect-server.sh "df -h /jenquist-cloud"

# List all pools
scripts/connect-server.sh "zpool list"

# Check available drives
scripts/connect-server.sh "lsblk"
```

## Common Issues

### Pool Not Mounted

```bash
# Try to import the pool
scripts/connect-server.sh "sudo zpool import jenquist-cloud"

# If "pool already exists" error, check if it's imported but not mounted
scripts/connect-server.sh "zpool list"
scripts/connect-server.sh "zfs mount jenquist-cloud"
```

### Drives Not Visible

If `lsblk` doesn't show all 4 drives:

1. **Check physical connections** - Power and SATA cables
2. **Check if drives feel warm** - Cold drives = no power
3. **Check BIOS** - May need to enable AHCI/SATA ports
4. **Reseat cables** - Often fixes intermittent issues

```bash
# Check what drives are visible
scripts/connect-server.sh "lsblk | grep -E 'sd[a-z]'"

# Check dmesg for drive errors
scripts/connect-server.sh "dmesg | grep -E 'sd[a-z]|ata|SATA' | tail -30"
```

### Pool Shows DEGRADED

One drive has failed but pool is still operational.

```bash
# Check which drive failed
scripts/connect-server.sh "zpool status jenquist-cloud"

# The DEGRADED drive will show OFFLINE, FAULTED, or UNAVAIL
```

**To replace a failed drive:**
```bash
# 1. Identify new drive
scripts/connect-server.sh "lsblk"

# 2. Replace the failed drive
scripts/connect-server.sh "sudo zpool replace jenquist-cloud <old-device> <new-device>"

# 3. Monitor resilver progress
scripts/connect-server.sh "zpool status jenquist-cloud"
```

### Pool Import Fails

```bash
# Force import (if pool was exported uncleanly)
scripts/connect-server.sh "sudo zpool import -f jenquist-cloud"

# Search for importable pools
scripts/connect-server.sh "sudo zpool import"

# Import with different mount point (if conflict)
scripts/connect-server.sh "sudo zpool import -R /mnt/recovery jenquist-cloud"
```

### After Reboot

If pool doesn't auto-mount after reboot:

```bash
# Check pool status
scripts/connect-server.sh "zpool status"

# If not imported, import it
scripts/connect-server.sh "sudo zpool import -a"

# Enable auto-import on boot
scripts/connect-server.sh "sudo systemctl enable zfs-import-cache.service"
scripts/connect-server.sh "sudo systemctl enable zfs-mount.service"
```

## Health Checks

```bash
# Full pool status with errors
scripts/connect-server.sh "zpool status -v jenquist-cloud"

# IO statistics
scripts/connect-server.sh "zpool iostat jenquist-cloud 1 5"

# Check SMART status of drives
scripts/connect-server.sh "sudo smartctl -a /dev/sda | grep -E 'Model|Serial|Health|Reallocated'"
scripts/connect-server.sh "sudo smartctl -a /dev/sdb | grep -E 'Model|Serial|Health|Reallocated'"
scripts/connect-server.sh "sudo smartctl -a /dev/sdc | grep -E 'Model|Serial|Health|Reallocated'"
scripts/connect-server.sh "sudo smartctl -a /dev/sdd | grep -E 'Model|Serial|Health|Reallocated'"
```

## Data Loss Scenarios

### RAID-Z1 Limits

- **1 drive failure**: Pool continues, data safe
- **2+ drive failures**: DATA LOSS - restore from B2 backup

### If Data Lost

1. Replace failed drives
2. Create new pool: `sudo zpool create jenquist-cloud raidz1 sda sdb sdc sdd`
3. Restore from B2: `rclone sync b2-encrypted: /jenquist-cloud --progress`

See `agents/reference/backups.md` for full disaster recovery procedures.

## Related

- `agents/reference/backups.md` - Backup and recovery
- `agents/reference/storage/` - Storage documentation
- `agents/skills/monitor-drive-health/` - Proactive monitoring
