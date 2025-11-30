# Dashboard Fixes Applied

## Issues Fixed

### 1. ✅ Dashboard Title
- **Changed**: "My Grafana Dashboard" → "Home Server AI"
- **Location**: Dashboard metadata

### 2. ✅ Docker Container Memory Panel
- **Issue**: Panel was using `limit` field which shows memory limit, not actual usage
- **Fixed**: Changed to use `usage` field for actual memory consumption
- **Panel**: "Per-Container Memory Usage (GB)"
- **Query**: Changed from `mean("limit")` to `mean("usage")`

### 3. ✅ ZFS L2 Cache I/O Panels
- **Issue**: L2 cache fields (`arcstats_l2_read_bytes`, `arcstats_l2_write_bytes`) were all 0 because L2 cache is not configured
- **Fixed**: Changed to use available metrics:
  - **Panel 1**: Changed from `arcstats_l2_read_bytes` to `zfetchstats_io_issued` (ZFS prefetch I/O operations)
  - **Panel 2**: Changed from `arcstats_l2_write_bytes` to `zil_commit_count` (ZFS Intent Log commits)
- **Panel Title**: "ZFS L2 Cache I/O (MB/s)" → "ZFS I/O Activity"
- **Y-Axis**: Changed from "MB/s" to "Count" format
- **Aliases**: Updated to reflect new metrics

## Panels That Should Now Have Data

1. ✅ **Per-Container Memory Usage** - Now shows actual memory usage instead of limits
2. ✅ **ZFS I/O Activity** - Now shows ZFS prefetch I/O and ZIL commits (active metrics)

## Notes

- ZFS L2 cache metrics are not available because L2 cache is not configured on this system
- The new ZFS metrics (`zfetchstats_io_issued` and `zil_commit_count`) are active and will show data
- All other panels should continue to work as before

## Verification

After importing the updated dashboard:
1. Check "Per-Container Memory Usage" panel - should show memory usage per container
2. Check "ZFS I/O Activity" panel - should show ZFS I/O operations and ZIL commits
3. Verify dashboard title shows "Home Server AI"

