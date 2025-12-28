# Disaster Recovery: ReaR + Ansible

**Status**: Planning
**Beads Epic**: `home-server-dyn`
**Related**: `home-server-rn2` (original ReaR task)
**Goal**: Rebuild entire server from scratch in <4 hours using bootable ISO + declarative config

## Overview

Two-layer disaster recovery approach:
1. **ReaR** - Bare metal restore (OS, partitions, boot, packages)
2. **Ansible** - Application layer (Docker, services, configs)
3. **rclone** - Data restore from B2

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DISASTER RECOVERY STACK                      │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: DATA                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  B2 Backup (encrypted)                                      ││
│  │  - /jenquist-cloud/archive (media)                          ││
│  │  - /jenquist-cloud/backups (rsnapshot)                      ││
│  │  - /jenquist-cloud/vault (important docs)                   ││
│  │  Restore: rclone sync b2-encrypted: /jenquist-cloud         ││
│  └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: APPLICATIONS                                           │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Ansible Playbook                                           ││
│  │  - Docker CE installation                                   ││
│  │  - ZFS pool creation/import                                 ││
│  │  - User accounts & SSH keys                                 ││
│  │  - Network configuration                                    ││
│  │  - Cron jobs & systemd services                             ││
│  │  - git clone home-server repo                               ││
│  │  - docker compose up for all apps                           ││
│  └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: BARE METAL                                             │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  ReaR (Relax-and-Recover)                                   ││
│  │  - Bootable recovery ISO                                    ││
│  │  - Disk layout (partitions, LVM, ZFS)                       ││
│  │  - Boot configuration (GRUB, EFI)                           ││
│  │  - Base packages                                            ││
│  │  - Network drivers                                          ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Recovery Timeline

| Phase | Duration | Actions |
|-------|----------|---------|
| 1. Boot ReaR | 10 min | Boot from USB/ISO, restore base system |
| 2. Network Up | 5 min | Verify connectivity, SSH access |
| 3. Run Ansible | 30 min | Install Docker, configure ZFS, setup users |
| 4. Clone Repo | 5 min | git clone home-server |
| 5. Start Services | 15 min | docker compose up for critical services |
| 6. Restore Data | 2-4 hours | rclone sync from B2 (bandwidth limited) |
| **Total** | **3-5 hours** | Full recovery |

---

## Phase 1: ReaR Setup

### Installation

```bash
# On server
sudo apt install rear

# Verify
rear --version
```

### Configuration

File: `/etc/rear/local.conf`

```bash
# Output format - create bootable ISO
OUTPUT=ISO

# Backup method - use existing B2 backup (not ReaR's built-in)
BACKUP=NETFS
BACKUP_URL=null  # We use rclone separately

# ISO output location
OUTPUT_URL=file:///jenquist-cloud/backups/rear/

# Include ZFS tools in recovery environment
REQUIRED_PROGS+=( zfs zpool rclone )

# Exclude large data (restored separately)
EXCLUDE_MOUNTPOINTS=( /jenquist-cloud )

# Keep 3 versions
KEEP_OLD_OUTPUT_COPY=3
```

### Generate Recovery ISO

```bash
# Create recovery ISO
sudo rear mkrescue

# Output: /jenquist-cloud/backups/rear/rear-*.iso

# Upload to B2
rclone copy /jenquist-cloud/backups/rear/ b2:jenquist-cloud/disaster-recovery/
```

### Weekly Cron

```bash
# /etc/cron.d/rear-backup
0 2 * * 0 root /usr/sbin/rear mkrescue && rclone copy /jenquist-cloud/backups/rear/ b2:jenquist-cloud/disaster-recovery/
```

---

## Phase 2: Ansible Playbook

### Directory Structure

```
home-server/
└── ansible/
    ├── inventory/
    │   └── hosts.yml
    ├── playbooks/
    │   ├── site.yml           # Main playbook
    │   ├── base.yml           # Base system setup
    │   ├── docker.yml         # Docker installation
    │   ├── zfs.yml            # ZFS pool setup
    │   └── services.yml       # Start Docker services
    ├── roles/
    │   ├── common/            # Users, SSH, packages
    │   ├── docker/            # Docker CE
    │   ├── zfs/               # ZFS utilities
    │   ├── networking/        # Static IP, firewall
    │   └── services/          # Docker compose
    ├── vars/
    │   └── secrets.yml        # Ansible vault encrypted
    └── ansible.cfg
```

### Main Playbook

```yaml
# ansible/playbooks/site.yml
---
- name: Full server recovery
  hosts: homeserver
  become: true

  vars_files:
    - ../vars/secrets.yml

  roles:
    - common        # Users, SSH keys, base packages
    - networking    # Static IP, DNS
    - zfs           # ZFS tools, pool import
    - docker        # Docker CE, docker-compose
    - services      # Clone repo, start containers
```

### Key Tasks

```yaml
# roles/docker/tasks/main.yml
- name: Install Docker prerequisites
  apt:
    name:
      - ca-certificates
      - curl
      - gnupg
    state: present

- name: Add Docker GPG key
  apt_key:
    url: https://download.docker.com/linux/ubuntu/gpg

- name: Add Docker repository
  apt_repository:
    repo: "deb https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} stable"

- name: Install Docker CE
  apt:
    name:
      - docker-ce
      - docker-ce-cli
      - containerd.io
      - docker-compose-plugin
    state: present

- name: Add user to docker group
  user:
    name: unarmedpuppy
    groups: docker
    append: yes
```

```yaml
# roles/services/tasks/main.yml
- name: Clone home-server repo
  git:
    repo: git@github.com:unarmedpuppy/home-server.git
    dest: /home/unarmedpuppy/server
    version: main
  become_user: unarmedpuppy

- name: Start critical services
  community.docker.docker_compose:
    project_src: "/home/unarmedpuppy/server/apps/{{ item }}"
    state: present
  loop:
    - traefik
    - homepage
    - adguard
    - cloudflare-ddns
```

---

## Phase 3: Data Restore

### Restore Script

```bash
#!/bin/bash
# scripts/disaster-restore-data.sh

# Restore from B2 encrypted backup
echo "Starting data restore from B2..."
echo "This will take several hours depending on bandwidth."

# Create mount point if needed
sudo zfs create jenquist-cloud || true

# Restore in priority order
echo "1. Restoring vault (critical docs)..."
rclone sync b2-encrypted:vault /jenquist-cloud/vault --progress

echo "2. Restoring backups (rsnapshot)..."
rclone sync b2-encrypted:backups /jenquist-cloud/backups --progress

echo "3. Restoring archive (media)..."
rclone sync b2-encrypted:archive /jenquist-cloud/archive --progress

echo "Data restore complete!"
```

---

## Recovery Runbook

### Prerequisites
- ReaR recovery USB/ISO (from B2 or local copy)
- Network access to GitHub
- Network access to B2
- rclone config (in B2 or 1Password)

### Step-by-Step Recovery

```bash
# 1. Boot from ReaR USB/ISO
# Select "Recover" from boot menu
# Follow prompts to restore disk layout

# 2. Reboot into restored system
reboot

# 3. Verify network
ip a
ping 8.8.8.8

# 4. Install Ansible (if not in ReaR image)
sudo apt update && sudo apt install -y ansible git

# 5. Clone recovery playbook
git clone https://github.com/unarmedpuppy/home-server.git /tmp/recovery
cd /tmp/recovery/ansible

# 6. Run recovery playbook
ansible-playbook playbooks/site.yml -i inventory/hosts.yml --ask-vault-pass

# 7. Restore rclone config
# Copy from 1Password or B2
mkdir -p ~/.config/rclone
# paste rclone.conf

# 8. Import ZFS pool (if existing drives)
sudo zpool import jenquist-cloud

# OR create new pool and restore data
sudo zpool create jenquist-cloud raidz1 /dev/sda /dev/sdb /dev/sdc /dev/sdd
./scripts/disaster-restore-data.sh

# 9. Start remaining services
cd ~/server
for app in apps/*/docker-compose.yml; do
  docker compose -f "$app" up -d
done

# 10. Verify services
docker ps
curl -I https://homepage.server.unarmedpuppy.com
```

---

## Testing Schedule

| Test | Frequency | Method |
|------|-----------|--------|
| ReaR ISO generation | Weekly (automated) | Cron job |
| Ansible dry-run | Monthly | `--check` mode |
| Full restore test | Annually | VM or spare hardware |
| Data restore sample | Quarterly | Restore single directory |

---

## Files to Create

| File | Purpose |
|------|---------|
| `/etc/rear/local.conf` | ReaR configuration |
| `/etc/cron.d/rear-backup` | Weekly ISO generation |
| `ansible/` | Complete Ansible structure |
| `scripts/disaster-restore-data.sh` | Data restore helper |
| `docs/DISASTER_RECOVERY.md` | Recovery runbook |

---

## Implementation Tasks

1. Install and configure ReaR
2. Generate first recovery ISO
3. Create Ansible playbook structure
4. Write base system role
5. Write Docker role
6. Write ZFS role
7. Write services role
8. Create recovery runbook
9. Test in VM
10. Set up weekly automation

---

## Related Documents

- [backups.md](../reference/backups.md) - B2 backup configuration
- [high-availability-failover.md](high-availability-failover.md) - Hot standby setup
