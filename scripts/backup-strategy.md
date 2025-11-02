# Home Server Backup Strategy

This document outlines comprehensive backup strategies for your home server to ensure zero data loss in case of hardware failure.

## Backup Components

The backup script (`backup-server.sh`) backs up:

1. **Docker Volumes** - All named Docker volumes containing application data
2. **Docker Configurations** - All docker-compose.yml files and app configs
3. **System Configurations** - /etc directory (system-wide configs)
4. **Home Directory Configs** - User dotfiles and configurations
5. **Cron Jobs** - User and root crontabs, system cron directories
6. **Mount Information** - fstab, mount points, disk information, ZFS configs
7. **Package Lists** - List of installed packages for easy restoration
8. **Docker System Info** - Container, image, network, and volume lists

## Low-Cost Backup Destination Options

### Option 1: Local External Drive (Recommended for Immediate Backups)
**Cost:** Free (if you already have drives)  
**Speed:** Very Fast  
**Reliability:** Medium (drive can fail)  
**Capacity:** Based on your drive size

You already have two external drives mounted:
- `/mnt/server-cloud` (8TB) - Intended for backups
- `/mnt/server-storage` (4TB) - Ephemeral media storage

**Setup:**
```bash
# On the server, set backup destination to server-cloud
export BACKUP_DEST="/mnt/server-cloud/backups"
bash ~/server/scripts/backup-server.sh
```

**Pros:**
- Fast backup and restore
- No ongoing costs
- Works offline
- Large capacity available

**Cons:**
- Single point of failure
- Can be lost/stolen
- Should be rotated off-site

### Option 2: Remote Server via SSH/rsync
**Cost:** $5-20/month (VPS like DigitalOcean, Linode, Vultr)  
**Speed:** Moderate (depends on bandwidth)  
**Reliability:** High (cloud provider redundancy)  
**Capacity:** 100GB-2TB typically

**Setup:**
```bash
# Create backup script that rsyncs to remote server
# Example with rsync:
rsync -avz --delete -e "ssh -p 2222" \
  /mnt/server-cloud/backups/ \
  user@backup-server.example.com:/backups/home-server/
```

**Recommended Providers:**
- **Hetzner** - $5.50/month for 500GB storage box
- **DigitalOcean Spaces** - $5/month for 250GB
- **Backblaze B2** - $5/TB/month + $10/TB download
- **Wasabi** - $6.99/TB/month (no egress fees)

### Option 3: Cloud Storage (S3-Compatible)
**Cost:** $5-10/month for 1TB  
**Speed:** Moderate to slow (depends on upload speed)  
**Reliability:** Very High  
**Capacity:** Virtually unlimited

**Options:**

#### Backblaze B2
- **Cost:** $5/TB/month storage, $10/TB download
- **Setup:** Use `rclone` or `b2` CLI
```bash
# Install rclone
sudo apt install rclone

# Configure
rclone config

# Backup
rclone sync /mnt/server-cloud/backups b2:home-server-backups --progress
```

#### Wasabi Hot Storage
- **Cost:** $6.99/TB/month (no egress fees)
- **Setup:** S3-compatible, use `rclone` or `aws-cli`

#### AWS S3 Glacier
- **Cost:** $4/TB/month (cheapest, but slow retrieval)
- **Best for:** Long-term archival backups

### Option 4: Network Attached Storage (NAS)
**Cost:** $200-500 one-time + drives  
**Speed:** Fast (local network)  
**Reliability:** High (RAID protection)  
**Capacity:** Depends on drives

**Setup:**
```bash
# Mount NAS via NFS or SMB
sudo mount -t nfs nas-ip:/backups /mnt/nas-backups

# Or use rsync over SSH
rsync -avz /mnt/server-cloud/backups/ user@nas:/volume1/backups/
```

### Option 5: Multiple Local Drives (3-2-1 Strategy)
**Cost:** $50-150 per drive  
**Strategy:** 
- 3 copies of data
- 2 different media types
- 1 copy off-site

**Implementation:**
1. Primary backup on `/mnt/server-cloud`
2. Secondary backup on separate external drive (rotate weekly)
3. Off-site backup on cloud storage or another location

## Recommended Backup Schedule

Based on your current setup, here's a recommended schedule:

### Daily Backups (Incremental)
- Time: 2:00 AM (low usage period)
- Destination: `/mnt/server-cloud/backups/daily/`
- Retention: 7 days
- What: Docker volumes, configs, critical data

### Weekly Backups (Full)
- Day: Sunday 1:00 AM
- Destination: `/mnt/server-cloud/backups/weekly/`
- Retention: 4 weeks
- What: Full system backup

### Monthly Backups (Full + Off-site)
- Day: First of month, 12:00 AM
- Destination: Local + Cloud
- Retention: 6 months locally, 12 months cloud
- What: Full system backup + sync to cloud

### Quarterly Backups (Archival)
- When: Start of each quarter
- Destination: Separate external drive (off-site)
- Retention: Indefinite
- What: Full system backup on separate media

## Automated Backup Setup

### 1. Install and Configure Backup Script

```bash
# Make script executable
chmod +x ~/server/scripts/backup-server.sh

# Create backup directory
sudo mkdir -p /mnt/server-cloud/backups
sudo chown unarmedpuppy:unarmedpuppy /mnt/server-cloud/backups
```

### 2. Setup Daily Backup Cron Job

```bash
sudo crontab -e

# Add these lines:
# Daily backup at 2 AM
0 2 * * * /home/unarmedpuppy/server/scripts/backup-server.sh > /var/log/server-backup-daily.log 2>&1

# Weekly backup on Sunday at 1 AM
0 1 * * 0 BACKUP_DEST=/mnt/server-cloud/backups/weekly /home/unarmedpuppy/server/scripts/backup-server.sh > /var/log/server-backup-weekly.log 2>&1

# Monthly backup on 1st at midnight
0 0 1 * * BACKUP_DEST=/mnt/server-cloud/backups/monthly /home/unarmedpuppy/server/scripts/backup-server.sh > /var/log/server-backup-monthly.log 2>&1
```

### 3. Setup Cloud Backup (Example: Backblaze B2)

```bash
# Install rclone
sudo apt install rclone

# Configure rclone
rclone config
# Follow prompts to add B2 remote

# Create sync script
cat > ~/server/scripts/sync-to-cloud.sh <<'EOF'
#!/bin/bash
# Sync monthly backups to cloud
rclone sync /mnt/server-cloud/backups/monthly \
  b2:home-server-backups/monthly \
  --progress \
  --log-file=/var/log/rclone-sync.log
EOF

chmod +x ~/server/scripts/sync-to-cloud.sh

# Add to crontab (runs day after monthly backup)
0 2 2 * * /home/unarmedpuppy/server/scripts/sync-to-cloud.sh
```

### 4. Setup Backup Rotation/Cleanup

```bash
cat > ~/server/scripts/cleanup-old-backups.sh <<'EOF'
#!/bin/bash
# Keep last 7 daily backups
find /mnt/server-cloud/backups/daily -maxdepth 1 -type d -name "server-backup-*" -mtime +7 -exec rm -rf {} \;

# Keep last 4 weekly backups
find /mnt/server-cloud/backups/weekly -maxdepth 1 -type d -name "server-backup-*" -mtime +28 -exec rm -rf {} \;

# Keep last 6 monthly backups
find /mnt/server-cloud/backups/monthly -maxdepth 1 -type d -name "server-backup-*" -mtime +180 -exec rm -rf {} \;
EOF

chmod +x ~/server/scripts/cleanup-old-backups.sh

# Add to crontab (runs daily after backup)
30 2 * * * /home/unarmedpuppy/server/scripts/cleanup-old-backups.sh
```

## Cost Comparison

| Option | Monthly Cost | Storage | Speed | Reliability |
|--------|--------------|---------|-------|-------------|
| Local External Drive | $0 | 8TB | Very Fast | Medium |
| Hetzner Storage Box | $5.50 | 500GB | Fast | High |
| Backblaze B2 | ~$5-10 | 1TB | Moderate | Very High |
| Wasabi | $6.99 | 1TB | Moderate | Very High |
| AWS S3 Glacier | ~$4 | 1TB | Slow | Very High |
| **Combined Approach** | **~$7-12** | **Multi-tier** | **Fast+Cloud** | **Very High** |

## Recommended Solution: Hybrid Approach

For maximum protection at low cost:

1. **Primary Backup:** `/mnt/server-cloud/backups` (local, fast)
   - Daily incremental backups
   - 7 days retention
   - Cost: Free

2. **Secondary Backup:** Separate external drive (rotated weekly)
   - Weekly full backups
   - Kept off-site when not backing up
   - Cost: ~$100 one-time

3. **Cloud Backup:** Backblaze B2 or Wasabi (monthly sync)
   - Monthly full backups
   - 12+ months retention
   - Cost: ~$7-12/month for 1TB

**Total Monthly Cost:** ~$7-12  
**Total One-time Cost:** ~$100 (for second external drive)  
**Protection Level:** Excellent (follows 3-2-1 rule)

## Testing Backups

Regularly test your backups to ensure they're working:

```bash
# Test restore of a single docker volume
docker volume create test-restore
docker run --rm -v test-restore:/data -v /mnt/server-cloud/backups/daily/latest/docker-volumes/immich_im-pgdata.tar.gz:/backup.tar.gz alpine sh -c "cd /data && tar xzf /backup.tar.gz"
docker volume rm test-restore

# Verify backup integrity
cd /mnt/server-cloud/backups/daily/latest
for file in docker-volumes/*.tar.gz; do
  echo "Checking $file"
  gzip -t "$file" || echo "ERROR: $file is corrupted"
done
```

## Monitoring Backups

Create a monitoring script to alert on backup failures:

```bash
cat > ~/server/scripts/check-backup-health.sh <<'EOF'
#!/bin/bash
# Check if latest backup exists and is recent (< 25 hours old)
LATEST_BACKUP="/mnt/server-cloud/backups/daily/latest"

if [ ! -d "$LATEST_BACKUP" ]; then
  echo "ERROR: Latest backup not found!"
  # Send notification (email, webhook, etc.)
  exit 1
fi

BACKUP_AGE=$(( ($(date +%s) - $(stat -c %Y "$LATEST_BACKUP")) / 3600 ))
if [ $BACKUP_AGE -gt 25 ]; then
  echo "WARNING: Latest backup is $BACKUP_AGE hours old!"
  exit 1
fi

echo "Backup health check passed"
EOF

chmod +x ~/server/scripts/check-backup-health.sh

# Add to crontab
0 3 * * * /home/unarmedpuppy/server/scripts/check-backup-health.sh
```

## Restoration Procedures

See `restore-server.sh` script for detailed restoration procedures.

## Additional Considerations

1. **Encryption:** Consider encrypting backups containing sensitive data
2. **Compression:** Backups are already compressed (tar.gz), but you can adjust compression level
3. **Network Bandwidth:** Monitor bandwidth usage for cloud backups
4. **Backup Verification:** Regularly verify backup integrity
5. **Documentation:** Keep this document updated with your actual backup configuration

## Next Steps

1. Review and adjust backup destinations based on your needs
2. Set up automated cron jobs
3. Configure cloud backup sync (if using cloud option)
4. Test backup and restore procedures
5. Set up backup monitoring/alerts
6. Document your specific backup configuration in this file

