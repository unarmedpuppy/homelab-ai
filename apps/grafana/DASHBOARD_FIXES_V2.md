# Dashboard Fixes - Version 2

## Issues Fixed

### 1. ✅ Container Memory Query
- **Problem**: Query was filtering by `host =~ /^$server$/` which didn't match (host is "telegraf", server variable might be different)
- **Fix**: Removed the host filter from the container memory query
- **Result**: Now shows actual memory usage per container (e.g., 0.013 GB for adguard, 0.038 GB for agent-monitoring-backend)

### 2. ✅ Disk Usage Panels
- **Status**: Queries are correct - they use `$mountpoint` variable
- **Note**: Make sure the "Mountpoint" variable is set in Grafana (should auto-populate from disk.path tags)
- **Queries**: 
  - `SELECT mean("used_percent") FROM "disk" WHERE ("path" =~ /$mountpoint/)`
  - `SELECT mean("used") / 1024 / 1024 / 1024, mean("free") / 1024 / 1024 / 1024 FROM "disk" WHERE ("path" =~ /$mountpoint/)`

### 3. ✅ Dynamic Container Panels
- **Added**: Container variable (`$container`) - allows filtering containers
- **Added**: Container Metrics Table panel - shows all containers dynamically with:
  - Memory Usage (GB)
  - Memory Usage (%)
  - CPU Usage (%)
- **Location**: New section "Container Metrics Table" at the bottom of dashboard
- **Features**:
  - Sorted by memory usage (highest first)
  - Color-coded thresholds (yellow at 80%, red at 90% for memory)
  - Filterable by container name using `$container` variable
  - Shows only running containers

## How to Use

### Container Variable
1. At the top of the dashboard, you'll see a "Container" dropdown
2. Select one or more containers to filter
3. Or select "All" to see all containers

### Container Metrics Table
- Shows real-time metrics for all running containers
- Automatically updates as containers start/stop
- Click on a container name to filter other panels (if linked)
- Sort by any column by clicking the header

## Verification

After importing:
1. **Container Memory Graph**: Should show different values per container (not 62GB for all)
2. **Disk Usage Panels**: Should show data if mountpoint variable is set correctly
3. **Container Metrics Table**: Should appear at bottom with all running containers listed

## Notes

- The 62GB you saw was likely the memory `limit` field, which is the same for all containers (system default)
- The `usage` field shows actual memory consumption, which varies per container
- The table panel uses `last()` function to show current values, not averages over time
- Container variable refreshes automatically to pick up new containers

