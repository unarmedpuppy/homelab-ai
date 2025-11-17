# Improving Music Downloads in Lidarr

Music indexers are generally less reliable than TV/movie indexers. Here are the best ways to improve your music download success rate.

## 🎯 Quick Fix: Add Music Indexers to NZBHydra2

**Step 1: Sign up for music-focused Usenet indexers**

Recommended indexers (best for music):
- **NZBGeek** ($15 lifetime): https://nzbgeek.info/ - Most popular, good music coverage
- **DrunkenSlug** ($10/year): https://drunkenslug.com/ - Excellent automation, good catalog
- **NZBPlanet** ($10/year): https://www.nzbplanet.net/ - Solid coverage, affordable

**Step 2: Add to NZBHydra2**

1. Open NZBHydra2: http://192.168.86.47:5076
2. Go to **Settings** → **Indexers** → **Add indexer**
3. Select **Newznab** type
4. Fill in:
   - **Name**: NZBGeek (or DrunkenSlug, etc.)
   - **Host**: `api.nzbgeek.info` (check indexer's docs for exact URL)
   - **API Key**: (from your indexer account)
   - **Categories**: `3000,3010,3040` (Music categories: 3000=Music, 3010=MP3, 3040=Lossless)
5. Click **Test** to verify
6. Click **Save**

**Step 3: Update Lidarr to use NZBHydra2**

If not already configured, add NZBHydra2 to Lidarr:
- URL: `http://media-download-nzbhydra2:5076`
- API Path: `/api`
- API Key: (from NZBHydra2 settings)

## 🚀 Better Solution: Use Prowlarr (Recommended)

Prowlarr is a unified indexer manager that works better with Lidarr than NZBHydra2.

### Step 1: Start Prowlarr

```bash
cd apps/media-download
mkdir -p prowlarr/config
docker-compose up -d prowlarr
```

Access at: http://192.168.86.47:9696

### Step 2: Add Music Indexers to Prowlarr

1. Open Prowlarr: http://192.168.86.47:9696
2. Go to **Indexers** → **Add Indexer**
3. Search for or add:
   - **NZBGeek** (Newznab)
   - **DrunkenSlug** (Newznab)
   - **NZBPlanet** (Newznab)
   - Any other music indexers you have

4. For each indexer:
   - Enter your API key
   - Set **Categories** to: `3000,3010,3040` (Music)
   - Test and save

### Step 3: Connect Prowlarr to Lidarr

**In Prowlarr:**
1. Go to **Apps** → **Add Application**
2. Select **Lidarr**
3. Fill in:
   - **Name**: Lidarr
   - **Prowlarr URL**: `http://media-download-prowlarr:9696`
   - **Lidarr URL**: `http://media-download-lidarr:8686`
   - **API Key**: (Lidarr API key from Settings > General > Security)
4. Click **Test** and **Save**

**In Lidarr:**
1. Go to **Settings** → **Indexers**
2. Prowlarr should auto-sync (if configured above)
3. Or manually add:
   - **Add Indexer** → **Prowlarr**
   - **URL**: `http://media-download-prowlarr:9696`
   - **API Key**: (from Prowlarr Settings > General > API Key)

### Step 4: Add Torrent Indexers (Optional)

In Prowlarr, you can also add torrent indexers:
1. Go to **Indexers** → **Add Indexer**
2. Search for torrent trackers (Jackett-style)
3. Add music-focused trackers if available

## 🎵 Additional Options

### Option 1: Tubifarry Plugin (YouTube + Soulseek)

Adds YouTube and Soulseek as music sources:

1. In Lidarr: **System** → **General** → Change branch to **plugins**
2. Update Lidarr
3. **System** → **Plugins** → Add from URL: `https://github.com/TypNull/Tubifarry`
4. Install and configure

### Option 2: Soularr (Soulseek Integration)

Integrates Soulseek network for rare/hard-to-find music:
- Website: https://www.soularr.net/
- Requires separate setup

## 📊 Why Music Downloads Fail

1. **Less content available**: Music has less Usenet/torrent coverage than TV/movies
2. **Quality expectations**: People want FLAC/lossless, which is rarer
3. **Copyright enforcement**: Music is more aggressively protected
4. **Indexer quality**: Many indexers focus on TV/movies, not music

## ✅ Best Practices

1. **Use multiple indexers**: Don't rely on just one
2. **Check quality profiles**: Make sure Lidarr accepts the formats you want
3. **Be patient**: Music downloads can take longer to find
4. **Consider manual downloads**: For rare albums, manual search/download may be needed
5. **Use Prowlarr**: It's better integrated with Lidarr than NZBHydra2

## 🔍 Troubleshooting

**No results found:**
- Check indexers are enabled and tested in Prowlarr/NZBHydra2
- Verify categories include music (3000, 3010, 3040)
- Try searching manually in the indexer's web UI

**Downloads not starting:**
- Verify download client (NZBGet) is configured correctly
- Check Lidarr logs: **System** → **Logs**

**Poor quality results:**
- Adjust quality profiles in Lidarr: **Settings** → **Quality**
- Set minimum file sizes for different formats

## 💰 Cost Estimate

**Minimum (good results):**
- 1-2 indexers: $10-15/year
- Total: ~$1-2/month

**Recommended:**
- 2-3 indexers: $20-30/year
- Total: ~$2-3/month

**Best value:** NZBGeek lifetime ($15 one-time) + DrunkenSlug ($10/year)

