# Plex Auto-Delete Watched Episodes

## Overview

Automatically deletes watched TV episodes after a configurable retention period. Uses Sonarr's tag system for show selection, giving you full control via Sonarr's UI.

| Component | Location |
|-----------|----------|
| Main script | `scripts/plex-cleanup.py` |
| Cron wrapper | `scripts/plex-cleanup-cron.sh` |
| Config file | `~/.plex-cleanup-config.json` |
| Log file | `~/server/logs/plex-cleanup.log` |

## How It Works

### Protection Logic

```
Show has 'auto-delete' tag in Sonarr?
├── YES → Delete watched episodes after retention period
│         └── Also unmonitor episode in Sonarr (prevents re-download)
└── NO  → Protected (never deleted)
```

### Flow

1. Script queries Sonarr API for shows with `auto-delete` tag
2. Scans Plex TV libraries for watched episodes
3. For each episode on a tagged show:
   - Check if watched longer than retention period
   - Delete from Plex
   - Unmonitor in Sonarr (prevents re-download)
4. Log all actions

## Configuration

### Managing Which Shows Are Deleted

**All control is via Sonarr's UI:**

1. Open Sonarr → Series → Select a show
2. Edit → Tags → Add `auto-delete`
3. Save

Shows with the `auto-delete` tag will have watched episodes deleted. All other shows are protected.

### Retention Periods

Default: 7 days after watching

Custom per-show retention in `~/.plex-cleanup-config.json`:

```json
{
  "global_defaults": {
    "delete_after_days": 7,
    "enabled": true
  },
  "sonarr_tag": "auto-delete",
  "custom_retention": {
    "Below Deck": 3,
    "The Challenge": 3,
    "Survivor": 7
  },
  "target_libraries": ["TV Shows", "tv", "Shows", "Kids - TV Shows"]
}
```

## Usage

### Manual Commands

```bash
# Preview what would be deleted (safe)
python3 ~/server/scripts/plex-cleanup.py --dry-run

# Actually delete episodes
python3 ~/server/scripts/plex-cleanup.py --run

# Show current configuration
python3 ~/server/scripts/plex-cleanup.py --config

# List all shows with watched counts
python3 ~/server/scripts/plex-cleanup.py --list-shows

# Interactive menu
python3 ~/server/scripts/plex-cleanup.py
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PLEX_URL` | `http://localhost:32400` | Plex server URL |
| `PLEX_TOKEN` | (required) | Plex authentication token |
| `SONARR_URL` | `http://localhost:8989` | Sonarr API URL |

The `PLEX_TOKEN` is stored in `~/.bashrc` on the server.

### Getting PLEX_TOKEN

1. Sign in to Plex web app
2. Visit: https://plex.tv/devices.xml
3. Find your server, copy the `token` attribute

## Scheduled Cleanup (Cron)

### Schedule

| Time | Task |
|------|------|
| 3:30 AM CST | Run plex-cleanup --run |

### Cron Entry

```cron
30 3 * * * /home/unarmedpuppy/server/scripts/plex-cleanup-cron.sh
```

### Managing Cron

```bash
# View current crontab
crontab -l

# Edit crontab
crontab -e

# Add plex-cleanup (if not present)
# Add this line: 30 3 * * * /home/unarmedpuppy/server/scripts/plex-cleanup-cron.sh
```

### Cron Wrapper Features

The wrapper script (`plex-cleanup-cron.sh`):

- Sets required environment variables (PLEX_TOKEN, SONARR_URL)
- Uses lock file to prevent concurrent runs
- Logs all output to `~/server/logs/plex-cleanup.log`
- Timestamps each run

## Sonarr Integration

### How Episodes Stay Deleted

When an episode is deleted:

1. Script deletes file from Plex/filesystem
2. Script calls Sonarr API to set `monitored: false` on that episode
3. Sonarr won't re-download unmonitored episodes

### Tag Lookup

The script finds the `auto-delete` tag ID via Sonarr API, then queries which series have that tag. This is cached per run for performance.

### API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v3/tag` | Find auto-delete tag ID |
| `GET /api/v3/series` | Get all series with tags |
| `GET /api/v3/episode?seriesId=X` | Get episodes for a series |
| `PUT /api/v3/episode/X` | Unmonitor an episode |

## Troubleshooting

### Script Can't Connect to Plex

```bash
# Check PLEX_TOKEN is set
echo $PLEX_TOKEN

# Test connection
curl -s "http://localhost:32400/library/sections?X-Plex-Token=$PLEX_TOKEN"
```

### Script Can't Connect to Sonarr

```bash
# Check Sonarr is running
docker ps | grep sonarr

# Test API (get key from config)
SONARR_KEY=$(grep -oP '(?<=<ApiKey>)[^<]+' ~/server/apps/media-download/sonarr/config/config.xml)
curl -s "http://localhost:8989/api/v3/series" -H "X-Api-Key: $SONARR_KEY" | head
```

### No Shows Found with Tag

1. Verify tag exists in Sonarr: Settings → Tags
2. Verify shows have the tag: Series → Edit → Tags
3. Check tag name matches config (default: `auto-delete`)

### Cron Not Running

```bash
# Check cron service
sudo systemctl status cron

# Check cron logs
grep CRON /var/log/syslog | tail -20

# Verify script is executable
ls -la ~/server/scripts/plex-cleanup-cron.sh
```

## Safety Features

1. **Sonarr tag control** - Only shows you explicitly tag are deleted
2. **Dry-run by default** - Use `--dry-run` to preview before deleting
3. **Lock file** - Prevents concurrent runs
4. **Retention period** - Episodes must be watched X days before deletion
5. **Logging** - All deletions logged with timestamps
6. **Unmonitor in Sonarr** - Prevents re-download of deleted episodes

## Logs

### Log Location

`~/server/logs/plex-cleanup.log`

### Log Format

```
[2024-12-26 03:30:01] Starting scheduled cleanup
[2024-12-26 03:30:05] DELETED: Below Deck S11E05 - Episode Title
[2024-12-26 03:30:05] UNMONITORED in Sonarr: Below Deck S11E05
[2024-12-26 03:30:10] Cleanup completed
```

### View Recent Logs

```bash
tail -50 ~/server/logs/plex-cleanup.log
```

## Space Savings

Potential savings depend on viewing habits:

| Show Type | Episodes/Week | Size/Episode | Monthly Savings |
|-----------|---------------|--------------|-----------------|
| Reality TV | 3-5 | 2-3 GB | 30-60 GB |
| Drama | 1-2 | 3-5 GB | 15-40 GB |
| Daily shows | 5 | 1-3 GB | 20-60 GB |

Aggressive cleanup of reality shows can free **1-2 TB** over time.
