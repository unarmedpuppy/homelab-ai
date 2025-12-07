# ZFS Two-Pool Strategy: Keep Existing + New RAID-Z2 Pool

## Strategy Overview

**Proposed Setup:**
- **Pool 1 (Existing)**: 4x 8TB BarraCuda (RAID-Z1) - `jenquist-cloud`
- **Pool 2 (New)**: 6x 8TB IronWolf (RAID-Z2) - `jenquist-cloud-new` or `jenquist-archive`
- **Total Bays Used**: 10/10 (all bays full)

## Capacity Analysis

### Pool 1: Existing 4x 8TB RAID-Z1
- **Raw**: 32 TB
- **Usable**: ~24 TB (75% efficiency)
- **Protection**: 1-drive failure
- **Status**: Keep as-is, no migration needed

### Pool 2: New 6x 8TB RAID-Z2
- **Raw**: 48 TB
- **Usable**: ~32 TB (67% efficiency)
- **Protection**: 2-drive failure
- **Status**: New pool, better redundancy

### Combined Capacity
- **Total Raw**: 80 TB
- **Total Usable**: ~56 TB
- **Total Protection**: Pool 1 (1-drive), Pool 2 (2-drive)

## Cost Analysis

### 6x 8TB IronWolf
- **Cost**: ~$900-1,080 (6 drives × $150-180)
- **Usable**: ~32 TB
- **Cost per Usable TB**: ~$28-34/TB

### Total Investment
- **New drives**: $900-1,080
- **Total capacity**: 56 TB usable (24 + 32)
- **No migration needed**: Old pool stays intact

## Pros of Two-Pool Strategy

### ✅ Advantages

1. **Zero Downtime**
   - Existing pool keeps running
   - No service interruption
   - No data migration required initially

2. **Lower Risk**
   - Old pool stays intact (backup)
   - Can migrate data gradually
   - No "all or nothing" migration
   - Can rollback if issues

3. **Lower Upfront Cost**
   - $900-1,080 vs $1,200-1,440 (8 drives)
   - vs $3,200-3,600 (8x 20TB)
   - More budget-friendly

4. **Better Redundancy on New Pool**
   - RAID-Z2 = 2-drive failure protection
   - Much safer than RAID-Z1
   - Better for long-term storage

5. **Flexible Data Management**
   - Can use pools for different purposes
   - Old pool: Current/active media
   - New pool: Archive/long-term storage
   - Or migrate gradually

6. **No Migration Complexity**
   - No need to export/import pools
   - No need to copy all data at once
   - Can migrate at your own pace

7. **Immediate Capacity Increase**
   - +32 TB usable immediately
   - Total: 56 TB usable (vs current 24 TB)
   - 2.3x capacity increase

## Cons of Two-Pool Strategy

### ⚠️ Disadvantages

1. **Two Pools to Manage**
   - More complex than single pool
   - Need to track which data is where
   - Two mount points to manage

2. **No Room for Expansion**
   - Uses all 10 drive bays
   - Can't add more drives later
   - Would need to replace drives to expand

3. **Old Pool Still Has Issues**
   - Still using SMR BarraCuda drives
   - Still RAID-Z1 (single-drive protection)
   - Still at risk during rebuilds

4. **Data Split Across Pools**
   - Need to decide what goes where
   - Might need to reorganize later
   - Services need to know which pool to use

5. **Eventually Need to Consolidate**
   - Might want single pool eventually
   - Would require migration later
   - More work down the road

## Recommended Data Strategy

### Option 1: Gradual Migration (Recommended)

**Phase 1: Use New Pool for New Content**
- New media goes to new pool (`jenquist-cloud-new`)
- Old pool (`jenquist-cloud`) keeps existing content
- Services can access both pools

**Phase 2: Migrate Old Content Gradually**
- Move content from old pool to new pool over time
- Use rsync to copy data
- Verify as you go
- No rush - can take weeks/months

**Phase 3: Eventually Consolidate (Optional)**
- Once old pool is mostly empty
- Can destroy old pool
- Or keep as backup/archive

### Option 2: Split by Purpose

**Old Pool (`jenquist-cloud`):**
- Active/current media
- Frequently accessed content
- Temporary storage

**New Pool (`jenquist-cloud-new`):**
- Archive/long-term storage
- Less frequently accessed
- Backup destination

### Option 3: Use New Pool as Primary

**New Pool (`jenquist-cloud-new`):**
- Primary media storage
- All new content
- Better redundancy

**Old Pool (`jenquist-cloud`):**
- Backup/archive
- Keep as-is
- Eventually phase out

## Service Configuration

### Jellyfin Configuration

You can configure Jellyfin to use both pools:

```yaml
# docker-compose.yml
volumes:
  - type: bind
    source: /jenquist-cloud/archive
    target: /media/old
  - type: bind
    source: /jenquist-cloud-new/archive
    target: /media/new
```

Or use a single mount point with symlinks:

```bash
# Create unified mount point
sudo mkdir -p /media/archive
sudo ln -s /jenquist-cloud/archive /media/archive/old
sudo ln -s /jenquist-cloud-new/archive /media/archive/new
```

## Setup Process

### Step 1: Install 6 New Drives

```bash
# Power down server
sudo shutdown -h now

# Install 6 new 8TB IronWolf drives
# (Use remaining 6 bays)

# Power on server
```

### Step 2: Identify New Drives

```bash
# List all drives
sudo lsblk

# Identify new drives (should be 6 new devices)
# Likely: sde, sdf, sdg, sdh, sdi, sdj
# Verify they're the new drives
for disk in sde sdf sdg sdh sdi sdj; do
  echo "=== /dev/$disk ==="
  sudo smartctl -i /dev/$disk | grep -E "Model|Capacity|Serial"
done
```

### Step 3: Create New RAID-Z2 Pool

```bash
# Create new pool with 6 drives
sudo zpool create jenquist-cloud-new raidz2 /dev/sde /dev/sdf /dev/sdg /dev/sdh /dev/sdi /dev/sdj

# Verify pool created
sudo zpool status jenquist-cloud-new

# Check capacity
sudo zpool list jenquist-cloud-new
```

### Step 4: Create Filesystem

```bash
# Create archive filesystem
sudo zfs create jenquist-cloud-new/archive

# Set compression
sudo zfs set compression=lz4 jenquist-cloud-new/archive

# Set mount point
sudo zfs set mountpoint=/jenquist-cloud-new jenquist-cloud-new/archive

# Verify
sudo zfs list jenquist-cloud-new
mount | grep jenquist-cloud-new
```

### Step 5: Configure Encryption (if using)

```bash
# If you want encryption on new pool
sudo zfs create -o encryption=aes-256-gcm -o keyformat=passphrase jenquist-cloud-new/archive-encrypted

# Or use keyfile (same as old pool if you want)
sudo zfs create -o encryption=aes-256-gcm -o keylocation=file:///path/to/keyfile jenquist-cloud-new/archive-encrypted
```

### Step 6: Update Services

```bash
# Update Jellyfin or other services to use new pool
# Or configure to use both pools

# Test services
cd ~/server/apps/jellyfin
docker compose up -d
docker compose logs --tail 50
```

## Migration Strategy (Optional)

### Gradual Migration Script

```bash
#!/bin/bash
# migrate-to-new-pool.sh

OLD_POOL="/jenquist-cloud/archive"
NEW_POOL="/jenquist-cloud-new/archive"

# Migrate specific directory
SOURCE_DIR="$1"
DEST_DIR="$2"

if [ -z "$SOURCE_DIR" ] || [ -z "$DEST_DIR" ]; then
  echo "Usage: $0 <source_dir> <dest_dir>"
  echo "Example: $0 /jenquist-cloud/archive/movies /jenquist-cloud-new/archive/movies"
  exit 1
fi

# Copy with progress
sudo rsync -avh --progress "$SOURCE_DIR/" "$DEST_DIR/"

# Verify
echo "Verifying..."
find "$SOURCE_DIR" -type f | wc -l
find "$DEST_DIR" -type f | wc -l

echo "Migration complete. Verify data, then you can remove old directory."
```

### Usage

```bash
# Migrate movies
bash migrate-to-new-pool.sh /jenquist-cloud/archive/movies /jenquist-cloud-new/archive/movies

# Verify, then remove old
# sudo rm -rf /jenquist-cloud/archive/movies
```

## Comparison: Two Pools vs Single Pool Migration

| Factor | Two Pools | Single Pool Migration |
|--------|-----------|----------------------|
| **Downtime** | Zero | 12-24 hours |
| **Risk** | Low | Medium-High |
| **Cost** | $900-1,080 | $1,200-1,440 |
| **Complexity** | Low | High |
| **Capacity** | 56 TB usable | 48 TB usable |
| **Redundancy** | Mixed (Z1 + Z2) | Z2 only |
| **Flexibility** | High | Low |
| **Management** | Two pools | Single pool |

## Long-Term Considerations

### Option A: Keep Both Pools
- **Pros**: More capacity, flexibility
- **Cons**: More complex, old pool still risky

### Option B: Eventually Migrate Everything
- **Pros**: Single pool, better redundancy
- **Cons**: Need to migrate eventually, old pool wasted

### Option C: Replace Old Pool Drives
- **Pros**: Better redundancy on both pools
- **Cons**: More expensive, more work

## My Recommendation

**This two-pool strategy is EXCELLENT!** Here's why:

1. **Low Risk**: Old pool stays intact
2. **Low Cost**: $900-1,080 vs $1,200-1,440
3. **Zero Downtime**: No service interruption
4. **Immediate Capacity**: +32 TB usable right away
5. **Better Redundancy**: New pool has RAID-Z2
6. **Flexible**: Can migrate gradually or keep both

**Recommended Approach:**
1. **Create new 6-drive RAID-Z2 pool**
2. **Use new pool for all new content**
3. **Gradually migrate old content** (no rush)
4. **Eventually phase out old pool** (when convenient)
5. **Or keep both** if you need the capacity

## Setup Checklist

- [ ] Purchase 6x 8TB IronWolf drives
- [ ] Power down server
- [ ] Install 6 new drives in remaining bays
- [ ] Power on server
- [ ] Identify new drive devices
- [ ] Create new RAID-Z2 pool
- [ ] Create filesystem and set mount point
- [ ] Configure encryption (if using)
- [ ] Update service configurations
- [ ] Test services with new pool
- [ ] Start using new pool for new content
- [ ] Plan gradual migration strategy (optional)

## Cost Summary

**Total Investment:**
- 6x 8TB IronWolf: $900-1,080
- **Total Usable Capacity**: 56 TB (24 + 32)
- **Cost per TB**: ~$16-20/TB (excellent value!)

**This is actually the BEST value option!**

## Bottom Line

**This two-pool strategy is smart because:**
- ✅ Lower cost than 8 drives
- ✅ Zero downtime
- ✅ Lower risk
- ✅ Immediate capacity increase
- ✅ Better redundancy on new pool
- ✅ Flexible migration options

**Go with 6x 8TB drives and create a new RAID-Z2 pool!**

