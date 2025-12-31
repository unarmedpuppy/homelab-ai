# Gaming Server Management Reference

Quick reference for diagnosing and resolving game server performance issues.

## Quick Diagnostics

### Check System Resources
```bash
# Overall system state
ssh -p 4242 unarmedpuppy@192.168.86.47 "free -h && echo '---' && uptime"

# Top memory-consuming containers
ssh -p 4242 unarmedpuppy@192.168.86.47 "docker stats --no-stream --format 'table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.CPUPerc}}' | sort -k3 -hr | head -20"

# Top system processes by memory
ssh -p 4242 unarmedpuppy@192.168.86.47 "ps aux --sort=-%mem | head -15"
```

### Check Specific Game Server
```bash
# Container stats
docker stats valheim --no-stream

# Recent logs
docker logs valheim --tail 100

# Search logs for errors
docker logs valheim 2>&1 | grep -E '(error|Error|ERROR|timeout|lag)' | tail -30
```

## Common Causes of Lag

### 1. Memory Pressure (>85% RAM usage)

**Symptoms**: High RAM usage, lag spikes, slow response

**Diagnosis**:
```bash
free -h  # Check available memory
```

**Common memory hogs**:
| Service | Typical RAM | Notes |
|---------|-------------|-------|
| Rust server | 8-12 GB | Very heavy |
| vLLM/AI models | 6-10 GB | GPU memory too |
| 7 Days to Die | 2-4 GB | Moderate |
| Valheim | 1-2 GB | Light |
| Plex (transcoding) | 1-2 GB | Per stream |

**Resolution**: Stop unused services
```bash
# Stop Rust server
cd ~/server/apps/rust && docker compose down

# Stop AI services if not needed
cd ~/server/apps/ollama-docker && docker compose down
```

### 2. CPU Contention (load average > CPU cores)

**Symptoms**: Sluggish gameplay, delayed actions

**Diagnosis**:
```bash
uptime  # Check load average
docker stats --no-stream  # Find CPU hogs
```

**Resolution**: Identify and restart misbehaving services
```bash
# Restart a service consuming excessive CPU
docker restart <container_name>
```

### 3. Runaway Monitoring Services

**Symptoms**: Telegraf/Prometheus using >10% CPU

**Diagnosis**:
```bash
docker stats telegraf prometheus --no-stream
```

**Resolution**:
```bash
docker restart telegraf
docker restart prometheus
```

### 4. Network/Crossplay Issues (Valheim-specific)

**Symptoms**: Players briefly disconnecting, "connection lost" messages

**Log indicators**:
```
PlayFab network error... code '4098': the operation was called with an invalid handle
network transport link was remotely terminated
ZRpc timeout detected
```

**Causes**:
- PlayFab crossplay networking is inherently less stable than direct Steam connections
- Mixed PC/Xbox player groups can have more issues
- Server resource pressure makes it worse

**Resolution**:
1. Ensure server has resource headroom (see above)
2. Restart Valheim if errors persist:
   ```bash
   cd ~/server/apps/valheim && docker compose restart
   ```
3. Players can try reconnecting with join code

## Game-Specific Notes

### Valheim

| Setting | Value |
|---------|-------|
| Container | `valheim` |
| Ports | UDP 2456-2458 |
| RAM | ~1.3 GB typical |
| CPU | 15-25% with 5 players |

**Get join code**:
```bash
docker logs valheim 2>&1 | grep "join code"
```

**Crossplay notes**:
- Uses PlayFab for matchmaking (not direct IP)
- Join code required when `CROSSPLAY=true`
- More prone to brief disconnects than Steam-only

**Graceful restart** (saves world first):
```bash
cd ~/server/apps/valheim && docker compose restart
```

### Rust

| Setting | Value |
|---------|-------|
| Container | `rust-rust-server-1` |
| Ports | UDP 28015, TCP 28016 (RCON) |
| RAM | 8-12 GB (heavy!) |
| CPU | 30-50% |

**Stop server** (frees significant resources):
```bash
cd ~/server/apps/rust && docker compose down
```

**Start server**:
```bash
cd ~/server/apps/rust && docker compose up -d
```

### 7 Days to Die

| Setting | Value |
|---------|-------|
| Container | `7daystodie` |
| Ports | TCP/UDP 26900 |
| RAM | 2-4 GB |
| CPU | 5-15% |

## Resource Budget

With 62GB RAM total, recommended allocation:

| Priority | Service | Max RAM |
|----------|---------|---------|
| 1 | Active game server | 12 GB |
| 2 | Plex + transcoding | 4 GB |
| 3 | Core services (Traefik, DBs) | 4 GB |
| 4 | Monitoring stack | 2 GB |
| 5 | AI services (if needed) | 10 GB |
| - | Buffer/cache | 10+ GB |

**Rule of thumb**: Keep RAM usage under 80% for smooth game server operation.

## Emergency Procedures

### Server Completely Unresponsive
```bash
# Hard restart via SSH (if accessible)
sudo reboot
```

### Single Game Server Hung
```bash
# Force kill and restart
docker kill <container>
cd ~/server/apps/<game> && docker compose up -d
```

### Out of Memory
```bash
# Quick wins - stop these first:
docker stop rust-rust-server-1  # 12GB
docker stop vllm-*              # 8GB
docker stop ollama              # Varies
```

## Monitoring

### Uptime Kuma
- URL: https://uptime.server.unarmedpuppy.com
- Game servers monitored via Gamedig
- Discord webhooks for down alerts

### Homepage Dashboard
- Gaming group shows server status
- Gamedig widgets show player counts

## Related Docs

- [Game Server Agent Persona](../personas/game-server-agent.md) - Setup and configuration
- [Troubleshoot Container Failure](../skills/troubleshoot-container-failure/) - General container debugging
