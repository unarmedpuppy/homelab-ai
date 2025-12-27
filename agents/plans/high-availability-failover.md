# High Availability: Hot Standby with Failover

**Status**: Planning
**Beads Epic**: `home-server-do8`
**Goal**: Automatic failover to secondary server within minutes of primary failure

## Overview

Run a secondary server with **essential services only**, ready to take over automatically when the primary fails. Non-essential services (media, monitoring, etc.) remain offline until primary recovers.

### Key Design Decisions

1. **Essential services only** - Reduces secondary hardware requirements
2. **Data sync from B2** - Not real-time ZFS replication (simpler, cheaper)
3. **`x-essential: true`** - Docker Compose flag marks services for failover
4. **Acceptable RPO** - Recovery Point Objective is last B2 backup (~24h max)

## Architecture

```
                         ┌─────────────────┐
                         │   Cloudflare    │
                         │   (DNS/Proxy)   │
                         └────────┬────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │      Virtual IP           │
                    │   192.168.86.100 (VIP)    │
                    │     (via Keepalived)      │
                    └─────────────┬─────────────┘
                                  │
              ┌───────────────────┴───────────────────┐
              │                                       │
     ┌────────┴────────┐                   ┌─────────┴────────┐
     │   PRIMARY       │                   │   SECONDARY      │
     │ 192.168.86.47   │                   │  192.168.86.48   │
     │                 │     B2 Backup     │                  │
     │  ┌───────────┐  │ ═══════════════►  │  ┌───────────┐   │
     │  │ ALL APPS  │  │  (daily sync)     │  │ ESSENTIAL │   │
     │  │  50+ svcs │  │                   │  │  ~10 svcs │   │
     │  │  ZFS Pool │  │                   │  │  SSD only │   │
     │  └───────────┘  │                   │  └───────────┘   │
     │                 │                   │                  │
     │  MASTER state   │                   │  BACKUP state    │
     └─────────────────┘                   └──────────────────┘
```

---

## Essential Services

Services marked with `x-essential: true` run on failover. All others wait for primary recovery.

### Proposed Essential Services

| Service | Why Essential | Data Needs |
|---------|---------------|------------|
| **traefik** | Reverse proxy for all services | Certs (in git) |
| **cloudflare-ddns** | DNS updates for domain | None |
| **adguard** | DNS for home network | Config (small) |
| **homepage** | Dashboard/status page | Config (in git) |
| **wireguard** | VPN access | Config (small) |
| **vaultwarden** | Password manager | DB (~50MB) |
| **authelia** | SSO/2FA | DB (small) |
| **n8n** | Automation workflows | DB, workflows |
| **homeassistant** | Smart home control | DB, config |
| **frigate** | Security cameras | Config only (no recordings) |

### Non-Essential (Stay Offline)

| Service | Why Not Essential |
|---------|-------------------|
| plex, jellyfin | Media streaming can wait |
| sonarr, radarr, etc. | Media automation can wait |
| paperless | Document management can wait |
| grafana, prometheus | Monitoring secondary is overkill |
| harbor | Registry not needed on secondary |
| polymarket-bot | Trading can pause |
| ollama, local-ai | AI inference can wait |

### Docker Compose Flag

```yaml
# apps/vaultwarden/docker-compose.yml
services:
  vaultwarden:
    image: vaultwarden/server:latest
    x-essential: true  # <-- Included in failover
    # ... rest of config
```

### Failover Script Reads Flag

```bash
#!/bin/bash
# scripts/start-essential-services.sh

cd /home/unarmedpuppy/server

for compose in apps/*/docker-compose.yml; do
    # Check for x-essential: true
    if grep -q "x-essential: true" "$compose"; then
        echo "Starting essential service: $(dirname $compose)"
        docker compose -f "$compose" up -d
    fi
done
```

## Components

### 1. Keepalived (Virtual IP Failover)

Manages a floating virtual IP that moves between servers:

```
Primary healthy   → VIP on primary (192.168.86.47)
Primary fails     → VIP moves to secondary (192.168.86.48)
Primary recovers  → VIP stays on secondary (manual failback)
```

### 2. Data Sync Strategy

**Not real-time ZFS replication** - Instead, use existing B2 backup:

```
Primary → B2 (daily backup) → Secondary (on-demand restore)
```

#### Essential Data Only
Most essential services have minimal data:
- **vaultwarden**: ~50MB SQLite DB
- **adguard**: Config files only
- **homeassistant**: Config + small DB
- **n8n**: Workflows + DB

#### Sync Options

| Option | RPO | Complexity | When to Use |
|--------|-----|------------|-------------|
| **B2 restore on failover** | ~24h | Low | Default |
| **Daily rclone to secondary** | ~24h | Low | Pre-staged data |
| **Hourly rclone critical DBs** | ~1h | Medium | If needed |

#### Pre-Staged Essential Data

```bash
# Daily cron on secondary - sync essential data only
0 4 * * * rclone sync b2-encrypted:vault/essential /data/essential
```

### 3. Docker Service Sync

Secondary pre-pulls essential images only:
- Git pull for configs (daily cron)
- `docker compose pull` for essential services
- Services start on failover via `start-essential-services.sh`

### 4. Cloudflare DNS

External DNS points to your public IP. Cloudflare handles:
- DDoS protection
- SSL termination (optional)
- Health checks (optional upgrade)

---

## Hardware Requirements

Since we only run ~10 essential services (not 50+), requirements are minimal.

### Secondary Server Options

| Option | Specs | Cost | Notes |
|--------|-------|------|-------|
| **Mini PC (recommended)** | Intel N100, 16GB RAM, 256GB NVMe | ~$200 | Perfect for essentials |
| **Raspberry Pi 5** | 8GB RAM, 256GB SD | ~$120 | Minimal power |
| **Old laptop** | Any 8GB+ RAM | $0 | Repurpose existing |
| **Cloud VM** | 2 vCPU, 4GB RAM | ~$20/mo | Off-site redundancy |

### Minimum Requirements
- **RAM**: 8GB (16GB preferred)
- **Storage**: 256GB SSD (essential data only, no media)
- **Network**: Gigabit LAN
- **CPU**: Any x86_64 (arm64 if all images support it)

### Why So Light?
- No media storage (Plex, Sonarr data stays on primary)
- No AI inference (Ollama, local-ai)
- No monitoring stack (Grafana, Prometheus)
- No Harbor registry
- Just core infrastructure + password manager + home automation

---

## Implementation Plan

### Phase 1: Secondary Server Setup

```bash
# 1. Install Ubuntu Server (same version as primary)
# 2. Basic setup
sudo apt update && sudo apt upgrade -y
sudo apt install -y zfsutils-linux docker.io docker-compose-plugin

# 3. Create ZFS pool (mirror of primary)
sudo zpool create jenquist-cloud raidz1 /dev/sda /dev/sdb /dev/sdc /dev/sdd

# 4. Setup SSH keys for replication
ssh-keygen -t ed25519
# Copy public key to primary's authorized_keys
```

### Phase 2: ZFS Replication

#### Initial Full Sync

```bash
# On primary - create snapshot and send
sudo zfs snapshot -r jenquist-cloud@initial
sudo zfs send -R jenquist-cloud@initial | ssh secondary sudo zfs recv -F jenquist-cloud
```

#### Incremental Sync Script

```bash
#!/bin/bash
# scripts/zfs-replicate.sh
# Run every 15 minutes via cron

POOL="jenquist-cloud"
SECONDARY="192.168.86.48"
SNAP_NAME="replicate-$(date +%Y%m%d-%H%M)"

# Create new snapshot
zfs snapshot -r ${POOL}@${SNAP_NAME}

# Get previous snapshot
PREV_SNAP=$(zfs list -t snapshot -o name -s creation ${POOL} | grep replicate | tail -2 | head -1)

if [ -n "$PREV_SNAP" ]; then
    # Incremental send
    zfs send -i ${PREV_SNAP} ${POOL}@${SNAP_NAME} | ssh ${SECONDARY} zfs recv -F ${POOL}
else
    # Full send (first time)
    zfs send -R ${POOL}@${SNAP_NAME} | ssh ${SECONDARY} zfs recv -F ${POOL}
fi

# Cleanup old snapshots (keep last 10)
zfs list -t snapshot -o name ${POOL} | grep replicate | head -n -10 | xargs -r -n1 zfs destroy
```

#### Cron Job

```bash
# /etc/cron.d/zfs-replicate
*/15 * * * * root /home/unarmedpuppy/server/scripts/zfs-replicate.sh >> /var/log/zfs-replicate.log 2>&1
```

### Phase 3: Keepalived Setup

#### Install on Both Servers

```bash
sudo apt install keepalived
```

#### Primary Configuration

```bash
# /etc/keepalived/keepalived.conf (PRIMARY)
global_defs {
    router_id homeserver_primary
}

vrrp_script check_traefik {
    script "/usr/bin/docker inspect -f '{{.State.Running}}' traefik"
    interval 5
    weight -20
    fall 3
    rise 2
}

vrrp_instance VI_1 {
    state MASTER
    interface enp2s0           # Your network interface
    virtual_router_id 51
    priority 100               # Higher = preferred master
    advert_int 1

    authentication {
        auth_type PASS
        auth_pass secretpass   # Same on both servers
    }

    virtual_ipaddress {
        192.168.86.100/24      # The floating VIP
    }

    track_script {
        check_traefik
    }

    notify_master "/home/unarmedpuppy/server/scripts/failover-master.sh"
    notify_backup "/home/unarmedpuppy/server/scripts/failover-backup.sh"
}
```

#### Secondary Configuration

```bash
# /etc/keepalived/keepalived.conf (SECONDARY)
global_defs {
    router_id homeserver_secondary
}

vrrp_script check_traefik {
    script "/usr/bin/docker inspect -f '{{.State.Running}}' traefik"
    interval 5
    weight -20
    fall 3
    rise 2
}

vrrp_instance VI_1 {
    state BACKUP
    interface enp2s0
    virtual_router_id 51
    priority 90                # Lower than primary
    advert_int 1

    authentication {
        auth_type PASS
        auth_pass secretpass
    }

    virtual_ipaddress {
        192.168.86.100/24
    }

    track_script {
        check_traefik
    }

    notify_master "/home/unarmedpuppy/server/scripts/failover-master.sh"
    notify_backup "/home/unarmedpuppy/server/scripts/failover-backup.sh"
}
```

### Phase 4: Failover Scripts

#### Become Master Script

```bash
#!/bin/bash
# scripts/failover-master.sh
# Called when this server becomes MASTER

LOG="/var/log/failover.log"
echo "$(date): Becoming MASTER" >> $LOG

# Start all Docker services
cd /home/unarmedpuppy/server
for compose in apps/*/docker-compose.yml; do
    echo "$(date): Starting $(dirname $compose)" >> $LOG
    docker compose -f "$compose" up -d
done

# Notify (optional - Discord, email, etc.)
# curl -X POST webhook_url -d '{"content": "Failover: Secondary is now MASTER"}'

echo "$(date): MASTER transition complete" >> $LOG
```

#### Become Backup Script

```bash
#!/bin/bash
# scripts/failover-backup.sh
# Called when this server becomes BACKUP

LOG="/var/log/failover.log"
echo "$(date): Becoming BACKUP" >> $LOG

# Stop services to avoid conflicts (except replication receiver)
cd /home/unarmedpuppy/server
for compose in apps/*/docker-compose.yml; do
    echo "$(date): Stopping $(dirname $compose)" >> $LOG
    docker compose -f "$compose" down
done

echo "$(date): BACKUP transition complete" >> $LOG
```

### Phase 5: Docker Sync

#### Git-based Config Sync

```bash
# On secondary - cron job to pull latest configs
*/5 * * * * cd /home/unarmedpuppy/server && git pull origin main
```

#### Pre-pull Images

```bash
#!/bin/bash
# scripts/sync-docker-images.sh
# Run daily on secondary to pre-pull images

cd /home/unarmedpuppy/server

for compose in apps/*/docker-compose.yml; do
    docker compose -f "$compose" pull
done
```

---

## Network Configuration

### Router/DHCP Changes

1. Reserve IPs:
   - Primary: `192.168.86.47`
   - Secondary: `192.168.86.48`
   - VIP: `192.168.86.100`

2. Port forwarding (if applicable):
   - Forward to VIP (`192.168.86.100`), not individual server

### Cloudflare DDNS Update

Update DDNS script to use VIP:

```bash
# The VIP is what gets advertised externally
# Cloudflare points to your public IP
# Internal services use VIP
```

---

## Monitoring

### Health Checks

```yaml
# On both servers - healthcheck container
services:
  healthcheck:
    image: willfarrell/autoheal
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - AUTOHEAL_CONTAINER_LABEL=all
```

### Alerting

```bash
# scripts/check-replication-lag.sh
#!/bin/bash

PRIMARY_SNAP=$(ssh primary "zfs list -t snapshot -o name -s creation jenquist-cloud | tail -1")
SECONDARY_SNAP=$(zfs list -t snapshot -o name -s creation jenquist-cloud | tail -1)

if [ "$PRIMARY_SNAP" != "$SECONDARY_SNAP" ]; then
    # Check if lag is more than 1 hour
    PRIMARY_TIME=$(ssh primary "zfs get -Hp creation $PRIMARY_SNAP | cut -f3")
    SECONDARY_TIME=$(zfs get -Hp creation $SECONDARY_SNAP | cut -f3)
    LAG=$((PRIMARY_TIME - SECONDARY_TIME))

    if [ $LAG -gt 3600 ]; then
        echo "ALERT: Replication lag is ${LAG} seconds"
        # Send notification
    fi
fi
```

---

## Failover Scenarios

| Scenario | Detection | Action | RTO |
|----------|-----------|--------|-----|
| Primary power loss | Keepalived timeout (3s) | VIP moves to secondary | ~30s |
| Traefik crash | Health check fails | VIP moves | ~15s |
| Primary network loss | Keepalived timeout | VIP moves | ~30s |
| ZFS pool failure | Manual detection | Manual failover | Minutes |
| Planned maintenance | Manual `systemctl stop keepalived` | Graceful failover | ~5s |

---

## Cost Estimate

| Item | One-time | Monthly |
|------|----------|---------|
| Secondary server (mini PC) | $300-500 | - |
| Extra drives (4x 8TB) | $400-600 | - |
| Extra UPS | $100-200 | - |
| Power consumption | - | ~$10-20 |
| **Total** | **$800-1300** | **~$15** |

---

## Implementation Tasks

1. Acquire secondary hardware
2. Install Ubuntu Server
3. Setup ZFS pool
4. Configure SSH key auth between servers
5. Implement ZFS replication script
6. Install and configure Keepalived on both
7. Write failover scripts
8. Test failover manually
9. Setup monitoring and alerting
10. Document runbooks

---

## Testing Checklist

- [ ] Pull power on primary → secondary takes over
- [ ] Stop Traefik on primary → secondary takes over
- [ ] Network disconnect primary → secondary takes over
- [ ] Verify data consistency after failover
- [ ] Test failback to primary
- [ ] Verify ZFS replication lag < 15 minutes
- [ ] Load test secondary under production load

---

## Related Documents

- [disaster-recovery-rear-ansible.md](disaster-recovery-rear-ansible.md) - Rebuild from scratch
- [backups.md](../reference/backups.md) - B2 backup configuration
