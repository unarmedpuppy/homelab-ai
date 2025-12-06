#!/usr/bin/env python3
"""
Organize music files from playlist folders into Plex-compatible structure.

This script:
1. Scans music files in playlist folders
2. Extracts metadata (artist, album, track, etc.)
3. Organizes into Artist/Album/Track structure
4. Optionally moves/copies to Plex music library
5. Generates playlist files for Plex import
"""

import os
import sys
import shutil
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import mutagen
from mutagen.id3 import ID3NoHeaderError
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4

# Configuration
DEFAULT_SOURCE_DIR = "./playlists"  # Directory with playlist folders
DEFAULT_TARGET_DIR = "/jenquist-cloud/archive/entertainment-media/Music"  # Plex music library
DEFAULT_DRY_RUN = True  # Set to False to actually move files
DEFAULT_COPY_MODE = True  # Set to False to move files instead of copying


class MusicOrganizer:
    """Organize music files into Plex-compatible structure."""
    
    def __init__(self, source_dir: str, target_dir: str, dry_run: bool = True, copy_mode: bool = True):
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.dry_run = dry_run
        self.copy_mode = copy_mode
        self.stats = {
            "processed": 0,
            "organized": 0,
            "skipped": 0,
            "errors": 0,
            "playlists": {}
        }
        
    def get_metadata(self, file_path: Path) -> Optional[Dict]:
        """Extract metadata from audio file."""
        try:
            if file_path.suffix.lower() == '.mp3':
                audio = MP3(str(file_path))
            elif file_path.suffix.lower() == '.flac':
                audio = FLAC(str(file_path))
            elif file_path.suffix.lower() in ['.m4a', '.mp4']:
                audio = MP4(str(file_path))
            else:
                return None
                
            metadata = {}
            
            # Extract common tags
            if hasattr(audio, 'tags'):
                tags = audio.tags
                
                # Artist
                if 'TPE1' in tags:  # ID3
                    metadata['artist'] = str(tags['TPE1'][0])
                elif 'ARTIST' in tags:  # Vorbis/FLAC
                    metadata['artist'] = str(tags['ARTIST'][0])
                elif '\xa9ART' in tags:  # MP4
                    metadata['artist'] = str(tags['\xa9ART'][0])
                
                # Album
                if 'TALB' in tags:  # ID3
                    metadata['album'] = str(tags['TALB'][0])
                elif 'ALBUM' in tags:  # Vorbis/FLAC
                    metadata['album'] = str(tags['ALBUM'][0])
                elif '\xa9alb' in tags:  # MP4
                    metadata['album'] = str(tags['\xa9alb'][0])
                
                # Title
                if 'TIT2' in tags:  # ID3
                    metadata['title'] = str(tags['TIT2'][0])
                elif 'TITLE' in tags:  # Vorbis/FLAC
                    metadata['title'] = str(tags['TITLE'][0])
                elif '\xa9nam' in tags:  # MP4
                    metadata['title'] = str(tags['\xa9nam'][0])
                
                # Track number
                if 'TRCK' in tags:  # ID3
                    metadata['track'] = str(tags['TRCK'][0]).split('/')[0]
                elif 'TRACKNUMBER' in tags:  # Vorbis/FLAC
                    metadata['track'] = str(tags['TRACKNUMBER'][0]).split('/')[0]
                elif 'trkn' in tags:  # MP4
                    metadata['track'] = str(tags['trkn'][0][0])
            
            # Fallback: try to parse filename
            if not metadata.get('artist') or not metadata.get('title'):
                self._parse_filename(file_path, metadata)
                
            return metadata if metadata else None
            
        except ID3NoHeaderError:
            # No ID3 tags, try filename parsing
            return self._parse_filename(file_path, {})
        except Exception as e:
            print(f"  ⚠ Error reading metadata from {file_path.name}: {e}")
            return self._parse_filename(file_path, {})
    
    def _parse_filename(self, file_path: Path, metadata: Dict) -> Dict:
        """Parse artist and title from filename (e.g., 'Artist - Title.mp3')."""
        name = file_path.stem  # filename without extension
        
        # Common patterns: "Artist - Title", "Artist-Title", "Artist_Title"
        for separator in [' - ', ' -', '- ', '-', '_', ' – ', ' — ']:
            if separator in name:
                parts = name.split(separator, 1)
                if len(parts) == 2:
                    metadata['artist'] = parts[0].strip()
                    metadata['title'] = parts[1].strip()
                    break
        
        if not metadata.get('title'):
            metadata['title'] = name
        
        if not metadata.get('artist'):
            metadata['artist'] = "Unknown Artist"
            
        if not metadata.get('album'):
            metadata['album'] = "Unknown Album"
            
        return metadata
    
    def sanitize_filename(self, name: str) -> str:
        """Sanitize filename for filesystem compatibility."""
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '')
        # Remove leading/trailing spaces and dots
        name = name.strip(' .')
        # Limit length
        if len(name) > 200:
            name = name[:200]
        return name
    
    def get_target_path(self, metadata: Dict, file_path: Path) -> Path:
        """Generate target path in Artist/Album/Track structure."""
        artist = self.sanitize_filename(metadata.get('artist', 'Unknown Artist'))
        album = self.sanitize_filename(metadata.get('album', 'Unknown Album'))
        track_num = metadata.get('track', '').zfill(2) if metadata.get('track') else ''
        title = self.sanitize_filename(metadata.get('title', file_path.stem))
        
        # Format: Artist/Album/TrackNumber - Title.ext
        if track_num:
            filename = f"{track_num} - {title}{file_path.suffix}"
        else:
            filename = f"{title}{file_path.suffix}"
        
        return self.target_dir / artist / album / filename
    
    def organize_file(self, file_path: Path, playlist_name: str = None) -> bool:
        """Organize a single music file."""
        self.stats["processed"] += 1
        
        # Get metadata
        metadata = self.get_metadata(file_path)
        if not metadata:
            print(f"  ⚠ Skipping {file_path.name}: Could not extract metadata")
            self.stats["skipped"] += 1
            return False
        
        # Generate target path
        target_path = self.get_target_path(metadata, file_path)
        
        # Skip if already in correct location
        if file_path.resolve() == target_path.resolve():
            print(f"  ✓ Already organized: {file_path.name}")
            self.stats["skipped"] += 1
            return True
        
        # Create target directory
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Handle duplicates
        if target_path.exists():
            print(f"  ⚠ Target exists: {target_path.name}")
            # Option: add suffix or skip
            counter = 1
            while target_path.exists():
                stem = target_path.stem
                target_path = target_path.parent / f"{stem} ({counter}){target_path.suffix}"
                counter += 1
        
        # Move or copy file
        try:
            if self.dry_run:
                print(f"  [DRY RUN] Would {'copy' if self.copy_mode else 'move'}:")
                print(f"    From: {file_path}")
                print(f"    To:   {target_path}")
            else:
                if self.copy_mode:
                    shutil.copy2(file_path, target_path)
                    print(f"  ✓ Copied: {target_path.name}")
                else:
                    shutil.move(str(file_path), str(target_path))
                    print(f"  ✓ Moved: {target_path.name}")
            
            # Track for playlist
            if playlist_name:
                if playlist_name not in self.stats["playlists"]:
                    self.stats["playlists"][playlist_name] = []
                self.stats["playlists"][playlist_name].append(str(target_path))
            
            self.stats["organized"] += 1
            return True
            
        except Exception as e:
            print(f"  ✗ Error {'copying' if self.copy_mode else 'moving'} {file_path.name}: {e}")
            self.stats["errors"] += 1
            return False
    
    def organize_playlist_folder(self, playlist_folder: Path) -> None:
        """Organize all music files in a playlist folder."""
        playlist_name = playlist_folder.name
        print(f"\n📁 Processing playlist: {playlist_name}")
        
        # Find all audio files
        audio_extensions = {'.mp3', '.flac', '.m4a', '.mp4', '.ogg', '.wav', '.aac'}
        music_files = [
            f for f in playlist_folder.rglob('*')
            if f.is_file() and f.suffix.lower() in audio_extensions
        ]
        
        if not music_files:
            print(f"  ⚠ No music files found in {playlist_name}")
            return
        
        print(f"  Found {len(music_files)} music file(s)")
        
        for file_path in music_files:
            self.organize_file(file_path, playlist_name)
    
    def organize_all(self) -> None:
        """Organize all playlist folders."""
        if not self.source_dir.exists():
            print(f"✗ Source directory not found: {self.source_dir}")
            return
        
        print("=" * 60)
        print("Music Organization for Plex")
        print("=" * 60)
        print(f"Source: {self.source_dir}")
        print(f"Target: {self.target_dir}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'} ({'COPY' if self.copy_mode else 'MOVE'})")
        print("=" * 60)
        
        # Find playlist folders
        playlist_folders = [
            d for d in self.source_dir.iterdir()
            if d.is_dir()
        ]
        
        if not playlist_folders:
            print(f"⚠ No playlist folders found in {self.source_dir}")
            return
        
        print(f"\nFound {len(playlist_folders)} playlist folder(s)\n")
        
        # Process each playlist folder
        for playlist_folder in playlist_folders:
            self.organize_playlist_folder(playlist_folder)
        
        # Print summary
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        print(f"Processed: {self.stats['processed']}")
        print(f"Organized: {self.stats['organized']}")
        print(f"Skipped: {self.stats['skipped']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"Playlists: {len(self.stats['playlists'])}")
        
        # Save playlist mappings
        if self.stats["playlists"]:
            playlist_file = self.target_dir / "playlist_mappings.json"
            if not self.dry_run:
                with open(playlist_file, 'w') as f:
                    json.dump(self.stats["playlists"], f, indent=2)
                print(f"\n✓ Playlist mappings saved to: {playlist_file}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Organize music files into Plex-compatible structure"
    )
    parser.add_argument(
        '--source',
        default=DEFAULT_SOURCE_DIR,
        help=f"Source directory with playlist folders (default: {DEFAULT_SOURCE_DIR})"
    )
    parser.add_argument(
        '--target',
        default=DEFAULT_TARGET_DIR,
        help=f"Target Plex music library directory (default: {DEFAULT_TARGET_DIR})"
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help="Actually move/copy files (default: dry run)"
    )
    parser.add_argument(
        '--move',
        action='store_true',
        help="Move files instead of copying (default: copy)"
    )
    
    args = parser.parse_args()
    
    organizer = MusicOrganizer(
        source_dir=args.source,
        target_dir=args.target,
        dry_run=not args.execute,
        copy_mode=not args.move
    )
    
    organizer.organize_all()


if __name__ == "__main__":
    main()

