---
name: add-root-folder
description: Add a root folder to Sonarr or Radarr for media organization
category: configuration
mcp_tools_required:
  - radarr_list_root_folders
  - radarr_add_root_folder
  - check_disk_space
prerequisites:
  - Service name (sonarr or radarr)
  - Path to add as root folder
  - MCP tools available
---

# Add Root Folder

## When to Use This Skill

Use this skill when:
- Radarr shows "Missing root folder" error
- Need to add a new media category (e.g., Kids movies)
- Organizing media into separate folders
- Setting up a new root folder path

## Overview

This skill adds a root folder to Sonarr or Radarr:
1. Check existing root folders
2. Verify path is accessible
3. Add new root folder
4. Verify root folder was added
5. Check for unmapped folders

## Workflow Steps

### Step 1: Check Existing Root Folders

List current root folders:

```python
# For Radarr
folders = await radarr_list_root_folders()

# Analyze
existing_paths = [f.get("path") for f in folders.get("folders", [])]
existing_ids = [f.get("id") for f in folders.get("folders", [])]

# Check if path already exists
if new_path in existing_paths:
    return {
        "status": "already_exists",
        "message": f"Root folder {new_path} already configured"
    }
```

**What to check:**
- Existing root folder paths
- Root folder IDs
- Whether path already exists

### Step 2: Verify Path Accessibility

Check if the path is accessible:

```python
# Check disk space (verifies path exists)
disk = await check_disk_space(path=new_path)

# Or check if path exists via container
# (Path should be accessible from within container)
```

**What to verify:**
- Path exists on filesystem
- Path is accessible from container
- Path has sufficient space
- Path matches Docker volume mount

### Step 3: Add Root Folder

Add the new root folder:

```python
# Add root folder
result = await radarr_add_root_folder(path=new_path)

# Analyze result
folder_id = result.get("folder_id")
accessible = result.get("accessible", False)
unmapped_folders = result.get("unmapped_folders", [])

if not accessible:
    return {
        "status": "error",
        "message": f"Path {new_path} is not accessible",
        "action": "Verify path exists and is mounted correctly"
    }
```

**What happens:**
- Radarr validates the path
- Checks accessibility
- Creates root folder entry
- Returns folder ID and unmapped folders

### Step 4: Verify Root Folder Added

Confirm root folder was added:

```python
# List root folders again
folders = await radarr_list_root_folders()

# Verify new folder exists
new_folder = next(
    (f for f in folders.get("folders", []) if f.get("path") == new_path),
    None
)

if new_folder:
    return {
        "status": "success",
        "folder_id": new_folder.get("id"),
        "path": new_folder.get("path"),
        "accessible": new_folder.get("accessible", False)
    }
else:
    return {
        "status": "error",
        "message": "Root folder was not added"
    }
```

### Step 5: Check for Unmapped Folders

Check if there are folders that can now be mapped:

```python
# Get unmapped folders from add result
unmapped = result.get("unmapped_folders", [])

if unmapped:
    return {
        "status": "success",
        "folder_added": True,
        "unmapped_folders": unmapped,
        "message": f"Root folder added. {len(unmapped)} folders can be imported."
    }
```

## MCP Tools Used

This skill uses the following MCP tools:

1. **`radarr_list_root_folders`** - List existing root folders
2. **`radarr_add_root_folder`** - Add new root folder
3. **`check_disk_space`** - Verify path accessibility (optional)

## Examples

### Example 1: Add Kids Movies Folder

**Symptom**: Radarr shows "Missing root folder for movie collection: /movies/Kids/Films"

**Workflow**:
```python
# Step 1: Check existing folders
folders = await radarr_list_root_folders()
# Returns: [{"id": 4, "path": "/movies/Films"}]

# Step 2: Add new root folder
result = await radarr_add_root_folder(path="/movies/Kids/Films")
# Returns: {
#   "folder_id": 5,
#   "path": "/movies/Kids/Films",
#   "accessible": True,
#   "unmapped_folders": [
#     {"name": "Shrek Collection", "path": "/movies/Kids/Films/Shrek Collection"},
#     {"name": "Toy Story Collection", "path": "/movies/Kids/Films/Toy Story Collection"}
#   ]
# }

# Step 3: Verify
folders = await radarr_list_root_folders()
# Returns: [
#   {"id": 4, "path": "/movies/Films"},
#   {"id": 5, "path": "/movies/Kids/Films"}
# ]

# Result: Root folder added successfully, collections can now be imported
```

### Example 2: Add Root Folder for New Category

**User Request**: "Add /movies/Documentaries as a root folder"

**Workflow**:
```python
# Step 1: Check existing
folders = await radarr_list_root_folders()

# Step 2: Add
result = await radarr_add_root_folder(path="/movies/Documentaries")

# Step 3: Verify
if result.get("accessible"):
    return {
        "status": "success",
        "message": f"Root folder added: {result['path']} (ID: {result['folder_id']})"
    }
```

## Error Handling

### Path Already Exists

**Action**: Root folder already configured, no action needed

### Path Not Accessible

**Action**: 
- Verify path exists on filesystem
- Check Docker volume mount configuration
- Verify path is accessible from container
- Check permissions

### Invalid Path

**Action**:
- Verify path format (must be absolute path)
- Check path doesn't contain invalid characters
- Ensure path is within mounted volumes

## Path Configuration Notes

### Radarr Root Folders

**Common paths:**
- `/movies/Films` - Main movies
- `/movies/Kids/Films` - Kids movies
- `/movies/Documentaries` - Documentaries

**Path requirements:**
- Must be absolute path (starting with `/`)
- Must be within Docker volume mount
- Must be accessible from Radarr container

### Docker Volume Mapping

Root folder paths must match Docker volume mounts:
- Host: `/jenquist-cloud/archive/entertainment-media/movies`
- Container: `/movies`
- Root folder: `/movies/Films`

## Related Skills

- **`troubleshoot-stuck-downloads`** - If missing root folder causes import issues
- **`system-health-check`** - To verify system configuration

## Notes

- Root folders are service-specific (Sonarr vs Radarr)
- Paths must match Docker volume mount paths
- Adding root folder doesn't automatically import existing folders
- Use `check_unmapped_folders` to find folders that can be imported
- Root folder ID is used when adding movies/series

