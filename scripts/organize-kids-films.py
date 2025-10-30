#!/usr/bin/env python3
"""
Organize video files in Kids/Films directory by extracting movie titles
and creating proper directory structure.
"""
import os
import re
import shutil
from pathlib import Path

def extract_movie_title(filename):
    """Extract clean movie title from filename."""
    # Remove file extension
    name = Path(filename).stem
    
    # Remove common release info patterns
    patterns = [
        r'\.(\d{4})\.',  # Year pattern like .2013.
        r'\.UHD\.',
        r'\.BluRay\.',
        r'\.2160p\.',
        r'\.1080p\.',
        r'\.720p\.',
        r'\.480p\.',
        r'\.TrueHD\.',
        r'\.Atmos\.',
        r'\.HEVC\.',
        r'\.REMUX.*?',
        r'\.HYBRID.*?',
        r'\.DV\.',
        r'\.[A-Z0-9\-]+\.',  # Release group codes
        r'#\d+',  # Numbers like #223
        r'-[A-Za-z0-9]+$',  # Trailing release group names
    ]
    
    for pattern in patterns:
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)
    
    # Clean up multiple dots and spaces
    name = re.sub(r'\.+', ' ', name)
    name = re.sub(r'\s+', ' ', name)
    name = name.strip()
    
    # Remove trailing separators
    name = re.sub(r'[-_\.]+$', '', name)
    
    return name.strip()

def organize_films(directory):
    """Organize video files into proper directories."""
    base_path = Path(directory)
    video_extensions = {'.avi', '.mkv', '.mp4', '.mov', '.m4v', '.wmv', '.flv'}
    
    files_to_move = []
    
    # Find all video files directly in the base directory (not in subdirectories)
    for file_path in base_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in video_extensions:
            files_to_move.append(file_path)
    
    if not files_to_move:
        print("No video files found directly in the directory.")
        return
    
    print(f"Found {len(files_to_move)} files to organize:\n")
    
    for file_path in files_to_move:
        original_name = file_path.name
        movie_title = extract_movie_title(original_name)
        
        if not movie_title:
            print(f"⚠️  Could not extract title from: {original_name}")
            continue
        
        # Create directory for this movie
        movie_dir = base_path / movie_title
        
        if not movie_dir.exists():
            movie_dir.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created directory: {movie_title}")
        
        # Move file to directory
        dest_file = movie_dir / original_name
        if dest_file.exists():
            print(f"⚠️  Destination already exists: {dest_file}")
        else:
            shutil.move(str(file_path), str(dest_file))
            print(f"✓ Moved: {original_name} → {movie_title}/")
    
    print(f"\n✅ Organization complete!")

if __name__ == "__main__":
    films_dir = "/jenquist-cloud/archive/entertainment-media/Kids/Films"
    
    if not os.path.exists(films_dir):
        print(f"Error: Directory does not exist: {films_dir}")
        exit(1)
    
    organize_films(films_dir)

