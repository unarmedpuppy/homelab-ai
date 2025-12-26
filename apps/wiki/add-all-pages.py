#!/usr/bin/env python3
"""
Batch add all wiki pages from generated markdown files.
Falls back to manual instructions if API fails.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests
import json

# Load environment
load_dotenv(Path(__file__).parent / '.env')

WIKI_URL = os.getenv('WIKI_URL', 'http://192.168.86.47:3001')
API_KEY = os.getenv('WIKI_API_KEY')
GRAPHQL_URL = f"{WIKI_URL}/graphql"

if not API_KEY:
    print("Error: WIKI_API_KEY not found in .env file")
    sys.exit(1)

HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

WIKI_PAGES_DIR = Path(__file__).parent / 'wiki-pages'

def graphql_query(query, variables=None):
    """Execute a GraphQL query."""
    payload = {'query': query}
    if variables:
        payload['variables'] = variables
    
    response = requests.post(GRAPHQL_URL, headers=HEADERS, json=payload)
    response.raise_for_status()
    return response.json()

def create_page(path, title, content, description="", tags=None):
    """Create a page using the correct API format."""
    mutation = """
    mutation CreatePage($content: String!, $description: String!, $editor: String!, $isPublished: Boolean!, $isPrivate: Boolean!, $locale: String!, $path: String!, $tags: [String]!, $title: String!) {
      pages {
        create(content: $content, description: $description, editor: $editor, isPublished: $isPublished, isPrivate: $isPrivate, locale: $locale, path: $path, tags: $tags, title: $title) {
          responseResult {
            succeeded
            errorCode
            slug
            message
          }
          page {
            id
            path
            title
          }
        }
      }
    }
    """
    
    variables = {
        "content": content,
        "description": description,
        "editor": "markdown",
        "isPublished": True,
        "isPrivate": False,
        "locale": "en",
        "path": path,
        "tags": tags or ["documentation"],
        "title": title
    }
    
    try:
        result = graphql_query(mutation, variables)
        return result
    except Exception as e:
        return {"error": str(e)}

def main():
    if not WIKI_PAGES_DIR.exists():
        print(f"Error: wiki-pages directory not found at {WIKI_PAGES_DIR}")
        print("Run create-wiki-pages.py first to generate the pages.")
        sys.exit(1)
    
    # Get all markdown files
    md_files = sorted(WIKI_PAGES_DIR.glob('*.md'))
    
    if not md_files:
        print("No markdown files found in wiki-pages directory")
        sys.exit(1)
    
    print(f"Found {len(md_files)} pages to add\n")
    print("="*60)
    
    # Pages to create (excluding index)
    pages_to_create = []
    
    # First, add homepage
    homepage_file = Path(__file__).parent / 'homepage-content.md'
    if homepage_file.exists():
        content = homepage_file.read_text(encoding='utf-8')
        pages_to_create.append({
            'path': '/home',
            'title': 'Home Server Overview',
            'content': content,
            'description': 'Overview of the home server infrastructure and services',
            'tags': ['server', 'overview']
        })
    
    # Then add documentation pages
    for md_file in md_files:
        if md_file.name == 'documentation-index.md':
            continue
        
        content = md_file.read_text(encoding='utf-8')
        # Extract title from first line (should be # Title)
        lines = content.split('\n')
        title = lines[0].replace('#', '').strip() if lines else md_file.stem
        
        # Remove title from content (already in H1)
        if lines[0].startswith('#'):
            content = '\n'.join(lines[1:]).strip()
        
        path = f"/documentation/{md_file.stem}"
        pages_to_create.append({
            'path': path,
            'title': title,
            'content': content,
            'description': f"Documentation: {title}",
            'tags': ['documentation', 'server']
        })
    
    # Try to create pages
    success_count = 0
    failed_count = 0
    manual_pages = []
    
    for page in pages_to_create:
        print(f"\nCreating: {page['title']} ({page['path']})")
        result = create_page(
            page['path'],
            page['title'],
            page['content'],
            page['description'],
            page['tags']
        )
        
        if result.get('data', {}).get('pages', {}).get('create', {}).get('responseResult', {}).get('succeeded'):
            created_page = result['data']['pages']['create']['page']
            print(f"  ✓ Success! ID: {created_page.get('id')}")
            success_count += 1
        elif result.get('errors'):
            error_msg = result['errors'][0].get('message', 'Unknown error')
            print(f"  ✗ Failed: {error_msg}")
            failed_count += 1
            manual_pages.append(page)
        else:
            print(f"  ✗ Failed: Unexpected response")
            failed_count += 1
            manual_pages.append(page)
    
    # Summary
    print("\n" + "="*60)
    print(f"Summary:")
    print(f"  ✓ Success: {success_count}")
    print(f"  ✗ Failed: {failed_count}")
    print("="*60)
    
    if manual_pages:
        print("\n⚠️  Some pages failed to create via API.")
        print("\nManual addition required:")
        print(f"\n1. Log in to Wiki.js: {WIKI_URL}/login")
        print("   Email: admin@unarmedpuppy.com")
        print("   Password: wikijsadmin2024")
        print("\n2. Add the following pages manually:")
        for page in manual_pages:
            print(f"\n   Path: {page['path']}")
            print(f"   Title: {page['title']}")
            print(f"   File: wiki-pages/{Path(page['path']).stem}.md")
        
        # Save manual instructions
        manual_file = WIKI_PAGES_DIR / 'MANUAL_ADD_INSTRUCTIONS.md'
        with open(manual_file, 'w') as f:
            f.write("# Manual Page Addition Instructions\n\n")
            f.write("The following pages need to be added manually:\n\n")
            for page in manual_pages:
                f.write(f"## {page['title']}\n\n")
                f.write(f"- **Path**: `{page['path']}`\n")
                f.write(f"- **File**: `wiki-pages/{Path(page['path']).stem}.md`\n\n")
        print(f"\n✓ Saved manual instructions to: {manual_file}")

if __name__ == '__main__':
    main()


