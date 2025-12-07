# ZFS Drive Recommendations for Media Storage

## Current Setup Analysis

**Current Drives:**
- 4x Seagate BarraCuda 8TB (ST8000DMZ04/004)
- 5400 RPM, 256 MB Cache
- **⚠️ CRITICAL**: These are likely **SMR (Shingled Magnetic Recording)** drives

**Current Configuration:**
- ZFS RAID-Z1 (4 drives)
- Use case: Plex media storage (2-3 concurrent users)
- Available bays: 6 open slots

## Critical Issue: SMR vs CMR

**Your current BarraCuda drives are likely SMR**, which causes problems with ZFS:
- **Poor write performance** during rebuilds
- **Extended rebuild times** (days/weeks)
- **Higher failure risk** during rebuilds
- **Incompatible with ZFS** best practices

**Solution**: Replace with **CMR (Conventional Magnetic Recording)** drives designed for NAS/RAID use.

## Drive Requirements for Your Use Case

### Performance Needs
- **Media streaming**: Sequential reads (not random I/O)
- **2-3 concurrent users**: Low I/O load
- **5400 RPM is sufficient** for media streaming
- **7200 RPM optional** for better performance, but not required

### ZFS Requirements
- **MUST be CMR** (not SMR)
- **Same or larger capacity** when replacing (8TB+)
- **NAS-optimized** drives preferred (vibration resistance, TLER)
- **Reliable** with good MTBF ratings

### Capacity Planning
- Current: 4x 8TB = ~24TB usable (RAID-Z1)
- With 6 open bays: Can expand to 10 drives total
- Options:
  - Stay at 4 drives (RAID-Z1)
  - Expand to 5-6 drives (RAID-Z1 or RAID-Z2)
  - Expand to 8-10 drives (RAID-Z2 recommended)

## Recommended Drive Options

### Option 1: Budget-Friendly NAS Drives (Recommended for Your Use Case)

#### **Seagate IronWolf 8TB (ST8000VN004)**
- **Price**: ~$150-180
- **RPM**: 7200
- **Cache**: 256 MB
- **Technology**: CMR
- **Workload**: 180 TB/year
- **Warranty**: 3 years
- **MTBF**: 1M hours
- **Best for**: Direct replacement, same capacity
- **Pros**: Good balance of cost/performance, NAS-optimized
- **Cons**: Slightly louder than 5400 RPM drives

#### **Western Digital Red Plus 8TB (WD80EFBX)**
- **Price**: ~$160-190
- **RPM**: 5640 (variable)
- **Cache**: 256 MB
- **Technology**: CMR
- **Workload**: 180 TB/year
- **Warranty**: 3 years
- **MTBF**: 1M hours
- **Best for**: Quieter operation, lower power
- **Pros**: Lower power consumption, quieter
- **Cons**: Slightly slower than 7200 RPM

### Option 2: Higher Capacity (Future-Proof)

#### **Seagate IronWolf 12TB (ST12000VN0008)**
- **Price**: ~$220-250
- **RPM**: 7200
- **Cache**: 256 MB
- **Technology**: CMR
- **Workload**: 180 TB/year
- **Warranty**: 3 years
- **Best for**: Expanding capacity while replacing
- **Pros**: More capacity, same price per TB
- **Cons**: Requires all drives to be same size for optimal ZFS

#### **Western Digital Red Plus 12TB (WD120EFBX)**
- **Price**: ~$230-260
- **RPM**: 5640 (variable)
- **Cache**: 256 MB
- **Technology**: CMR
- **Best for**: Capacity expansion with lower power
- **Pros**: Good capacity, efficient
- **Cons**: Slower than 7200 RPM

### Option 3: Enterprise-Grade (Maximum Reliability)

#### **Seagate Exos 7E8 8TB (ST8000NM000A)**
- **Price**: ~$180-220
- **RPM**: 7200
- **Cache**: 256 MB
- **Technology**: CMR
- **Workload**: 550 TB/year
- **Warranty**: 5 years
- **MTBF**: 2.5M hours
- **Best for**: Maximum reliability, longer warranty
- **Pros**: Enterprise-grade, 5-year warranty, higher workload rating
- **Cons**: More expensive, louder

#### **Toshiba MG Series 8TB**
- **Price**: ~$170-200
- **RPM**: 7200
- **Cache**: 256 MB
- **Technology**: CMR
- **Workload**: 550 TB/year
- **Warranty**: 5 years
- **Best for**: Enterprise reliability at better price
- **Pros**: Good value for enterprise features
- **Cons**: Less common, may be harder to find

## Recommendation Matrix

| Priority | Drive | Capacity | Price | RPM | Best For |
|----------|-------|----------|-------|-----|----------|
| **#1** | Seagate IronWolf 8TB | 8TB | $150-180 | 7200 | Direct replacement, best value |
| **#2** | WD Red Plus 8TB | 8TB | $160-190 | 5640 | Quieter, lower power |
| **#3** | Seagate IronWolf 12TB | 12TB | $220-250 | 7200 | Capacity expansion |
| **#4** | Seagate Exos 7E8 8TB | 8TB | $180-220 | 7200 | Maximum reliability |

## Replacement Strategy

### Phase 1: Replace Current Drives (One at a Time)

**Recommended Approach:**
1. **Buy 2-4 replacement drives** (same model for consistency)
2. **Replace one drive at a time**:
   ```bash
   # 1. Offline the failing/old drive
   sudo zpool offline jenquist-cloud /dev/sda
   
   # 2. Physically replace the drive
   # 3. Replace in pool
   sudo zpool replace jenquist-cloud /dev/sda /dev/sdX
   
   # 4. Monitor rebuild
   sudo zpool status jenquist-cloud
   ```
3. **Wait for rebuild to complete** before replacing next drive
4. **Keep old drives as spares** (if still functional)

### Phase 2: Expand Pool (Optional)

**If you want more capacity/redundancy:**

**Option A: Expand to 5-6 drives (RAID-Z1)**
- Add 1-2 more drives
- More capacity, still single-drive failure protection
- **Risk**: Rebuild time increases with more drives

**Option B: Expand to 6-8 drives (RAID-Z2) - RECOMMENDED**
- Add 2-4 more drives
- **Two-drive failure protection** (much safer)
- Better for larger pools
- **Requires recreating pool** (backup first!)

```bash
# This requires recreating the pool - BACKUP FIRST!
# 1. Backup all data
# 2. Destroy old pool
# 3. Create new RAID-Z2 pool with all drives
sudo zpool create jenquist-cloud raidz2 /dev/sda /dev/sdb /dev/sdc /dev/sdd /dev/sde /dev/sdf
# 4. Restore data
```

## Capacity Planning

### Current Setup (4x 8TB RAID-Z1)
- **Raw**: 32 TB
- **Usable**: ~24 TB (75% efficiency)
- **Protection**: 1 drive failure

### Expanded to 6x 8TB RAID-Z1
- **Raw**: 48 TB
- **Usable**: ~40 TB (83% efficiency)
- **Protection**: 1 drive failure
- **Rebuild time**: Longer (more risky)

### Expanded to 6x 8TB RAID-Z2 (RECOMMENDED)
- **Raw**: 48 TB
- **Usable**: ~32 TB (67% efficiency)
- **Protection**: 2 drive failures
- **Rebuild time**: Safer (can lose 2 drives)

### Expanded to 8x 8TB RAID-Z2
- **Raw**: 64 TB
- **Usable**: ~48 TB (75% efficiency)
- **Protection**: 2 drive failures
- **Best for**: Large capacity needs

## Cost Analysis

### Replacement Only (4 drives)
- **IronWolf 8TB**: $600-720 (4 drives)
- **WD Red Plus 8TB**: $640-760 (4 drives)
- **Exos 8TB**: $720-880 (4 drives)

### Expansion to 6 drives (RAID-Z2)
- **IronWolf 8TB**: $900-1080 (6 drives)
- **WD Red Plus 8TB**: $960-1140 (6 drives)
- **Exos 8TB**: $1080-1320 (6 drives)

### Expansion to 8 drives (RAID-Z2)
- **IronWolf 8TB**: $1200-1440 (8 drives)
- **WD Red Plus 8TB**: $1280-1520 (8 drives)
- **Exos 8TB**: $1440-1760 (8 drives)

## My Specific Recommendation

**For your use case (Plex, 2-3 users, gradual replacement):**

1. **Start with**: **Seagate IronWolf 8TB (ST8000VN004)**
   - Best balance of cost, performance, reliability
   - NAS-optimized (vibration resistance)
   - CMR technology (ZFS compatible)
   - 3-year warranty
   - 7200 RPM (good performance, not overkill)

2. **Buy 2-4 drives initially** to have spares ready

3. **Replace one at a time** as current drives show signs of failure

4. **Consider expanding to RAID-Z2** when you have 6 drives:
   - Much safer (2-drive failure protection)
   - Better for long-term reliability
   - Worth the capacity trade-off

5. **Keep old BarraCuda drives as cold spares** (if still functional) - but don't use them in the pool

## Drive Verification Before Purchase

**Always verify CMR before buying:**

1. Check manufacturer specs (should say "CMR" or "Conventional")
2. Avoid drives that say "SMR" or "Shingled"
3. Check ZFS compatibility lists online
4. Common SMR drives to avoid:
   - Seagate BarraCuda (most models)
   - WD Blue (some models)
   - Some Toshiba desktop drives

## Installation Notes

1. **Mix drives carefully**: ZFS works best with identical drives, but can mix sizes (uses smallest)
2. **Hot-swap**: Your chassis supports hot-swap, but safer to power down for first replacement
3. **SMART monitoring**: Use the `check-drive-health.sh` script regularly
4. **Backup before expansion**: Always backup before changing pool configuration

## Next Steps

1. **Verify current drives are SMR**: Check SMART data or manufacturer specs
2. **Purchase 2-4 replacement drives** (IronWolf 8TB recommended)
3. **Set up SMART monitoring** (Task T18-T21)
4. **Replace drives gradually** as they show issues
5. **Consider RAID-Z2 expansion** when you have 6+ drives

