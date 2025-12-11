---
name: monitor-drive-health
description: Monitor drive health using SMART status and ZFS pool status
when_to_use: Check drive health, detect failing drives, monitor ZFS pool status
script: scripts/check-drive-health.sh
---

# Monitor Drive Health

Monitor drive health using SMART status checks and ZFS pool monitoring.

## Quick Usage

```bash
# Run manual health check
bash scripts/check-drive-health.sh

# Or from local machine (via SSH)
ssh -p 4242 unarmedpuppy@192.168.86.47 "bash ~/server/scripts/check-drive-health.sh"
```

## What It Checks

1. **SMART Health Status** - Overall health for each drive
2. **Critical SMART Attributes**:
   - Reallocated_Sector_Ct - Bad sectors that have been remapped
   - Current_Pending_Sector - Sectors waiting to be remapped
   - Offline_Uncorrectable - Unrecoverable sectors
   - UDMA_CRC_Error_Count - Interface errors
3. **Drive Temperature** - Warns if > 60°C
4. **Power-on Hours** - Drive age/usage
5. **ZFS Pool Status** - Checks for errors, degraded, or faulted drives

## Installation

### 1. Install smartmontools

```bash
sudo apt update
sudo apt install smartmontools -y
```

### 2. Enable SMART on all drives

```bash
# Enable SMART for all drives
for disk in /dev/sd[a-z]; do
    sudo smartctl -s on "$disk" 2>/dev/null || true
done
```

### 3. Test the script

```bash
bash scripts/check-drive-health.sh
```

## Automated Monitoring Setup

### Option 1: Daily Cron Job

```bash
# Add to crontab
sudo crontab -e

# Add this line (runs daily at 3 AM)
0 3 * * * /home/unarmedpuppy/server/scripts/check-drive-health.sh >> /var/log/drive-health.log 2>&1
```

### Option 2: Weekly Email Alerts

```bash
# Create alert script
cat > ~/server/scripts/drive-health-alert.sh <<'EOF'
#!/bin/bash
OUTPUT=$(bash ~/server/scripts/check-drive-health.sh 2>&1)
if echo "$OUTPUT" | grep -q "ERROR\|FAILING"; then
    # Send email alert (requires mail setup)
    echo "$OUTPUT" | mail -s "Drive Health Alert - $(hostname)" your-email@example.com
fi
EOF

chmod +x ~/server/scripts/drive-health-alert.sh

# Add to crontab (weekly on Monday at 2 AM)
0 2 * * 1 /home/unarmedpuppy/server/scripts/drive-health-alert.sh
```

## Understanding SMART Attributes

### Critical Attributes to Monitor

1. **Reallocated_Sector_Ct**
   - **What**: Number of bad sectors remapped to spare sectors
   - **Warning**: Any value > 0 means drive has bad sectors
   - **Action**: Monitor closely, replace if increasing

2. **Current_Pending_Sector**
   - **What**: Sectors waiting to be remapped
   - **Warning**: Any value > 0 is concerning
   - **Action**: Immediate attention needed

3. **Offline_Uncorrectable**
   - **What**: Sectors that couldn't be recovered
   - **Warning**: Any value > 0 is critical
   - **Action**: Replace drive immediately

4. **UDMA_CRC_Error_Count**
   - **What**: Interface communication errors
   - **Warning**: High values indicate cable/connection issues
   - **Action**: Check cables, replace if persistent

### Temperature Guidelines

- **< 40°C**: Excellent
- **40-50°C**: Normal
- **50-60°C**: Acceptable
- **60-70°C**: High (check cooling)
- **> 70°C**: Critical (immediate action)

## ZFS Pool Health

The script also checks ZFS pool status:

- **ONLINE**: All drives healthy
- **DEGRADED**: One drive failed, pool still functional
- **FAULTED**: Critical failure, data at risk
- **Errors**: Check error counts

### ZFS Pool Commands

```bash
# Check pool status
sudo zpool status

# Check pool health
sudo zpool status jenquist-cloud

# Get detailed drive info
sudo zpool status -v jenquist-cloud

# Check for errors
sudo zpool status | grep -i error
```

## Manual Drive Health Checks

### Check Specific Drive

```bash
# Get SMART info
sudo smartctl -i /dev/sda

# Get SMART health
sudo smartctl -H /dev/sda

# Get all SMART attributes
sudo smartctl -A /dev/sda

# Run short self-test
sudo smartctl -t short /dev/sda

# Run extended self-test (takes hours)
sudo smartctl -t long /dev/sda

# Check test results
sudo smartctl -l selftest /dev/sda
```

### Check All Drives in ZFS Pool

```bash
# List all drives in pool
sudo zpool status jenquist-cloud | grep -E "sda|sdb|sdc|sdd"

# Check each drive
for disk in sda sdb sdc sdd; do
    echo "=== /dev/$disk ==="
    sudo smartctl -H /dev/$disk
    sudo smartctl -A /dev/$disk | grep -E "Reallocated|Pending|Uncorrectable|Temperature"
done
```

## Signs of Failing Drive

1. **SMART Health**: Not "PASSED"
2. **Increasing Bad Sectors**: Reallocated_Sector_Ct increasing
3. **Pending Sectors**: Current_Pending_Sector > 0
4. **ZFS Errors**: Errors in `zpool status`
5. **Slow Performance**: Unusually slow read/write
6. **Strange Noises**: Clicking, grinding sounds
7. **System Crashes**: Unexplained crashes or hangs

## When to Replace a Drive

**Replace Immediately**:
- SMART health is not "PASSED"
- Current_Pending_Sector > 0
- Offline_Uncorrectable > 0
- ZFS pool shows DEGRADED or FAULTED

**Replace Soon**:
- Reallocated_Sector_Ct increasing over time
- Multiple SMART attributes near threshold
- Drive age > 5 years with heavy usage
- Temperature consistently high

**Monitor Closely**:
- Any Reallocated_Sector_Ct > 0
- Temperature > 60°C
- UDMA_CRC_Error_Count increasing

## Integration with Monitoring

This script can be integrated with:
- **Grafana**: Parse output and create alerts
- **Email**: Send alerts on failures
- **Homepage**: Display drive health status
- **Cron**: Automated daily/weekly checks

## Related Tools

- `scripts/backup-server.sh` - Backup system before drive failure
- `scripts/check-backup-health.sh` - Verify backups are working
- `scripts/check-service-health.sh` - Overall system health

## Troubleshooting

### smartctl not found
```bash
sudo apt install smartmontools
```

### Permission denied
```bash
# Run with sudo
sudo bash scripts/check-drive-health.sh
```

### SMART not available
```bash
# Enable SMART
sudo smartctl -s on /dev/sda
```

### ZFS pool not accessible
```bash
# Check if pool exists
sudo zpool list

# Load keys if encrypted
sudo zfs load-key -a
```

