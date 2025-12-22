# Plan: Persistent OpenCode Development Environment

**Status**: Partially Working - Traefik routing blocked by Docker networking
**Created**: 2025-12-21
**Priority**: P1
**Effort**: Medium

## Objective

Configure a persistent tmux session with ttyd web terminal that:
- Auto-starts on boot (survives daily 5am restarts)
- Provides SSH access for laptop (Ghostty)
- Provides browser access for mobile via existing Traefik reverse proxy

## Architecture Decision: Traefik vs Cloudflare Tunnel

**Current Infrastructure**: Your server uses **Traefik + Cloudflare DDNS** (not cloudflared tunnel).

| Option | Pros | Cons |
|--------|------|------|
| **A. Traefik (Recommended)** | Uses existing infra, consistent with other services, proper auth patterns already in place | None significant |
| B. Cloudflare Tunnel | Zero-trust, no port exposure | Requires new setup, separate auth system |

**Recommendation**: Use Traefik to expose ttyd, following the same pattern as other services.

---

## Pre-Implementation Checklist

Before starting, verify:

```bash
# SSH to server
ssh -p 4242 unarmedpuppy@192.168.86.47

# Check OS and user
cat /etc/os-release
whoami  # Should be: unarmedpuppy

# Check for existing packages
which tmux || echo "tmux not installed"
which ttyd || echo "ttyd not installed"

# Verify systemd
systemctl --version

# Check Traefik is running
docker ps | grep traefik
```

---

## Implementation Tasks

### Task 1: Install Required Packages

**Objective**: Install tmux and ttyd on the server

**Commands** (run on server via SSH):
```bash
sudo apt update && sudo apt install -y tmux

# ttyd may need manual install - check package availability
sudo apt install -y ttyd || {
    # If not in repos, install from GitHub releases
    wget https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.x86_64 -O /tmp/ttyd
    sudo mv /tmp/ttyd /usr/local/bin/ttyd
    sudo chmod +x /usr/local/bin/ttyd
}

# Verify
which tmux && tmux -V
which ttyd && ttyd --version
```

**Success Criteria**:
- [ ] `tmux -V` returns version
- [ ] `ttyd --version` returns version

---

### Task 2: Create tmux Systemd Service

**Objective**: Create systemd service that maintains persistent tmux session

**File**: `/etc/systemd/system/opencode-tmux.service`

```ini
[Unit]
Description=OpenCode tmux session
After=network.target

[Service]
Type=forking
User=unarmedpuppy
ExecStart=/usr/bin/tmux new-session -d -s opencode
ExecStop=/usr/bin/tmux kill-session -t opencode
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Commands**:
```bash
# Create service file
sudo tee /etc/systemd/system/opencode-tmux.service << 'EOF'
[Unit]
Description=OpenCode tmux session
After=network.target

[Service]
Type=forking
User=unarmedpuppy
ExecStart=/usr/bin/tmux new-session -d -s opencode
ExecStop=/usr/bin/tmux kill-session -t opencode
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable opencode-tmux.service
sudo systemctl start opencode-tmux.service

# Verify
sudo systemctl status opencode-tmux.service
tmux list-sessions
```

**Success Criteria**:
- [ ] Service is active/running
- [ ] `tmux list-sessions` shows `opencode` session

---

### Task 3: Create ttyd Docker Service (via Docker Compose)

**Objective**: Run ttyd in Docker with Traefik labels for HTTPS access

**Rationale**: Using Docker instead of systemd for ttyd allows:
- Consistent management with other services
- Native Traefik integration via labels
- Easy restart/update workflow

**File**: `apps/opencode-terminal/docker-compose.yml`

```yaml
version: "3"
services:
  opencode-terminal:
    image: tsl0922/ttyd:latest
    container_name: opencode-terminal
    restart: unless-stopped
    network_mode: host  # Required to access host's tmux socket
    user: "1000:1000"  # Match unarmedpuppy user
    volumes:
      - /tmp:/tmp:rw  # tmux socket location
    command: >
      ttyd
      --writable
      --port 7681
      --base-path /
      tmux attach -t opencode
    labels:
      - "traefik.enable=true"
      - "traefik.docker.network=my-network"
      # HTTPS redirect
      - "traefik.http.middlewares.terminal-redirect.redirectscheme.scheme=https"
      - "traefik.http.routers.terminal-redirect.middlewares=terminal-redirect"
      - "traefik.http.routers.terminal-redirect.rule=Host(`terminal.server.unarmedpuppy.com`)"
      - "traefik.http.routers.terminal-redirect.entrypoints=web"
      # Local network access (no auth) - highest priority
      - "traefik.http.routers.terminal-local.rule=Host(`terminal.server.unarmedpuppy.com`) && ClientIP(`192.168.86.0/24`)"
      - "traefik.http.routers.terminal-local.priority=100"
      - "traefik.http.routers.terminal-local.entrypoints=websecure"
      - "traefik.http.routers.terminal-local.tls.certresolver=myresolver"
      - "traefik.http.routers.terminal-local.service=terminal"
      # External access (requires auth) - lowest priority
      - "traefik.http.routers.terminal.rule=Host(`terminal.server.unarmedpuppy.com`)"
      - "traefik.http.routers.terminal.priority=1"
      - "traefik.http.routers.terminal.entrypoints=websecure"
      - "traefik.http.routers.terminal.tls.certresolver=myresolver"
      - "traefik.http.routers.terminal.tls=true"
      - "traefik.http.routers.terminal.middlewares=terminal-auth"
      # Service and auth middleware
      - "traefik.http.services.terminal.loadbalancer.server.port=7681"
      - "traefik.http.middlewares.terminal-auth.basicauth.users=unarmedpuppy:$$apr1$$yE.A6vVX$$p7.fpGKw5Unp0UW6H/2c.0"
      - "traefik.http.middlewares.terminal-auth.basicauth.realm=Terminal"
      # Homepage labels
      - "homepage.group=Development"
      - "homepage.name=Terminal"
      - "homepage.icon=mdi-console"
      - "homepage.href=https://terminal.server.unarmedpuppy.com"
      - "homepage.description=Web-based terminal (ttyd + tmux)"
```

**Alternative: Systemd-based ttyd** (if you prefer not using Docker):

```ini
# /etc/systemd/system/opencode-ttyd.service
[Unit]
Description=ttyd web terminal for OpenCode
After=opencode-tmux.service
Requires=opencode-tmux.service

[Service]
Type=simple
User=unarmedpuppy
ExecStart=/usr/bin/ttyd -W -p 7681 tmux attach -t opencode
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

If using systemd, you'd expose via Traefik's file-based configuration instead.

---

### Task 4: Add DNS Entry to Cloudflare DDNS

**Objective**: Register `terminal.server.unarmedpuppy.com` with Cloudflare

**File to modify**: `apps/cloudflare-ddns/docker-compose.yml`

**Change**: Add `terminal.server.unarmedpuppy.com` to the DOMAINS list.

---

### Task 5: Deploy and Verify

**Deployment Steps**:

```bash
# 1. Commit changes locally
git add apps/opencode-terminal apps/cloudflare-ddns/docker-compose.yml
git commit -m "feat: Add persistent OpenCode terminal environment"
git push

# 2. SSH to server and pull
ssh -p 4242 unarmedpuppy@192.168.86.47 "cd ~/server && git pull"

# 3. Create/start tmux service (Task 2 commands)
# ... run commands from Task 2 ...

# 4. Start ttyd container
ssh -p 4242 unarmedpuppy@192.168.86.47 "cd ~/server/apps/opencode-terminal && docker compose up -d"

# 5. Restart cloudflare-ddns to pick up new domain
ssh -p 4242 unarmedpuppy@192.168.86.47 "cd ~/server/apps/cloudflare-ddns && docker compose restart"
```

---

## Verification Matrix

| Test | Command | Expected Result |
|------|---------|-----------------|
| tmux session exists | `tmux list-sessions` | Shows `opencode` |
| ttyd container running | `docker ps \| grep opencode-terminal` | Container running |
| ttyd responding locally | `curl -I http://localhost:7681` | HTTP 200 |
| tmux service enabled | `systemctl is-enabled opencode-tmux` | `enabled` |
| HTTPS access (local) | Browse `https://terminal.server.unarmedpuppy.com` on LAN | Loads ttyd, no auth prompt |
| HTTPS access (external) | Browse from mobile data | Auth prompt, then ttyd loads |
| SSH attach works | `ssh -p 4242 unarmedpuppy@192.168.86.47 "tmux attach -t opencode"` | Attaches to session |

---

## Success Criteria

- [x] tmux session `opencode` running and persists across reboots
- [x] ttyd accessible on port 7681 locally (verified: `curl -I http://localhost:7681` returns HTTP 200)
- [x] Both services enabled for auto-start (systemd for tmux, socat proxy for Traefik)
- [x] DNS `terminal.server.unarmedpuppy.com` resolves (verified: 192.168.86.47)
- [ ] ~~Browser access via HTTPS with valid Let's Encrypt certificate~~ **BLOCKED** - Traefik can't reach host
- [ ] Browser access works via mobile (with basic auth) - **BLOCKED**
- [ ] Browser access works on LAN (no auth required) - **BLOCKED**
- [x] SSH + `tmux attach -t opencode` works from laptop
- [x] Direct LAN access works: `http://192.168.86.47:7681`

---

## Files Created/Modified

| File | Action | Status |
|------|--------|--------|
| `apps/opencode-terminal/docker-compose.yml` | Created (ttyd in Docker with Traefik labels) | Done |
| `apps/traefik/docker-compose.yml` | Modified (added extra_hosts for host access) | Done |
| `apps/traefik/fileConfig.yml` | Modified (removed terminal file routing, now uses Docker labels) | Done |
| `apps/homepage/config/services.yaml` | Modified (added terminal service) | Done |
| `apps/cloudflare-ddns/docker-compose.yml` | Modified (added domain) | Done |
| `/etc/systemd/system/opencode-tmux.service` (on server) | Created | Done |
| `/etc/systemd/system/opencode-ttyd.service` (on server) | Created but deprecated | Superseded by Docker |
| `/usr/local/bin/ttyd` (on server) | Installed from GitHub | Done (still used by systemd, backup) |

**Note**: Final architecture uses Docker-based ttyd with Traefik Docker labels for routing. The systemd ttyd service is kept as fallback but Docker container is the primary.

**Key Fix**: Traefik running in Docker couldn't reach the systemd ttyd on the host due to network isolation. Solution was to run ttyd in Docker on the same `my-network` network, mounting the tmux socket from the host.

---

## Open Questions

1. **Docker vs Systemd for ttyd?**
   - Docker: Consistent with other services, native Traefik integration
   - Systemd: Simpler, fewer layers, but needs Traefik file config

2. **Session naming**: Should we use `opencode` or something else for the tmux session name?

3. **Auto-attaching to existing session**: The ttyd command uses `tmux attach` which will fail if the session doesn't exist. Consider using `tmux new-session -A -s opencode` instead (attaches if exists, creates if not).

4. **Security considerations**:
   - Basic auth is used for external access (same pattern as other services)
   - Consider whether terminal access warrants stronger auth (2FA, IP restrictions beyond LAN)
   - The writable flag (`-W`) allows full terminal control - ensure auth is robust

---

## Rollback Plan

If issues arise:

```bash
# Stop Docker ttyd container
cd ~/server/apps/opencode-terminal && docker compose down

# Stop and disable tmux service
sudo systemctl stop opencode-tmux
sudo systemctl disable opencode-tmux

# Remove DNS entry from cloudflare-ddns config
# Restart cloudflare-ddns

# Remove files
sudo rm /etc/systemd/system/opencode-tmux.service
sudo rm /etc/systemd/system/opencode-ttyd.service
rm -rf apps/opencode-terminal/
```

---

## Implementation Notes (2025-12-21)

### Current Working State

**What Works:**
- ✅ `http://192.168.86.47:7681` - Direct LAN access (no HTTPS, no auth)
- ✅ SSH + `tmux a -t opencode` - Full persistent tmux session from laptop
- ✅ tmux session auto-starts on boot via systemd
- ✅ ttyd systemd service running on port 7681

**What Doesn't Work:**
- ❌ `https://terminal.server.unarmedpuppy.com` - Traefik can't reach host services

### Root Cause: Docker Network Isolation

Docker containers (including Traefik) cannot reach services running on the host, even when using:
- `host.docker.internal` (maps to 172.17.0.1 but traffic blocked)
- Bridge gateway IPs (192.168.160.1, 172.17.0.1)
- LAN IP (192.168.86.47)

This is due to iptables rules that block traffic from Docker bridge networks to the host.

### Attempted Solutions

1. **Docker-based ttyd with tmux socket mount** - Failed: Unix sockets don't work across container boundaries
2. **socat proxy with host network** - Works locally but Traefik still can't reach it
3. **Traefik file-based config pointing to host** - Gateway timeout due to network isolation

### Architecture (Current)

```
┌─────────────────────────────────────────────────────────────┐
│ Host (192.168.86.47)                                        │
│                                                             │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │ opencode-tmux    │    │ opencode-ttyd    │              │
│  │ (systemd)        │◄───│ (systemd)        │              │
│  │ tmux session     │    │ port 7681        │              │
│  └──────────────────┘    └────────┬─────────┘              │
│                                   │                         │
│                                   ▼                         │
│                          ┌────────────────┐                │
│                          │ socat proxy    │                │
│                          │ (Docker, host  │                │
│                          │ network)       │                │
│                          │ port 17681     │                │
│                          └────────┬───────┘                │
│                                   │                         │
│                                   ▼                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │ my-network (Docker bridge: 192.168.160.0/20)       │    │
│  │                                                    │    │
│  │  ┌─────────────┐                                   │    │
│  │  │ Traefik     │──────X─── CAN'T REACH HOST ───X   │    │
│  │  └─────────────┘                                   │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Fix Options (Requires sudo)

**Option 1: iptables rule**
```bash
sudo iptables -I INPUT -i br-+ -p tcp --dport 17681 -j ACCEPT
sudo iptables -I INPUT -i docker0 -p tcp --dport 17681 -j ACCEPT
```

**Option 2: Add Traefik to host network** (breaks other routing)

**Option 3: Use Cloudflare Tunnel instead of Traefik** (different architecture)

### Files Currently in Repo

| File | Purpose | Status |
|------|---------|--------|
| `apps/opencode-terminal/docker-compose.yml` | socat proxy container | Active but not working |
| `apps/opencode-terminal/Dockerfile` | Custom ttyd+tmux image | Unused (Docker approach abandoned) |
| `apps/traefik/fileConfig.yml` | Terminal routing config | Has terminal routes |
| `apps/traefik/docker-compose.yml` | Traefik with extra_hosts | Modified |

### Systemd Services (on server)

| Service | Purpose | Status |
|---------|---------|--------|
| `opencode-tmux.service` | Persistent tmux session | ✅ Running |
| `opencode-ttyd.service` | ttyd web terminal on 7681 | ✅ Running |

### Recommended Workflow Until Fixed

1. **For coding on laptop**: SSH + `tmux a -t opencode`
2. **For quick LAN access**: `http://192.168.86.47:7681` (no HTTPS)
3. **For mobile/external**: Not available until iptables fix applied

### Next Steps

1. Apply iptables rule with sudo to allow Docker→Host traffic
2. Or: Investigate Cloudflare Tunnel as alternative to Traefik for this service
3. Or: Accept LAN-only access and use Tailscale for mobile

---

### Key Technical Details (Historical)

- ttyd container mounts `/tmp` to access tmux socket at `/tmp/tmux-1000/default`
- ttyd container mounts `/home/unarmedpuppy` for proper working directory
- Docker networking: ttyd on `my-network` allows Traefik to route directly to it
- Traefik `extra_hosts` added for `host.docker.internal` (for future host service access)
