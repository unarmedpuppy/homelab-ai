---
name: system-health-check
description: Comprehensive system status check
when_to_use: Regular maintenance, after system changes, before deployments, when things seem slow
---

# System Health Check

Comprehensive system status check.

## When to Use

- Regular maintenance
- After system changes
- Before deployments
- When things seem slow

## Steps

### 1. Check Disk Space

```bash
df -h
docker system df
```

### 2. Check System Resources

```bash
# CPU and memory
top -l 1 | head -10  # macOS
htop                 # Linux

# Load average
uptime
```

### 3. Check All Containers

```bash
docker ps -a
docker stats --no-stream
```

### 4. Check for Errors in Logs

```bash
# Check each service
docker logs SERVICE_NAME --tail 50 2>&1 | grep -i error

# Or check all at once
for c in $(docker ps -q); do echo "=== $c ==="; docker logs $c --tail 20 2>&1 | grep -i error; done
```

### 5. Check Network

```bash
# Test connectivity
ping -c 3 google.com

# Check Docker networks
docker network ls
```

## Quick Health Summary

```bash
echo "=== DISK ===" && df -h | grep -E "/$|/data"
echo "=== MEMORY ===" && free -h 2>/dev/null || vm_stat
echo "=== CONTAINERS ===" && docker ps --format "table {{.Names}}\t{{.Status}}"
echo "=== ERRORS ===" && docker ps -q | xargs -I {} docker logs {} --tail 10 2>&1 | grep -i error | tail -5
```

