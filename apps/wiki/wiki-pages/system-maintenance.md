# System Maintenance

### System Monitoring

#### Fan Speed Monitoring

**Install lm-sensors**:
```bash
sudo apt update && sudo apt install lm-sensors
sudo sensors-detect
sensors
```

**Install fancontrol**:
```bash
sudo apt-get install fancontrol
sudo pwmconfig
```
When prompted, answer `y` to set up configuration file at `/etc/fancontrol`.

**Coolero (Fan Control)**:
```bash
curl -1sLf 'https://dl.cloudsmith.io/public/coolercontrol/coolercontrol/setup.deb.sh' | sudo -E bash
sudo apt update
sudo apt install coolercontrol
sudo coolercontrol-liqctld
```

**Add Fans to Sensors Output** (Custom Module):
```bash
git clone https://github.com/a1wong/it87.git
cd it87
sudo make clean
sudo make && sudo make install
sudo modprobe it87 ignore_resource_conflict=1 force_id=0x8622
```

#### Temperature Sensor Calibration

Create `/etc/sensors.d/k10temp.conf` for accurate CPU temperature:
```
chip "k10temp-*"
   label temp1 "CPU Temp"
   compute  temp1  (@/2.56)+36.4921875, (@-36.4921875)*2.56
```

**Calibration Method**:
1. Let computer idle, compare `sensors` output with BIOS temperature
2. Run stress test, compare again
3. Calculate calibration formula based on differences
4. Formula: `real_temp = (sensors_temp / 2.56) + 36.4921875`

#### System Stress Testing
```bash
sudo apt install stress
stress --cpu 8
```

### Scheduled Tasks (Cron Jobs)

```bash
sudo crontab -e
```

**Prune Docker Images** (Weekly, Monday at 5:00 AM):
```
0 5 * * 1 docker system prune -a -f
```

**Restart Machine** (Nightly at 5:15 AM):
```
15 5 * * * /sbin/reboot
```

**Backup Rust Player Data** (First Wednesday of each month):
```
0 0 1-7 * * [ "$(date +\%u)" = "3" ] && ~/server/scripts/backup-rust.sh
```

### File System Operations

**Resize Filesystem**:
```bash
sudo resize2fs /dev/nvme0n1p2
```

---