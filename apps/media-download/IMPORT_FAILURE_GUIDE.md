# Understanding "Downloaded but Failed to Import" - Complete Guide

## The Problem

You see: **"Downloaded - Waiting to Import"** but when you try to manually import, you can't find the files.

## What's Actually Happening

### The Download Flow

```
1. Sonarr/Radarr → Sends download to NZBGet
   └─> Includes category: "tv" or "movies"
   
2. NZBGet → Downloads files
   └─> Saves to: /downloads/completed/tv/ (if category = "tv")
   └─> OR saves to: /downloads/ (if NO category)
   
3. Sonarr/Radarr → Looks for files
   └─> Expects: /downloads/completed/tv/ShowName/
   └─> But finds: /downloads/ShowName/ (WRONG LOCATION!)
   
4. Import Fails → "No files found"
```

### Why Files Are in the Wrong Place

**Problem**: Download was added **without a category** or category wasn't applied.

**Result**: 
- Files go to `/downloads/ShowName/` (main directory)
- Sonarr expects `/downloads/completed/tv/ShowName/` (category directory)
- **Mismatch = Import fails**

## How to Find Your Files

### Method 1: Check NZBGet History (Best Method)

1. Open NZBGet: http://192.168.86.47:6789
2. Click **History** tab
3. Find your download
4. Look at **DestDir** column - **THIS is where files actually are**
5. Use that path for Manual Import

### Method 2: Search from Command Line

```bash
# Search for files
docker exec media-download-sonarr find /downloads -name "*ShowName*" -type f

# Or search for directories
docker exec media-download-sonarr find /downloads -type d -name "*ShowName*"
```

### Method 3: Check Common Locations

Files might be in:
- `/downloads/ShowName/` (wrong - no category)
- `/downloads/completed/tv/ShowName/` (correct - with category)
- `/downloads/intermediate/ShowName/` (still processing)

## How to Fix It

### For Existing Files (Manual Import)

1. **Open Sonarr/Radarr** → **Activity** → **Queue**
2. Find the failed import
3. Click the **Manual Import icon** (folder icon)
4. **IMPORTANT**: Don't use the default path shown
5. Click **Browse** and navigate to where files **actually are**
   - If files are in `/downloads/ShowName/`, browse there
   - If files are in `/downloads/completed/tv/ShowName/`, browse there
6. Select the video files (`.mkv`, `.mp4`, etc.)
7. Click **Import**

### For Future Downloads (Prevention)

**Ensure category is set correctly:**

1. **Sonarr**: Settings → Download Clients → NZBGet
   - Check **Category** field = `tv`
   
2. **Radarr**: Settings → Download Clients → NZBGet
   - Check **Category** field = `movies`

3. **Verify in NZBGet**: Settings → Categories
   - Should see: `tv` → `/downloads/completed/tv`
   - Should see: `movies` → `/downloads/completed/movies`

## Common Scenarios

### Scenario 1: Files in `/downloads/` (No Category)

**Symptom**: Files in `/downloads/ShowName/` but Sonarr expects `/downloads/completed/tv/ShowName/`

**Solution**: 
- Use Manual Import
- Browse to `/downloads/ShowName/`
- Import files

**Prevention**: Set category to "tv" in Sonarr download client settings

### Scenario 2: Files Still Unpacking

**Symptom**: Download shows "complete" but directory is empty or has `.rar` files

**Solution**: 
- Wait 5-10 minutes
- Check NZBGet History → Status should be "SUCCESS/UNPACK"
- Then try Manual Import

### Scenario 3: Files in Intermediate Directory

**Symptom**: Files in `/downloads/intermediate/ShowName/`

**Solution**: 
- Check NZBGet History → Status
- If "FAILURE/HEALTH" → Download had errors
- If "DOWNLOADING" → Still downloading
- Wait for completion, then import

### Scenario 4: Empty Directory

**Symptom**: Directory exists but is empty

**Possible causes**:
- Download failed
- Files were deleted
- Files moved elsewhere
- Still unpacking

**Solution**: 
- Check NZBGet History for actual status
- Check if files are in a subdirectory
- Check if files were moved to completed directory

## Quick Diagnostic Commands

```bash
# Find all video files in downloads
docker exec media-download-sonarr find /downloads -type f \( -name "*.mkv" -o -name "*.mp4" \) | head -20

# Find specific show
docker exec media-download-sonarr find /downloads -name "*ShowName*" -type f

# Check NZBGet history via API
curl -u nzbget:nzbget http://192.168.86.47:6789/jsonrpc -d '{"method":"history","params":[false]}'
```

## Summary

**The Key Insight**: 
- Files ARE downloaded successfully
- Files ARE somewhere on disk
- Sonarr just can't FIND them because they're in the wrong location
- **Manual Import** lets you point Sonarr to where files actually are

**The Fix**:
1. Find where files actually are (NZBGet History)
2. Use Manual Import
3. Browse to that location
4. Import files

**Prevention**:
- Always ensure category is set in download client settings
- Monitor NZBGet History to see where files are saved
- Set up remote path mappings correctly

