#!/usr/bin/env python3
"""
Export Spotify playlist to JSON file.

This is a simpler script that just exports the track list.
You can then use this with SpotifyDL and manually create Plex playlists.

Requirements:
- spotipy: pip install spotipy
- Spotify API credentials
"""

import os
import sys
import json
from typing import List, Dict

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
except ImportError:
    print("ERROR: spotipy not installed. Run: pip install spotipy")
    sys.exit(1)


def get_playlist_tracks(playlist_url: str, client_id: str, client_secret: str) -> List[Dict]:
    """Get all tracks from a Spotify playlist."""
    client_credentials_manager = SpotifyClientCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    
    # Extract playlist ID
    if 'playlist/' in playlist_url:
        playlist_id = playlist_url.split('playlist/')[1].split('?')[0]
    else:
        playlist_id = playlist_url
    
    tracks = []
    results = sp.playlist_tracks(playlist_id)
    
    while results:
        for item in results['items']:
            track = item.get('track')
            if track:
                tracks.append({
                    'name': track['name'],
                    'artist': ', '.join([a['name'] for a in track['artists']]),
                    'album': track['album']['name'],
                    'spotify_url': track['external_urls']['spotify'],
                    'spotify_id': track['id'],
                    'duration_ms': track.get('duration_ms', 0)
                })
        
        if results['next']:
            results = sp.next(results)
        else:
            break
    
    return tracks


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Export Spotify playlist to JSON")
    parser.add_argument("playlist_url", help="Spotify playlist URL")
    parser.add_argument("--output", "-o", default="playlist.json", help="Output JSON file")
    parser.add_argument("--client-id", help="Spotify Client ID (or set SPOTIFY_CLIENT_ID)")
    parser.add_argument("--client-secret", help="Spotify Client Secret (or set SPOTIFY_CLIENT_SECRET)")
    
    args = parser.parse_args()
    
    client_id = args.client_id or os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = args.client_secret or os.getenv("SPOTIFY_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("ERROR: Spotify API credentials required")
        print("\nGet them from: https://developer.spotify.com/dashboard")
        print("Then set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables")
        print("Or pass --client-id and --client-secret")
        sys.exit(1)
    
    print(f"Exporting playlist: {args.playlist_url}")
    tracks = get_playlist_tracks(args.playlist_url, client_id, client_secret)
    
    print(f"Found {len(tracks)} tracks")
    
    # Save to JSON
    with open(args.output, 'w') as f:
        json.dump({
            'playlist_url': args.playlist_url,
            'track_count': len(tracks),
            'tracks': tracks
        }, f, indent=2)
    
    print(f"✓ Saved to {args.output}")
    print(f"\nTo download tracks, use:")
    print(f"  docker exec -it spotdl spotdl download \"{args.playlist_url}\"")


if __name__ == "__main__":
    main()

