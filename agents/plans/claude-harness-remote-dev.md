# Claude Harness Remote Development Workflow

## Goal

Enable interactive Claude Code development from any machine by connecting directly to the claude-harness container, mirroring the local development experience.

## Architecture

```
┌─────────────────┐     SSH (port 2222)      ┌────────────────────────────────┐
│  Local Machine  │ ────────────────────────▶│  claude-harness container      │
│  (any computer) │                          │  ┌──────────────────────────┐  │
└─────────────────┘                          │  │ Claude Code CLI          │  │
                                             │  │ - Interactive sessions   │  │
                                             │  │ - /workspace repos       │  │
                                             │  │ - SSH to server          │  │
                                             │  │ - Git with PAT           │  │
                                             │  └──────────────────────────┘  │
                                             └────────────────────────────────┘
```

## Implementation Plan

### Phase 1: Add SSH Server to Container

**Modify Dockerfile** (`homelab-ai/claude-harness/Dockerfile`):
```dockerfile
# Add openssh-server
RUN apt-get update && apt-get install -y \
    openssh-server \
    tmux \
    && mkdir /var/run/sshd

# Configure SSH
RUN sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config && \
    echo "AllowUsers appuser" >> /etc/ssh/sshd_config
```

**Modify entrypoint.sh**:
```bash
# Start SSH server (as root, before dropping to appuser)
/usr/sbin/sshd

# Then continue with existing entrypoint...
```

### Phase 2: Expose SSH Port

**Modify docker-compose.yml** (`apps/homelab-ai/docker-compose.yml`):
```yaml
claude-harness:
  ports:
    - "2222:22"  # SSH access
    - "8013:8013"  # API (existing)
```

### Phase 3: Add Your SSH Key

Mount your public key or add to authorized_keys:

**Option A: Mount from host**
```yaml
volumes:
  - /home/unarmedpuppy/.ssh/authorized_keys:/home/appuser/.ssh/authorized_keys:ro
```

**Option B: Separate key in volume** (more secure)
```yaml
volumes:
  - claude-dev-ssh:/home/appuser/.ssh
```
Then copy your public key into the volume.

### Phase 4: Pre-clone Repos

**Modify entrypoint.sh** to clone repos on startup:
```bash
setup_workspace() {
    cd /workspace
    
    # Clone repos if not present
    if [ ! -d "home-server" ]; then
        gosu "$APPUSER" git clone https://github.com/unarmedpuppy/home-server.git
    fi
    
    if [ ! -d "homelab-ai" ]; then
        gosu "$APPUSER" git clone https://github.com/unarmedpuppy/homelab-ai.git
    fi
}
```

### Phase 5: Create Connection Script

**Local script** (`~/.local/bin/claude-remote`):
```bash
#!/bin/bash
# Connect to remote Claude Code environment

HOST="${CLAUDE_REMOTE_HOST:-192.168.86.47}"
PORT="${CLAUDE_REMOTE_PORT:-2222}"
USER="appuser"

# SSH with tmux attach/create
ssh -p "$PORT" "$USER@$HOST" -t "tmux attach -t claude || tmux new -s claude"
```

## Usage After Implementation

```bash
# From any machine
claude-remote

# Or directly
ssh -p 2222 appuser@192.168.86.47

# Inside container - full Claude Code access
claude                    # Interactive Claude Code
claude -p "..."           # One-shot prompts
cd /workspace/home-server # Work on repos
```

## Security Considerations

1. **SSH key only** - No password auth
2. **Firewall** - Consider restricting port 2222 to local network
3. **Traefik option** - Could route through Traefik with client cert instead of direct port

## Alternative: Tailscale SSH

If you use Tailscale, the container could join the tailnet:
```yaml
services:
  claude-harness:
    environment:
      - TS_AUTHKEY=${TAILSCALE_AUTHKEY}
    # ... tailscale setup
```
Then: `ssh appuser@claude-harness` from any tailnet device.

## Files to Modify

| File | Changes |
|------|---------|
| `homelab-ai/claude-harness/Dockerfile` | Add openssh-server, tmux |
| `homelab-ai/claude-harness/entrypoint.sh` | Start sshd, setup workspace |
| `home-server/apps/homelab-ai/docker-compose.yml` | Expose port 2222, mount SSH key |
| `~/.local/bin/claude-remote` (local) | Connection script |

## Next Steps

1. [ ] Approve this plan
2. [ ] Implement Dockerfile changes
3. [ ] Implement entrypoint changes
4. [ ] Update docker-compose.yml
5. [ ] Push and rebuild via GitHub Actions
6. [ ] Deploy on server
7. [ ] Test connection
8. [ ] Create local connection script
