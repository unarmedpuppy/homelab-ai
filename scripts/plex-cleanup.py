#!/usr/bin/env python3
"""
Plex Auto-Delete Watched Episodes

Automatically deletes watched TV episodes after a configurable time period.
Uses Sonarr's 'auto-delete' tag to determine which shows to clean up.

Usage:
    python3 plex-cleanup.py                    # Interactive TUI
    python3 plex-cleanup.py --dry-run          # Preview what would be deleted
    python3 plex-cleanup.py --run              # Actually delete watched episodes
    python3 plex-cleanup.py --list-shows       # List all shows with watched counts
    python3 plex-cleanup.py --config           # Show current configuration

Environment:
    PLEX_URL      - Plex server URL (default: http://localhost:32400)
    PLEX_TOKEN    - Plex authentication token (required)

Protection Logic:
    - Shows with 'auto-delete' tag in Sonarr = Deleted after retention period
    - All other shows = Protected (never deleted)
    - When episodes are deleted, they are also unmonitored in Sonarr to prevent re-download
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path

try:
    from plexapi.server import PlexServer
except ImportError:
    print("Error: plexapi not installed. Run: pip3 install plexapi")
    sys.exit(1)

# Configuration
CONFIG_FILE = Path.home() / ".plex-cleanup-config.json"
LOG_FILE = Path.home() / "server/logs/plex-cleanup.log"
SONARR_CONFIG_FILE = Path.home() / "server/apps/media-download/sonarr/config/config.xml"

DEFAULT_CONFIG = {
    "global_defaults": {
        "delete_after_days": 7,
        "enabled": True
    },
    "sonarr_tag": "auto-delete",  # Sonarr tag name for shows to auto-delete
    "custom_retention": {
        # Custom retention periods (days) - overrides global default
        "Below Deck": 3,
        "Below Deck Mediterranean": 3,
        "Below Deck Down Under": 3,
        "The Challenge": 3,
        "Naked and Afraid": 5,
        "Survivor": 7,
        "The Walking Dead": 7
    },
    "target_libraries": ["TV Shows", "tv", "Shows", "Kids - TV Shows"]
}

# Cache for Sonarr data (refreshed each run)
_sonarr_cache = None
_sonarr_tag_id = None
_sonarr_series_data = None


def get_sonarr_api_key():
    """Get Sonarr API key from environment or config file."""
    api_key = os.environ.get('SONARR_API_KEY')
    if api_key:
        return api_key

    # Try to read from Sonarr config
    if SONARR_CONFIG_FILE.exists():
        try:
            import re
            content = SONARR_CONFIG_FILE.read_text()
            match = re.search(r'<ApiKey>([^<]+)</ApiKey>', content)
            if match:
                return match.group(1)
        except Exception:
            pass

    return None


def get_sonarr_tag_id(config):
    """Get the tag ID for the auto-delete tag."""
    global _sonarr_tag_id
    if _sonarr_tag_id is not None:
        return _sonarr_tag_id

    sonarr_url = os.environ.get('SONARR_URL', 'http://localhost:8989')
    api_key = get_sonarr_api_key()
    tag_name = config.get('sonarr_tag', 'auto-delete')

    if not api_key:
        return None

    try:
        url = f"{sonarr_url}/api/v3/tag"
        req = urllib.request.Request(url, headers={'X-Api-Key': api_key})
        with urllib.request.urlopen(req, timeout=10) as response:
            tags = json.loads(response.read().decode())
            for tag in tags:
                if tag.get('label', '').lower() == tag_name.lower():
                    _sonarr_tag_id = tag['id']
                    return _sonarr_tag_id
    except Exception as e:
        print(f"Warning: Could not fetch Sonarr tags ({e})")

    return None


def get_sonarr_series():
    """Fetch all series from Sonarr with their full data."""
    global _sonarr_series_data
    if _sonarr_series_data is not None:
        return _sonarr_series_data

    sonarr_url = os.environ.get('SONARR_URL', 'http://localhost:8989')
    api_key = get_sonarr_api_key()

    if not api_key:
        print("Warning: Could not get Sonarr API key.")
        _sonarr_series_data = []
        return _sonarr_series_data

    try:
        url = f"{sonarr_url}/api/v3/series"
        req = urllib.request.Request(url, headers={'X-Api-Key': api_key})
        with urllib.request.urlopen(req, timeout=10) as response:
            _sonarr_series_data = json.loads(response.read().decode())
            return _sonarr_series_data
    except Exception as e:
        print(f"Warning: Could not connect to Sonarr ({e})")
        _sonarr_series_data = []
        return _sonarr_series_data


def get_shows_with_auto_delete_tag(config):
    """Get list of show titles that have the auto-delete tag."""
    tag_id = get_sonarr_tag_id(config)
    if tag_id is None:
        print(f"Warning: Tag '{config.get('sonarr_tag', 'auto-delete')}' not found in Sonarr")
        return set()

    series = get_sonarr_series()
    return {s['title'] for s in series if tag_id in s.get('tags', [])}


def unmonitor_episode_in_sonarr(show_title, season_num, episode_num):
    """Unmonitor an episode in Sonarr to prevent re-download."""
    sonarr_url = os.environ.get('SONARR_URL', 'http://localhost:8989')
    api_key = get_sonarr_api_key()

    if not api_key:
        return False

    series = get_sonarr_series()
    series_data = next((s for s in series if s['title'] == show_title), None)
    if not series_data:
        print(f"    Warning: Could not find '{show_title}' in Sonarr")
        return False

    series_id = series_data['id']

    try:
        # Get episodes for this series
        url = f"{sonarr_url}/api/v3/episode?seriesId={series_id}"
        req = urllib.request.Request(url, headers={'X-Api-Key': api_key})
        with urllib.request.urlopen(req, timeout=10) as response:
            episodes = json.loads(response.read().decode())

        # Find the matching episode
        for ep in episodes:
            if ep.get('seasonNumber') == season_num and ep.get('episodeNumber') == episode_num:
                # Unmonitor this episode
                ep['monitored'] = False
                put_url = f"{sonarr_url}/api/v3/episode/{ep['id']}"
                put_data = json.dumps(ep).encode('utf-8')
                put_req = urllib.request.Request(
                    put_url,
                    data=put_data,
                    headers={'X-Api-Key': api_key, 'Content-Type': 'application/json'},
                    method='PUT'
                )
                urllib.request.urlopen(put_req, timeout=10)
                return True

    except Exception as e:
        print(f"    Warning: Could not unmonitor episode in Sonarr ({e})")

    return False


def should_protect_show(show_title, config):
    """
    Determine if a show should be protected from deletion.

    Protection logic:
    - Shows with 'auto-delete' tag in Sonarr = NOT protected (delete after watching)
    - All other shows = Protected (keep forever)
    """
    deletable_shows = get_shows_with_auto_delete_tag(config)
    return show_title not in deletable_shows


def load_config():
    """Load configuration from file or create default."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG


def save_config(config):
    """Save configuration to file."""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"Configuration saved to {CONFIG_FILE}")


def log_action(message):
    """Log an action to the log file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry)
    print(log_entry.strip())


def get_plex_server():
    """Connect to Plex server."""
    plex_url = os.environ.get('PLEX_URL', 'http://localhost:32400')
    plex_token = os.environ.get('PLEX_TOKEN')

    if not plex_token:
        print("Error: PLEX_TOKEN environment variable not set.")
        print("Get your token from: https://plex.tv/devices.xml")
        print("Then run: export PLEX_TOKEN=your_token_here")
        sys.exit(1)

    try:
        return PlexServer(plex_url, plex_token)
    except Exception as e:
        print(f"Error connecting to Plex: {e}")
        sys.exit(1)


def get_tv_libraries(plex, config):
    """Get all TV libraries matching config."""
    libraries = []
    for section in plex.library.sections():
        if section.type == 'show' or section.title in config['target_libraries']:
            libraries.append(section)
    return libraries


def is_protected(show_title, config):
    """Check if a show is protected from deletion (uses Sonarr as source of truth)."""
    return should_protect_show(show_title, config)


def get_retention_days(show_title, config):
    """Get retention days for a show (custom or default)."""
    if show_title in config['custom_retention']:
        return config['custom_retention'][show_title]
    return config['global_defaults']['delete_after_days']


def find_deletable_episodes(plex, config, dry_run=True):
    """Find all episodes that can be deleted based on config."""
    now = datetime.now()
    deletable = []

    for library in get_tv_libraries(plex, config):
        print(f"\nScanning library: {library.title}")

        for show in library.all():
            if is_protected(show.title, config):
                continue

            retention_days = get_retention_days(show.title, config)

            for episode in show.episodes():
                if not episode.isWatched:
                    continue

                if episode.lastViewedAt is None:
                    continue

                days_since_watched = (now - episode.lastViewedAt.replace(tzinfo=None)).days

                if days_since_watched >= retention_days:
                    size_mb = 0
                    if episode.media and episode.media[0].parts:
                        size_mb = sum(p.size for p in episode.media[0].parts) / (1024 * 1024)

                    deletable.append({
                        'show': show.title,
                        'season': episode.seasonNumber,
                        'episode': episode.episodeNumber,
                        'title': episode.title,
                        'watched_days_ago': days_since_watched,
                        'retention_days': retention_days,
                        'size_mb': size_mb,
                        'episode_obj': episode
                    })

    return deletable


def list_shows(plex, config):
    """List all shows with watched episode counts."""
    print("\n" + "=" * 80)
    print("TV SHOWS - WATCHED EPISODE COUNTS")
    print("=" * 80)
    print("Legend: 🗑️=auto-delete (has Sonarr tag), 🛡️=protected")

    # Get shows with auto-delete tag from Sonarr
    deletable_shows = get_shows_with_auto_delete_tag(config)
    if not deletable_shows:
        print(f"\n⚠️  No shows found with '{config.get('sonarr_tag', 'auto-delete')}' tag in Sonarr")

    for library in get_tv_libraries(plex, config):
        print(f"\n📺 Library: {library.title}")
        print("-" * 60)

        shows_data = []
        for show in library.all():
            total_eps = len(show.episodes())
            watched_eps = sum(1 for ep in show.episodes() if ep.isWatched)
            retention = get_retention_days(show.title, config)

            # Determine status based on Sonarr auto-delete tag
            if show.title in deletable_shows:
                status = "🗑️"  # Will be deleted
            else:
                status = "🛡️"  # Protected

            shows_data.append({
                'title': show.title,
                'watched': watched_eps,
                'total': total_eps,
                'status': status,
                'retention': retention
            })

        # Sort by watched count
        shows_data.sort(key=lambda x: x['watched'], reverse=True)

        for s in shows_data:
            if s['watched'] > 0:
                print(f"  {s['status']} {s['title']}: {s['watched']}/{s['total']} watched (delete after {s['retention']}d)")


def show_config(config):
    """Display current configuration."""
    print("\n" + "=" * 80)
    print("CURRENT CONFIGURATION")
    print("=" * 80)

    print(f"\nGlobal Defaults:")
    print(f"  Delete after: {config['global_defaults']['delete_after_days']} days")
    print(f"  Enabled: {config['global_defaults']['enabled']}")

    # Show Sonarr tag info
    tag_name = config.get('sonarr_tag', 'auto-delete')
    tag_id = get_sonarr_tag_id(config)
    print(f"\nSonarr Integration:")
    print(f"  Tag name: {tag_name}")
    print(f"  Tag ID: {tag_id if tag_id else 'NOT FOUND'}")

    # Show which shows have the auto-delete tag
    deletable_shows = get_shows_with_auto_delete_tag(config)
    print(f"\nShows with '{tag_name}' tag ({len(deletable_shows)}):")
    if deletable_shows:
        for show in sorted(deletable_shows):
            retention = get_retention_days(show, config)
            print(f"  🗑️ {show} (delete after {retention}d)")
    else:
        print("  (none - add tag in Sonarr to enable auto-delete)")

    print(f"\nCustom Retention ({len(config['custom_retention'])}):")
    for show, days in sorted(config['custom_retention'].items()):
        print(f"  {show}: {days} days")

    print(f"\nTarget Libraries: {', '.join(config['target_libraries'])}")
    print(f"\nConfig file: {CONFIG_FILE}")
    print(f"\nNote: To enable auto-delete for a show, add the '{tag_name}' tag in Sonarr's UI.")


def run_cleanup(plex, config, dry_run=True):
    """Run the cleanup process."""
    mode = "DRY RUN" if dry_run else "LIVE DELETE"
    print(f"\n{'='*80}")
    print(f"PLEX CLEANUP - {mode}")
    print(f"{'='*80}")

    deletable = find_deletable_episodes(plex, config, dry_run)

    if not deletable:
        print("\n✅ No episodes to delete!")
        return

    # Group by show
    by_show = {}
    total_size = 0
    for ep in deletable:
        if ep['show'] not in by_show:
            by_show[ep['show']] = []
        by_show[ep['show']].append(ep)
        total_size += ep['size_mb']

    print(f"\nFound {len(deletable)} episodes to delete ({total_size/1024:.2f} GB)")
    print("-" * 60)

    for show, episodes in sorted(by_show.items()):
        show_size = sum(ep['size_mb'] for ep in episodes)
        print(f"\n📺 {show} ({len(episodes)} episodes, {show_size/1024:.2f} GB)")
        for ep in sorted(episodes, key=lambda x: (x['season'], x['episode'])):
            print(f"   S{ep['season']:02d}E{ep['episode']:02d} - {ep['title']} "
                  f"(watched {ep['watched_days_ago']}d ago, {ep['size_mb']:.0f} MB)")

    if dry_run:
        print(f"\n⚠️  DRY RUN - No files deleted")
        print(f"    Run with --run to actually delete")
    else:
        print(f"\n🗑️  DELETING {len(deletable)} episodes...")
        for ep in deletable:
            try:
                # Delete from Plex
                ep['episode_obj'].delete()
                log_action(f"DELETED: {ep['show']} S{ep['season']:02d}E{ep['episode']:02d} - {ep['title']}")

                # Unmonitor in Sonarr to prevent re-download
                if unmonitor_episode_in_sonarr(ep['show'], ep['season'], ep['episode']):
                    log_action(f"UNMONITORED in Sonarr: {ep['show']} S{ep['season']:02d}E{ep['episode']:02d}")
            except Exception as e:
                log_action(f"ERROR deleting {ep['show']} S{ep['season']:02d}E{ep['episode']:02d}: {e}")

        print(f"✅ Cleanup complete! Freed {total_size/1024:.2f} GB")


def interactive_menu(plex, config):
    """Interactive TUI menu."""
    tag_name = config.get('sonarr_tag', 'auto-delete')

    while True:
        print("\n" + "=" * 60)
        print("PLEX CLEANUP MANAGER")
        print("=" * 60)
        print("1. List shows with watched counts")
        print("2. Preview cleanup (dry run)")
        print("3. Run cleanup (DELETE files)")
        print("4. Show configuration")
        print("5. Set custom retention for show")
        print("6. Save and exit")
        print("7. Exit without saving")
        print("-" * 60)
        print(f"Note: Add/remove '{tag_name}' tag in Sonarr to manage auto-delete")
        print("-" * 60)

        choice = input("Choose option: ").strip()

        if choice == '1':
            list_shows(plex, config)
        elif choice == '2':
            run_cleanup(plex, config, dry_run=True)
        elif choice == '3':
            confirm = input("⚠️  This will DELETE files. Type 'yes' to confirm: ")
            if confirm.lower() == 'yes':
                run_cleanup(plex, config, dry_run=False)
            else:
                print("Cancelled.")
        elif choice == '4':
            show_config(config)
        elif choice == '5':
            show_name = input("Enter show name: ").strip()
            try:
                days = int(input("Enter retention days: "))
                config['custom_retention'][show_name] = days
                print(f"Set retention for '{show_name}' to {days} days")
            except ValueError:
                print("Invalid number")
        elif choice == '6':
            save_config(config)
            print("Configuration saved. Goodbye!")
            break
        elif choice == '7':
            print("Exiting without saving. Goodbye!")
            break
        else:
            print("Invalid option")


def main():
    parser = argparse.ArgumentParser(description='Plex Auto-Delete Watched Episodes')
    parser.add_argument('--dry-run', action='store_true', help='Preview what would be deleted')
    parser.add_argument('--run', action='store_true', help='Actually delete episodes')
    parser.add_argument('--list-shows', action='store_true', help='List shows with watched counts')
    parser.add_argument('--config', action='store_true', help='Show current configuration')

    args = parser.parse_args()

    config = load_config()
    plex = get_plex_server()

    print(f"Connected to Plex: {plex.friendlyName}")

    if args.list_shows:
        list_shows(plex, config)
    elif args.config:
        show_config(config)
    elif args.dry_run:
        run_cleanup(plex, config, dry_run=True)
    elif args.run:
        run_cleanup(plex, config, dry_run=False)
    else:
        # Interactive mode
        interactive_menu(plex, config)


if __name__ == '__main__':
    main()
