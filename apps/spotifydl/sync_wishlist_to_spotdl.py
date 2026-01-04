#!/usr/bin/env python3
"""
SoulSync Wishlist → SpotDL Fallback Downloader

This script reads failed downloads from SoulSync's wishlist and attempts
to download them using SpotDL (YouTube source) as a fallback.

Usage:
    # Dry run - see what would be downloaded
    python sync_wishlist_to_spotdl.py --dry-run
    
    # Download all wishlist tracks
    python sync_wishlist_to_spotdl.py
    
    # Download with limit
    python sync_wishlist_to_spotdl.py --limit 10
    
    # Remove successful downloads from wishlist
    python sync_wishlist_to_spotdl.py --remove-on-success

Requirements:
    - SoulSync container running with database at /app/database/music_library.db
    - SpotDL container running
    - YouTube cookies configured for yt-dlp (see README)
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


# Configuration
SOULSYNC_CONTAINER = "soulsync"
SPOTDL_CONTAINER = "spotdl"
DATABASE_PATH = "/app/database/music_library.db"
OUTPUT_PATH = "/music"  # Inside spotdl container
OUTPUT_TEMPLATE = "{artist}/{album}/{title}.{output-ext}"

# For direct music library output (after fixing volume mount):
# OUTPUT_PATH = "/jenquist-cloud/archive/entertainment-media/Music"


def run_command(cmd: list, timeout: int = 300) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def get_wishlist_tracks(limit: Optional[int] = None) -> list[dict]:
    """Query SoulSync database for wishlist tracks."""
    query = "SELECT id, spotify_track_id, spotify_data, failure_reason, retry_count FROM wishlist_tracks"
    if limit:
        query += f" LIMIT {limit}"
    
    python_code = f'''
import sqlite3
import json
conn = sqlite3.connect("{DATABASE_PATH}")
cursor = conn.cursor()
cursor.execute("""{query}""")
for row in cursor.fetchall():
    data = json.loads(row[2])
    print(json.dumps({{
        "id": row[0],
        "spotify_id": row[1],
        "name": data.get("name", "Unknown"),
        "artist": data.get("artists", [{{}}])[0].get("name", "Unknown"),
        "album": data.get("album", {{}}).get("name", "Unknown"),
        "failure_reason": row[3],
        "retry_count": row[4]
    }}))
conn.close()
'''
    
    cmd = ["docker", "exec", SOULSYNC_CONTAINER, "python3", "-c", python_code]
    returncode, stdout, stderr = run_command(cmd)
    
    if returncode != 0:
        print(f"Error querying database: {stderr}")
        return []
    
    tracks = []
    for line in stdout.strip().split("\n"):
        if line:
            try:
                tracks.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    
    return tracks


def download_track(spotify_id: str, track_info: dict) -> bool:
    """Download a track using SpotDL."""
    url = f"https://open.spotify.com/track/{spotify_id}"
    output = f"{OUTPUT_PATH}/{OUTPUT_TEMPLATE}"
    
    cmd = [
        "docker", "exec", SPOTDL_CONTAINER,
        "uv", "run", "--project", "/app",
        "spotdl", "download", url,
        "--output", output
    ]
    
    print(f"  Downloading: {track_info['artist']} - {track_info['name']}")
    returncode, stdout, stderr = run_command(cmd, timeout=180)
    
    if returncode == 0:
        # Check if it was skipped (already exists) or downloaded
        if "Skipping" in stdout or "Skipping" in stderr:
            print(f"    ⏭️  Already exists")
            return True
        elif "Downloaded" in stdout or "Downloaded" in stderr:
            print(f"    ✅ Downloaded successfully")
            return True
        else:
            # Check for errors
            if "AudioProviderError" in stderr or "ERROR" in stderr:
                print(f"    ❌ Download failed: YouTube authentication required")
                return False
            print(f"    ✅ Completed")
            return True
    else:
        print(f"    ❌ Failed: {stderr[:100] if stderr else 'Unknown error'}")
        return False


def remove_from_wishlist(track_id: int) -> bool:
    """Remove a track from the wishlist after successful download."""
    python_code = f'''
import sqlite3
conn = sqlite3.connect("{DATABASE_PATH}")
cursor = conn.cursor()
cursor.execute("DELETE FROM wishlist_tracks WHERE id = ?", ({track_id},))
conn.commit()
print(f"Deleted {{cursor.rowcount}} row(s)")
conn.close()
'''
    
    cmd = ["docker", "exec", SOULSYNC_CONTAINER, "python3", "-c", python_code]
    returncode, stdout, stderr = run_command(cmd)
    return returncode == 0


def update_retry_count(track_id: int) -> bool:
    """Increment retry count for failed downloads."""
    python_code = f'''
import sqlite3
from datetime import datetime
conn = sqlite3.connect("{DATABASE_PATH}")
cursor = conn.cursor()
cursor.execute("""
    UPDATE wishlist_tracks 
    SET retry_count = retry_count + 1, 
        last_attempted = ?
    WHERE id = ?
""", (datetime.now().isoformat(), {track_id}))
conn.commit()
conn.close()
'''
    
    cmd = ["docker", "exec", SOULSYNC_CONTAINER, "python3", "-c", python_code]
    returncode, _, _ = run_command(cmd)
    return returncode == 0


def main():
    parser = argparse.ArgumentParser(
        description="Download SoulSync wishlist tracks using SpotDL"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Show what would be downloaded without actually downloading"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of tracks to process"
    )
    parser.add_argument(
        "--remove-on-success",
        action="store_true",
        help="Remove tracks from wishlist after successful download"
    )
    parser.add_argument(
        "--skip-retried",
        type=int,
        default=None,
        help="Skip tracks that have been retried N or more times"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("SoulSync Wishlist → SpotDL Fallback Downloader")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Get wishlist tracks
    print("Fetching wishlist tracks from SoulSync...")
    tracks = get_wishlist_tracks(args.limit)
    
    if not tracks:
        print("No tracks found in wishlist.")
        return 0
    
    print(f"Found {len(tracks)} tracks in wishlist")
    print()
    
    if args.dry_run:
        print("DRY RUN - Would download:")
        for i, track in enumerate(tracks, 1):
            print(f"  {i}. {track['artist']} - {track['name']} ({track['album']})")
            print(f"      Spotify ID: {track['spotify_id']}")
            print(f"      Retries: {track['retry_count']}, Reason: {track['failure_reason']}")
        return 0
    
    # Download tracks
    success_count = 0
    fail_count = 0
    skip_count = 0
    
    for i, track in enumerate(tracks, 1):
        print(f"\n[{i}/{len(tracks)}] Processing: {track['artist']} - {track['name']}")
        
        # Skip if retried too many times
        if args.skip_retried and track['retry_count'] >= args.skip_retried:
            print(f"  ⏭️  Skipping (retried {track['retry_count']} times)")
            skip_count += 1
            continue
        
        success = download_track(track['spotify_id'], track)
        
        if success:
            success_count += 1
            if args.remove_on_success:
                if remove_from_wishlist(track['id']):
                    print(f"    🗑️  Removed from wishlist")
        else:
            fail_count += 1
            update_retry_count(track['id'])
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Total processed: {len(tracks)}")
    print(f"  ✅ Successful: {success_count}")
    print(f"  ❌ Failed: {fail_count}")
    print(f"  ⏭️  Skipped: {skip_count}")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
