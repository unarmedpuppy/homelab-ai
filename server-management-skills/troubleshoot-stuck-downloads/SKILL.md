---
name: troubleshoot-stuck-downloads
description: Diagnose Sonarr/Radarr queue issues: check queue → verify clients → clear stuck items
category: troubleshooting
mcp_tools_required:
  - sonarr_queue_status
  - radarr_queue_status
  - sonarr_check_download_clients
  - radarr_check_download_clients
  - troubleshoot_failed_downloads
  - diagnose_download_client_unavailable
  - remove_stuck_downloads
  - check_disk_space
prerequisites:
  - Sonarr or Radarr service name
  - MCP tools available
---

# Troubleshoot Stuck Downloads

## When to Use This Skill

Use this skill when:
- Downloads stuck in Sonarr/Radarr queue
- Queue shows "downloadClientUnavailable" errors
- Downloads not processing or importing
- Queue items stuck in error/warning status
- User reports queue is stuck

## Overview

This skill provides a systematic approach to diagnosing and fixing stuck downloads in Sonarr/Radarr:
1. Check queue status and identify stuck items
2. Verify download client configuration
3. Diagnose root cause
4. Fix issues (if possible)
5. Clear stuck items
6. Verify resolution

## Workflow Steps

### Step 1: Check Queue Status

Get current queue status for the service:

```python
# For Sonarr
queue_status = await sonarr_queue_status()

# For Radarr
queue_status = await radarr_queue_status()

# Analyze results
data = queue_status.get("data", {})
stuck_count = data.get("stuck_count", 0)
stuck_items = data.get("stuck_items", [])

if stuck_count > 0:
    # Identify stuck statuses
    statuses = set([item["status"] for item in stuck_items])
    # Common: "downloadClientUnavailable", "error", "warning"
```

**What to check:**
- Total items in queue
- Items by status (downloading, queued, error, etc.)
- Items by protocol (torrent, usenet)
- Stuck items count and details

### Step 2: Verify Download Clients

Check download client configuration:

```python
# For Sonarr
clients = await sonarr_check_download_clients()

# For Radarr
clients = await radarr_check_download_clients()

# Analyze
issues = []
for client in clients.get("clients", []):
    if not client.get("enabled"):
        issues.append({
            "client": client.get("name"),
            "problem": "Client disabled",
            "fix": f"Enable {client['name']} in settings"
        })
    
    # Check if required clients are configured
    if "downloadClientUnavailable" in statuses:
        if "torrent" in stuck_items[0].get("protocol", ""):
            # Need qBittorrent
            qbt_found = any(c.get("name", "").lower() == "qbittorrent" for c in clients.get("clients", []))
            if not qbt_found:
                issues.append({
                    "problem": "qBittorrent not configured",
                    "fix": "Add qBittorrent download client"
                })
```

**What to check:**
- Download clients are enabled
- Required clients configured (qBittorrent for torrents, NZBGet for usenet)
- Client connection settings correct
- Authentication credentials valid

### Step 3: Run Comprehensive Diagnostic

Use the troubleshooting tool for detailed analysis:

```python
# Comprehensive diagnostic
diagnosis = await troubleshoot_failed_downloads(
    service="sonarr",  # or "radarr"
    include_logs=True
)

# Analyze results
queue_issues = diagnosis.get("queue_issues", {})
client_issues = diagnosis.get("client_issues", [])
disk_issues = diagnosis.get("disk_issues", [])
recommendations = diagnosis.get("recommendations", [])
```

**What this provides:**
- Queue issues summary
- Client configuration issues
- Disk space issues
- Recent error logs
- Actionable recommendations

### Step 4: Diagnose Specific Issue

If "downloadClientUnavailable" is the issue:

```python
# Specific diagnostic
diagnosis = await diagnose_download_client_unavailable("sonarr")

# Get root cause
root_cause = diagnosis.get("root_cause")
affected_count = diagnosis.get("affected_items", 0)
fix_steps = diagnosis.get("fix_steps", [])
can_auto_fix = diagnosis.get("can_auto_fix", False)

if can_auto_fix:
    # Apply fixes automatically
    # (Currently most fixes require manual intervention)
else:
    # Report fix steps to user
    return {
        "root_cause": root_cause,
        "affected_items": affected_count,
        "fix_steps": fix_steps
    }
```

**Common root causes:**
- Download client disabled
- qBittorrent not configured (for torrents)
- NZBGet not configured (for usenet)
- Client connection issues
- Authentication failures

### Step 5: Check Disk Space

Verify disk space is not the issue:

```python
# Check disk space
disk = await check_disk_space()

if disk.get("data", {}).get("status") != "ok":
    # Disk space issue
    return {
        "issue": "Low disk space",
        "usage_percent": disk["data"]["usage_percent"],
        "recommendation": "Clean up old files or increase disk space"
    }
```

**What to check:**
- Root filesystem usage
- Download directory space
- Status: ok, warning (>80%), critical (>90%)

### Step 6: Clear Stuck Items

After fixing root cause, remove stuck items:

```python
# Remove only stuck items
result = await remove_stuck_downloads(
    service="sonarr",
    status_filter=["downloadClientUnavailable", "error"]
)

# Or clear entire queue if needed
if clear_all:
    result = await sonarr_clear_queue(
        blocklist=False,
        remove_from_client=True
    )
```

**Options:**
- Remove only stuck items (recommended)
- Clear entire queue (if queue is completely broken)
- Blocklist items (if they should never be retried)

### Step 7: Verify Resolution

Verify queue is working:

```python
# Check queue again
queue_status = await sonarr_queue_status()

# Verify
if queue_status.get("data", {}).get("stuck_count", 0) == 0:
    return {
        "status": "resolved",
        "message": "Queue is now working correctly"
    }
else:
    return {
        "status": "partial",
        "remaining_stuck": queue_status.get("data", {}).get("stuck_count", 0),
        "action": "Review remaining stuck items"
    }
```

## MCP Tools Used

This skill uses the following MCP tools:

1. **`sonarr_queue_status`** / **`radarr_queue_status`** - Get queue summary
2. **`sonarr_check_download_clients`** / **`radarr_check_download_clients`** - Verify client config
3. **`troubleshoot_failed_downloads`** - Comprehensive diagnostic
4. **`diagnose_download_client_unavailable`** - Specific diagnostic for client issues
5. **`remove_stuck_downloads`** - Remove stuck items from queue
6. **`check_disk_space`** - Verify disk space availability
7. **`sonarr_clear_queue`** / **`radarr_clear_queue`** - Clear entire queue (if needed)

## Examples

### Example 1: Download Client Unavailable

**Symptom**: Queue shows "downloadClientUnavailable" for all torrent items

**Workflow**:
```python
# Step 1: Check queue
queue = await sonarr_queue_status()
# Returns: {"stuck_count": 45, "stuck_items": [{"status": "downloadClientUnavailable", "protocol": "torrent"}]}

# Step 2: Check clients
clients = await sonarr_check_download_clients()
# Returns: {"clients": [{"name": "NZBGet", "enabled": true}], "issues": []}
# Missing: qBittorrent

# Step 3: Diagnose
diagnosis = await diagnose_download_client_unavailable("sonarr")
# Returns: {"root_cause": "qBittorrent not configured for torrent downloads"}

# Step 4: Fix (manual - add qBittorrent in Sonarr settings)
# Host: media-download-gluetun
# Port: 8080
# Username: admin
# Password: adminadmin

# Step 5: Clear stuck items
await remove_stuck_downloads("sonarr", ["downloadClientUnavailable"])

# Step 6: Verify
queue = await sonarr_queue_status()
# Returns: {"stuck_count": 0}
```

### Example 2: Queue Stuck with Errors

**Symptom**: Queue has many items in error status

**Workflow**:
```python
# Step 1: Comprehensive diagnostic
diagnosis = await troubleshoot_failed_downloads("sonarr", include_logs=True)

# Step 2: Analyze
issues = diagnosis.get("queue_issues", {})
# Returns: {"stuck_items": 163, "statuses": ["error", "downloadClientUnavailable"]}

# Step 3: Check disk space
disk = await check_disk_space()
# Returns: {"status": "critical", "usage_percent": 95}

# Root cause: Disk full preventing downloads
# Action: Clean up disk space first

# Step 4: After cleanup, clear stuck items
await remove_stuck_downloads("sonarr", ["error", "downloadClientUnavailable"])

# Step 5: Verify
queue = await sonarr_queue_status()
# Returns: {"stuck_count": 0, "total_items": 0}
```

### Example 3: Client Disabled

**Symptom**: Downloads not processing, client shows as disabled

**Workflow**:
```python
# Step 1: Check clients
clients = await sonarr_check_download_clients()
# Returns: {"issues": [{"client": "qBittorrent", "problem": "Client is disabled"}]}

# Step 2: Fix (enable client in Sonarr settings)

# Step 3: Clear stuck items
await remove_stuck_downloads("sonarr", ["downloadClientUnavailable"])

# Step 4: Verify
queue = await sonarr_queue_status()
# Returns: {"stuck_count": 0}
```

## Error Handling

### No Stuck Items Found

**Action**: Queue is working correctly, no action needed

### Client Configuration Issues

**Action**: 
- Enable disabled clients
- Add missing clients (qBittorrent for torrents, NZBGet for usenet)
- Verify connection settings
- Check authentication credentials

### Disk Space Issues

**Action**: 
- Clean up old files using `cleanup_archive_files` skill
- Remove unused Docker images/volumes
- Increase disk space if possible

### Persistent Issues

**Action**:
- Check download client logs
- Verify network connectivity
- Check VPN status (if using Gluetun)
- Review Sonarr/Radarr logs for errors

## Recommended Fixes by Issue

| Issue | Recommended Fix |
|-------|----------------|
| qBittorrent not configured | Add qBittorrent client: host=media-download-gluetun, port=8080, username=admin, password=adminadmin |
| NZBGet not configured | Add NZBGet client: host=media-download-gluetun, port=6789, username=nzbget, password=nzbget |
| Client disabled | Enable client in Sonarr/Radarr settings |
| Client connection failed | Verify network connectivity, check VPN status |
| Disk full | Clean up archive files, remove unused resources |
| Authentication failed | Verify credentials, check if password changed |

## Related Skills

- **`cleanup-disk-space`** - If disk space is the issue
- **`system-health-check`** - For comprehensive system verification
- **`troubleshoot-container-failure`** - If download clients are failing

## Notes

- Always check download client configuration first - most issues are configuration-related
- qBittorrent requires a permanent password (set via API or WebUI)
- All download clients should connect through Gluetun VPN (media-download-gluetun hostname)
- Clearing the queue is safe - items can be re-added if needed
- Use `remove_stuck_downloads` to only remove problematic items, not the entire queue
