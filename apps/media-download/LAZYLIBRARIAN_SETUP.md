# LazyLibrarian Setup Guide

## Quick Configuration Steps

### Step 1: Enable API (Optional, for automation)
1. Open LazyLibrarian: http://192.168.86.47:8787
2. Go to **Config** > **General**
3. Find **API Key** section
4. Click **Generate** or copy the existing API key
5. Enable **API** if there's a checkbox

### Step 2: Configure NZBHydra2 Indexer

1. Go to **Config** > **Providers** (or **Search Providers**)
2. Click **Add Provider** or find the **Newznab** section
3. Fill in:
   - **Name**: `NZBHydra2`
   - **URL**: `http://media-download-nzbhydra2:5076`
   - **API Path**: `/api`
   - **API Key**: `2SQ42T9209NUIQCAJTPBMTLBJF`
   - **Priority**: `0` (or leave default)
   - **Types**: Check `E` (Ebooks) and `A` (Audiobooks)
   - **Enabled**: ✓ (check the box)
4. Click **Test** to verify connection
5. Click **Save**

### Step 3: Configure Jackett Indexer

1. Still in **Config** > **Providers**
2. Click **Add Provider** or find the **Torznab** section
3. Fill in:
   - **Name**: `Jackett`
   - **URL**: `http://media-download-jackett:9117`
   - **API Path**: `/api/v2.0/indexers/all/results/torznab`
   - **API Key**: `orjbnk0p7ar5s2u521emxrwb8cjvrz8c`
   - **Priority**: `0` (or leave default)
   - **Seeders**: `0` (minimum seeders, 0 = no minimum)
   - **Types**: Check `E` (Ebooks) and `A` (Audiobooks)
   - **Enabled**: ✓ (check the box)
4. Click **Test** to verify connection
5. Click **Save**

### Step 4: Configure NZBGet Download Client

1. Go to **Config** > **Downloaders** (or **Download Clients**)
2. Find **NZBGet** section
3. Fill in:
   - **Host**: `media-download-gluetun`
   - **Port**: `6789`
   - **Username**: `nzbget`
   - **Password**: `nzbget`
   - **Category**: `books`
   - **Priority**: `0` (or leave default)
   - **Enabled**: ✓ (check the box)
4. Click **Test** to verify connection
5. Click **Save**

### Step 5: Configure Metadata Sources

1. Go to **Config** > **General** (or **Metadata**)
2. Find **Book API** or **Metadata Provider** section
3. Set to **Open Library** (not Goodreads!)
4. Enable **Open Library API**: ✓
5. Click **Save**

### Step 6: Add Books

1. Go to **Authors** or **Wishlist** tab
2. Click **Add Author** or **Add Book**
3. Search by:
   - Author name
   - Book title
   - ISBN
4. Add books to your wishlist
5. LazyLibrarian will automatically search and download!

## Configuration Summary

### Indexers
- **NZBHydra2**: `http://media-download-nzbhydra2:5076/api` (API key: `2SQ42T9209NUIQCAJTPBMTLBJF`)
- **Jackett**: `http://media-download-jackett:9117/api/v2.0/indexers/all/results/torznab` (API key: `orjbnk0p7ar5s2u521emxrwb8cjvrz8c`)

### Download Client
- **NZBGet**: `http://media-download-gluetun:6789` (username: `nzbget`, password: `nzbget`)

### Metadata
- **Use Open Library** (not Goodreads - avoids timeout issues!)

## Troubleshooting

- **Can't connect to indexers?** Make sure they're running: `docker ps | grep -E 'nzbhydra2|jackett'`
- **No search results?** Check that indexers are enabled and tested successfully
- **Downloads not starting?** Verify NZBGet is configured and tested
- **Metadata not loading?** Make sure Open Library is enabled, not Goodreads

