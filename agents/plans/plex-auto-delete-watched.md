# Plex Auto-Delete Watched Episodes

## Overview

Automatically delete watched TV episodes after a configurable time period, with the ability to protect specific shows from deletion.

## Requirements

1. **Auto-delete watched episodes** after X days (configurable per-show or global default)
2. **Protected shows list** - never delete episodes from these shows
3. **Configurable retention** - different retention periods per show
4. **Dry-run mode** - preview what would be deleted before actually deleting
5. **Logging** - track what was deleted and when

## Configuration Model

```json
{
  "global_defaults": {
    "delete_after_days": 7,
    "enabled": true
  },
  "protected_shows": [
    "30 Rock",
    "The Office",
    "Parks and Recreation",
    "Breaking Bad",
    "Better Call Saul"
  ],
  "custom_retention": {
    "Below Deck": 3,
    "The Challenge": 3,
    "Naked and Afraid": 5,
    "Survivor": 7
  },
  "target_libraries": ["TV Shows", "tv"]
}
```

## Architecture

### Option A: TUI (Recommended First)
- Python script similar to backup-configurator
- Interactive menu for:
  - View all shows with watched episode counts
  - Add/remove shows from protected list
  - Set custom retention periods
  - Run cleanup (dry-run or real)
  - View deletion history

### Option B: Web UI (Future Enhancement)
- Flask/FastAPI container
- Visual show browser with posters
- Toggle switches for protection
- Slider for retention days
- Integration with homepage dashboard

## Implementation Steps

### Phase 1: Core Logic
1. **Plex API integration** - Query watched episodes with timestamps
2. **Config management** - JSON config file for settings
3. **Delete logic** - Safe deletion with confirmation
4. **Logging** - Track all deletions

### Phase 2: TUI Interface
1. **Show browser** - List all TV shows with stats
2. **Protection management** - Add/remove protected shows
3. **Retention configuration** - Set per-show retention
4. **Cleanup runner** - Dry-run and execute modes

### Phase 3: Automation
1. **Cron job** - Daily cleanup at 4 AM
2. **Discord notification** - Report deletions (optional)
3. **Disk space tracking** - Report space freed

### Phase 4: Web UI (Optional)
1. **Flask container** - Simple web interface
2. **Traefik integration** - plex-cleanup.server.unarmedpuppy.com
3. **Homepage widget** - Show cleanup stats

## Plex API Usage

```python
from plexapi.server import PlexServer

# Connect to Plex
plex = PlexServer(PLEX_URL, PLEX_TOKEN)

# Get TV library
tv_library = plex.library.section('TV Shows')

# Find watched episodes
for show in tv_library.all():
    for episode in show.episodes():
        if episode.isWatched:
            watched_at = episode.lastViewedAt
            # Check if older than retention period
            if (now - watched_at).days > retention_days:
                # Delete episode
                episode.delete()
```

## Files to Create

| File | Purpose |
|------|---------|
| `scripts/plex-cleanup.py` | Main TUI application |
| `~/.plex-cleanup-config.json` | Configuration (on server) |
| `~/server/logs/plex-cleanup.log` | Deletion history |

## Safety Features

1. **Protected shows can never be deleted** - hardcoded safety check
2. **Dry-run by default** - must explicitly enable real deletion
3. **Confirmation prompt** - show what will be deleted before proceeding
4. **Minimum retention** - cannot set retention below 1 day
5. **Logging** - all deletions logged with timestamps

## Environment Variables

```bash
PLEX_URL=http://localhost:32400
PLEX_TOKEN=<from Plex settings>
```

## Estimated Storage Impact

Based on current library analysis:
- The Challenge (779 GB) - if 50% watched, could free ~390 GB
- Below Deck series (~1.3 TB total) - could free ~500+ GB
- Reality shows average ~50-100 GB per completed season

Potential savings: **1-2 TB** with aggressive cleanup of reality shows.

## Status

**Planned** - Waiting for implementation

## Notes

- Plex token can be found at: https://plex.tv/devices.xml (when logged in)
- Or in Plex settings → General → "Claim Token"
- plexapi library: `pip install plexapi`
