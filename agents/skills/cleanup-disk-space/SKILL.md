---
name: cleanup-disk-space
description: Clean up disk space by removing archive files and unused resources
category: maintenance
mcp_tools_required:
  - check_disk_space
  - cleanup_archive_files
  - docker_list_images
  - docker_prune_images
  - docker_list_volumes
  - docker_prune_volumes
prerequisites:
  - MCP tools available
  - Disk space issue identified
---

# Cleanup Disk Space

## When to Use This Skill

Use this skill when:
- Disk space is above 80% usage
- Disk space is critical (>90%)
- System health check shows disk space warnings
- Downloads failing due to disk space
- User requests disk cleanup

## Overview

This skill provides a systematic approach to freeing disk space:
1. Check current disk usage
2. Identify cleanup opportunities
3. Remove archive files from completed downloads
4. Remove unused Docker resources
5. Verify space freed
6. Report results

## Workflow Steps

### Step 1: Check Current Disk Space

Get current disk usage:

```python
# Check disk space
disk = await check_disk_space()

# Analyze
usage_percent = disk.get("data", {}).get("usage_percent", 0)
status = disk.get("data", {}).get("status", "ok")
available = disk.get("data", {}).get("available", "unknown")

if status == "critical":
    # Urgent cleanup needed
    priority = "high"
elif status == "warning":
    # Cleanup recommended
    priority = "medium"
else:
    # Preventive cleanup
    priority = "low"
```

**What to check:**
- Current usage percentage
- Available space
- Status: ok, warning (>80%), critical (>90%)

### Step 2: Clean Up Archive Files

Remove unpacked archive files from completed downloads:

```python
# First, do a dry run to see what would be removed
dry_run = await cleanup_archive_files(
    dry_run=True,
    category="all"  # or "tv", "movies", "music", "books"
)

# Review what would be removed
files_to_remove = dry_run.get("files_removed_list", [])
count = dry_run.get("files_removed", 0)

# If acceptable, proceed with actual cleanup
if count > 0:
    result = await cleanup_archive_files(
        dry_run=False,
        category="all"
    )
    
    space_freed = result.get("space_freed", "unknown")
    files_removed = result.get("files_removed", 0)
```

**What gets removed:**
- `.rar` files (after extraction)
- `.par2` files (parity files)
- `.nzb` files (Usenet index files)

**Safety:**
- Only removes files from completed download directories
- Only removes files where videos are already extracted
- Dry run available to preview changes

### Step 3: Clean Up Docker Images

Remove unused Docker images:

```python
# List all images
images = await docker_list_images()

# Identify unused images
# (Images not used by any running container)

# Prune unused images
prune_result = await docker_prune_images()

# Get space freed
space_freed = prune_result.get("space_freed", "unknown")
images_removed = prune_result.get("images_removed", 0)
```

**What gets removed:**
- Dangling images (untagged)
- Unused images (not referenced by containers)
- Old image layers

**Safety:**
- Only removes images not in use
- Preserves images used by running containers

### Step 4: Clean Up Docker Volumes

Remove unused Docker volumes:

```python
# List all volumes
volumes = await docker_list_volumes()

# Prune unused volumes
prune_result = await docker_prune_volumes()

# Get space freed
space_freed = prune_result.get("space_freed", "unknown")
volumes_removed = prune_result.get("volumes_removed", 0)
```

**What gets removed:**
- Unused volumes (not attached to containers)

**Safety:**
- Only removes volumes not in use
- Preserves volumes attached to running containers
- **Warning**: Make sure volumes don't contain important data

### Step 5: Verify Space Freed

Check disk space after cleanup:

```python
# Check disk space again
disk_after = await check_disk_space()

# Calculate improvement
usage_before = usage_percent
usage_after = disk_after.get("data", {}).get("usage_percent", 0)
improvement = usage_before - usage_after

# Report results
return {
    "status": "success",
    "usage_before": usage_before,
    "usage_after": usage_after,
    "improvement": improvement,
    "space_freed": {
        "archive_files": archive_space_freed,
        "docker_images": images_space_freed,
        "docker_volumes": volumes_space_freed,
        "total": total_space_freed
    }
}
```

## MCP Tools Used

This skill uses the following MCP tools:

1. **`check_disk_space`** - Check current disk usage
2. **`cleanup_archive_files`** - Remove archive files from downloads
3. **`docker_list_images`** - List Docker images
4. **`docker_prune_images`** - Remove unused Docker images
5. **`docker_list_volumes`** - List Docker volumes
6. **`docker_prune_volumes`** - Remove unused Docker volumes

## Examples

### Example 1: Critical Disk Space

**Symptom**: Disk at 95% usage, downloads failing

**Workflow**:
```python
# Step 1: Check disk
disk = await check_disk_space()
# Returns: {"usage_percent": 95, "status": "critical"}

# Step 2: Clean archive files (biggest impact)
archive_result = await cleanup_archive_files(dry_run=False, category="all")
# Returns: {"files_removed": 1937, "space_freed": "200G"}

# Step 3: Prune Docker images
images_result = await docker_prune_images()
# Returns: {"images_removed": 15, "space_freed": "5G"}

# Step 4: Verify
disk_after = await check_disk_space()
# Returns: {"usage_percent": 78, "status": "ok"}

# Result: Freed 205G, reduced usage from 95% to 78%
```

### Example 2: Preventive Cleanup

**Symptom**: Disk at 82% usage, want to prevent issues

**Workflow**:
```python
# Step 1: Check disk
disk = await check_disk_space()
# Returns: {"usage_percent": 82, "status": "warning"}

# Step 2: Dry run first
dry_run = await cleanup_archive_files(dry_run=True, category="all")
# Returns: {"files_removed": 500, "space_freed": "50G"}

# Step 3: Clean archive files
archive_result = await cleanup_archive_files(dry_run=False, category="all")

# Step 4: Verify
disk_after = await check_disk_space()
# Returns: {"usage_percent": 75, "status": "ok"}
```

### Example 3: Category-Specific Cleanup

**Symptom**: TV downloads directory has many archive files

**Workflow**:
```python
# Clean only TV category
result = await cleanup_archive_files(
    dry_run=False,
    category="tv"
)

# Returns: {"files_removed": 800, "space_freed": "80G", "category": "tv"}
```

## Error Handling

### No Files to Remove

**Action**: No cleanup needed, disk space is already optimized

### Docker Prune Fails

**Action**: 
- Check if Docker daemon is accessible
- Verify permissions
- Try individual cleanup steps

### Insufficient Space Freed

**Action**:
- Check for large files manually
- Review download directories for large files
- Consider increasing disk space
- Check for log file accumulation

## Recommended Cleanup Order

1. **Archive files** (usually biggest impact, safest)
2. **Docker images** (can free significant space)
3. **Docker volumes** (careful - may contain data)
4. **Log files** (if applicable)
5. **Old backups** (if applicable)

## Safety Considerations

### Archive Files
- ✅ Safe: Only removes files after extraction
- ✅ Safe: Only in completed download directories
- ✅ Safe: Dry run available

### Docker Images
- ✅ Safe: Only removes unused images
- ✅ Safe: Preserves images in use
- ⚠️ Note: May need to re-download images later

### Docker Volumes
- ⚠️ Warning: Only remove if sure volumes don't contain important data
- ⚠️ Warning: Check volume contents before removing
- ✅ Safe: Only removes unused volumes

## Related Skills

- **`system-health-check`** - To identify disk space issues
- **`troubleshoot-stuck-downloads`** - If disk space is causing download issues

## Notes

- Archive file cleanup is the safest and usually most effective cleanup
- Always do a dry run first to preview changes
- Docker image/volume cleanup should be done carefully
- Regular cleanup prevents critical disk space issues
- Monitor disk space after cleanup to verify improvement

