# Storage Audit Reference

## Overview

This document tracks storage usage across the server and documents findings from storage audits.

## Storage Summary

| Storage | Capacity | Used | Available | Usage |
|---------|----------|------|-----------|-------|
| **System Drive** (nvme0n1p2) | 916 GB | 516 GB | 363 GB | 59% |
| **ZFS Pool** (jenquist-cloud) | 29.1 TB | 23.9 TB | 5.19 TB | 82% |

---

## System Drive Breakdown (916 GB)

### Top-Level Usage

| Directory | Size | Notes |
|-----------|------|-------|
| `/var/lib/docker` | ~140 GB | Docker images, containers, volumes |
| `/home/unarmedpuppy/server/apps` | ~96 GB | Application data |
| `/usr` | ~8 GB | System binaries |
| `/var` (excluding docker) | ~4 GB | System logs, packages |
| Other | ~10 GB | Boot, tmp, etc. |

### Docker Storage Breakdown

| Component | Size | Reclaimable |
|-----------|------|-------------|
| Images | 70 GB | 11 GB (16%) |
| Container logs | Variable | Depends on log rotation |
| Local Volumes | 8 GB | 3 GB (42%) |
| Overlay2 (layers) | ~60 GB | Managed by Docker |

### Application Data (~/server/apps/)

| Application | Size | Notes |
|-------------|------|-------|
| media-download | 26 GB | Sonarr/Radarr/Prowlarr configs and databases |
| bedrock-viz | 26 GB | Minecraft map visualization data |
| rust | 19 GB | Rust game server |
| plex | 16 GB | Plex metadata and thumbnails |
| valheim | 3.4 GB | Valheim game server |
| minecraft | 3.4 GB | Minecraft Bedrock server |
| adguard-home | 1.4 GB | DNS filtering logs and stats |
| spotifydl | 945 MB | Spotify downloader cache |
| ollama-docker | 889 MB | AI model data |

---

## ZFS Pool Breakdown (29.1 TB)

### Datasets

| Dataset | Used | Purpose |
|---------|------|---------|
| jenquist-cloud | 620 GB | Root (Harbor, backups, misc) |
| jenquist-cloud/archive | 16.7 TB | Media archive |
| jenquist-cloud/vault | 36.9 GB | Encrypted personal data |

---

## Container Log Issues (Historical)

### Problem: Runaway Container Logs

Docker containers without log rotation can accumulate massive log files.

**Audit Date: 2024-12-26**

| Container | Log Size | Status |
|-----------|----------|--------|
| polymarket-bot | 220 GB | Fixed - truncated, added rotation |
| habitica-db | 6.5 GB | Fixed - container removed |
| newsblur-mongodb | 1.0 GB | Needs log rotation |
| nzbget | 622 MB | Needs log rotation |
| trading-bot-grafana | 306 MB | Needs log rotation |

### Solution: Add Log Rotation

Add to docker-compose.yml for each service:

```yaml
services:
  myservice:
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"
```

This limits each container to 300 MB of logs maximum (3 files x 100 MB).

### Truncate Existing Logs

```bash
# Find container ID
docker ps --no-trunc | grep container-name

# Truncate logs (requires privileged access)
docker run --rm --privileged -v /var/lib/docker/containers:/containers alpine \
  sh -c 'truncate -s 0 /containers/<container-id>/*-json.log'
```

---

## Cleanup Commands

### Check Storage Usage

```bash
# System drive overview
df -h /

# Docker usage summary
docker system df

# Docker detailed breakdown
docker system df -v

# Check container log sizes
docker run --rm -v /var/lib/docker/containers:/c:ro alpine \
  sh -c 'du -sh /c/*/ 2>/dev/null | sort -hr | head -10'

# Check apps directory
du -sh ~/server/apps/*/ | sort -hr | head -20
```

### Reclaim Space

```bash
# Prune unused Docker resources
docker image prune -f       # Remove dangling images
docker volume prune -f      # Remove unused volumes
docker system prune -f      # Remove all unused data
docker system prune -a -f   # Remove ALL unused images (aggressive)

# Find large files
find / -xdev -type f -size +1G 2>/dev/null

# Check for deleted files still held open
lsof 2>/dev/null | grep deleted | head -20
```

---

## Audit Checklist

Run periodically (monthly recommended):

- [ ] Check `df -h /` - system drive usage
- [ ] Check `docker system df` - Docker usage
- [ ] Check container log sizes (see command above)
- [ ] Review apps directory sizes
- [ ] Prune unused Docker images
- [ ] Verify log rotation is configured for all services

---

## Services Needing Attention

### Log Rotation Status

All major services now have log rotation configured:

| Service | Status | Notes |
|---------|--------|-------|
| polymarket-bot | ✅ Fixed | Log rotation added 2024-12-26 |
| nzbget | ✅ Fixed | Log rotation added 2024-12-26 |
| trading-bot (grafana) | ✅ Fixed | Log rotation added 2024-12-26 |
| newsblur | ❌ Removed | Service deleted 2024-12-26 |

### Consider Removing

| Service | Size | Notes |
|---------|------|-------|
| bedrock-viz | 26 GB | Large, infrequently used map data |
| rust | 19 GB | Game server - active? |
| valheim | 3.4 GB | Game server - active? |

---

## Historical Fixes

### 2024-12-26: polymarket-bot logs (220 GB)

**Problem**: polymarket-bot container had no log rotation, accumulated 220 GB of JSON logs.

**Fix**:
1. Truncated log file
2. Added log rotation to docker-compose.yml
3. Restarted container

**Space freed**: 220 GB

### 2024-12-26: habitica removal (6.5 GB + 3 GB image)

**Problem**: habitica was unused but consuming ~10 GB total.

**Fix**:
1. Stopped containers
2. Removed volumes
3. Deleted app directory

**Space freed**: ~10 GB

### 2024-12-26: newsblur removal (~1 GB logs + volumes)

**Problem**: NewsBlur was unused (had 4 containers: web, postgres, mongodb, redis).

**Fix**:
1. Stopped all containers with `docker compose down -v`
2. Removed all volumes (postgres-data, mongodb-data, redis-data)
3. Deleted app directory

**Space freed**: ~1-2 GB

---

## Prevention

### Default Log Rotation Template

All new docker-compose services should include:

```yaml
services:
  myservice:
    image: myimage
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"
    # ... rest of config
```

### Weekly Docker Prune

Already scheduled via cron:
```
0 5 * * 1 docker system prune -a -f
```

---

## Quick Reference

### Space Freed in Cleanup

| Date | Action | Space Freed |
|------|--------|-------------|
| 2024-12-26 | polymarket-bot log truncation | 220 GB |
| 2024-12-26 | habitica removal | ~10 GB |
| 2024-12-26 | newsblur removal | ~1-2 GB |
| 2024-12-26 | Docker prune | ~1 GB |
| **Total** | | **~232-233 GB** |

### Current Largest Consumers (System Drive)

1. Docker overlay2: ~60-130 GB
2. media-download: 26 GB
3. bedrock-viz: 26 GB
4. rust: 19 GB
5. plex: 16 GB
