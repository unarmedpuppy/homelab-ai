# ZFS Migration: RAID-Z1 to RAID-Z2 with 8 New Drives

**Status**: Planning
**Beads Epic**: `home-server-46d`

## Overview

This guide covers migrating from a 4-drive RAID-Z1 pool to an 8-drive RAID-Z2 pool using 8 new drives.

**Current Setup:**
- Pool: `jenquist-cloud`
- Configuration: RAID-Z1 (4 drives: sda, sdb, sdc, sdd)
- Filesystem: `jenquist-cloud/archive`
- Encryption: Enabled (requires key loading)

**Target Setup:**
- Pool: `jenquist-cloud` (same name, new pool)
- Configuration: RAID-Z2 (8 new drives)
- Filesystem: `jenquist-cloud/archive` (restored)
- Encryption: Re-enabled

## ⚠️ CRITICAL: Pre-Migration Checklist

- [ ] **Full backup completed** (use `backup-server.sh`)
- [ ] **Backup verified** (test restore if possible)
- [ ] **8 new drives purchased and verified** (CMR, same size or larger)
- [ ] **All services using ZFS stopped** (Jellyfin, etc.)
- [ ] **Maintenance window scheduled** (plan for 8-24 hours depending on data size)
- [ ] **Encryption keys backed up** (if using ZFS encryption)
- [ ] **Current pool status checked** (`zpool status jenquist-cloud`)

## Migration Strategy Options

### Option 1: New Pool + Data Copy (RECOMMENDED - Safest)

**Pros:**
- Old pool remains intact until migration verified
- Can rollback if issues occur
- Safer for large datasets
- Can test new pool before destroying old

**Cons:**
- Requires enough space for both pools temporarily
- Takes longer (copy time)

### Option 2: In-Place Replacement (Faster, Riskier)

**Pros:**
- Faster (no data copy)
- Less space needed

**Cons:**
- Higher risk (old pool destroyed immediately)
- No rollback option
- More complex process

**We'll use Option 1 (safest approach)**

## Step-by-Step Migration Process

### Phase 1: Preparation

#### 1.1 Stop All Services Using ZFS

```bash
# Stop Jellyfin (uses ZFS)
cd ~/server/apps/jellyfin
docker compose down

# Check for any other services using /jenquist-cloud
docker ps --format "table {{.Names}}\t{{.Mounts}}" | grep jenquist-cloud

# Stop any services found
# Also check systemd services
systemctl list-units | grep -i zfs
```

#### 1.2 Verify Current Pool Status

```bash
# Check pool status
sudo zpool status jenquist-cloud

# Check filesystem usage
sudo zfs list jenquist-cloud/archive

# Check encryption status
sudo zfs get encryption jenquist-cloud/archive

# Record current mount point
mount | grep jenquist-cloud
```

#### 1.3 Backup Encryption Keys (if using ZFS encryption)

```bash
# If you have encryption keys stored, back them up
# Check where keys are stored
sudo zfs get keylocation jenquist-cloud/archive

# Backup key files if they exist
# (Location depends on your setup)
```

#### 1.4 Create Full Backup

```bash
# Run comprehensive backup
bash ~/server/scripts/backup-server.sh

# Verify backup completed successfully
ls -lh /mnt/server-cloud/backups/latest/

# Test backup integrity (optional but recommended)
cd /mnt/server-cloud/backups/latest
for file in docker-volumes/*.tar.gz; do
  echo "Checking $file"
  gzip -t "$file" || echo "ERROR: $file is corrupted"
done
```

#### 1.5 Identify New Drives

```bash
# List all drives
sudo lsblk

# Identify new drives (should be 8 new drives)
# They'll likely be sde, sdf, sdg, sdh, sdi, sdj, sdk, sdl
# Or check by size/model
sudo fdisk -l | grep -i "disk /dev/sd"

# Verify new drives are correct size/model
for disk in sde sdf sdg sdh sdi sdj sdk sdl; do
  echo "=== /dev/$disk ==="
  sudo smartctl -i /dev/$disk | grep -E "Model|Capacity|Serial"
done
```

**⚠️ IMPORTANT**: Note which devices are your NEW drives. We'll assume they're `sde, sdf, sdg, sdh, sdi, sdj, sdk, sdl` for this guide. **Verify this matches your system!**

### Phase 2: Create New RAID-Z2 Pool

#### 2.1 Create New Pool with 8 Drives

```bash
# Create new RAID-Z2 pool with 8 new drives
# Using different pool name temporarily for safety
sudo zpool create jenquist-cloud-new raidz2 /dev/sde /dev/sdf /dev/sdg /dev/sdh /dev/sdi /dev/sdj /dev/sdk /dev/sdl

# Verify pool created
sudo zpool status jenquist-cloud-new

# Check pool capacity
sudo zpool list jenquist-cloud-new
```

#### 2.2 Create Filesystem Structure

```bash
# Create archive filesystem
sudo zfs create jenquist-cloud-new/archive

# Set compression (recommended for media)
sudo zfs set compression=lz4 jenquist-cloud-new/archive

# Set encryption (if you were using it)
# First, generate or use existing encryption key
# Then enable encryption:
sudo zfs create -o encryption=aes-256-gcm -o keyformat=passphrase jenquist-cloud-new/archive-encrypted
# OR if you have a keyfile:
sudo zfs create -o encryption=aes-256-gcm -o keylocation=file:///path/to/keyfile jenquist-cloud-new/archive-encrypted

# Set mount point
sudo zfs set mountpoint=/jenquist-cloud-new jenquist-cloud-new/archive
```

#### 2.3 Test New Pool

```bash
# Test write performance
sudo dd if=/dev/zero of=/jenquist-cloud-new/testfile bs=1M count=1000
sudo rm /jenquist-cloud-new/testfile

# Check pool health
sudo zpool status jenquist-cloud-new

# Verify filesystem
sudo zfs list jenquist-cloud-new
```

### Phase 3: Data Migration

#### 3.1 Mount Old Pool (if not already mounted)

```bash
# Load encryption keys for old pool
sudo zfs load-key -a

# Mount old pool
sudo zfs mount -a

# Verify both pools are mounted
mount | grep jenquist-cloud
```

#### 3.2 Copy Data from Old Pool to New Pool

**Option A: Using rsync (Recommended - preserves permissions, can resume)**

```bash
# Install rsync if not installed
sudo apt install rsync -y

# Copy data with progress
sudo rsync -avh --progress /jenquist-cloud/archive/ /jenquist-cloud-new/archive/

# Verify copy completed
# Compare sizes (should be similar, new pool may be slightly different due to compression)
sudo du -sh /jenquist-cloud/archive
sudo du -sh /jenquist-cloud-new/archive
```

**Option B: Using zfs send/receive (Faster, but requires snapshot)**

```bash
# Create snapshot of old pool
sudo zfs snapshot jenquist-cloud/archive@migration-$(date +%Y%m%d)

# Send snapshot to new pool
sudo zfs send -R jenquist-cloud/archive@migration-$(date +%Y%m%d) | sudo zfs receive -F jenquist-cloud-new/archive

# This preserves ZFS features (compression, encryption, etc.)
# But requires both pools to be ZFS
```

**Option C: Using tar (Simple, but slower)**

```bash
# Create archive and extract
cd /jenquist-cloud/archive
sudo tar czf /tmp/archive-backup.tar.gz .
cd /jenquist-cloud-new/archive
sudo tar xzf /tmp/archive-backup.tar.gz
sudo rm /tmp/archive-backup.tar.gz
```

**Recommended: Use rsync (Option A)** - it's reliable, shows progress, and can resume if interrupted.

#### 3.3 Verify Data Integrity

```bash
# Compare file counts
find /jenquist-cloud/archive -type f | wc -l
find /jenquist-cloud-new/archive -type f | wc -l

# Compare directory structure
diff -r /jenquist-cloud/archive /jenquist-cloud-new/archive | head -20

# Spot check random files
# Pick a few files and verify they're identical
md5sum /jenquist-cloud/archive/path/to/file1
md5sum /jenquist-cloud-new/archive/path/to/file1

# Should match!
```

### Phase 4: Switch to New Pool

#### 4.1 Stop Services Again (if any started)

```bash
# Ensure all services are stopped
cd ~/server/apps/jellyfin
docker compose down
```

#### 4.2 Unmount Old Pool

```bash
# Unmount old pool
sudo zfs unmount jenquist-cloud/archive

# Export old pool (makes it unavailable)
sudo zpool export jenquist-cloud
```

#### 4.3 Rename New Pool to Original Name

```bash
# Export new pool
sudo zpool export jenquist-cloud-new

# Import with original name
sudo zpool import jenquist-cloud-new jenquist-cloud

# Verify
sudo zpool status jenquist-cloud
sudo zfs list jenquist-cloud
```

#### 4.4 Update Mount Point

```bash
# Set mount point to original location
sudo zfs set mountpoint=/jenquist-cloud jenquist-cloud/archive

# Mount
sudo zfs mount jenquist-cloud/archive

# Verify
mount | grep jenquist-cloud
ls -la /jenquist-cloud/archive
```

#### 4.5 Update Service Configurations

```bash
# Check Jellyfin docker-compose.yml
cd ~/server/apps/jellyfin
cat docker-compose.yml | grep -i zfs

# If ZFS_PATH is set, verify it points to correct location
# Should be: /jenquist-cloud/archive (or subdirectory)

# Update if needed (usually not needed if mount point is same)
```

### Phase 5: Verification and Cleanup

#### 5.1 Start Services and Test

```bash
# Start Jellyfin
cd ~/server/apps/jellyfin
docker compose up -d

# Check logs
docker compose logs --tail 50

# Test media playback
# Access Jellyfin and verify media is accessible

# Check other services using ZFS
```

#### 5.2 Verify Pool Health

```bash
# Check pool status
sudo zpool status jenquist-cloud

# Should show:
# - state: ONLINE
# - 8 drives in raidz2-0
# - No errors

# Check filesystem
sudo zfs list jenquist-cloud

# Check encryption (if used)
sudo zfs get encryption jenquist-cloud/archive
```

#### 5.3 Update Auto-Mount (if needed)

```bash
# Check if you have auto-mount scripts
# Usually ZFS auto-mounts, but check:

# Check systemd services
systemctl status zfs-mount.service
systemctl status zfs-import-cache.service

# If using encryption, ensure keys load on boot
# Check /etc/systemd/system/ or cron jobs for key loading
```

#### 5.4 Clean Up Old Pool (ONLY AFTER VERIFICATION)

**⚠️ WAIT AT LEAST 1 WEEK** before destroying old pool to ensure everything works!

```bash
# After thorough testing (1+ week), you can destroy old pool:

# First, verify old pool is exported and not in use
sudo zpool list | grep jenquist-cloud-old

# If you kept old pool with different name, destroy it:
sudo zpool destroy jenquist-cloud-old

# Physically remove old drives (power down first!)
```

### Phase 6: Physical Drive Removal

#### 6.1 Power Down Server

```bash
# Shutdown server
sudo shutdown -h now
```

#### 6.2 Remove Old Drives

1. **Power off server completely**
2. **Remove 4 old BarraCuda drives** (sda, sdb, sdc, sdd)
3. **Keep them as spares** (or dispose of safely)
4. **Verify 8 new drives are properly connected**
5. **Power on server**

#### 6.3 Verify on Boot

```bash
# After boot, verify pool status
sudo zpool status jenquist-cloud

# Should show 8 drives, all ONLINE

# Load encryption keys (if using encryption)
sudo zfs load-key -a

# Mount
sudo zfs mount -a

# Verify services start correctly
cd ~/server/apps/jellyfin
docker compose ps
```

## Alternative: In-Place Migration (Advanced - Not Recommended)

If you want to migrate in-place without creating a separate pool:

```bash
# ⚠️ THIS IS RISKY - BACKUP FIRST!

# 1. Export current pool
sudo zpool export jenquist-cloud

# 2. Physically replace all 4 drives with 8 new drives
# (Power down, swap drives, power up)

# 3. Import pool (will fail - drives changed)
# This won't work - you need to recreate

# 4. Create new pool with 8 drives
sudo zpool create jenquist-cloud raidz2 /dev/sda /dev/sdb /dev/sdc /dev/sdd /dev/sde /dev/sdf /dev/sdg /dev/sdh

# 5. Restore from backup
# Use restore-server.sh or manually restore
```

**This approach is NOT recommended** because:
- No rollback option
- Requires full restore from backup
- More downtime
- Higher risk

## Troubleshooting

### Issue: Pool won't import

```bash
# List available pools
sudo zpool import

# Import with specific name
sudo zpool import -f old-pool-name new-pool-name
```

### Issue: Encryption keys not loading

```bash
# Manually load keys
sudo zfs load-key -a

# Check key location
sudo zfs get keylocation jenquist-cloud/archive

# Update key location if needed
sudo zfs set keylocation=file:///path/to/key jenquist-cloud/archive
```

### Issue: Services can't find data

```bash
# Verify mount point
mount | grep jenquist-cloud

# Check permissions
ls -la /jenquist-cloud/archive

# Verify ZFS_PATH in docker-compose.yml
cd ~/server/apps/jellyfin
grep ZFS_PATH docker-compose.yml
```

### Issue: Pool shows errors after migration

```bash
# Check for errors
sudo zpool status jenquist-cloud

# Scrub pool (checks data integrity)
sudo zpool scrub jenquist-cloud

# Monitor scrub progress
sudo zpool status jenquist-cloud
```

## Migration Timeline Estimate

**For ~20TB of data:**

- Preparation: 1-2 hours
- Backup creation: 2-4 hours (depends on backup destination speed)
- New pool creation: 5-10 minutes
- Data copy (rsync): 8-16 hours (depends on drive speed)
- Verification: 1-2 hours
- Service restart/verification: 30 minutes
- **Total: 12-24 hours**

**Plan for a full day maintenance window!**

## Post-Migration Checklist

- [ ] New pool created and verified
- [ ] Data copied and verified (file counts, spot checks)
- [ ] Services tested and working
- [ ] Pool health verified (no errors)
- [ ] Encryption working (if used)
- [ ] Auto-mount configured
- [ ] SMART monitoring set up for new drives
- [ ] Old pool exported (kept for 1+ week as backup)
- [ ] Documentation updated
- [ ] Old drives removed (after verification period)

## Summary

**Recommended Process:**
1. **Backup everything** (critical!)
2. **Create new RAID-Z2 pool** with 8 new drives
3. **Copy data** from old pool to new pool (rsync)
4. **Verify data integrity**
5. **Switch to new pool** (export old, import new with original name)
6. **Test services**
7. **Keep old pool for 1+ week** before destroying
8. **Remove old drives** after verification

This approach is the safest and allows rollback if issues occur.

