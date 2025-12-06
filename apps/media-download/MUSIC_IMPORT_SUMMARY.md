# Music Import Options Summary

## Your Situation

✅ **You have**: Music files organized by playlist folders  
✅ **You need**: Files organized as `Artist/Album/Track.mp3` for Plex  
✅ **You want**: Playlists imported into Plex

## Option Comparison

| Method | Best For | Pros | Cons | Difficulty |
|--------|----------|------|------|------------|
| **Automated Script** | Quick organization, existing metadata | Fast, preserves playlists, dry-run mode | Requires metadata in files | Easy |
| **beets** | Large collections, missing metadata | Auto-tags from MusicBrainz, handles duplicates | Setup required, Docker recommended | Medium |
| **MusicBrainz Picard** | Manual control, fixing tags | GUI, precise control, great matching | Manual work, time-consuming | Medium |
| **Lidarr** | Future automated downloads | Integrates with your stack | Not ideal for one-time imports | Medium |

## Recommended Approach

### For Your Current Situation: **Automated Script**

1. **Quick**: Run script, review, execute
2. **Safe**: Dry-run mode shows what will happen
3. **Preserves playlists**: Generates playlist mappings
4. **Works with existing metadata**: Uses tags already in files

### For Future Downloads: **beets**

1. **Better metadata**: Matches against MusicBrainz database
2. **Handles missing info**: Fills in artist/album automatically
3. **Deduplicates**: Finds and handles duplicate files
4. **Automated**: Can process folders automatically

## Quick Start (Automated Script)

```bash
# 1. Install dependency
pip3 install mutagen

# 2. Dry run (see what will happen)
cd apps/media-download
python3 organize_music_for_plex.py \
  --source /path/to/playlist/folders \
  --target /jenquist-cloud/archive/entertainment-media/Music

# 3. Execute (copy files)
python3 organize_music_for_plex.py \
  --source /path/to/playlist/folders \
  --target /jenquist-cloud/archive/entertainment-media/Music \
  --execute

# 4. Scan Plex library
# Open Plex → Settings → Library → Scan Library Files

# 5. Create playlists (optional)
export PLEX_TOKEN="your-token"
python3 create_plex_playlist.py --mappings playlist_mappings.json
```

## File Structure

**Before (your current structure):**
```
playlists/
  Playlist 1/
    Song1.mp3
    Song2.mp3
  Playlist 2/
    Song3.mp3
```

**After (Plex structure):**
```
Music/
  Artist Name/
    Album Name/
      01 - Track Title.mp3
      02 - Another Track.mp3
```

## Importing Playlists to Plex

### Method 1: Manual (Easiest)
1. Open Plex Music library
2. Select tracks (Ctrl/Cmd + Click)
3. Add to Playlist → New Playlist
4. Name it

### Method 2: Automated Script
```bash
python3 create_plex_playlist.py \
  --mappings playlist_mappings.json \
  --plex-token "your-token"
```

## Your Paths

- **Plex Music Library**: `/jenquist-cloud/archive/entertainment-media/Music`
- **Lidarr Music Library**: Same location
- **Scripts**: `apps/media-download/`

## Next Steps

1. **Read**: `MUSIC_QUICK_START.md` for step-by-step instructions
2. **Choose**: Automated script (fast) or beets (better metadata)
3. **Run**: Dry run first, then execute
4. **Verify**: Check files in Plex
5. **Create**: Playlists manually or via script

## Need More Details?

- **Quick Start**: See `MUSIC_QUICK_START.md`
- **Full Guide**: See `MUSIC_ORGANIZATION_GUIDE.md`
- **Script Help**: Run `python3 organize_music_for_plex.py --help`

