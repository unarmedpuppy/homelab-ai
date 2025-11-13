# Media Download Stack - Agent Tools

Quick reference for agent tools to manage Sonarr/Radarr/NZBGet.

## Quick Start

```bash
# Install dependencies (if using Python approach)
cd apps/media-download/tools
pip install -r requirements.txt

# Run a tool
python -m tools.cli clear_sonarr_queue

# Or via remote execution
bash ../../scripts/connect-server.sh "cd ~/server/apps/media-download && python3 -m tools.cli clear_sonarr_queue"
```

## Tool Reference

### Queue Management

```python
# Clear entire queue
clear_sonarr_queue(blocklist=False, remove_from_client=True)
clear_radarr_queue(blocklist=False, remove_from_client=True)

# Get queue status
get_sonarr_queue_status()  # Returns: {total_items, by_status, by_protocol, stuck_items}
get_radarr_queue_status()

# Remove only stuck items
remove_stuck_downloads(service="sonarr", status_filter=["downloadClientUnavailable"])
```

### Import & Scans

```python
# Trigger manual import scans
trigger_sonarr_import_scan(path="/downloads/completed/tv")
trigger_radarr_import_scan(path="/downloads/completed/movies")

# Check import progress
check_import_progress(service="sonarr", command_id=None)
```

### Download Clients

```python
# Check client status
check_download_clients(service="sonarr")
# Returns: {clients: [...], connection_status: {...}, issues: [...]}

# Configure qBittorrent
configure_qbittorrent(
    service="sonarr",
    host="media-download-gluetun",
    port=8080,
    username="admin",
    password="adminadmin",
    category="tv"
)

# Set qBittorrent password
set_qbittorrent_password(password="adminadmin", temp_password=None)
```

### Root Folders

```python
# List root folders
list_root_folders(service="radarr")

# Add root folder
add_root_folder(service="radarr", path="/movies/Kids/Films")

# Check for missing root folders
check_missing_root_folders(service="radarr")
```

### Troubleshooting

```python
# Comprehensive troubleshooting
troubleshoot_failed_downloads(service="sonarr", include_logs=True)

# Specific diagnostic
diagnose_download_client_unavailable(service="sonarr")

# Health check
check_service_health(service="all")  # or "sonarr", "radarr", etc.
```

### Library Management

```python
# List library contents
list_sonarr_series(search=None)
list_radarr_movies(search=None, root_folder=None)

# Find unmapped folders
check_unmapped_folders(service="sonarr", root_folder_id=None)
```

### Logs & Diagnostics

```python
# Get recent errors
get_recent_errors(service="sonarr", lines=50, level="error")

# Check disk space
check_disk_space(path="/")

# Cleanup archive files
cleanup_archive_files(dry_run=False, category="all")
```

## Common Workflows

### Fix Stuck Queue

```python
# 1. Diagnose the problem
diagnosis = diagnose_download_client_unavailable("sonarr")

# 2. Apply fixes
if "qBittorrent not configured" in diagnosis["root_cause"]:
    configure_qbittorrent("sonarr")

# 3. Clear stuck items
remove_stuck_downloads("sonarr")
```

### Fix Missing Root Folder Error

```python
# 1. Check what's missing
missing = check_missing_root_folders("radarr")

# 2. Add missing folders
for path in missing["missing_paths"]:
    add_root_folder("radarr", path)
```

### Complete Troubleshooting Workflow

```python
# 1. Run comprehensive check
health = check_service_health("all")

# 2. If issues found, troubleshoot each service
if health["status"] != "healthy":
    for service in ["sonarr", "radarr"]:
        issues = troubleshoot_failed_downloads(service)
        
        # 3. Apply recommended fixes
        for rec in issues["recommendations"]:
            apply_fix(rec)  # Helper function to parse and apply
```

## Error Handling

All tools return a standard response format:

```python
# Success
{
    "status": "success",
    "data": {...},  # Tool-specific data
    "message": "Operation completed successfully"
}

# Error
{
    "status": "error",
    "error_type": "ConnectionError",
    "message": "Could not connect to Sonarr",
    "details": {
        "service": "sonarr",
        "operation": "clear_queue",
        "suggestion": "Check if container is running"
    }
}
```

## Configuration

Tools automatically load configuration from:
1. Environment variables (e.g., `SONARR_API_KEY`)
2. `tools/config.json` file
3. Default values from `PIRATE_AGENT_CONTEXT.md`

To override defaults, create `tools/config.json`:
```json
{
    "sonarr": {
        "api_key": "your-key-here"
    },
    "radarr": {
        "api_key": "your-key-here"
    }
}
```

