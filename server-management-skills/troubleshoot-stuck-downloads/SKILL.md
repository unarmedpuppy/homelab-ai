---
name: troubleshoot-stuck-downloads
description: Diagnose Sonarr/Radarr queue issues: check queue → verify clients → clear stuck items
category: troubleshooting
mcp_tools_required:
  - sonarr_queue_status
  - sonarr_check_download_clients
  - radarr_queue_status
  - sonarr_clear_queue
  - radarr_clear_queue
  - nzbget_status
  - qbittorrent_status
prerequisites:
  - Sonarr or Radarr service running
  - MCP tools available
---

# Troubleshoot Stuck Downloads

## When to Use This Skill

Use this skill when:
- Downloads stuck in Sonarr/Radarr queue
- Downloads not processing
- Queue items in "downloading" state for extended time
- Download client not responding
- Import scans not working

## Overview

This skill diagnoses and fixes stuck download issues:
1. Check queue status (stuck items, status breakdown)
2. Verify download client configuration
3. Check download client status
4. Identify root cause
5. Clear stuck items if needed
6. Verify resolution

## Workflow Steps

### Step 1: Check Queue Status

Get detailed queue status:

```python
# Check Sonarr queue
sonarr_queue = await sonarr_queue_status()

# Check Radarr queue
radarr_queue = await radarr_queue_status()

# Analyze stuck items
stuck_items = []
for item in sonarr_queue.get("stuck_items", []):
    stuck_items.append({
        "service": "sonarr",
        "item": item,
        "status": item.get("status"),
        "age": item.get("age_hours", 0)
    })

for item in radarr_queue.get("stuck_items", []):
    stuck_items.append({
        "service": "radarr",
        "item": item,
        "status": item.get("status"),
        "age": item.get("age_hours", 0)
    })
```

**What to check:**
- Total items in queue
- Items by status (downloading, queued, paused)
- Stuck items (same status for >1 hour)
- Items by protocol (usenet vs torrent)

### Step 2: Verify Download Client Configuration

Check if download clients are properly configured:

```python
# Check Sonarr download clients
sonarr_clients = await sonarr_check_download_clients()

# Analyze client status
client_issues = []
for client in sonarr_clients.get("clients", []):
    if client["status"] != "connected":
        client_issues.append({
            "service": "sonarr",
            "client": client["name"],
            "issue": client.get("error", "Not connected"),
            "severity": "critical"
        })
```

**What to check:**
- Download clients configured
- Clients connected and responding
- Client-specific errors
- Protocol availability (usenet vs torrent)

### Step 3: Check Download Client Status

Verify download clients are actually working:

```python
# Check NZBGet status
nzbget = await nzbget_status()

# Check qBittorrent status
qbittorrent = await qbittorrent_status()

# Analyze client health
client_status = {
    "nzbget": {
        "status": "ok" if nzbget.get("server_status") == "running" else "error",
        "active_downloads": nzbget.get("active_downloads", 0),
        "speed": nzbget.get("download_speed", 0)
    },
    "qbittorrent": {
        "status": "ok" if qbittorrent.get("status") == "connected" else "error",
        "active_torrents": qbittorrent.get("active_torrents", 0),
        "speed": qbittorrent.get("download_speed", 0)
    }
}
```

**What to check:**
- Download client running
- Active downloads/torrents
- Download speeds
- Client errors

### Step 4: Identify Root Cause

Based on collected information, identify the root cause:

**Common Issues:**

1. **Download Client Not Configured**
   - Symptom: No clients in configuration
   - Action: Configure download client in Sonarr/Radarr

2. **Download Client Not Connected**
   - Symptom: Client shows "not connected" status
   - Action: Check client URL, credentials, network connectivity

3. **Download Client Not Running**
   - Symptom: Client status check fails
   - Action: Start download client container/service

4. **Stuck Items in Queue**
   - Symptom: Items in "downloading" state for >1 hour
   - Action: Clear stuck items, verify client is working

5. **Protocol Issues**
   - Symptom: Usenet items stuck but torrents work (or vice versa)
   - Action: Check protocol-specific client configuration

6. **Root Folder Issues**
   - Symptom: Downloads complete but not importing
   - Action: Check root folder configuration, permissions

### Step 5: Clear Stuck Items

If stuck items identified, clear them:

```python
# Clear Sonarr queue if needed
if sonarr_queue.get("stuck_items_count", 0) > 0:
    clear_result = await sonarr_clear_queue(
        blocklist=False,
        remove_from_client=True
    )
    
# Clear Radarr queue if needed
if radarr_queue.get("stuck_items_count", 0) > 0:
    clear_result = await radarr_clear_queue(
        blocklist=False,
        remove_from_client=True
    )
```

**When to clear:**
- Items stuck for >1 hour
- Download client confirmed working
- Items not progressing

**When NOT to clear:**
- Items actively downloading (check age first)
- Download client not working (fix client first)

### Step 6: Verify Resolution

After clearing, verify queue is working:

```python
# Re-check queue status
new_queue = await sonarr_queue_status()

# Verify stuck items cleared
if new_queue.get("stuck_items_count", 0) == 0:
    return {
        "status": "success",
        "message": "Stuck items cleared, queue should process normally"
    }
else:
    return {
        "status": "partial",
        "message": f"Some items still stuck: {new_queue.get('stuck_items_count')}",
        "action": "Investigate remaining stuck items"
    }
```

## MCP Tools Used

This skill uses the following MCP tools:

1. **`sonarr_queue_status`** - Get Sonarr queue status and stuck items
2. **`radarr_queue_status`** - Get Radarr queue status
3. **`sonarr_check_download_clients`** - Verify download client configuration
4. **`sonarr_clear_queue`** - Clear stuck items from Sonarr
5. **`radarr_clear_queue`** - Clear stuck items from Radarr
6. **`nzbget_status`** - Check NZBGet download client status
7. **`qbittorrent_status`** - Check qBittorrent status

## Examples

### Example 1: Stuck Downloads in Sonarr

**Symptom**: Downloads stuck in "downloading" state for hours

**Workflow**:
```python
# Step 1: Check queue
queue = await sonarr_queue_status()
# Returns: {"stuck_items_count": 5, "stuck_items": [...]}

# Step 2: Check clients
clients = await sonarr_check_download_clients()
# Returns: {"clients": [{"name": "NZBGet", "status": "connected"}]}

# Step 3: Check NZBGet
nzbget = await nzbget_status()
# Returns: {"server_status": "running", "active_downloads": 0}

# Step 4: Clear stuck items
clear_result = await sonarr_clear_queue(remove_from_client=True)
# Returns: {"removed_count": 5}

# Step 5: Verify
new_queue = await sonarr_queue_status()
# Returns: {"stuck_items_count": 0}
```

### Example 2: Download Client Not Connected

**Symptom**: Queue items not processing, client shows "not connected"

**Workflow**:
```python
# Step 1: Check queue
queue = await sonarr_queue_status()
# Returns: {"total_items": 10, "stuck_items_count": 10}

# Step 2: Check clients
clients = await sonarr_check_download_clients()
# Returns: {"clients": [{"name": "qBittorrent", "status": "not_connected", "error": "Connection refused"}]}

# Root cause: Download client not connected
# Action: Check qBittorrent container status, verify URL/credentials
# Don't clear queue until client is fixed
```

### Example 3: Protocol-Specific Issue

**Symptom**: Usenet downloads stuck, but torrents work

**Workflow**:
```python
# Step 1: Check queue by protocol
queue = await sonarr_queue_status()
# Returns: {"by_protocol": {"usenet": {"stuck": 5}, "torrent": {"stuck": 0}}}

# Step 2: Check usenet client (NZBGet)
nzbget = await nzbget_status()
# Returns: {"server_status": "error", "error": "Server not responding"}

# Root cause: NZBGet not working
# Action: Restart NZBGet container, verify configuration
```

## Error Handling

### Download Client Not Found

**Action**: Verify download client is configured in Sonarr/Radarr settings

### Client Connection Failed

**Action**: 
- Check client URL and port
- Verify credentials
- Check network connectivity
- Verify client container is running

### Queue Clear Failed

**Action**: 
- Check if items are actually stuck (verify age)
- Try clearing individual items
- Check Sonarr/Radarr API status

### Items Re-stuck After Clear

**Action**: 
- Root cause not fixed (client still not working)
- Fix download client first, then clear queue
- Check for root folder or permission issues

## Recommended Fixes by Issue

| Issue | Recommended Fix |
|-------|----------------|
| Download client not configured | Configure client in Sonarr/Radarr settings |
| Client not connected | Check URL, credentials, network, container status |
| Client not running | Start download client container/service |
| Stuck items | Clear queue after verifying client is working |
| Protocol issues | Check protocol-specific client configuration |
| Root folder issues | Verify root folder paths and permissions |

## Related Skills

- **`troubleshoot-container-failure`** - If download client container is failing
- **`system-health-check`** - For comprehensive system verification
- **`standard-deployment`** - If issue occurred after deployment

## Notes

- Always verify download client is working before clearing queue
- Stuck items are typically >1 hour in same status
- Clearing queue removes items - verify this is desired
- Check both Sonarr and Radarr if both are having issues
- Protocol-specific issues require checking the specific client

