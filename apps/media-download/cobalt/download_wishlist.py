#!/usr/bin/env python3
"""
Download SoulSync wishlist tracks using Cobalt API.
Uses ytmusicapi for YouTube search, Cobalt for downloading.
Tracks failures for retry with different methods.
"""

import json
import requests
import os
import time
import re
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# Add local bin to path for ytmusicapi
import sys
sys.path.insert(0, '/home/unarmedpuppy/.local/lib/python3.11/site-packages')

from ytmusicapi import YTMusic

# Configuration
COBALT_API = "http://localhost:9000"
MUSIC_DIR = "/jenquist-cloud/archive/entertainment-media/Music"
FAILED_LOG = "/home/unarmedpuppy/server/apps/media-download/cobalt/failed_downloads.json"

# Initialize YouTube Music API (no auth needed for search)
ytmusic = YTMusic()

def sanitize_filename(name: str) -> str:
    """Remove invalid characters from filename."""
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = name.strip('. ')
    return name[:200]

def search_youtube(artist: str, title: str) -> list:
    """Search YouTube Music and return list of video URLs to try."""
    try:
        query = f"{artist} {title}"
        results = ytmusic.search(query, filter="songs", limit=5)
        
        if not results:
            results = ytmusic.search(query, limit=5)
        
        urls = []
        for result in results[:3]:  # Try top 3 results
            video_id = result.get("videoId")
            if video_id:
                urls.append(f"https://www.youtube.com/watch?v={video_id}")
        
        return urls
    except Exception as e:
        print(f"  Search error: {e}")
        return []

def download_with_cobalt(url: str, output_path: str) -> tuple:
    """Download audio using Cobalt API. Returns (success, error_code)."""
    try:
        response = requests.post(
            COBALT_API,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            json={
                "url": url,
                "downloadMode": "audio",
                "audioFormat": "mp3",
                "audioBitrate": "320"
            },
            timeout=30
        )
        
        if response.status_code != 200:
            return False, f"http_{response.status_code}"
            
        data = response.json()
        
        if data.get("status") == "error":
            error_code = data.get('error', {}).get('code', 'unknown')
            return False, error_code
            
        if data.get("status") not in ("tunnel", "redirect"):
            return False, f"unexpected_status_{data.get('status')}"
        
        tunnel_url = data.get("url")
        if not tunnel_url:
            return False, "no_tunnel_url"
            
        tunnel_url = tunnel_url.replace(
            "https://cobalt.server.unarmedpuppy.com",
            "http://localhost:9000"
        )
        
        dl_response = requests.get(tunnel_url, stream=True, timeout=300)
        
        if dl_response.status_code != 200:
            return False, f"download_http_{dl_response.status_code}"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            for chunk in dl_response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = os.path.getsize(output_path)
        if file_size < 10000:
            os.remove(output_path)
            return False, "file_too_small"
            
        return True, None
        
    except Exception as e:
        return False, str(e)

def get_wishlist_tracks(limit: int = None) -> list:
    """Get tracks from SoulSync wishlist database via docker exec."""
    query = "SELECT id, spotify_track_id, spotify_data FROM wishlist_tracks"
    if limit:
        query += f" LIMIT {limit}"
    
    cmd = f'''docker exec soulsync python3 -c "
import sqlite3
import json
conn = sqlite3.connect('/app/database/music_library.db')
cursor = conn.cursor()
cursor.execute('{query}')
results = []
for row in cursor.fetchall():
    results.append({{'db_id': row[0], 'spotify_id': row[1], 'data': row[2]}})
print(json.dumps(results))
conn.close()
"'''
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error getting tracks: {result.stderr}")
        return []
    
    raw_tracks = json.loads(result.stdout)
    tracks = []
    for t in raw_tracks:
        data = json.loads(t['data'])
        artists = data.get("artists", [{}])
        tracks.append({
            "db_id": t["db_id"],
            "spotify_id": t["spotify_id"],
            "title": data.get("name", "Unknown"),
            "artist": artists[0].get("name", "Unknown") if artists else "Unknown",
            "album": data.get("album", {}).get("name", "Unknown")
        })
    
    return tracks

def remove_from_wishlist(db_id: int):
    """Remove successfully downloaded track from wishlist."""
    cmd = f'''docker exec soulsync python3 -c "
import sqlite3
conn = sqlite3.connect('/app/database/music_library.db')
cursor = conn.cursor()
cursor.execute('DELETE FROM wishlist_tracks WHERE id = ?', ({db_id},))
conn.commit()
conn.close()
"'''
    subprocess.run(cmd, shell=True, capture_output=True)

def load_failed_log() -> dict:
    """Load the failed downloads log."""
    if os.path.exists(FAILED_LOG):
        with open(FAILED_LOG, 'r') as f:
            return json.load(f)
    return {"failures": [], "last_updated": None}

def save_failed_log(log: dict):
    """Save the failed downloads log."""
    log["last_updated"] = datetime.now().isoformat()
    with open(FAILED_LOG, 'w') as f:
        json.dump(log, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Download SoulSync wishlist tracks via Cobalt")
    parser.add_argument("--limit", type=int, help="Limit number of tracks to process")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually download")
    parser.add_argument("--keep-wishlist", action="store_true", help="Don't remove from wishlist after download")
    args = parser.parse_args()
    
    print("Fetching wishlist tracks...")
    tracks = get_wishlist_tracks(args.limit)
    print(f"Found {len(tracks)} tracks in wishlist\n")
    
    failed_log = load_failed_log()
    success = 0
    failed = 0
    skipped = 0
    
    for i, track in enumerate(tracks, 1):
        artist = track["artist"]
        title = track["title"]
        print(f"[{i}/{len(tracks)}] {artist} - {title}")
        
        if args.dry_run:
            print("  [DRY RUN] Would search and download")
            continue
        
        # Check output path first
        safe_artist = sanitize_filename(artist)
        safe_title = sanitize_filename(title)
        output_path = os.path.join(MUSIC_DIR, safe_artist, f"{safe_title}.mp3")
        
        if os.path.exists(output_path):
            print(f"  Already exists, skipping")
            if not args.keep_wishlist:
                remove_from_wishlist(track["db_id"])
            skipped += 1
            continue
        
        print(f"  Searching YouTube Music...")
        yt_urls = search_youtube(artist, title)
        
        if not yt_urls:
            print("  No YouTube results found")
            failed_log["failures"].append({
                "spotify_id": track["spotify_id"],
                "artist": artist,
                "title": title,
                "error": "no_search_results",
                "timestamp": datetime.now().isoformat()
            })
            failed += 1
            continue
        
        # Try each URL until one works
        download_success = False
        last_error = None
        
        for url in yt_urls:
            print(f"  Trying: {url}")
            result, error = download_with_cobalt(url, output_path)
            
            if result:
                download_success = True
                file_size = os.path.getsize(output_path)
                print(f"  Success! Downloaded {file_size / 1024 / 1024:.2f} MB")
                break
            else:
                last_error = error
                if "login" in error.lower():
                    print(f"  Requires login, trying next...")
                else:
                    print(f"  Failed: {error}")
        
        if download_success:
            success += 1
            if not args.keep_wishlist:
                remove_from_wishlist(track["db_id"])
                print("  Removed from wishlist")
        else:
            failed += 1
            failed_log["failures"].append({
                "spotify_id": track["spotify_id"],
                "artist": artist,
                "title": title,
                "error": last_error,
                "tried_urls": yt_urls,
                "timestamp": datetime.now().isoformat()
            })
            print(f"  All URLs failed, logged for retry")
        
        time.sleep(1)
    
    # Save failed log
    save_failed_log(failed_log)
    
    print(f"\n{'='*50}")
    print(f"Complete! Success: {success}, Failed: {failed}, Skipped: {skipped}")
    if failed > 0:
        print(f"Failed tracks logged to: {FAILED_LOG}")

if __name__ == "__main__":
    main()
