# Useful Commands

### System Information

```bash
# Local IP
hostname -I

# MAC address
sudo apt-get install net-tools
/sbin/ifconfig

# RAM details
sudo dmidecode --type memory

# Disk usage visualization
sudo apt install ncdu
sudo ncdu /

# Top 10 largest directories
sudo du -sh * | sort -hr | head -n10

# Directory size
du -sh server/apps/bedrock-viz/
```

### Backup Operations

```bash
# Full disk image backup
sudo dd if=/dev/sda of=/mnt/server-storage/test-bk.img status=progress

# rsnapshot backup
sudo rsnapshot configtest  # Test configuration
sudo rsnapshot alpha       # Run backup
```

### File Transfer

```bash
# Copy file to server
scp -P 4242 <local_file> unarmedpuppy@192.168.86.47:<remote_path>

# Copy directory to server
scp -P 4242 -r <local_dir> unarmedpuppy@192.168.86.47:<remote_path>

# Copy from server
scp -P 4242 unarmedpuppy@192.168.86.47:<remote_path> <local_file>
```

---