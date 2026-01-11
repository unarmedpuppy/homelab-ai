# Memory Usage Reference

Quick reference for understanding and troubleshooting memory usage on the home server.

## Current Baseline (Jan 2026)

| Metric    | Value        |
|-----------|--------------|
| Total RAM | 62.7 GiB     |
| Used      | 59 GiB (94%) |
| Free      | 1.7 GiB      |
| Available | 3.6 GiB      |
| Swap      | None         |

**Key insight**: 94% "used" is normal and expected due to ZFS ARC caching.

## Memory Breakdown

| Category              | Size     | % of Total |
|-----------------------|----------|------------|
| ZFS ARC Cache         | 25.1 GiB | 40%        |
| Application Processes | ~17 GiB  | 27%        |
| Shared Memory         | 8.1 GiB  | 13%        |
| Kernel Slab           | 4.0 GiB  | 6%         |
| Page Cache/Buffers    | ~1.6 GiB | 3%         |
| Other/Overhead        | ~7 GiB   | 11%        |

## ZFS ARC Cache

The ARC (Adaptive Replacement Cache) is ZFS's read cache that uses available RAM.

| Metric              | Value                       |
|---------------------|-----------------------------|
| Current ARC Size    | 25.1 GiB (40% of total RAM) |
| Max Limit (c_max)   | 31.4 GiB                    |
| Min Limit (c_min)   | 1.96 GiB                    |
| zfs_arc_max setting | 0 (unlimited/default)       |

**Important**: ARC memory is **reclaimable** - it automatically shrinks when applications need more RAM. High ARC usage is not a problem; it improves read performance for the ZFS pool.

### Check ARC Status

```bash
# Current ARC size and stats
cat /proc/spl/kstat/zfs/arcstats | grep -E "^(size|c_max|c_min)"

# Human-readable
arc_summary
```

### Limit ARC Size (if needed)

```bash
# Temporary (until reboot)
echo 16106127360 > /sys/module/zfs/parameters/zfs_arc_max  # 15 GiB

# Permanent - add to /etc/modprobe.d/zfs.conf
options zfs zfs_arc_max=16106127360
```

## Top Memory Consumers

| Process                    | RSS     | % RAM |
|----------------------------|---------|-------|
| vLLM (Qwen2.5-7B AI model) | 8.2 GiB | 13.0% |
| 7 Days to Die Server       | 2.0 GiB | 3.1%  |
| Valheim Server             | 1.3 GiB | 2.0%  |
| InfluxDB                   | 1.1 GiB | 1.8%  |
| rclone sync                | 0.6 GiB | 0.9%  |
| NZBHydra2                  | 0.6 GiB | 0.9%  |
| Open WebUI                 | 0.5 GiB | 0.8%  |
| Xvfb (virtual display)     | 0.5 GiB | 0.8%  |
| IB Gateway (Java)          | 0.5 GiB | 0.7%  |
| MySQL (x2 instances)       | 0.7 GiB | 1.0%  |

### Check Process Memory

```bash
# Top memory consumers
ps aux --sort=-%mem | head -20

# Docker container memory
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}"

# Detailed memory breakdown
smem -t -k -c "pid user command swap uss pss rss"
```

## Kernel Memory

| Type                  | Value   |
|-----------------------|---------|
| Slab (total)          | 4.0 GiB |
| Slab (reclaimable)    | 1.5 GiB |
| Slab (unreclaimable)  | 2.5 GiB |
| Shared Memory (Shmem) | 8.1 GiB |

### Check Kernel Memory

```bash
# Slab usage
cat /proc/meminfo | grep -E "Slab|SReclaimable|SUnreclaim"

# Top slab consumers
slabtop -o | head -20

# Shared memory
cat /proc/meminfo | grep Shmem
```

## Quick Diagnostics

```bash
# Overall memory status
free -h

# What's using memory?
cat /proc/meminfo

# Memory pressure indicators
cat /proc/pressure/memory

# OOM killer history
dmesg | grep -i "out of memory"
journalctl -k | grep -i oom
```

## Understanding "Available" vs "Free"

- **Free**: Completely unused RAM (typically low on Linux - this is normal)
- **Available**: Memory that can be reclaimed for applications (includes reclaimable caches)

Linux aggressively caches to improve performance. Low "free" memory with adequate "available" memory is healthy.

## When to Be Concerned

1. **Available < 1 GiB** - Applications may start getting OOM killed
2. **OOM kills in logs** - Check `dmesg | grep -i oom`
3. **Swap thrashing** - If swap is configured and heavily used
4. **Memory pressure** - Check `/proc/pressure/memory` for stall percentages

## Reducing Memory Usage

### Quick Wins
```bash
# Drop caches (temporary relief)
sync; echo 3 > /proc/sys/vm/drop_caches

# Limit ZFS ARC
echo $((16*1024*1024*1024)) > /sys/module/zfs/parameters/zfs_arc_max

# Stop game servers when not in use
docker stop 7daystodie valheim
```

### Long-term Options
1. Add swap (safety net for memory pressure)
2. Limit ARC permanently via `/etc/modprobe.d/zfs.conf`
3. Stop or migrate heavy services (vLLM, game servers)
4. Add more RAM

## Notes

- No swap is configured - consider adding for OOM protection
- vLLM is the largest single application consumer at 8.2 GiB
- ZFS pool is DEGRADED (separate issue from memory - see drive health docs)
