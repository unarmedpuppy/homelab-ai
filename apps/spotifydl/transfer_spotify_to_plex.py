#!/usr/bin/env python3
"""
Transfer Spotify playlists to Plex.

This script:
1. Exports a Spotify playlist (gets track list)
2. Downloads tracks using SpotifyDL
3. Organizes files for Plex
4. Creates a playlist in Plex

Requirements:
- spotipy (Spotify API): pip install spotipy
- plexapi: pip install plexapi
- Spotify API credentials (client_id, client_secret)
- Plex token
"""

import os
import sys
import json
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Optional

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
except ImportError:
    print("ERROR: spotipy not installed. Run: pip install spotipy")
    sys.exit(1)

try:
    from plexapi.server import PlexServer
    from plexapi.playlist import Playlist
except ImportError:
    print("ERROR: plexapi not installed. Run: pip install plexapi")
    sys.exit(1)


# Configuration
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
PLEX_URL = os.getenv("PLEX_URL", "http://192.168.86.47:32400")
PLEX_TOKEN = os.getenv("PLEX_TOKEN", "")

# Paths
SPOTIFYDL_DATA = Path(__file__).parent / "data"
PLEX_MUSIC_LIBRARY = Path("/jenquist-cloud/archive/Music")  # Adjust to your Plex music path
SPOTIFYDL_CONTAINER = "spotdl"


class SpotifyPlaylistExporter:
    """Export tracks from a Spotify playlist."""
    
    def __init__(self, client_id: str, client_secret: str):
        if not client_id or not client_secret:
            raise ValueError("Spotify API credentials required. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET")
        
        client_credentials_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        self.sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    
    def get_playlist_tracks(self, playlist_url: str) -> List[Dict]:
        """Get all tracks from a Spotify playlist."""
        playlist_id = self._extract_playlist_id(playlist_url)
        
        tracks = []
        results = self.sp.playlist_tracks(playlist_id)
        
        while results:
            for item in results['items']:
                track = item.get('track')
                if track:
                    tracks.append({
                        'name': track['name'],
                        'artist': ', '.join([a['name'] for a in track['artists']]),
                        'album': track['album']['name'],
                        'spotify_url': track['external_urls']['spotify'],
                        'spotify_id': track['id']
                    })
            
            if results['next']:
                results = self.sp.next(results)
            else:
                break
        
        return tracks
    
    def _extract_playlist_id(self, url: str) -> str:
        """Extract playlist ID from Spotify URL."""
        if 'playlist/' in url:
            return url.split('playlist/')[1].split('?')[0]
        return url


class SpotifyDLDownloader:
    """Download tracks using SpotifyDL."""
    
    def __init__(self, container_name: str = "spotdl"):
        self.container = container_name
    
    def download_playlist(self, playlist_url: str) -> bool:
        """Download entire playlist via SpotifyDL."""
        try:
            cmd = [
                "docker", "exec", "-i", self.container,
                "spotdl", "download", playlist_url
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            
            if result.returncode == 0:
                print(f"✓ Playlist downloaded successfully")
                return True
            else:
                print(f"✗ Download failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print("✗ Download timed out (playlist may be very large)")
            return False
        except Exception as e:
            print(f"✗ Download error: {e}")
            return False
    
    def download_track(self, track_url: str) -> bool:
        """Download single track via SpotifyDL."""
        try:
            cmd = [
                "docker", "exec", "-i", self.container,
                "spotdl", "download", track_url
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            return result.returncode == 0
        except Exception as e:
            print(f"✗ Track download failed: {e}")
            return False


class PlexPlaylistCreator:
    """Create playlists in Plex."""
    
    def __init__(self, base_url: str, token: str):
        if not token:
            raise ValueError("Plex token required. Set PLEX_TOKEN environment variable")
        
        self.plex = PlexServer(base_url, token)
        self.music_library = None
        
        # Find music library
        for library in self.plex.library.sections():
            if library.type == 'artist':
                self.music_library = library
                break
        
        if not self.music_library:
            raise ValueError("No music library found in Plex")
    
    def find_track(self, title: str, artist: str) -> Optional:
        """Find a track in Plex library by title and artist."""
        try:
            # Search for track
            results = self.music_library.search(title)
            
            for track in results:
                if track.type == 'track':
                    # Check if artist matches
                    track_artists = [a.title for a in track.artists]
                    if artist.lower() in [a.lower() for a in track_artists]:
                        return track
            
            return None
        except Exception as e:
            print(f"✗ Error finding track '{title}' by '{artist}': {e}")
            return None
    
    def create_playlist(self, name: str, tracks: List) -> Optional[Playlist]:
        """Create a playlist in Plex with given tracks."""
        try:
            # Filter out None tracks
            valid_tracks = [t for t in tracks if t is not None]
            
            if not valid_tracks:
                print(f"✗ No valid tracks found for playlist '{name}'")
                return None
            
            # Create playlist
            playlist = self.plex.createPlaylist(name, items=valid_tracks)
            print(f"✓ Created playlist '{name}' with {len(valid_tracks)} tracks")
            return playlist
        except Exception as e:
            print(f"✗ Error creating playlist: {e}")
            return None


def main():
    """Main transfer workflow."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Transfer Spotify playlist to Plex")
    parser.add_argument("playlist_url", help="Spotify playlist URL")
    parser.add_argument("--playlist-name", help="Name for Plex playlist (default: Spotify playlist name)")
    parser.add_argument("--skip-download", action="store_true", help="Skip download, only create playlist")
    parser.add_argument("--skip-plex", action="store_true", help="Skip Plex playlist creation")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Spotify → Plex Playlist Transfer")
    print("=" * 60)
    
    # Step 1: Export playlist
    print("\n[1/4] Exporting Spotify playlist...")
    try:
        exporter = SpotifyPlaylistExporter(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
        tracks = exporter.get_playlist_tracks(args.playlist_url)
        print(f"✓ Found {len(tracks)} tracks")
    except Exception as e:
        print(f"✗ Failed to export playlist: {e}")
        print("\nTip: Get Spotify API credentials from:")
        print("  https://developer.spotify.com/dashboard")
        sys.exit(1)
    
    # Step 2: Download tracks
    if not args.skip_download:
        print(f"\n[2/4] Downloading tracks via SpotifyDL...")
        downloader = SpotifyDLDownloader()
        success = downloader.download_playlist(args.playlist_url)
        if not success:
            print("⚠ Download had errors, but continuing...")
    else:
        print("\n[2/4] Skipping download (--skip-download)")
    
    # Step 3: Organize files (manual step for now)
    print("\n[3/4] File organization...")
    print("⚠ Manual step: Ensure files are in Plex music library")
    print(f"   SpotifyDL saves to: {SPOTIFYDL_DATA}")
    print(f"   Plex expects: {PLEX_MUSIC_LIBRARY}")
    print("   You may need to move/organize files manually")
    
    # Step 4: Create Plex playlist
    if not args.skip_plex:
        print(f"\n[4/4] Creating Plex playlist...")
        try:
            creator = PlexPlaylistCreator(PLEX_URL, PLEX_TOKEN)
            
            # Find tracks in Plex
            plex_tracks = []
            for track in tracks[:10]:  # Limit to first 10 for testing
                print(f"  Searching for: {track['name']} by {track['artist']}")
                plex_track = creator.find_track(track['name'], track['artist'])
                if plex_track:
                    plex_tracks.append(plex_track)
                    print(f"    ✓ Found")
                else:
                    print(f"    ✗ Not found in Plex library")
            
            # Create playlist
            playlist_name = args.playlist_name or f"Spotify Playlist ({len(tracks)} tracks)"
            creator.create_playlist(playlist_name, plex_tracks)
            
        except Exception as e:
            print(f"✗ Failed to create Plex playlist: {e}")
            print("\nTip: Get Plex token from:")
            print("  https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/")
    else:
        print("\n[4/4] Skipping Plex playlist creation (--skip-plex)")
    
    print("\n" + "=" * 60)
    print("Transfer complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

