# LazyLibrarian UI Configuration Guide

## Exact Steps to Add Providers

### Step 1: Access Providers Page

1. Open LazyLibrarian: **http://192.168.86.47:8787**
2. Click **"Config"** in the top menu
3. Click **"Providers"** tab (or look for "Search Providers" or "Newznab/Torznab")

### Step 2: Add NZBHydra2 (Newznab Provider)

**Look for a section labeled:**
- "Newznab Providers" 
- OR "Usenet Providers"
- OR a button/table with "Add Provider" or "+" button

**If you see a table/list:**
1. Click **"Add"** or **"New"** or **"+"** button
2. Fill in these fields:
   - **Name**: `NZBHydra2`
   - **URL** or **Host**: `http://media-download-nzbhydra2:5076`
   - **API Path** or **Path**: `/api`
   - **API Key**: `2SQ42T9209NUIQCAJTPBMTLBJF`
   - **Priority**: `0`
   - **Types**: Check boxes for `E` (Ebooks) and `A` (Audiobooks)
   - **Enabled**: ✓ (check the box)
3. Click **"Save"** or **"Test"** (which also saves)

**If you see form fields directly on the page:**
- Fill in the fields as above
- Look for a **"Save"** or **"Apply"** button at the bottom

### Step 3: Add Jackett (Torznab Provider)

**Look for a section labeled:**
- "Torznab Providers"
- OR "Torrent Providers"  
- OR "Jackett Providers"

**Fill in:**
- **Name**: `Jackett`
- **URL** or **Host**: `http://media-download-jackett:9117`
- **API Path** or **Path**: `/api/v2.0/indexers/all/results/torznab`
- **API Key**: `orjbnk0p7ar5s2u521emxrwb8cjvrz8c`
- **Priority**: `0`
- **Seeders** or **Min Seeders**: `0`
- **Types**: Check boxes for `E` (Ebooks) and `A` (Audiobooks)
- **Enabled**: ✓ (check the box)
- Click **"Save"**

### Step 4: Test Providers

After adding each provider:
1. Look for a **"Test"** button next to each provider
2. Click it to verify the connection works
3. You should see a success message

### If You Can't Find the Providers Section

**Alternative locations to check:**
1. **Config** > **Search** tab
2. **Config** > **Indexers** tab
3. **Config** > **Newznab** tab
4. **Config** > **Torznab** tab
5. Look for a **"+"** or **"Add"** button anywhere in the Config area

**If the page looks empty or you only see download clients:**
- The providers section might be on a different tab
- Try clicking through all tabs in the Config menu
- Look for any section mentioning "Newznab", "Torznab", "Providers", or "Indexers"

### Screenshot Locations

The providers are typically configured in one of these locations:
- A table with columns: Name, URL, API Key, Enabled, etc.
- A form with labeled input fields
- Expandable sections that you click to open

### Still Can't Find It?

If you absolutely cannot find where to add providers:
1. Take a screenshot of the Config > Providers page
2. Or describe what you see on that page
3. The UI might be different than expected

### Quick Values Reference

**NZBHydra2:**
- URL: `http://media-download-nzbhydra2:5076`
- API Path: `/api`
- API Key: `2SQ42T9209NUIQCAJTPBMTLBJF`

**Jackett:**
- URL: `http://media-download-jackett:9117`
- API Path: `/api/v2.0/indexers/all/results/torznab`
- API Key: `orjbnk0p7ar5s2u521emxrwb8cjvrz8c`

