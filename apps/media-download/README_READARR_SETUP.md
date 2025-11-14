# Readarr Setup Guide

## Current Issues
1. **NZBGet Authentication Failed**: Readarr can't authenticate with NZBGet
2. **All Download Clients Unavailable**: Download clients not configured correctly
3. **No Search Results**: Indexers not configured

## Quick Fix

### Step 1: Get Readarr API Key

1. Open Readarr: http://192.168.86.47:8787
2. Go to: Settings > General > Security
3. Copy the API Key

Or get it from config file on server:
```bash
bash scripts/connect-server.sh "cat ~/server/apps/media-download/readarr/config/config.xml | grep ApiKey"
```

### Step 2: Run Fix Script

**Option A: Run locally (if you have API key)**
```bash
cd apps/media-download
python3 fix_readarr.py YOUR_READARR_API_KEY
```

**Option B: Run on server**
```bash
# Copy script to server
bash scripts/connect-server.sh "cd ~/server/apps/media-download && python3 fix_readarr.py YOUR_READARR_API_KEY"
```

### Step 3: Get Indexer API Keys

**NZBHydra2 API Key:**
1. Open NZBHydra2: http://192.168.86.47:5076
2. Go to: Config > Main
3. Copy the API Key

**Jackett API Key:**
1. Open Jackett: http://192.168.86.47:9117
2. Click the API key button (top right)
3. Copy the API Key

The script will prompt for these if not provided.

## Manual Configuration

### Configure NZBGet Download Client

1. Open Readarr: http://192.168.86.47:8787
2. Go to: Settings > Download Clients
3. Click: Add Download Client > NZBGet
4. Configure:
   - **Name**: NZBGet
   - **Host**: `media-download-gluetun`
   - **Port**: `6789`
   - **Username**: `nzbget`
   - **Password**: `nzbget`
   - **Category**: `books`
   - **Use SSL**: No
5. Click: Test (should pass)
6. Click: Save

### Configure Indexers

#### NZBHydra2 Indexer

1. Go to: Settings > Indexers
2. Click: Add Indexer > Newznab
3. Configure:
   - **Name**: NZBHydra2
   - **URL**: `http://media-download-nzbhydra2:5076/nzbhydra2`
   - **API Key**: (from NZBHydra2 config)
   - **Categories**: 
     - 3030 (E-Book)
     - 7000-7060 (Book categories)
4. Click: Test (should pass)
5. Click: Save

#### Jackett Indexer

1. Go to: Settings > Indexers
2. Click: Add Indexer > Torznab
3. Configure:
   - **Name**: Jackett
   - **URL**: `http://media-download-jackett:9117`
   - **API Key**: (from Jackett UI)
   - **Categories**: 
     - 3030 (E-Book)
     - 7000-7060 (Book categories)
4. Click: Test (should pass)
5. Click: Save

## Verification

### Test Download Client

1. Go to: Settings > Download Clients
2. Click: Test button next to NZBGet
3. Should show: "Connection successful"

### Test Indexers

1. Go to: Settings > Indexers
2. Click: Test button next to each indexer
3. Should show: "Indexer is working correctly"

### Test Search

1. Go to: Add New > Search
2. Search for a book (e.g., "Harry Potter")
3. Should show results from indexers

## Troubleshooting

### NZBGet Authentication Failed

**Symptoms:**
- "Unable to communicate with NZBGet"
- "Authentication failed for NzbGet"

**Fix:**
1. Verify NZBGet credentials:
   - Username: `nzbget`
   - Password: `nzbget`
   - Host: `media-download-gluetun` (NOT `media-download-nzbget`)
   - Port: `6789`
2. Test connection in Readarr: Settings > Download Clients > Test
3. Check NZBGet is running:
   ```bash
   bash scripts/connect-server.sh "docker ps | grep nzbget"
   ```

### No Search Results

**Symptoms:**
- No results when searching for books
- "All download clients are unavailable"

**Fix:**
1. Verify indexers are configured:
   - Settings > Indexers
   - Should see NZBHydra2 and/or Jackett
2. Test each indexer:
   - Click Test button
   - Should show "Indexer is working correctly"
3. Check indexer categories:
   - Should include book categories (3030, 7000-7060)
4. Verify indexers are running:
   ```bash
   bash scripts/connect-server.sh "docker ps | grep -E 'nzbhydra2|jackett'"
   ```

### All Download Clients Unavailable

**Symptoms:**
- Red error in Readarr UI
- "All download clients are unavailable due to failures"

**Fix:**
1. Check download client configuration (see above)
2. Verify network connectivity:
   - Readarr can reach `media-download-gluetun:6789`
3. Restart Readarr:
   ```bash
   bash scripts/connect-server.sh "cd ~/server/apps/media-download && docker-compose restart readarr"
   ```

## Configuration Reference

### NZBGet Settings
- **Host**: `media-download-gluetun` (routed through VPN)
- **Port**: `6789`
- **Username**: `nzbget`
- **Password**: `nzbget`
- **Category**: `books`

### Indexer URLs
- **NZBHydra2**: `http://media-download-nzbhydra2:5076/nzbhydra2`
- **Jackett**: `http://media-download-jackett:9117`

### Book Categories (Newznab/Torznab)
- `3030` - E-Book
- `7000` - Misc Books
- `7010` - Comics
- `7020` - Magazines
- `7030` - E-Learning
- `7040` - Fiction
- `7050` - Non-Fiction
- `7060` - Technical Documentation

