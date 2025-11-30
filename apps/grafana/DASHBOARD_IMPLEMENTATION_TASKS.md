# Grafana Dashboard Enhancement - Implementation Tasks

## Task List (Prioritized)

### ✅ Task 1: Temperature Monitoring (HIGH PRIORITY)
**Status**: In Progress
**Implementation Details**:
- Add row section: "Temperature & Health"
- Panel 1: CPU Temperature Gauge
  - Query: `SELECT mean("temp_input") FROM "sensors" WHERE ("chip" = 'k10temp-pci-00c3') AND $timeFilter GROUP BY time($interval) fill(null)`
  - Type: Gauge
  - Thresholds: Green < 60°C, Yellow 60-70°C, Orange 70-80°C, Red > 80°C
  - Position: y: 70, x: 0, w: 4, h: 6
- Panel 2: Temperature Trend Graph
  - Query: `SELECT mean("temp_input") FROM "sensors" WHERE $timeFilter GROUP BY time($interval), "chip" fill(null)`
  - Type: Time series graph
  - Multiple series for each chip (CPU, NVMe, etc.)
  - Position: y: 70, x: 4, w: 20, h: 6

**Metrics Used**: `sensors.temp_input`, `sensors.temp_crit`, `sensors.temp_max`
**Panel IDs**: 70001-70002

---

### 📋 Task 2: ZFS Pool Health & Performance (HIGH PRIORITY)
**Status**: Pending
**Implementation Details**:
- Add row section: "ZFS Storage"
- Panel 1: ZFS Pool Space Usage
  - Query: `SELECT mean("pool_allocated") / mean("pool_size") * 100 FROM "zfs" WHERE $timeFilter GROUP BY time($interval), "pool" fill(null)`
  - Type: Gauge or Stat
  - Position: y: 76, x: 0, w: 6, h: 4
- Panel 2: ZFS Read/Write Operations
  - Query: `SELECT mean("read_ops") AS "Read Ops/s", mean("write_ops") AS "Write Ops/s" FROM "zfs" WHERE $timeFilter GROUP BY time($interval), "pool" fill(null)`
  - Type: Time series graph
  - Position: y: 76, x: 6, w: 9, h: 4
- Panel 3: ZFS I/O Statistics
  - Query: `SELECT mean("read_bytes") / 1024 / 1024 AS "Read MB/s", mean("write_bytes") / 1024 / 1024 AS "Write MB/s" FROM "zfs" WHERE $timeFilter GROUP BY time($interval), "pool" fill(null)`
  - Type: Time series graph
  - Position: y: 76, x: 15, w: 9, h: 4

**Metrics Used**: `zfs.pool_allocated`, `zfs.pool_size`, `zfs.read_ops`, `zfs.write_ops`, `zfs.read_bytes`, `zfs.write_bytes`
**Panel IDs**: 70003-70005
**Note**: Only add if ZFS metrics are available in InfluxDB

---

### 📋 Task 3: Detailed Disk I/O Performance (HIGH PRIORITY)
**Status**: Pending
**Implementation Details**:
- Add row section: "Storage I/O"
- Panel 1: Disk I/O Read/Write Rates
  - Query: `SELECT mean("read_bytes") / 1024 / 1024 AS "Read MB/s", mean("write_bytes") / 1024 / 1024 AS "Write MB/s" FROM "diskio" WHERE ("name" =~ /$disk/) AND $timeFilter GROUP BY time($interval), "name" fill(null)`
  - Type: Time series graph
  - Position: y: 80, x: 0, w: 12, h: 6
- Panel 2: Disk IOPS
  - Query: `SELECT mean("reads") + mean("writes") AS "IOPS" FROM "diskio" WHERE ("name" =~ /$disk/) AND $timeFilter GROUP BY time($interval), "name" fill(null)`
  - Type: Time series graph
  - Position: y: 80, x: 12, w: 12, h: 6
- Panel 3: Disk I/O Wait Time
  - Query: `SELECT mean("io_time") FROM "diskio" WHERE ("name" =~ /$disk/) AND $timeFilter GROUP BY time($interval), "name" fill(null)`
  - Type: Time series graph
  - Position: y: 86, x: 0, w: 12, h: 6
- Panel 4: Top Disks by I/O Activity
  - Query: `SELECT top("read_bytes", 5) FROM "diskio" WHERE $timeFilter`
  - Type: Table or Bar gauge
  - Position: y: 86, x: 12, w: 12, h: 6

**Metrics Used**: `diskio.read_bytes`, `diskio.write_bytes`, `diskio.reads`, `diskio.writes`, `diskio.io_time`, `diskio.weighted_io_time`
**Panel IDs**: 70006-70009

---

### 📋 Task 4: Per-Interface Network Statistics (HIGH PRIORITY)
**Status**: Pending
**Implementation Details**:
- Add row section: "Network Interfaces"
- Panel 1: Network Traffic per Interface
  - Query: `SELECT mean("bytes_sent") * 8 / 1000000 AS "Upload Mbps", mean("bytes_recv") * 8 / 1000000 AS "Download Mbps" FROM "net" WHERE ("interface" =~ /$netif/ OR "interface" = 'docker0' OR "interface" = 'tun0') AND $timeFilter GROUP BY time($interval), "interface" fill(null)`
  - Type: Time series graph
  - Position: y: 92, x: 0, w: 12, h: 6
- Panel 2: Network Packet Rates
  - Query: `SELECT mean("packets_sent") AS "Packets Sent/s", mean("packets_recv") AS "Packets Recv/s" FROM "net" WHERE ("interface" =~ /$netif/) AND $timeFilter GROUP BY time($interval), "interface" fill(null)`
  - Type: Time series graph
  - Position: y: 92, x: 12, w: 12, h: 6
- Panel 3: Network Error Rates
  - Query: `SELECT mean("err_in") AS "Errors In", mean("err_out") AS "Errors Out", mean("drop_in") AS "Drops In", mean("drop_out") AS "Drops Out" FROM "net" WHERE ("interface" =~ /$netif/) AND $timeFilter GROUP BY time($interval), "interface" fill(null)`
  - Type: Time series graph
  - Position: y: 98, x: 0, w: 24, h: 6

**Metrics Used**: `net.bytes_sent`, `net.bytes_recv`, `net.packets_sent`, `net.packets_recv`, `net.err_in`, `net.err_out`, `net.drop_in`, `net.drop_out`
**Panel IDs**: 70010-70012

---

### 📋 Task 5: Per-Container Detailed Metrics (MEDIUM PRIORITY)
**Status**: Pending
**Implementation Details**:
- Add row section: "Docker Container Details"
- Panel 1: Per-Container CPU Usage
  - Query: `SELECT mean("cpu_usage_percent") FROM "docker" WHERE ("container_name" != '') AND $timeFilter GROUP BY time($interval), "container_name" fill(null)`
  - Type: Time series graph
  - Position: y: 104, x: 0, w: 12, h: 6
- Panel 2: Per-Container Memory Usage
  - Query: `SELECT mean("mem_usage_percent") FROM "docker" WHERE ("container_name" != '') AND $timeFilter GROUP BY time($interval), "container_name" fill(null)`
  - Type: Time series graph (stacked area)
  - Position: y: 104, x: 12, w: 12, h: 6
- Panel 3: Per-Container Network I/O
  - Query: `SELECT mean("net_bytes_rcvd") / 1024 / 1024 AS "Network In MB/s", mean("net_bytes_sent") / 1024 / 1024 AS "Network Out MB/s" FROM "docker" WHERE ("container_name" != '') AND $timeFilter GROUP BY time($interval), "container_name" fill(null)`
  - Type: Time series graph
  - Position: y: 110, x: 0, w: 12, h: 6
- Panel 4: Container Status Overview
  - Query: `SELECT last("n_containers_running") AS "Running", last("n_containers_stopped") AS "Stopped", last("n_containers_paused") AS "Paused" FROM "docker" WHERE $timeFilter GROUP BY time($interval) fill(null)`
  - Type: Stat panels or Bar gauge
  - Position: y: 110, x: 12, w: 12, h: 6

**Metrics Used**: `docker.cpu_usage_percent`, `docker.mem_usage_percent`, `docker.net_bytes_rcvd`, `docker.net_bytes_sent`, `docker.n_containers_running`, `docker.n_containers_stopped`
**Panel IDs**: 70013-70016
**Note**: May need to verify exact field names in docker measurement

---

### 📋 Task 6: Disk Usage by Mount Point (MEDIUM PRIORITY)
**Status**: Pending
**Implementation Details**:
- Add row section: "Disk Usage by Mount"
- Panel 1: Disk Usage per Mount Point
  - Query: `SELECT mean("used_percent") FROM "disk" WHERE ("path" =~ /$mountpoint/) AND $timeFilter GROUP BY time($interval), "path" fill(null)`
  - Type: Time series graph
  - Position: y: 116, x: 0, w: 12, h: 6
- Panel 2: Disk Space Used/Free per Mount
  - Query: `SELECT mean("used") / 1024 / 1024 / 1024 AS "Used GB", mean("free") / 1024 / 1024 / 1024 AS "Free GB" FROM "disk" WHERE ("path" =~ /$mountpoint/) AND $timeFilter GROUP BY time($interval), "path" fill(null)`
  - Type: Time series graph
  - Position: y: 116, x: 12, w: 12, h: 6
- Panel 3: Inode Usage per Mount
  - Query: `SELECT mean("inodes_used_percent") FROM "disk" WHERE ("path" =~ /$mountpoint/) AND $timeFilter GROUP BY time($interval), "path" fill(null)`
  - Type: Time series graph
  - Position: y: 122, x: 0, w: 24, h: 6

**Metrics Used**: `disk.used_percent`, `disk.used`, `disk.free`, `disk.inodes_used_percent`
**Panel IDs**: 70017-70019

---

### 📋 Task 7: Memory Pressure Indicators (MEDIUM PRIORITY)
**Status**: Pending
**Implementation Details**:
- Add row section: "Memory Health"
- Panel 1: Available Memory Trend
  - Query: `SELECT mean("available") / 1024 / 1024 / 1024 AS "Available GB" FROM "mem" WHERE $timeFilter GROUP BY time($interval) fill(null)`
  - Type: Time series graph
  - Position: y: 128, x: 0, w: 12, h: 6
- Panel 2: Memory Pressure (Available vs Total)
  - Query: `SELECT (mean("available") / mean("total")) * 100 AS "Available %" FROM "mem" WHERE $timeFilter GROUP BY time($interval) fill(null)`
  - Type: Time series graph with thresholds
  - Position: y: 128, x: 12, w: 12, h: 6
- Panel 3: Cache and Buffer Usage
  - Query: `SELECT mean("cached") / 1024 / 1024 / 1024 AS "Cached GB", mean("buffered") / 1024 / 1024 / 1024 AS "Buffered GB" FROM "mem" WHERE $timeFilter GROUP BY time($interval) fill(null)`
  - Type: Time series graph
  - Position: y: 134, x: 0, w: 12, h: 6
- Panel 4: Swap Usage Trend
  - Query: `SELECT mean("used_percent") FROM "swap" WHERE $timeFilter GROUP BY time($interval) fill(null)`
  - Type: Time series graph
  - Position: y: 134, x: 12, w: 12, h: 6

**Metrics Used**: `mem.available`, `mem.total`, `mem.cached`, `mem.buffered`, `swap.used_percent`
**Panel IDs**: 70020-70023

---

### 📋 Task 8: Enhanced HTTP/DNS Panels (LOW PRIORITY)
**Status**: Pending
**Implementation Details**:
- Enhance existing HTTP response panels
- Add response time percentiles (p50, p95, p99)
- Add success/failure rate
- Enhance DNS query panels with detailed breakdowns

**Panel IDs**: Update existing panels

---

### 📋 Task 9: Dashboard Reorganization (LOW PRIORITY)
**Status**: Pending
**Implementation Details**:
- Reorganize existing panels into logical sections
- Add collapsible row sections:
  - "System Overview" (existing)
  - "Temperature & Health" (new)
  - "Storage" (enhanced)
  - "Network" (enhanced)
  - "Docker Containers" (enhanced)
  - "System Performance" (enhanced)

---

## Implementation Notes

1. **Panel ID Generation**: Use IDs starting from 70001 to avoid conflicts
2. **Grid Positioning**: Last panel ends at y: 69, new panels start at y: 70
3. **Query Format**: All queries use InfluxDB format with `$timeFilter` and `$interval`
4. **Variable Usage**: Leverage existing variables: `$server`, `$interval`, `$mountpoint`, `$netif`, `$disk`
5. **Thresholds**: Use color-coded thresholds for critical metrics (temperature, disk usage, memory)
6. **Units**: Properly format units (MB/s, GB, %, °C, etc.)

## Testing Checklist

- [ ] Verify all queries work with actual InfluxDB data
- [ ] Check panel positioning and layout
- [ ] Verify thresholds are appropriate
- [ ] Test variable filters work correctly
- [ ] Ensure dashboard loads without errors
- [ ] Verify all metrics are displaying correctly

## Next Steps

1. Generate complete enhanced dashboard JSON
2. Test queries against live InfluxDB
3. Import updated dashboard to Grafana
4. Verify all panels display correctly
5. Adjust thresholds and formatting as needed

