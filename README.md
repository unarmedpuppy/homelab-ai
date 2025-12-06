# Linux Home Server

Comprehensive documentation for the home server setup, configuration, and maintenance.

## Table of Contents

- [Quick Reference](#quick-reference)
- [System Overview](#system-overview)
- [Hardware Specifications](#hardware-specifications)
- [Initial Setup](#initial-setup)
- [Storage Configuration](#storage-configuration)
- [Network Configuration](#network-configuration)
- [Security Configuration](#security-configuration)
- [Docker & Containers](#docker--containers)
- [Services & Applications](#services--applications)
- [System Maintenance](#system-maintenance)
- [Useful Commands](#useful-commands)
- [Development Workflow](#development-workflow)

---

## Quick Reference

### Connection Information

- **SSH Access**: `ssh unarmedpuppy@192.168.86.47 -p 4242`
- **Local IP**: `192.168.86.47` (check with `hostname -I`)
- **MAC Address**: `74:56:3c:e1:8b:3a`
- **EdgeRouter Access**: `ssh unarmedpuppy@172.16.30.1` (password in 1Password)
- **Domain**: `server.unarmedpuppy.com`

### Custom Aliases

- `cycle` - Runs `~/server/docker-restart.sh` (stops and starts all Docker containers)
- `server` - Runs `connect-server.sh` (SSH connection wrapper)
- `sync` - Git pull, add, commit & push operations

### Quick Commands

```bash
# Get local IP
hostname -I

# Get MAC address (requires net-tools)
sudo apt-get install net-tools
/sbin/ifconfig

# Check disk usage
sudo ncdu /
sudo du -sh * | sort -hr | head -n10

# Check directory size
du -sh server/apps/bedrock-viz/
```

---

## System Overview

### Operating System

- **OS**: Debian 12 (Bookworm)
- **Installation Method**: Created bootable USB using [Etcher](https://etcher.balena.io/)

### Power Management

- **Power Mode**: Performance
- **Screen Blank**: Never
- **Auto Suspend**: Off
- **Power Button Behavior**: Nothing (disabled)

### Users

- **root** - Root user
- **unarmedpuppy** - Primary user (added to sudoers file)
- **Docker Group ID**: 994 (`stat -c '%g' /var/run/docker.sock`)

### Prevent System Suspend

```bash
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
```

---

## Hardware Specifications

### BIOS

- **Version**: MC123IOE.100
- **ME FW Version**: 12/0.41.1435

### CHASSIS

- Sliger CX3701 | 3U 15" Deep Chassis | 10 X tray-less 3.5 HDD hot-swap/direct-wired SATA connectors | SFX PSU | Mini ITX Motherboard

### MOTHERBOARD

- B550I AORUS Pro AX AMD AM4 Mini-ITX Motherboard

### POWER SUPPLY

- Corsair SF750 (2018) 750 W 80+ Platinum Certified Fully Modular SFX Power Supply

### CPU

**Original**:
- Model: Intel(R) Celeron(R) G4900T CPU @ 2.90GHz
- Cores: 2
- Memory: 64008 MB

**Upgraded**:
- Model: Intel Core i7-6700K
- Cores: 4 (8 threads with hyperthreading)
- Clock Speed: 4.0 GHz (base)
- Socket: LGA 1151
- TDP: 91W
- Integrated Graphics: Intel HD Graphics 530

### RAM

- **Capacity**: 32GB
- **Type**: DDR4
- **Manufacturer**: Kingston
- **Part Number**: CBD26D4S9S8ME-8

To inspect detailed RAM information:
```bash
sudo dmidecode --type memory
```

### Storage

- **Internal SSD**: 1TB
- **server-storage**: 4TB (used for syncing media & photo content to/from Seafile - intended to be ephemeral)
- **server-cloud**: 8TB (Seafile sync server, server backups - intended to be a backup of Jenquist cloud & serve as a syncing source for other devices, including server-storage)
- **Jenquist Cloud**: ZFS RAID (raidz1) - primary archive storage

### Current File System Layout

```
/boot/efi
/dev/sda2      fuseblk      1.9T  1.8T   54G  98% /mnt/plex
/dev/sdb1      fuseblk      1.8T  120G  1.7T   7% /mnt/server-storage
/dev/sdb2      fuseblk      2.0T   39G  1.9T   2% /mnt/server-backup
```

---

## Initial Setup

### User Management

#### Add User to Sudoers

```bash
# Switch to root
su -

# Install sudo (if not installed)
apt-get install sudo

# Add user to sudo group
adduser unarmedpuppy sudo

# Verify
getent group sudo

# Switch back to user
su - unarmedpuppy

# Test sudo access
sudo whoami
```

### SSH Configuration

#### Enable and Configure SSH

```bash
# Update packages
sudo apt-get update

# Install SSH server
sudo apt-get install openssh-server

# Check status
sudo systemctl status ssh

# Enable SSH on boot
sudo systemctl enable ssh
```

#### Secure SSH Configuration

Edit `/etc/ssh/sshd_config`:

```bash
sudo nano /etc/ssh/sshd_config
```

**Settings**:
- `PermitRootLogin no` - Disable root login
- `Port 4242` - Change from default port 22

```bash
# Restart SSH service
sudo systemctl restart ssh
```

#### Lock Down SSH to Key-Only Access

**1. Create SSH Key Pair (Server)**:
```bash
ssh-keygen -t rsa -b 4096
# Passphrase: same as unarmedpuppy password
# (Note: not actually used yet)
```

**2. Create SSH Key Pair (Client)**:
```bash
ssh-keygen -t rsa -b 4096
# Location: /c/Users/micro/.ssh/id_rsa (Windows example)
```

**3. Copy Public Key to Server**:
```bash
ssh-copy-id -i /c/Users/micro/.ssh/id_rsa.pub -o 'Port=4242' unarmedpuppy@192.168.86.47
```

**4. Test Key-Based Login**:
```bash
ssh -o 'Port=4242' 'unarmedpuppy@192.168.86.47'
```

**5. Disable Password Authentication**:

Edit `/etc/ssh/sshd_config`:
```
PasswordAuthentication no
ChallengeResponseAuthentication no
UsePAM no
```

**6. Reload SSH Service**:
```bash
sudo systemctl reload sshd
```

**Additional Security**:
- [Securing SSH with FIDO2](https://developers.yubico.com/SSH/Securing_SSH_with_FIDO2.html) - YubiKey authentication

---

## Storage Configuration

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

## Network Configuration

### Firewall (UFW)

**1. Install UFW**:
```bash
sudo apt install ufw
```

**2. Allow SSH**:
```bash
sudo ufw allow 4242/tcp
```

**3. Enable UFW**:
```bash
sudo ufw enable
```

**4. Set Default Policies**:
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
```

**5. Allow Specific Services**:
```bash
sudo ufw allow 32400/tcp    # Plex
sudo ufw allow 19132/udp    # Minecraft
sudo ufw allow 28015/udp    # Rust
sudo ufw allow 28015/tcp    # Rust
sudo ufw allow 28016/tcp    # Rust (RCON)
sudo ufw allow 8080/tcp     # Rust (Web RCON)
sudo ufw allow 53/tcp       # AdGuard DNS
sudo ufw allow 53/udp       # AdGuard DNS
sudo ufw allow 51820/udp    # WireGuard VPN
```

**6. Check Status**:
```bash
sudo ufw status verbose
```

**Important**: For external traffic (game servers), don't forget to set up port forwarding on your router.

### Cloudflare Tunnel

Install and configure Cloudflare tunnel:
```bash
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb && \
sudo dpkg -i cloudflared.deb && \
sudo cloudflared service install eyJhIjoiYjk2OWY3ZmQ5MzlkYTZmOTQ0NDUyNzc0Nzg2YzViZjUiLCJ0IjoiMDQ4YmZiMjAtZjA2NC00NzU2LWJmZWEtYjM1NTg3MjQ5MzZkIiwicyI6Ik5HWTFNbU0zWWpndE9XSm1aQzAwTVRreExXSTRPREF0WkRZeVpqZ3lNalpoWldFeCJ9
```

### Reverse Proxy (Traefik)

Traefik is used as the reverse proxy with automatic HTTPS via Let's Encrypt.

**1. Create Configuration Directory**:
```bash
mkdir -p ~/server/apps/traefik/{config,logs}
```

**2. Create Traefik Configuration** (`~/server/apps/traefik/config/traefik.yml`):
```yaml
api:
  dashboard: true
  entryPoints:
    web:
      address: ":80"
    websecure:
      address: ":443"

  providers:
    docker:
      endpoint: "unix:///var/run/docker.sock"
      exposedByDefault: false
      network: my-network

certificatesResolvers:
  myresolver:
    acme:
      email: traefik@jenquist.com
      storage: acme.json
      httpChallenge:
        # Using httpChallenge means we're going to solve a challenge using port 80
        entryPoint: web
      # dnsChallenge:
        # provider: cloudflare
        # Delay before checking DNS propagation
        # delayBeforeCheck: 0

accessLog:
  filePath: "~/server/apps/traefik/logs/access.log"
  format: json

metrics:
  prometheus: {}

tracing:
  jaeger:
    samplingType: const
    samplingParam: 1.0
```

**3. Create acme.json for Certificates**:
```bash
touch ~/server/apps/traefik/config/acme.json && chmod 600 ~/server/apps/traefik/config/acme.json
```

**4. Docker Compose Example**:
See `apps/traefik/docker-compose.yml` for full configuration.

**5. Generate Basic Auth Credentials**:
```bash
sudo apt-get install apache2-utils
htpasswd -nb admin example
```

**6. Enable Traefik on Containers**:

Example labels for containers:
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.service.rule=Host(`service.server.unarmedpuppy.com`)"
  - "traefik.http.routers.service.entrypoints=websecure"
  - "traefik.http.routers.service.tls.certresolver=myresolver"
```

**7. Bypass Basic Auth for LAN**:

Example configuration to bypass auth for local IPs:
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.homepage.rule=Host(`server.unarmedpuppy.com`) && ClientIP(`192.168.1.0/24`, `76.156.139.101/24`)"
  - "traefik.http.routers.homepage.priority=99"
  - "traefik.http.routers.homepage.entrypoints=websecure"
  - "traefik.http.routers.homepage.middlewares=bypass"
  - "traefik.http.routers.homepage.tls.certresolver=myresolver"
  - "traefik.http.routers.homepage2.rule=Host(`server.unarmedpuppy.com`)"
  - "traefik.http.routers.homepage2.priority=100"
  - "traefik.http.routers.homepage2.entrypoints=websecure"
  - "traefik.http.routers.homepage2.middlewares=do-auth"
  - "traefik.http.middlewares.do-auth.chain.middlewares=homepage-auth"
  - "traefik.http.middlewares.bypass.chain.middlewares="
  - "traefik.http.middlewares.homepage-auth.basicauth.users=unarmedpuppy:$$apr1$$yE.A6vVX$$p7.fpGKw5Unp0UW6H/2c.0"
```

---

## Security Configuration

### System Security

#### Malware Check (Lynis)
```bash
sudo apt install lynis
sudo lynis audit system
```

#### System Logging

**View Logs**:
```bash
journalctl
```

**Limit Journal Size**:
```bash
sudo journalctl --vacuum-size=100M
```

---

## Docker & Containers

### Docker Installation

**1. Install Required Packages**:
```bash
sudo apt-get install apt-transport-https ca-certificates curl gnupg2 software-properties-common
```

**2. Add Docker's Official GPG Key**:
```bash
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add -
```

**Modern method (recommended)**:
```bash
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo tee /etc/apt/keyrings/docker.gpg > /dev/null
```

**3. Set Up Docker Repository**:
```bash
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable"
```

Modern method:
```bash
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bookworm stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

**4. Install Docker CE**:
```bash
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io
```

**5. Verify Installation**:
```bash
sudo systemctl status docker
sudo docker run hello-world
```

**6. Add User to Docker Group**:
```bash
sudo usermod -aG docker unarmedpuppy
```
Log out and log back in for group membership to take effect.

**7. Enable Docker on Boot**:
```bash
sudo systemctl enable docker
```

**8. Install Docker Compose**:
```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.4/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

**9. Enable Docker TCP** (optional):
See: [Docker TCP Configuration Guide](https://gist.github.com/styblope/dc55e0ad2a9848f2cc3307d4819d819f)

### Docker Networks

**Create Networks**:
```bash
docker network create my-network          # General use
docker network create monitoring_default  # Grafana services
```

**Network Configuration Example**:
```yaml
networks:
  - my-network

networks:
  my-network:
    driver: bridge
    external: true
```

**Inspect Network**:
```bash
docker network inspect my-network
```

Expected subnet: `192.168.160.0/20`, Gateway: `192.168.160.1`

### Docker Maintenance

**Prune Old Images**:
```bash
docker rmi $(docker images -a -q)
docker system prune -a -f
```

**View Reclaimable Space**:
```bash
docker system df
```

**Prune Unused Volumes**:
```bash
docker volume prune
```

**Cron Job for Weekly Pruning**:
```
0 5 * * 1 docker system prune -a -f
```

### NVIDIA GPU Support (Optional)

**1. Add NVIDIA Container Toolkit Repository**:
```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list > /dev/null
```

**2. Install NVIDIA Container Toolkit**:
```bash
sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo systemctl restart docker
```

**3. Install NVIDIA Drivers**:
```bash
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository contrib
sudo add-apt-repository non-free
sudo add-apt-repository non-free-firmware
sudo apt update
sudo apt install -y nvidia-driver nvidia-smi firmware-misc-nonfree
```

**4. Test GPU Access**:
```bash
docker run --rm --gpus all nvidia/cuda:12.2.0-runtime-ubuntu22.04 nvidia-smi
```

---

## Services & Applications

For detailed information about all applications, their ports, and active status, see [APPS_DOCUMENTATION.md](./apps/docs/APPS_DOCUMENTATION.md).

### Key Services

#### Homepage
- **Docs**: [Homepage GitHub](https://github.com/gethomepage/homepage)
- **Configuration**: See `apps/homepage/docker-compose.yml`

To add services to homepage, add labels to containers:
```yaml
labels:
  - "homepage.group=Game Servers"
  - "homepage.name=Service Name"
  - "homepage.href=http://service.server.unarmedpuppy.com"
  - "homepage.description=Service description"
```

#### AdGuard Home

**Previous DNS**: 172.16.30.1

**Configuration**:
- Admin Web Interface: Port 80 (after initial setup on port 3003)
- DNS Server: Port 53 (TCP/UDP)
- Listen Interface: All interfaces
- Static IP Required: Yes (for proper function)

**Setup**: Configure router DHCP/DNS settings to point to AdGuard Home server addresses.

#### Grafana Monitoring Stack

Provides:
- **Grafana**: Web dashboard (port 3000/3010)
- **Telegraf**: Metrics collection from Docker host
- **InfluxDB**: Time-series database (port 8086)
  - Default database: `telegraf`
  - Default username: `telegrafuser`
  - Default password: `MyStrongTelegrafPassword`
- **Promtail**: Log shipper
- **Loki**: Log aggregation (port 3100, localhost only)

**Interrogate InfluxDB**:
```bash
docker exec -it influxdb influx -username <username> -password <password>
USE telegraf
SHOW MEASUREMENTS
```

**Dashboard**: Import `Grafana_Dashboard_Template.json` in Grafana.

**Auto-Login and Fullscreen Dashboard Setup**:

Configure the server to auto-login on boot and automatically open Grafana in fullscreen:

1. **Configure GDM3 Auto-Login**:
   ```bash
   sudo nano /etc/gdm3/custom.conf
   ```
   Add or update the `[daemon]` section:
   ```ini
   [daemon]
   AutomaticLogin=unarmedpuppy
   AutomaticLoginEnable=true
   ```

2. **Autostart Entry** (already created):
   - Location: `~/.config/autostart/grafana-dashboard.desktop`
   - Launches Firefox in kiosk mode with Grafana dashboard

3. **Startup Script** (backup method):
   - Location: `~/.xprofile`
   - Automatically launches browser on login

4. **Restart GDM**:
   ```bash
   sudo systemctl restart gdm3
   ```
   Or reboot: `sudo reboot`

**Quick Setup Script**:
```bash
# Copy setup script to server
scp -P 4242 scripts/setup-auto-login-grafana.sh unarmedpuppy@192.168.86.47:~/

# Run on server (requires sudo password)
ssh -p 4242 unarmedpuppy@192.168.86.47 "sudo bash ~/setup-auto-login-grafana.sh"
```

**Manual Browser Launch** (for testing):
```bash
firefox -kiosk http://192.168.86.47:3010/
```

**Disable Auto-Login**:
Edit `/etc/gdm3/custom.conf` and comment out or remove the `AutomaticLogin` lines, then restart GDM.

For detailed setup instructions, see [AUTO_LOGIN_GRAFANA_SETUP.md](./agents/reference/setup/AUTO_LOGIN_GRAFANA_SETUP.md).

#### Game Servers

**Rust Server**:
- Server Banner: [1024x512](https://i.imgur.com/FIXxuRI.jpg)
- RCON Access: http://192.168.86.47:8080/#/192.168.86.47:28016/playerlist

**Minecraft Bedrock Server**:
- Copy world from PC:
  ```bash
  scp -P 4242 -r ~/Desktop/server/minecraft/gumberlund unarmedpuppy@192.168.86.47:~/server/apps/minecraft/gumberlund
  ```
- Server commands:
  ```bash
  docker exec minecraft-bedrock-1 send-command op unarmedpupy
  ```
- Player XUID: `2535454866260420`

**Bedrock Viz** (Minecraft Map Visualization):
- Generate map on PC:
  ```bash
  bedrock-viz.exe --db C:\Users\micro\Desktop\server\minecraft\gumberlund --out ./map --html-most
  ```
- Copy to server:
  ```bash
  scp -P 4242 -r ~/Desktop/server/minecraft/map unarmedpuppy@192.168.86.47:~/server/apps/bedrock-viz/data/output
  ```
- Build from source: [Bedrock Viz Build Guide](https://github.com/bedrock-viz/bedrock-viz/blob/master/docs/BUILD.md)
  ```bash
  sudo apt install cmake libpng++-dev zlib1g-dev libboost-program-options-dev build-essential
  ```
- Generate map on server:
  ```bash
  ./bedrock-viz --db ~/server/apps/minecraft/backup-gumberlund --cfg ~/server/apps/bedrock-viz/repo/data/bedrock_viz.cfg --xml ~/server/apps/bedrock-viz/repo/data/bedrock_viz.xml --html-all
  ```

**Libreddit**:
- JavaScript snippet to extract all subscribed subreddits:
  ```javascript
  var items = ''
  document.querySelectorAll('left-nav-community-item').forEach(function (el){
    items = items + el.getAttribute('prefixedname') + "+"
  });
  ```

### Additional Tools

#### Node.js Installation
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

#### Immich CLI
```bash
sudo npm i -g @immich/cli
```

---

## System Maintenance

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

## Useful Commands

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

## Development Workflow

### Workspace Automations

The [Run on Save](https://marketplace.visualstudio.com/items?itemName=emeraldwalk.RunOnSave) extension is enabled in this repository. Settings are in `.vscode/settings.json`.

**How it works**: When a file is saved in this workspace, the bash script `scripts/git-server-sync.sh` executes. This will:
1. Pull latest changes
2. Add all changed files to a new commit
3. Push to remote repository
4. SSH into the home server and run the same git operations

This effectively syncs any changes made locally to the server automatically.

### Repository Structure

- **Root**: `/Users/joshuajenquist/repos/personal/home-server` (local)
- **Server**: `~/server` (usually `/home/unarmedpuppy/server`)

### Git Sync Script

The `scripts/git-server-sync.sh` script handles automatic synchronization between local repository and server.

---

## Additional Notes

### Router Configuration

- Router: Google Home
- Port forwarding configured for external services (game servers)
- DNS settings configured for AdGuard Home

### Deprecated Services

- **Caddy**: Previously used reverse proxy, now replaced by Traefik
- **Pihole**: Replaced by AdGuard Home
- **Nextcloud**: Moved to inactive (reverse proxy issues)

### Reference Links

- [Vaultwarden Issue #5069](https://github.com/dani-garcia/vaultwarden/issues/5069)
- [Nextcloud Reverse Proxy Guide](https://github.com/nextcloud/all-in-one/blob/main/reverse-proxy.md)

---

## Troubleshooting

### Common Issues

1. **Services not accessible**: Check Traefik labels and network configuration
2. **Port conflicts**: Use `netstat -tulpn | grep <port>` to check port usage
3. **File permissions**: Ensure directories are owned by `1000:1000` (PUID/PGID)
4. **Docker network issues**: Verify `my-network` exists and services are connected
5. **ZFS mount issues**: Run `sudo zfs load-key -a && sudo zfs mount -a`

### Log Locations

- **System logs**: `journalctl`
- **Traefik logs**: `~/server/apps/traefik/logs/`
- **Docker logs**: `docker logs <container_name>`

---

**Last Updated**: See git history for latest changes
**Server**: 192.168.86.47 (unarmedpuppy@home-server)
