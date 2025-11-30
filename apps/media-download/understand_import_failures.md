# Understanding "Downloaded but Failed to Import" Issues

## What's Happening

When Sonarr/Radarr says a file is "downloaded" but "failed to import", here's what's actually happening:

### The Download Process

1. **Download Starts**: Sonarr/Radarr sends the download to NZBGet/qBittorrent
2. **Download Completes**: NZBGet/qBittorrent finishes downloading the files
3. **Post-Processing**: NZBGet may need to:
   - Repair files (par2)
   - Unpack/extract files (from .rar or .zip)
   - Move files to the completed directory
4. **Import Attempt**: Sonarr/Radarr tries to find and import the files
5. **Import Fails**: Sonarr/Radarr can't find the files where it expects them

### Common Reasons for Import Failures

#### 1. **Files in Wrong Location**
- **Problem**: Files are in `/downloads/` instead of `/downloads/completed/tv/` or `/downloads/completed/movies/`
- **Why**: Download was added without a category, or category wasn't applied
- **Solution**: Use Manual Import and browse to where files actually are

#### 2. **Files Still Unpacking**
- **Problem**: Download shows "complete" but files are still being extracted
- **Why**: Large downloads take time to unpack
- **Solution**: Wait a few minutes, then try manual import

#### 3. **Files in Intermediate Directory**
- **Problem**: Files are in `/downloads/intermediate/` instead of `/downloads/completed/`
- **Why**: Download failed health check or is still processing
- **Solution**: Check NZBGet history for download status

#### 4. **Path Mapping Issue**
- **Problem**: Sonarr/Radarr can't see files because of path mismatch
- **Why**: Remote path mapping doesn't match actual file location
- **Solution**: Check Settings > Download Clients > Remote Path Mappings

#### 5. **Files Deleted/Moved**
- **Problem**: Files were deleted or moved after download
- **Why**: Cleanup script, manual deletion, or disk space issue
- **Solution**: Check NZBGet history to see if files were deleted

## How to Diagnose

### Step 1: Check Where Files Actually Are

```bash
# From Sonarr container
docker exec media-download-sonarr find /downloads -name "*ShowName*" -type f

# From NZBGet container  
docker exec media-download-nzbget find /downloads -name "*ShowName*" -type f
```

### Step 2: Check NZBGet History

1. Open NZBGet web UI: http://192.168.86.47:6789
2. Go to **History** tab
3. Find the download
4. Check:
   - **Status**: Should be "SUCCESS/UNPACK"
   - **DestDir**: Where files were saved
   - **Category**: Should be "tv" or "movies"

### Step 3: Check Sonarr/Radarr Queue

1. Go to **Activity** > **Queue**
2. Find the failed import
3. Click on it to see:
   - **Output Path**: Where Sonarr thinks files should be
   - **Status Messages**: Why import failed

### Step 4: Manual Import

1. Go to **Activity** > **Queue**
2. Find the failed import
3. Click the **manual import icon** (folder icon)
4. Browse to where files actually are
5. Select the video files
6. Click **Import**

## Common File Locations

### Expected Locations (with category):
- TV Shows: `/downloads/completed/tv/ShowName/`
- Movies: `/downloads/completed/movies/MovieName/`

### Actual Locations (when category missing):
- `/downloads/ShowName/` or `/downloads/MovieName/`
- `/downloads/intermediate/ShowName/`

## Prevention

1. **Always use categories**: Ensure Sonarr/Radarr send downloads with category "tv" or "movies"
2. **Check download client settings**: Verify category is set correctly
3. **Monitor downloads**: Check NZBGet history to see where files are saved
4. **Set up remote path mappings**: Configure correctly in Sonarr/Radarr

## Quick Fix Script

See `fix_sonarr_import_paths.py` for automated diagnosis and fixes.

