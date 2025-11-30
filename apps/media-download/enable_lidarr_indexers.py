#!/usr/bin/env python3
"""
Enable and configure indexers in Lidarr for music.
"""

import requests
import json
import sys

LIDARR_URL = "http://192.168.86.47:8686/api/v1"
LIDARR_API_KEY = "75e8d1fd2316459085340afd4879d2b6"

# Music categories
MUSIC_CATEGORIES = [3000, 3010, 3040]  # 3000=Music, 3010=MP3, 3040=Lossless


def enable_indexer(indexer):
    """Enable an indexer and set music categories."""
    indexer_id = indexer.get("id")
    name = indexer.get("name", "Unknown")
    
    # Enable the indexer
    indexer["enable"] = True
    
    # Update categories for music
    for field in indexer.get("fields", []):
        field_name = field.get("name")
        
        if field_name == "categories":
            current = field.get("value", [])
            if isinstance(current, list):
                # Merge with music categories
                combined = list(set(current + MUSIC_CATEGORIES))
                field["value"] = combined
            else:
                field["value"] = MUSIC_CATEGORIES
    
    # Update via API
    try:
        response = requests.put(
            f"{LIDARR_URL}/indexer/{indexer_id}",
            headers={"X-Api-Key": LIDARR_API_KEY, "Content-Type": "application/json"},
            json=indexer,
            timeout=10
        )
        
        if response.status_code == 200:
            return True, None
        else:
            return False, f"HTTP {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return False, str(e)


def main():
    print("=" * 60)
    print("Enable Lidarr Indexers for Music")
    print("=" * 60)
    
    # Get all indexers
    response = requests.get(
        f"{LIDARR_URL}/indexer",
        headers={"X-Api-Key": LIDARR_API_KEY},
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"✗ Error fetching indexers: {response.status_code}")
        sys.exit(1)
    
    indexers = response.json()
    
    if not indexers:
        print("✗ No indexers found in Lidarr")
        print("\nYou need to add indexers first:")
        print("  1. Add NZBHydra2 or Prowlarr as an indexer")
        print("  2. Then run this script to enable them")
        sys.exit(1)
    
    print(f"\nFound {len(indexers)} indexer(s):\n")
    
    enabled_count = 0
    for idx in indexers:
        name = idx.get("name", "Unknown")
        currently_enabled = idx.get("enable", False)
        
        print(f"{name}:")
        if currently_enabled:
            print(f"  ✓ Already enabled")
            enabled_count += 1
        else:
            print(f"  Enabling...")
            success, error = enable_indexer(idx)
            if success:
                print(f"  ✓ Enabled and configured for music")
                enabled_count += 1
            else:
                print(f"  ✗ Failed: {error}")
        print()
    
    print("=" * 60)
    if enabled_count > 0:
        print(f"✓ {enabled_count} indexer(s) enabled")
        print("\nNext steps:")
        print("1. Go to Lidarr > Settings > Indexers")
        print("2. Test each indexer")
        print("3. Try searching for music again")
        print("\nNote: Music is harder to find than TV/movies.")
        print("You may need to add music-specific indexers:")
        print("  - NZBGeek ($15 lifetime)")
        print("  - DrunkenSlug ($10/year)")
        print("  - Add these to NZBHydra2 or Prowlarr")
    else:
        print("✗ No indexers could be enabled")
        print("\nManual steps:")
        print("1. Open Lidarr: http://192.168.86.47:8686")
        print("2. Go to Settings > Indexers")
        print("3. Enable each indexer manually")
        print("4. Set categories to include: 3000, 3010, 3040")


if __name__ == "__main__":
    main()

