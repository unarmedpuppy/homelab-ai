#!/usr/bin/env python3
"""
Wiki.js Content Editor
Uses the Wiki.js GraphQL API to create and update pages.

Usage:
    python edit-wiki.py create --path "/home" --title "Home" --content "content.md"
    python edit-wiki.py update --path "/home" --content "content.md"
    python edit-wiki.py get --path "/home"
"""

import os
import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

WIKI_URL = os.getenv('WIKI_URL', 'http://192.168.86.47:3001')
API_KEY = os.getenv('WIKI_API_KEY')

if not API_KEY:
    print("Error: WIKI_API_KEY not found in .env file")
    sys.exit(1)

GRAPHQL_URL = f"{WIKI_URL}/graphql"
HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}


def read_file_content(file_path):
    """Read content from a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def graphql_query(query, variables=None):
    """Execute a GraphQL query."""
    payload = {'query': query}
    if variables:
        payload['variables'] = variables
    
    response = requests.post(GRAPHQL_URL, headers=HEADERS, json=payload)
    response.raise_for_status()
    return response.json()


def create_page(path, title, content, description=None, is_published=True, locale='en', editor='markdown', tags=None):
    """Create a new page in Wiki.js."""
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
        "description": description or "",
        "editor": editor,
        "isPublished": is_published,
        "isPrivate": False,
        "locale": locale,
        "path": path,
        "tags": tags or [],
        "title": title
    }
    
    result = graphql_query(mutation, variables)
    return result


def update_page(path, content, title=None, description=None, locale='en'):
    """Update an existing page in Wiki.js."""
    # First, get the page ID
    page_info = get_page_info(path, locale)
    if not page_info:
        print(f"Error: Page not found at path '{path}'")
        return None
    
    page_id = page_info['id']
    
    mutation = """
    mutation UpdatePage($id: Int!, $input: PageInput!) {
      pages {
        update(id: $id, input: $input) {
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
    
    input_data = {
        "path": path,
        "content": content,
        "localeCode": locale
    }
    
    if title:
        input_data["title"] = title
    if description:
        input_data["description"] = description
    
    variables = {
        "id": page_id,
        "input": input_data
    }
    
    result = graphql_query(mutation, variables)
    return result


def get_page_info(path, locale='en'):
    """Get page information by path."""
    query = """
    query GetPage($path: String!, $locale: String!) {
      pages {
        single(path: $path, locale: $locale) {
          id
          path
          title
          content
          description
        }
      }
    }
    """
    
    variables = {
        "path": path,
        "locale": locale
    }
    
    result = graphql_query(query, variables)
    page = result.get('data', {}).get('pages', {}).get('single')
    return page


def render_page(path, locale='en'):
    """Trigger page rendering."""
    mutation = """
    mutation RenderPage($path: String!, $locale: String!) {
      pages {
        render(path: $path, locale: $locale) {
          responseResult {
            succeeded
            errorCode
            slug
            message
          }
        }
      }
    }
    """
    
    variables = {
        "path": path,
        "locale": locale
    }
    
    result = graphql_query(mutation, variables)
    return result


def main():
    parser = argparse.ArgumentParser(description='Edit Wiki.js pages via API')
    parser.add_argument('action', choices=['create', 'update', 'get', 'render'],
                       help='Action to perform')
    parser.add_argument('--path', required=True, help='Page path (e.g., /home)')
    parser.add_argument('--title', help='Page title (required for create)')
    parser.add_argument('--content', help='Content file path or direct content')
    parser.add_argument('--description', help='Page description')
    parser.add_argument('--locale', default='en', help='Locale code (default: en)')
    parser.add_argument('--published', action='store_true', default=True,
                       help='Publish page (default: True)')
    
    args = parser.parse_args()
    
    # Read content if file path provided
    content = None
    if args.content:
        if os.path.isfile(args.content):
            content = read_file_content(args.content)
        else:
            content = args.content
    
    try:
        if args.action == 'create':
            if not args.title:
                print("Error: --title is required for create action")
                sys.exit(1)
            if not content:
                print("Error: --content is required for create action")
                sys.exit(1)
            
            result = create_page(args.path, args.title, content, args.description,
                               args.published, args.locale)
            if result.get('data', {}).get('pages', {}).get('create', {}).get('responseResult', {}).get('succeeded'):
                page = result['data']['pages']['create']['page']
                print(f"✓ Page created: {page['title']} at {page['path']}")
            else:
                error = result.get('data', {}).get('pages', {}).get('create', {}).get('responseResult', {})
                print(f"✗ Error: {error.get('message', 'Unknown error')}")
                sys.exit(1)
        
        elif args.action == 'update':
            if not content:
                print("Error: --content is required for update action")
                sys.exit(1)
            
            result = update_page(args.path, content, args.title, args.description, args.locale)
            if result.get('data', {}).get('pages', {}).get('update', {}).get('responseResult', {}).get('succeeded'):
                page = result['data']['pages']['update']['page']
                print(f"✓ Page updated: {page['title']} at {page['path']}")
            else:
                error = result.get('data', {}).get('pages', {}).get('update', {}).get('responseResult', {})
                print(f"✗ Error: {error.get('message', 'Unknown error')}")
                sys.exit(1)
        
        elif args.action == 'get':
            page = get_page_info(args.path, args.locale)
            if page:
                print(f"Page: {page['title']}")
                print(f"Path: {page['path']}")
                print(f"\nContent:\n{page.get('content', 'N/A')}")
            else:
                print(f"Page not found at path: {args.path}")
                sys.exit(1)
        
        elif args.action == 'render':
            result = render_page(args.path, args.locale)
            if result.get('data', {}).get('pages', {}).get('render', {}).get('responseResult', {}).get('succeeded'):
                print(f"✓ Page rendered: {args.path}")
            else:
                error = result.get('data', {}).get('pages', {}).get('render', {}).get('responseResult', {})
                print(f"✗ Error: {error.get('message', 'Unknown error')}")
                sys.exit(1)
    
    except requests.exceptions.RequestException as e:
        print(f"✗ Request error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

