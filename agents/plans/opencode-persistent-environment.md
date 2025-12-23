# Plan: Persistent OpenCode Development Environment

**Status**: In Progress - Debugging Traefik Routing
**Created**: 2025-12-21
**Priority**: P1
**Effort**: Medium
**Beads Task**: home-server-chi (in_progress)

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
- [x] Both services enabled for auto-start (both systemd services enabled)
- [ ] **BLOCKING**: Traefik routes terminal traffic correctly (currently 404)
- [ ] DNS `terminal.server.unarmedpuppy.com` resolves
- [ ] Browser access works via mobile (with basic auth)
- [ ] Browser access works on LAN (no auth required)
- [x] SSH + `tmux attach -t opencode` works from laptop

---

## Files Created/Modified

| File | Action | Status |
|------|--------|--------|
| `apps/traefik/fileConfig.yml` | Modified (added terminal routing) | Done |
| `apps/homepage/config/services.yaml` | Modified (added terminal service) | Done |
| `apps/cloudflare-ddns/docker-compose.yml` | Modified (added domain) | Done |
| `/etc/systemd/system/opencode-tmux.service` (on server) | Created | Done |
| `/etc/systemd/system/opencode-ttyd.service` (on server) | Created | Done |
| `/usr/local/bin/ttyd` (on server) | Installed from GitHub | Done |
| `README.md` | Modified (documented services) | Done |

**Note**: Changed from Docker-based ttyd to systemd-based ttyd because network_mode:host is incompatible with Traefik Docker labels. Using Traefik file-based config instead.

**Current Issue**: Traefik file-based routes not working - returning 404. See "Current Blocking Issue" section above for debugging steps.

---

## Decisions Made

1. **Docker vs Systemd for ttyd?** → **Systemd chosen**
   - Docker with `network_mode: host` doesn't work with Traefik labels
   - Using systemd + Traefik file-based config instead

2. **Session naming**: Using `opencode` for the tmux session name

## Open Questions

1. **Auto-attaching to existing session**: The ttyd command uses `tmux attach` which will fail if the session doesn't exist. Consider using `tmux new-session -A -s opencode` instead (attaches if exists, creates if not).

2. **Security considerations**:
   - Basic auth is used for external access (same pattern as other services)
   - Consider whether terminal access warrants stronger auth (2FA, IP restrictions beyond LAN)
   - The writable flag (`-W`) allows full terminal control - ensure auth is robust

---

## Current Blocking Issue: Traefik 404

**Symptom**: `https://terminal.server.unarmedpuppy.com` returns 404 Not Found

### What's Working
- tmux systemd service running (`opencode-tmux.service`)
- ttyd systemd service running (`opencode-ttyd.service`)
- ttyd responds locally: `curl -I http://localhost:7681` → HTTP 200
- SSH attach works: `ssh -p 4242 unarmedpuppy@192.168.86.47 "tmux attach -t opencode"`
- Traefik fileConfig.yml is mounted and readable inside container

### What's NOT Working
- Traefik is not routing `terminal.server.unarmedpuppy.com` to ttyd
- Returns 404 (Traefik's default "no matching route" response)
- SSL cert shows self-signed (Let's Encrypt hasn't issued cert yet - likely because route not working)

### Debugging Already Done
1. **Initial URL mistake**: Used `http://127.0.0.1:7681` in fileConfig.yml - this is wrong because localhost inside Traefik container can't reach host services
2. **Fixed to server IP**: Changed to `http://192.168.86.47:7681` (server's LAN IP)
3. **Verified fileConfig.yml is mounted**: `docker exec traefik cat /etc/traefik/fileConfig.yml` shows terminal routes
4. **Restarted Traefik**: `docker compose restart traefik` - still 404

### Next Debugging Steps (Resume Here)

1. **Check if file provider is loading routes**:
   ```bash
   # SSH to server
   ssh -p 4242 unarmedpuppy@192.168.86.47
   
   # Check Traefik API for loaded routers (if API exposed)
   docker exec traefik wget -qO- http://localhost:8080/api/http/routers 2>/dev/null | grep -i terminal
   
   # Or check Traefik logs for file provider errors
   docker logs traefik 2>&1 | grep -i "file\|terminal\|error"
   ```

2. **Verify traefik.yml file provider config**:
   ```bash
   # Ensure file provider is configured correctly
   docker exec traefik cat /etc/traefik/traefik.yml | grep -A5 "file:"
   ```

3. **Check DNS resolution**:
   ```bash
   dig terminal.server.unarmedpuppy.com
   nslookup terminal.server.unarmedpuppy.com
   ```

4. **Restart cloudflare-ddns** (may not have picked up new domain):
   ```bash
   cd ~/server/apps/cloudflare-ddns && docker compose restart
   ```

5. **Consider `extra_hosts` in Traefik** (better than hardcoded IP):
   Add to `apps/traefik/docker-compose.yml`:
   ```yaml
   extra_hosts:
     - "host.docker.internal:host-gateway"
   ```
   Then use `http://host.docker.internal:7681` in fileConfig.yml

6. **Check if routes appear in Traefik dashboard**:
   - If Traefik dashboard is exposed, check HTTP Routers section
   - Look for `terminal@file` and `terminal-local@file` entries

### Key Files to Check
- `apps/traefik/traefik.yml` - Main Traefik config (file provider setup)
- `apps/traefik/fileConfig.yml` - File-based routes (terminal routes here)
- `apps/traefik/docker-compose.yml` - Traefik container config

---

## Rollback Plan

If issues arise:

```bash
# Stop and disable services
sudo systemctl stop opencode-tmux
sudo systemctl disable opencode-tmux
docker stop opencode-terminal && docker rm opencode-terminal

# Remove DNS entry from cloudflare-ddns config
# Restart cloudflare-ddns

# Remove files
sudo rm /etc/systemd/system/opencode-tmux.service
rm -rf apps/opencode-terminal/
```
