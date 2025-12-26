# USB Auto-Backup Feature

## Overview

Automatically detect when a specific USB external drive is connected and trigger backup sync of the same directories that are backed up to B2.

## Requirements

- Detect specific USB drive by UUID (not just any USB drive)
- Auto-mount the drive
- Run rclone sync to mirror the same "essential-plus-music" directories
- Log backup progress
- Send notification when complete (optional)

## Implementation Steps

### 1. Identify the USB Drive

When drive is connected, run:
```bash
# Find the new device
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,UUID

# Get detailed info
sudo blkid /dev/sdX1

# Get udev attributes
udevadm info --query=all --name=/dev/sdX
```

### 2. Create Mount Point

```bash
sudo mkdir -p /mnt/usb-backup
```

### 3. Create udev Rule

File: `/etc/udev/rules.d/99-backup-drive.rules`
```bash
# Auto-mount and backup when specific drive is connected
ACTION=="add", SUBSYSTEM=="block", ENV{ID_FS_UUID}=="<DRIVE-UUID>", RUN+="/home/unarmedpuppy/server/scripts/usb-backup.sh"
```

### 4. Create Backup Script

File: `scripts/usb-backup.sh`
```bash
#!/bin/bash
# USB Auto-Backup Script
# Triggered by udev when backup drive is connected

DRIVE_UUID="<DRIVE-UUID>"
MOUNT_POINT="/mnt/usb-backup"
LOG_FILE="/home/unarmedpuppy/server/logs/backups/usb-backup.log"
LOCK_FILE="/tmp/usb-backup.lock"

# Prevent multiple runs
if [ -f "$LOCK_FILE" ]; then
    echo "Backup already running" >> "$LOG_FILE"
    exit 0
fi
touch "$LOCK_FILE"

# Find device by UUID
DEVICE=$(blkid -U "$DRIVE_UUID")
if [ -z "$DEVICE" ]; then
    echo "$(date): Drive not found" >> "$LOG_FILE"
    rm "$LOCK_FILE"
    exit 1
fi

# Mount drive
mkdir -p "$MOUNT_POINT"
mount "$DEVICE" "$MOUNT_POINT"

# Run backup (same dirs as B2 backup)
echo "$(date): Starting USB backup" >> "$LOG_FILE"

rclone sync /jenquist-cloud/archive/personal-media "$MOUNT_POINT/archive/personal-media" \
    --exclude "*.tmp" --exclude ".DS_Store" --exclude ".cache/**" \
    --progress --log-file "$LOG_FILE" --log-level INFO &

rclone sync /jenquist-cloud/backups "$MOUNT_POINT/backups" \
    --exclude "*.tmp" --exclude ".DS_Store" --exclude ".cache/**" \
    --progress --log-file "$LOG_FILE" --log-level INFO &

rclone sync /jenquist-cloud/vault "$MOUNT_POINT/vault" \
    --progress --log-file "$LOG_FILE" --log-level INFO &

rclone sync /jenquist-cloud/archive/entertainment-media/Music "$MOUNT_POINT/archive/entertainment-media/Music" \
    --exclude "*.tmp" --exclude ".DS_Store" \
    --progress --log-file "$LOG_FILE" --log-level INFO &

wait

echo "$(date): USB backup complete" >> "$LOG_FILE"

# Unmount (optional - leave mounted for manual inspection)
# umount "$MOUNT_POINT"

rm "$LOCK_FILE"
```

### 5. Enable the Rule

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

## Baseline Device State (Before USB)

Captured 2024-12-26:
- sda-sdd: 7.3TB each (ZFS pool)
- nvme0n1: 931GB (boot drive)
- No USB storage devices connected

## Status

**Pending** - Waiting for user to connect USB drive for identification.

## Notes

- Same directories as "essential-plus-music" B2 config
- Uses rclone sync (deletions propagate)
- Parallel sync for faster completion
- Logs to ~/server/logs/backups/usb-backup.log
