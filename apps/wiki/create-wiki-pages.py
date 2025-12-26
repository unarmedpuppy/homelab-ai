#!/usr/bin/env python3
"""
Parse README.md and create structured markdown files for Wiki.js pages.
"""

import re
import os
from pathlib import Path

README_PATH = Path(__file__).parent.parent.parent / 'README.md'
OUTPUT_DIR = Path(__file__).parent / 'wiki-pages'

def extract_sections(content):
    """Extract major sections from README."""
    sections = []
    current_section = None
    current_content = []
    
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        # Check for H2 headers (##)
        if line.startswith('## ') and not line.startswith('###'):
            if current_section:
                sections.append({
                    'title': current_section,
                    'content': '\n'.join(current_content).strip()
                })
            current_section = line[3:].strip()
            current_content = []
        else:
            current_content.append(line)
    
    # Add last section
    if current_section:
        sections.append({
            'title': current_section,
            'content': '\n'.join(current_content).strip()
        })
    
    return sections

def create_page_file(title, content, path_suffix=''):
    """Create a markdown file for a wiki page."""
    # Sanitize title for filename
    filename = re.sub(r'[^\w\s-]', '', title.lower())
    filename = re.sub(r'[-\s]+', '-', filename)
    filename = filename.strip('-')
    
    if path_suffix:
        filename = f"{path_suffix}-{filename}"
    
    filepath = OUTPUT_DIR / f"{filename}.md"
    
    # Add title as H1
    full_content = f"# {title}\n\n{content}"
    
    filepath.write_text(full_content, encoding='utf-8')
    return filepath

def main():
    # Read README
    if not README_PATH.exists():
        print(f"Error: README.md not found at {README_PATH}")
        return
    
    content = README_PATH.read_text(encoding='utf-8')
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Extract sections
    sections = extract_sections(content)
    
    print(f"Found {len(sections)} sections")
    print("\nCreating wiki page files...\n")
    
    # Create pages
    created_files = []
    for section in sections:
        title = section['title']
        content = section['content']
        
        # Skip table of contents
        if 'Table of Contents' in title:
            continue
        
        filepath = create_page_file(title, content)
        created_files.append({
            'title': title,
            'file': filepath.name,
            'path': f"/documentation/{filepath.stem}"
        })
        print(f"✓ Created: {filepath.name} - {title}")
    
    # Create index file
    index_content = "# Server Documentation\n\n"
    index_content += "Complete documentation for the home server setup, configuration, and maintenance.\n\n"
    index_content += "## Pages\n\n"
    
    for item in created_files:
        index_content += f"- [{item['title']}]({item['path']})\n"
    
    index_file = OUTPUT_DIR / "documentation-index.md"
    index_file.write_text(index_content, encoding='utf-8')
    print(f"\n✓ Created index: {index_file.name}")
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Created {len(created_files)} page files in {OUTPUT_DIR}")
    print(f"{'='*60}")
    print("\nNext steps:")
    print("1. Review the generated files in apps/wiki/wiki-pages/")
    print("2. Add them to Wiki.js using the API tool or manually")
    print("3. Update paths and organization as needed")

if __name__ == '__main__':
    main()


