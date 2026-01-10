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
- **claude-deploy** - Restricted service account for Claude Harness deployments (see [Claude Deploy User](#claude-deploy-user))
- **github-deploy** - Restricted service account for GitHub Actions CI/CD deployments (see [GitHub Deploy User](#github-deploy-user))
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

### GPU

- **Model**: NVIDIA GeForce RTX 3070
- **VRAM**: 8GB GDDR6
- **PCIe**: Slot 07:00.0 (external vertical rack mount via PCIe 4.0 x16 riser)
- **Use Case**: Local AI inference (vLLM), hardware transcoding

**Mount Configuration**:
- **Type**: External vertical rack mount (GPU mounted above server on dedicated 1U shelf)
- **Shelf**: StarTech.com CABSHELF116V (1U, 16" deep, vented, 44lb capacity)
- **Bracket**: NZXT Vertical GPU Mounting Kit (AB-RH175-B1) on steel L-brackets
- **Riser**: GLOTRENDS 400mm PCIe 4.0 x16 riser cable
- **Orientation**: Vertical, fans facing outward for optimal airflow
- **Serviceability**: Server remains fully removable - GPU mount is attached to rack shelf, not server chassis

**Previous GPU** (Removed):
- ~~GT 1030~~ - Removed during RTX 3070 installation

**Driver Info**:
```bash
nvidia-smi
# Driver: 535.247.01
# CUDA: 12.2
```

**Maintenance Log**:
| Date | Action | Command/Notes |
|------|--------|---------------|
| 2025-12-30 | Installed RTX 3070 in external rack mount | Completed rack mount project per `agents/plans/gpu-rack-mount-3070.md` |
| 2025-12-30 | Removed GT 1030 | No longer needed with RTX 3070 |
| 2025-12-30 | Installed NVIDIA driver 535.247.01 + CUDA 12.2 | `sudo apt install -y nvidia-driver && sudo reboot` |
| 2025-12-30 | Installed nvidia-container-toolkit | Docker GPU support for containers |

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

#### Claude Deploy User

Restricted service account for Claude Harness container to deploy code changes via SSH.

**Purpose**: Allows the Claude Harness container to SSH into the server for git operations and docker commands without using the main user account.

**Created**: 2025-01-02

**Complete Setup** (run all commands on server):

```bash
# 1. Create user with bash shell
sudo useradd -m -s /bin/bash claude-deploy

# 2. Get the container's SSH public key (container must be running)
docker exec -u appuser claude-harness cat /home/appuser/.ssh/id_ed25519.pub
# Copy the output (starts with ssh-ed25519...)

# 3. Set up SSH authorized_keys
sudo mkdir -p /home/claude-deploy/.ssh
echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIH9qRw+hzNh8GVFv3Ec89mQh4n247nvSoJBhWkUpknob claude-harness@container' | sudo tee /home/claude-deploy/.ssh/authorized_keys
sudo chmod 700 /home/claude-deploy/.ssh
sudo chmod 600 /home/claude-deploy/.ssh/authorized_keys
sudo chown -R claude-deploy:claude-deploy /home/claude-deploy/.ssh

# 4. Unlock account (required - new users are locked by default)
# Sets a locked password that allows SSH key auth but blocks password login
sudo usermod -p '*' claude-deploy

# 5. Set up restricted sudo access (NOT docker group - see Security Hardening below)
# This is done via /etc/sudoers.d/claude-deploy - see "Claude Deploy Security Hardening" section
```

**Verify Setup**:
```bash
# Test SSH from container to server (must use -u appuser)
docker exec -u appuser claude-harness ssh -p 4242 claude-deploy@192.168.86.47 'whoami'
# Should output: claude-deploy

# Test docker access
docker exec -u appuser claude-harness ssh -p 4242 claude-deploy@192.168.86.47 'docker ps --format "{{.Names}}" | head -3'
# Should list running containers
```

**SSH Key**: Auto-generated by Claude Harness container on first boot. Key persists in `claude-ssh` Docker volume.

**Access Scope** (after security hardening):
- SSH key-only authentication (no password login possible)
- Authorized key from Claude Harness container only
- **NOT in docker group** (removed for security)
- Restricted sudo via `/etc/sudoers.d/claude-deploy`:
  - `sudo docker ps/logs/inspect/images/stats` (read-only)
  - `sudo docker start/stop/restart` (manage containers)
  - `sudo docker compose` (only in `/home/unarmedpuppy/server/apps/`)
  - `sudo git` (only in `/home/unarmedpuppy/server`)
- **Blocked**: `docker rm`, `docker rmi`, `docker volume rm`, `docker system prune`

**Groups**: `claude-deploy` (own group only, UID 8002)

**Troubleshooting**:

| Issue | Solution |
|-------|----------|
| `Permission denied (publickey)` | Check: 1) Key in authorized_keys matches container key, 2) Account is unlocked (`sudo usermod -p '*' claude-deploy`) |
| `account is locked` in ssh logs | Run `sudo usermod -p '*' claude-deploy` |
| `Host key verification failed` | Add `-o StrictHostKeyChecking=accept-new` to SSH command |
| `permission denied` for docker | Use `sudo docker ...` (not in docker group) |
| SSH looks in wrong key path | Use `docker exec -u appuser` (not root) |

**Debug Commands**:
```bash
# Check account status
sudo passwd -S claude-deploy  # Should show "P" (password set) not "L" (locked)

# Check SSH logs
sudo journalctl -u ssh --since "5 minutes ago" | grep claude-deploy

# Verbose SSH (shows auth details)
docker exec -u appuser claude-harness ssh -vvv -p 4242 claude-deploy@192.168.86.47 'whoami' 2>&1 | tail -30
```

**Related**:
- Container: `claude-harness` in `apps/homelab-ai/docker-compose.yml`
- SSH volume: `claude-ssh` (persists SSH keys across container restarts)
- Source: `homelab-ai` repo (`claude-harness/` directory)

#### Claude Harness GitHub Access

The claude-harness container can clone, commit, and push to GitHub repositories using a Personal Access Token (PAT).

**Environment Variables** (in `apps/homelab-ai/.env`):
```bash
GITHUB_TOKEN=ghp_xxxxxxxxxxxx  # PAT with repo write access
```

**Docker Compose Config** (already set in `apps/homelab-ai/docker-compose.yml`):
```yaml
environment:
  - GITHUB_TOKEN=${GITHUB_TOKEN:-}
  - GIT_AUTHOR_NAME=Claude Code
  - GIT_AUTHOR_EMAIL=claude@server.unarmedpuppy.com
  - GIT_COMMITTER_NAME=Claude Code
  - GIT_COMMITTER_EMAIL=claude@server.unarmedpuppy.com
```

**First-Time Git Setup** (run once after container starts):
```bash
docker exec -u appuser claude-harness bash -c '
git config --global user.name "Claude Code"
git config --global user.email "claude@server.unarmedpuppy.com"
git config --global credential.helper "!f() { echo username=x-access-token; echo password=\$GITHUB_TOKEN; }; f"
'
```

**Test GitHub Access**:
```bash
# Clone a repo
docker exec -u appuser claude-harness bash -c '
cd /workspace
git clone https://github.com/unarmedpuppy/home-server.git test-repo --depth 1
ls test-repo
'

# Verify push access (creates and removes test file)
docker exec -u appuser claude-harness bash -c '
cd /workspace/test-repo
echo "test" > .test-file
git add .test-file && git commit -m "test: verify push access"
git push origin main
git rm .test-file && git commit -m "chore: cleanup test"
git push origin main
'
```

**Workspace Volume**: Repos cloned to `/workspace` persist in the `claude-workspace` Docker volume.

**PAT Permissions Required**: `repo` scope (full control of private repositories)

#### Claude Deploy Security Hardening

By default, `claude-deploy` in the docker group can run ANY docker command (including destructive ones like `docker system prune -af --volumes`). To lock it down:

**Remove from docker group and add sudoers whitelist:**
```bash
# Remove from docker group
sudo gpasswd -d claude-deploy docker

# Create sudoers file with whitelisted commands
sudo tee /etc/sudoers.d/claude-deploy << 'EOF'
# Claude-deploy - restricted docker access
# Safe read/restart commands only - NO delete operations

# View operations
claude-deploy ALL=(ALL) NOPASSWD: /usr/bin/docker ps *
claude-deploy ALL=(ALL) NOPASSWD: /usr/bin/docker logs *
claude-deploy ALL=(ALL) NOPASSWD: /usr/bin/docker inspect *
claude-deploy ALL=(ALL) NOPASSWD: /usr/bin/docker images
claude-deploy ALL=(ALL) NOPASSWD: /usr/bin/docker stats *

# Restart operations (safe)
claude-deploy ALL=(ALL) NOPASSWD: /usr/bin/docker restart *
claude-deploy ALL=(ALL) NOPASSWD: /usr/bin/docker start *
claude-deploy ALL=(ALL) NOPASSWD: /usr/bin/docker stop *

# Compose operations (in server directory only)
claude-deploy ALL=(ALL) NOPASSWD: /usr/bin/docker compose -f /home/unarmedpuppy/server/apps/*/docker-compose.yml *

# Git operations (for deployments)
claude-deploy ALL=(ALL) NOPASSWD: /usr/bin/git -C /home/unarmedpuppy/server *
EOF

# Validate sudoers syntax
sudo visudo -cf /etc/sudoers.d/claude-deploy
```

**After hardening**, SSH commands from container require `sudo`:
```bash
# Commands now require sudo prefix
sudo docker ps
sudo docker restart claude-harness
sudo docker compose -f /home/unarmedpuppy/server/apps/homelab-ai/docker-compose.yml up -d
```

**What's blocked** (no sudo entry = denied):
- `docker rm` - can't delete containers
- `docker rmi` - can't delete images
- `docker volume rm` - can't delete volumes
- `docker system prune` - can't wipe everything

#### GitHub Deploy User

Restricted service account for GitHub Actions CI/CD to deploy code changes via SSH on tag push.

**Purpose**: Allows GitHub Actions workflows to SSH into the server for git pull and docker compose operations without exposing the main user account.

**Created**: 2025-01-02

**Complete Setup** (run all commands on server):

```bash
# 1. Create user with bash shell
sudo useradd -m -s /bin/bash github-deploy

# 2. Set up SSH directory with public key
sudo mkdir -p /home/github-deploy/.ssh
echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBj72n4xRrLNU4mNNao+jNip11q/NbwbH1imNkhzT8qX github-actions-deploy' | sudo tee /home/github-deploy/.ssh/authorized_keys
sudo chmod 700 /home/github-deploy/.ssh
sudo chmod 600 /home/github-deploy/.ssh/authorized_keys
sudo chown -R github-deploy:github-deploy /home/github-deploy/.ssh

# 3. Unlock account (required - new users are locked by default)
sudo usermod -p '*' github-deploy

# 4. Set up restricted sudo access
sudo tee /etc/sudoers.d/github-deploy << 'EOF'
github-deploy ALL=(ALL) NOPASSWD: /usr/bin/docker compose *
github-deploy ALL=(ALL) NOPASSWD: /usr/bin/docker pull *
github-deploy ALL=(ALL) NOPASSWD: /usr/bin/docker image prune -f
github-deploy ALL=(ALL) NOPASSWD: /usr/bin/git *
EOF

# 5. Validate sudoers syntax
sudo visudo -cf /etc/sudoers.d/github-deploy

# 6. Grant access to server directory
sudo usermod -aG unarmedpuppy github-deploy

# 7. Fix directory permissions for github-deploy access
chmod 711 /home/unarmedpuppy
chmod -R g+rX /home/unarmedpuppy/server
```

**Verify Setup**:
```bash
# Test SSH from local machine (private key at ~/.ssh/github-deploy-key)
ssh -p 4242 -i ~/.ssh/github-deploy-key github-deploy@192.168.86.47 'whoami'
# Should output: github-deploy

# Test docker access
ssh -p 4242 -i ~/.ssh/github-deploy-key github-deploy@192.168.86.47 'sudo docker ps --format "{{.Names}}" | head -3'
```

**SSH Key**: Private key stored locally at `~/.ssh/github-deploy-key`. Public key added to server authorized_keys.

**GitHub Secrets Required** (in each repo using auto-deploy):
| Secret | Value |
|--------|-------|
| `DEPLOY_HOST` | `73.94.229.18` (external IP) |
| `DEPLOY_PORT` | `4242` |
| `DEPLOY_USER` | `github-deploy` |
| `DEPLOY_SSH_KEY` | Contents of `~/.ssh/github-deploy-key` |

**Access Scope**:
- SSH key-only authentication (no password login possible)
- **NOT in docker group** (uses sudo whitelist)
- Restricted sudo via `/etc/sudoers.d/github-deploy`:
  - `sudo docker compose *` (full compose control)
  - `sudo docker pull *` (pull images)
  - `sudo docker image prune -f` (cleanup)
  - `sudo git -C /home/unarmedpuppy/server *` (git in server dir)
- **Blocked**: `docker rm`, `docker rmi`, `docker volume rm`, `docker system prune`

**Troubleshooting**:

| Issue | Solution |
|-------|----------|
| `Permission denied (publickey)` | Check: 1) Key in authorized_keys matches, 2) Account is unlocked (`sudo usermod -p '*' github-deploy`) |
| `Connection refused` | Ensure port 4242 is forwarded on router to 192.168.86.47:4242 |
| `permission denied` for docker | Use `sudo docker ...` (not in docker group) |

**Related**:
- Skill: `agents/skills/github-actions-auto-deploy/` (in shared agents repo)
- Example workflow: `agent-gateway/.github/workflows/build-and-push.yml`

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

### Cloud Backup with Backblaze B2

The ZFS pool (`jenquist-cloud`) is backed up to Backblaze B2 cloud storage using rclone. This provides offsite disaster recovery in case of hardware failure, fire, theft, or other catastrophic events.

**All backups are encrypted client-side** using rclone crypt before upload. Backblaze cannot see your files.

#### Overview

| Component | Details |
|-----------|---------|
| **Provider** | Backblaze B2 Cloud Storage |
| **Bucket** | `jenquist-cloud` |
| **Source** | `/jenquist-cloud` (entire ZFS pool) |
| **Tool** | rclone with crypt encryption |
| **Encryption** | AES-256 (files) + EME (filenames) |
| **Schedule** | Daily at 3:00 AM |
| **Cost** | ~$6/TB/month storage, $0.01/GB download |

#### Encryption Details

- **Algorithm**: AES-256 in CTR mode with HMAC-SHA256 authentication
- **Filename encryption**: EME wide-block encryption (filenames are unreadable in B2)
- **Directory encryption**: Enabled (directory names also encrypted)
- **Password**: Stored in 1Password - **REQUIRED FOR RECOVERY**

**WARNING**: If you lose the encryption password, your backup is permanently unrecoverable. Backblaze cannot help you - they only see encrypted blobs.

#### Configuration

**rclone config location**: `~/.config/rclone/rclone.conf`

```ini
[b2]
type = b2
account = <keyID>
key = <applicationKey>

[b2-encrypted]
type = crypt
remote = b2:jenquist-cloud
password = <obscured-password>
filename_encryption = standard
directory_name_encryption = true
```

**Cron job** (user crontab):
```
30 5 * * * /home/unarmedpuppy/server/scripts/backup-to-b2.sh >> /home/unarmedpuppy/server/logs/backups/cron.log 2>&1
```

> **TEMPORARY (Jan 2026)**: Schedule changed from 1:00 AM to 5:30 AM to allow initial B2 sync to complete. The server restarts at 5:00 AM daily, which was terminating backups after only 4 hours. Running at 5:30 AM gives ~23.5 hours per day. **Revert to `0 1 * * *` once initial sync completes.**

#### Usage

**Run manual backup:**
```bash
bash ~/server/scripts/backup-to-b2.sh
```

**Dry-run (preview what would be uploaded):**
```bash
bash ~/server/scripts/backup-to-b2.sh --dry-run
```

**Check B2 bucket size:**
```bash
rclone size b2-encrypted:
```

**List files in B2 (decrypted view):**
```bash
rclone ls b2-encrypted:
```

**Restore a file from B2:**
```bash
# Single file
rclone copy b2-encrypted:path/to/file.txt /local/destination/

# Entire directory
rclone copy b2-encrypted:some-folder /local/destination/
```

**Full restore (disaster recovery):**
```bash
# Restore entire archive to new ZFS pool
rclone sync b2-encrypted: /jenquist-cloud/archive --progress
```

**View raw encrypted files (what Backblaze sees):**
```bash
rclone ls b2:jenquist-cloud  # Shows encrypted filenames
```

#### Backup Script Details

**Location**: `scripts/backup-to-b2.sh`

The script:
- Uses `rclone sync` to mirror local files to B2
- Runs with 4 parallel transfers and 8 checkers for performance
- Logs to `~/server/logs/backups/backup-YYYYMMDD-HHMMSS.log`
- Automatically cleans up logs older than 30 backups
- Supports `--dry-run` flag for testing

#### Monitoring

**Check backup logs:**
```bash
# Latest backup log
ls -lt ~/server/logs/backups/backup-*.log | head -1 | xargs cat

# Cron execution log
tail -100 ~/server/logs/backups/cron.log
```

**Check last backup time:**
```bash
ls -lt ~/server/logs/backups/backup-*.log | head -1
```

**Verify B2 credentials are working:**
```bash
rclone lsd b2:
```

#### Backblaze B2 Web Console

- **Login**: https://secure.backblaze.com/b2_buckets.htm
- **Bucket**: `jenquist-cloud`
- **Application Keys**: Account → Application Keys

#### Cost Estimation

| Data Size | Monthly Storage | Download (full restore) |
|-----------|-----------------|------------------------|
| 1 TB | $6 | $10 |
| 5 TB | $30 | $50 |
| 10 TB | $60 | $100 |
| 27 TB | $162 | $270 |

**Note**: First 1GB download per day is free. Uploads are always free.

#### Disaster Recovery (New Machine)

If you need to restore to a completely new server:

1. **Install rclone**: `sudo apt install rclone`

2. **Create config with encryption password**:
   ```bash
   mkdir -p ~/.config/rclone
   # Get password from 1Password, then:
   rclone obscure "YOUR-PASSWORD-HERE"
   # Copy the obscured output
   ```

3. **Create rclone.conf**:
   ```ini
   [b2]
   type = b2
   account = <keyID from Backblaze>
   key = <applicationKey from Backblaze>

   [b2-encrypted]
   type = crypt
   remote = b2:jenquist-cloud
   password = <obscured-password-from-step-2>
   filename_encryption = standard
   directory_name_encryption = true
   ```

4. **Restore data**:
   ```bash
   rclone sync b2-encrypted: /jenquist-cloud/archive --progress
   ```

#### Troubleshooting

**Backup failed with "no space left on device":**
- Check local disk space: `df -h /`
- rclone needs temp space for checksums

**Authentication error:**
- Verify credentials: `rclone config show b2`
- Regenerate application key in B2 console if needed

**Slow uploads:**
- Check internet upload speed
- Adjust `--transfers` in backup script (default: 4)

**Check what would be transferred:**
```bash
rclone sync /jenquist-cloud/archive b2:jenquist-cloud/archive --dry-run -v
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

# Docker network to host services (for containers reaching systemd services)
sudo ufw allow from 192.168.160.0/20 to any port 8013 proto tcp  # Claude Harness (my-network)
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

#### SSH Intrusion Prevention (fail2ban)

fail2ban is installed and configured to protect SSH from brute force attacks.

**Status**: ✅ Active (configured 2025-01-02)

**Configuration** (`/etc/fail2ban/jail.local`):
- **Port**: 4242
- **Max retries**: 3 attempts
- **Ban time**: 24 hours
- **Find time**: 10 minutes
- **Backend**: systemd journal

**Useful Commands**:
```bash
sudo fail2ban-client status           # Check overall status
sudo fail2ban-client status sshd      # Check SSH jail
sudo fail2ban-client set sshd unbanip <IP>  # Unban an IP
sudo fail2ban-client set sshd banip <IP>    # Ban an IP manually
sudo tail -f /var/log/fail2ban.log    # View logs
```

**Setup Script**: `scripts/setup-fail2ban.sh`

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

Automated maintenance runs weekly via `scripts/docker-maintenance.sh`. The script:
- Removes stopped containers (orphans from deleted apps)
- Removes unused images
- Removes unused networks
- Cleans build cache
- Does NOT prune volumes (too risky for data loss)

**Manual Commands**:
```bash
# Run maintenance script manually
bash ~/server/scripts/docker-maintenance.sh

# View reclaimable space
docker system df

# Prune unused volumes (use with caution!)
docker volume prune
```

**Cron Job** (user crontab, runs Monday 5:00 AM):
```
0 5 * * 1 ~/server/scripts/docker-maintenance.sh >> ~/server/logs/docker-maintenance.log 2>&1
```

### System Tuning

**inotify Limits** (required for apps like slskd that watch many files):

Config file: `/etc/sysctl.d/99-inotify.conf`
```
fs.inotify.max_user_instances = 512
fs.inotify.max_user_watches = 524288
```

To apply after creating/updating the config:
```bash
sudo cp ~/server/scripts/sysctl.d/99-inotify.conf /etc/sysctl.d/
sudo sysctl -p /etc/sysctl.d/99-inotify.conf
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

#### OpenCode Terminal (ttyd + tmux)

Persistent web-based terminal accessible via browser or SSH. Survives daily 5am restarts.

**Access**:
- **Browser**: https://terminal.server.unarmedpuppy.com (basic auth required externally, no auth on LAN)
- **SSH**: `ssh -p 4242 unarmedpuppy@192.168.86.47` then `tmux attach -t opencode`

**Systemd Services** (installed on server, not Docker):
- `opencode-tmux.service` - Maintains persistent tmux session named `opencode`
- `opencode-ttyd.service` - Web terminal on port 7681, attaches to tmux session

**Service Files**:
- `/etc/systemd/system/opencode-tmux.service`
- `/etc/systemd/system/opencode-ttyd.service`

**Installed Packages**:
- `tmux` (via apt)
- `ttyd` v1.7.7 (installed to `/usr/local/bin/ttyd` from GitHub releases)
- `python3-pip` (via apt: `sudo apt-get install python3-pip`) - for Python package management

**Management Commands**:
```bash
sudo systemctl status opencode-tmux.service
sudo systemctl status opencode-ttyd.service
sudo systemctl restart opencode-tmux.service opencode-ttyd.service
tmux list-sessions
```

**Routing**: Traefik file-based config in `apps/traefik/fileConfig.yml` (not Docker labels, since ttyd runs as systemd service).

#### Claude Harness (Claude Max API)

OpenAI-compatible API wrapper for Claude Code CLI. Enables the Local AI Router to use Claude models via Claude Max subscription without API keys.

**Access**:
- **Local**: `http://localhost:8013`
- **Via Router**: `http://localhost:8012/v1/chat/completions` with `model: "claude-sonnet"`

**Systemd Service** (installed on server, not Docker):
- `claude-harness.service` - FastAPI service wrapping Claude Code CLI

**Service File**:
- `/etc/systemd/system/claude-harness.service`

**Installed Dependencies**:
- `@anthropic-ai/claude-code` (via npm: `sudo npm install -g @anthropic-ai/claude-code`)
- Python packages: `uvicorn`, `fastapi`, `pydantic` (system packages via apt)

**Management** (use the management script):
```bash
cd ~/server/apps/claude-harness
./manage.sh status              # Check service status and health
./manage.sh logs 50             # View last 50 log lines
./manage.sh test                # Run health check and test completion
sudo ./manage.sh restart        # Restart service
sudo ./manage.sh update         # Update after git pull
```

**Authentication**: Claude Code uses OAuth tokens stored in `~/.claude.json`. Re-authenticate by running `claude` interactively if tokens expire (~30 days).

**Documentation**: [apps/claude-harness/README.md](./apps/claude-harness/README.md)

### Non-Docker Services Summary

Services running as systemd units (not in Docker containers):

| Service | Port | Purpose | Management |
|---------|------|---------|------------|
| `opencode-tmux.service` | - | Persistent tmux session | `systemctl status opencode-tmux` |
| `opencode-ttyd.service` | 7681 | Web terminal | `systemctl status opencode-ttyd` |
| `claude-harness.service` | 8013 | Claude Max API | `./manage.sh status` |

**Why not Docker?** These services need access to host resources (tmux sessions, OAuth tokens in `~/.claude.json`) that are simpler to manage via systemd than Docker volume mounts.

#### Gitea (Self-Hosted Git)

Self-hosted Git service with pull mirrors from GitHub for backup and offline access.

**Access**:
- **Web**: https://gitea.server.unarmedpuppy.com
- **SSH**: `ssh://git@gitea.server.unarmedpuppy.com:2223`
- **Ports**: 3007 (web), 2223 (SSH)

**Purpose**:
- Backup of all GitHub repositories (19 repos mirrored)
- Offline access to code when internet is down
- Future: Local CI/CD alternative to GitHub Actions

**Mirror Configuration**:
- Pull mirrors sync every 8 hours from GitHub
- Uses GitHub PAT for authentication
- Mirrors are read-only (push to GitHub, not Gitea)

**Management Commands**:
```bash
# Check status
docker ps | grep gitea

# View logs
docker logs gitea --tail 50

# Trigger manual sync for a repo
curl -X POST "https://gitea.server.unarmedpuppy.com/api/v1/repos/unarmedpuppy/REPO_NAME/mirror-sync" \
  -H "Authorization: token YOUR_GITEA_TOKEN"
```

**Setup New Mirrors**:
```bash
# Bulk setup (all repos)
bash scripts/setup-gitea-mirrors.sh

# Single repo - see agents/skills/add-gitea-mirror/SKILL.md
```

**Documentation**:
- App README: [apps/gitea/README.md](./apps/gitea/README.md)
- Mirror Skill: [agents/skills/add-gitea-mirror/SKILL.md](./agents/skills/add-gitea-mirror/SKILL.md)
- Agent Persona: [agents/personas/gitea-agent.md](./agents/personas/gitea-agent.md)

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

#### rclone (Cloud Backup)
```bash
sudo apt update && sudo apt install rclone
```
Used for syncing backups to Backblaze B2 cloud storage. Configuration stored in `~/.config/rclone/rclone.conf`.

#### Node.js Installation
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

#### Immich CLI
```bash
sudo npm i -g @immich/cli
```

#### Claude Code CLI
```bash
sudo npm install -g @anthropic-ai/claude-code
```
Used by Claude Harness service. Requires one-time OAuth authentication:
```bash
claude  # Follow URL to authenticate with Claude Max account
```
Tokens stored in `~/.claude.json`.

### Server Dependencies Summary

Packages installed directly on server (needed for bare metal restore):

**Via apt:**
```bash
sudo apt install -y \
  python3-pip \
  tmux \
  rclone \
  lm-sensors \
  fancontrol
```

**Via npm (global):**
```bash
sudo npm install -g @anthropic-ai/claude-code @immich/cli
```

**Via pip (system packages, already installed):**
- `uvicorn` - ASGI server (in `/usr/lib/python3/dist-packages`)
- `fastapi` - Web framework
- `pydantic` - Data validation

**Manual installs:**
- `ttyd` v1.7.7 - Installed to `/usr/local/bin/ttyd` from [GitHub releases](https://github.com/tsl0922/ttyd/releases)

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

**Docker Maintenance** (Weekly, Monday at 5:00 AM):
```
0 5 * * 1 ~/server/scripts/docker-maintenance.sh >> ~/server/logs/docker-maintenance.log 2>&1
```
Prunes stopped containers, unused images, networks, and build cache. See [Docker Maintenance](#docker-maintenance) for details.

**Restart Machine** (Nightly at 5:15 AM):
```
15 5 * * * /sbin/reboot
```

**Plex Cleanup** (Daily at 3:30 AM):
```
30 3 * * * /home/unarmedpuppy/server/scripts/plex-cleanup-cron.sh
```
Auto-deletes watched TV episodes based on Sonarr's `auto-delete` tag. See [agents/reference/plex-cleanup.md](agents/reference/plex-cleanup.md) for details.

**Bird Bookmark Processor** (Every 6 hours):
```
0 */6 * * * /home/unarmedpuppy/server/scripts/bird-cron.sh
```
Fetches X/Twitter bookmarks and likes, stores in SQLite database. See [apps/bird/README.md](apps/bird/README.md) for details.

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

### Custom App Deployment (Watchtower)

**Custom apps (in `homelab/` org repos) deploy automatically via Watchtower.** No SSH required.

```
git tag v1.0.x → push → Gitea Actions builds → Harbor (:latest) → Watchtower auto-deploys (~1 min)
```

**How it works:**
1. Push a tag to app repo (e.g., `git tag v1.0.5 && git push origin v1.0.5`)
2. Gitea Actions builds the Docker image and pushes to Harbor (version tag + `:latest`)
3. Watchtower (running on server) polls Harbor every 60 seconds
4. When it detects a new `:latest` digest, it automatically pulls and restarts the container

**Watched containers** have this label in their docker-compose.yml:
```yaml
labels:
  - "com.centurylinklabs.watchtower.enable=true"
```

See `docs/WATCHTOWER_DEPLOYMENT_PLAN.md` for complete documentation.

### Docker-Compose Changes

For config changes (new env vars, ports, volumes), SSH is still required:
```bash
ssh unarmedpuppy@192.168.86.47 -p 4242
cd ~/server/apps/<app>
git pull
docker compose up -d
```

### Workspace Automations (home-server repo)

The [Run on Save](https://marketplace.visualstudio.com/items?itemName=emeraldwalk.RunOnSave) extension is enabled in this repository. Settings are in `.vscode/settings.json`.

**How it works**: When a file is saved in this workspace, the bash script `scripts/git-server-sync.sh` executes. This will:
1. Pull latest changes
2. Add all changed files to a new commit
3. Push to remote repository
4. SSH into the home server and run the same git operations

This syncs docker-compose.yml changes to the server automatically.

### Repository Structure

- **Root**: `/Users/joshuajenquist/repos/personal/homelab/home-server` (local)
- **Server**: `~/server` (usually `/home/unarmedpuppy/server`)

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
