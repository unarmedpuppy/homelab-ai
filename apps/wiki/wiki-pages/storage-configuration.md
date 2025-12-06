# Storage Configuration

### Mount External Hard Drives

**1. Identify Drives**:
```bash
sudo blkid
```

Example output:
```
/dev/sdc1: LABEL="server-storage" BLOCK_SIZE="512" UUID="0812C2CF12C2C0C4" TYPE="ntfs"
/dev/sdd1: LABEL="server-cloud" BLOCK_SIZE="512" UUID="F030A88630A8557E" TYPE="ntfs"
```

**2. Create Mount Points**:
```bash
sudo mkdir /mnt/server-storage
sudo mkdir /mnt/server-cloud
```

**3. Edit /etc/fstab**:
```bash
sudo nano /etc/fstab
```

Add entries:
```
UUID=0812C2CF12C2C0C4  /mnt/server-storage  ntfs  defaults,nofail  0  0
UUID=5970408A4427DC74  /mnt/server-cloud  ntfs  defaults,nofail  0  0
```

**4. Test Mount**:
```bash
sudo mount -a
```

### ZFS RAID Configuration

#### Install ZFS

**1. Add Contrib Repository**:
```bash
sed -r -i'.BAK' 's/^deb(.*)$/deb\1 contrib/g' /etc/apt/sources.list
```

Result:
```
deb http://deb.debian.org/debian bookworm main non-free non-free-firmware contrib
deb http://deb.debian.org/debian bookworm-updates main non-free non-free-firmware contrib
deb http://deb.debian.org/debian-security/ bookworm-security main non-free non-free-firmware contrib
```

**2. Install ZFS Packages**:
```bash
sudo apt update
sudo apt install linux-headers-amd64 zfsutils-linux zfs-dkms zfs-zed -y
```

For cloud kernel:
```bash
sudo apt install linux-headers-cloud-amd64 zfsutils-linux zfs-dkms zfs-zed
```

**3. Load ZFS Module**:
```bash
sudo modprobe zfs
```

**4. Verify Installation**:
```bash
zfs version
```

Expected output:
```
zfs-2.1.11-1
zfs-kmod-2.1.11-1
```

#### Create ZFS Pool

**Create RAID-Z1 Pool**:
```bash
sudo zpool create jenquist-cloud raidz1 /dev/sda /dev/sdb /dev/sdc /dev/sdd
```

**Create ZFS Filesystem**:
```bash
sudo zfs create jenquist-cloud/archive
```

**Pool Status**:
```
pool: jenquist-cloud
state: ONLINE
config:
    NAME            STATE     READ WRITE CKSUM
    jenquist-cloud  ONLINE       0     0     0
      raidz1-0      ONLINE       0     0     0
        sda         ONLINE       0     0     0
        sdb         ONLINE       0     0     0
        sdc         ONLINE       0     0     0
        sdd         ONLINE       0     0     0
```

#### Mount ZFS Filesystems

```bash
# Load encryption keys
sudo zfs load-key -a

# Mount all filesystems
sudo zfs mount -a
```

### RAID 5 Configuration (Alternative)

**Note**: RAID 5 information is documented for reference. ZFS RAID-Z1 is currently used.

#### Install mdadm
```bash
sudo apt update
sudo apt install mdadm
```

#### Create RAID 5 Array
```bash
sudo mdadm --create --verbose /dev/md0 --level=5 --raid-devices=4 /dev/sdb /dev/sdc /dev/sdd /dev/sde
```

#### Verify Array
```bash
cat /proc/mdstat
```

**Warning**: All data on drives will be lost when creating RAID array. Backup important data first.

#### Replace Failed Drive

1. Identify failed drive: `cat /proc/mdstat` (shows [U_U] instead of [UUU])
2. Mark as failed and remove:
   ```bash
   sudo mdadm --manage /dev/md0 --fail /dev/sdb
   sudo mdadm --manage /dev/md0 --remove /dev/sdb
   ```
3. Physically replace the drive
4. Add new drive:
   ```bash
   sudo mdadm --manage /dev/md0 --add /dev/sdc
   ```
5. Monitor rebuild: `cat /proc/mdstat`

### Backup Configuration

#### Daily Backups with rsnapshot

**1. Install rsnapshot**:
```bash
sudo apt-get install rsnapshot
```

**2. Configure**:
```bash
sudo nano /etc/rsnapshot.conf
```
Backing up to external drive: `/mnt/archive`

**3. Test Configuration**:
```bash
sudo rsnapshot configtest
```

**4. Run Manually**:
```bash
sudo rsnapshot alpha
```

**5. Automate via Cron**:
```bash
sudo crontab -e
```

Add:
```
0 */4 * * *     /usr/bin/rsnapshot alpha
00 00 * * *     /usr/bin/rsnapshot beta
00 23 * * 6     /usr/bin/rsnapshot gamma
00 22 1 * *     /usr/bin/rsnapshot delta
```

Schedule:
- `alpha`: Every 4 hours (check frequency)
- `beta`: Daily at midnight
- `gamma`: Saturdays at 11:00 PM
- `delta`: First day of month at 10:00 PM

### Backup Disk Image

```bash
sudo dd if=/dev/sda of=/mnt/server-storage/test-bk.img status=progress
```

---