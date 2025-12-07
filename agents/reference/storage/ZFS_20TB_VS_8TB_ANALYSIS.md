# ZFS Drive Analysis: 20TB IronWolf Pro vs 8TB Options

## Drive Comparison

### Seagate IronWolf Pro 20TB (ST20000NT001)
- **Capacity**: 20TB
- **RPM**: 7200
- **Cache**: 256 MB
- **Technology**: CMR ✅
- **Workload**: 300 TB/year
- **Warranty**: 5 years
- **Price**: ~$400-450 per drive
- **Price per TB**: ~$20-22.50/TB

### Seagate IronWolf 8TB (ST8000VN004)
- **Capacity**: 8TB
- **RPM**: 7200
- **Cache**: 256 MB
- **Technology**: CMR ✅
- **Workload**: 180 TB/year
- **Warranty**: 3 years
- **Price**: ~$150-180 per drive
- **Price per TB**: ~$18.75-22.50/TB

## Capacity Analysis

### With 8x 20TB Drives (RAID-Z2)
- **Raw Capacity**: 160 TB
- **Usable Capacity**: ~120 TB (75% efficiency with RAID-Z2)
- **Protection**: 2-drive failure tolerance

### With 8x 8TB Drives (RAID-Z2)
- **Raw Capacity**: 64 TB
- **Usable Capacity**: ~48 TB (75% efficiency with RAID-Z2)
- **Protection**: 2-drive failure tolerance

## Cost Analysis

### 8x 20TB IronWolf Pro
- **Total Cost**: ~$3,200-3,600
- **Usable Capacity**: ~120 TB
- **Cost per Usable TB**: ~$26.67-30/TB

### 8x 8TB IronWolf
- **Total Cost**: ~$1,200-1,440
- **Usable Capacity**: ~48 TB
- **Cost per Usable TB**: ~$25-30/TB

**Cost per TB is similar**, but 20TB gives you 2.5x more capacity for 2.5x the cost.

## Pros of 20TB Drives

### ✅ Advantages

1. **Massive Capacity**
   - 120 TB usable vs 48 TB
   - Room for years of growth
   - Less frequent upgrades needed

2. **Enterprise-Grade Reliability**
   - 5-year warranty (vs 3-year)
   - 300 TB/year workload (vs 180 TB/year)
   - Better for 24/7 operation
   - IronWolf Pro = higher quality than regular IronWolf

3. **Fewer Drives Needed**
   - 8 drives vs potentially needing more later
   - Less power consumption (fewer drives)
   - Less heat generation
   - Simpler management

4. **Future-Proofing**
   - Won't need to expand for a long time
   - 4K/8K media files are getting larger
   - Room for growth

5. **Better Cost Efficiency Long-Term**
   - If you'd eventually need 10-12x 8TB drives, 8x 20TB is cheaper
   - Less frequent upgrades = less downtime

## Cons of 20TB Drives

### ⚠️ Disadvantages

1. **Higher Upfront Cost**
   - $3,200-3,600 vs $1,200-1,440
   - 2.5x more expensive upfront
   - Significant budget impact

2. **Longer Rebuild Times**
   - 20TB drives take **much longer** to rebuild
   - Estimated rebuild time: **2-4 days** (vs 1-2 days for 8TB)
   - Higher risk during rebuild (more time = more chance of second failure)
   - RAID-Z2 helps, but still a concern

3. **Overkill for Current Needs**
   - Current usage: ~24 TB (4x 8TB RAID-Z1)
   - 120 TB usable = 5x current capacity
   - You'd be using ~20% of capacity initially
   - Might be more than you need for years

4. **Higher Risk Per Drive**
   - If a 20TB drive fails, you lose more capacity
   - More data at risk per drive
   - Rebuild stress affects larger drives more

5. **Less Flexibility**
   - Harder to add drives incrementally
   - If you need more capacity later, you'd need to add 20TB drives
   - Can't mix sizes efficiently in ZFS (uses smallest drive)

## Rebuild Time Comparison

### 8TB Drive Rebuild (RAID-Z2)
- **Time**: ~12-24 hours
- **Risk**: Moderate (shorter window)
- **Stress**: Lower (less data to rebuild)

### 20TB Drive Rebuild (RAID-Z2)
- **Time**: ~48-96 hours (2-4 days)
- **Risk**: Higher (longer window = more time for second failure)
- **Stress**: Higher (more data to rebuild)

**With RAID-Z2, you can lose 2 drives, but rebuild time is still a concern.**

## Use Case Analysis

### Your Current Situation
- **Current capacity**: ~24 TB usable
- **Usage**: Media storage for 2-3 Plex users
- **Growth rate**: Unknown, but media files are getting larger
- **Budget**: Need to consider

### Capacity Projections

**Conservative Estimate** (assuming 1 TB/month growth):
- Year 1: 24 TB → 36 TB
- Year 2: 36 TB → 48 TB
- Year 3: 48 TB → 60 TB
- Year 4: 60 TB → 72 TB
- Year 5: 72 TB → 84 TB

**8x 8TB (48 TB usable)**: Would need expansion in ~2-3 years
**8x 20TB (120 TB usable)**: Would last 5+ years easily

**Aggressive Estimate** (assuming 2 TB/month growth):
- Year 1: 24 TB → 48 TB
- Year 2: 48 TB → 72 TB
- Year 3: 72 TB → 96 TB
- Year 4: 96 TB → 120 TB

**8x 8TB (48 TB usable)**: Would need expansion in ~1 year
**8x 20TB (120 TB usable)**: Would last ~4 years

## Recommendation Matrix

### Choose 20TB If:
- ✅ **Budget allows** ($3,200-3,600)
- ✅ **You want to future-proof** (5+ years)
- ✅ **You're adding lots of 4K/8K content**
- ✅ **You want enterprise-grade reliability** (5-year warranty)
- ✅ **You prefer fewer drives** (less power, heat, complexity)
- ✅ **You don't want to expand again soon**

### Choose 8TB If:
- ✅ **Budget is a concern** ($1,200-1,440)
- ✅ **48 TB is enough for 2-3 years**
- ✅ **You want faster rebuild times** (12-24 hours vs 2-4 days)
- ✅ **You prefer lower risk per drive**
- ✅ **You might want to expand incrementally**
- ✅ **You're okay with 3-year warranty**

## Hybrid Approach (Alternative)

### Option: Mix of Both
- **Start with 6x 8TB** (~36 TB usable, RAID-Z2)
- **Add 2x 20TB later** when needed
- **Problem**: ZFS uses smallest drive size, so 20TB drives would only use 8TB
- **Not recommended** - ZFS works best with identical drives

## My Specific Recommendation

### For Your Use Case (Plex, 2-3 users, gradual growth):

**I recommend 8TB drives** for these reasons:

1. **Cost Efficiency**
   - $1,200-1,440 vs $3,200-3,600
   - You can buy 2.5x more 8TB drives for same price
   - Better value for current needs

2. **Rebuild Time**
   - 12-24 hours vs 2-4 days
   - Much lower risk during rebuilds
   - Less stress on remaining drives

3. **Current Needs**
   - 48 TB usable is likely enough for 2-3 years
   - You're currently using ~24 TB
   - 48 TB = 2x current capacity

4. **Flexibility**
   - Can expand later if needed
   - Can add more 8TB drives (up to 10 total in your chassis)
   - Or upgrade to larger drives later if needed

5. **Risk Management**
   - Lower risk per drive (less data lost if failure)
   - Faster recovery times
   - Less catastrophic if issues occur

### When 20TB Makes Sense

**Choose 20TB if:**
- You have the budget ($3,200-3,600)
- You're adding lots of 4K/8K content rapidly
- You want to "set it and forget it" for 5+ years
- You value enterprise-grade reliability (5-year warranty)
- You prefer fewer drives (power/heat management)

## Cost-Benefit Summary

| Factor | 8TB IronWolf | 20TB IronWolf Pro |
|--------|--------------|-------------------|
| **Upfront Cost** | $1,200-1,440 | $3,200-3,600 |
| **Usable Capacity** | 48 TB | 120 TB |
| **Cost per TB** | ~$25-30 | ~$27-30 |
| **Rebuild Time** | 12-24 hours | 48-96 hours |
| **Warranty** | 3 years | 5 years |
| **Workload Rating** | 180 TB/year | 300 TB/year |
| **Time to Fill** | 2-3 years | 5+ years |
| **Risk Level** | Lower | Higher (rebuild time) |

## Final Verdict

**For most home media servers with 2-3 users: 8TB drives are the better choice.**

**Reasons:**
1. Better value for current needs
2. Faster rebuild times = lower risk
3. 48 TB is likely enough for 2-3 years
4. Can expand later if needed
5. Lower upfront investment

**20TB makes sense if:**
- Budget is not a concern
- You want maximum future-proofing
- You're rapidly adding large 4K/8K content
- You value enterprise-grade reliability

## Alternative: Start with 6x 8TB, Expand Later

**Consider starting with 6x 8TB drives:**
- **Cost**: ~$900-1,080
- **Usable**: ~32 TB (RAID-Z2)
- **Protection**: 2-drive failure
- **Expand later**: Add 2 more 8TB drives when needed
- **Total capacity**: 48 TB usable when fully expanded

This gives you:
- Lower initial investment
- Room to grow
- Can add drives incrementally
- Still get RAID-Z2 protection

## Bottom Line

**8TB drives are the better choice** for your use case unless:
- Budget is not a concern AND
- You want maximum future-proofing AND
- You're okay with longer rebuild times

The 20TB drives are excellent quality, but the extra capacity and cost may not be justified for a 2-3 user Plex server unless you're rapidly growing your media library.

