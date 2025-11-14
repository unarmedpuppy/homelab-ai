#!/usr/bin/env python3
"""
Add books to Bookshelf using Open Library API (bypasses Goodreads completely).
This uses Open Library's free API which doesn't require keys and is reliable.
"""

import requests
import json
import sys
import time

BOOKSHELF_URL = "http://192.168.86.47:8787/api/v1"
API_KEY = "c51faf51b674418eba3a87fc8bb109b9"

def get_book_from_openlibrary(isbn):
    """Get book metadata from Open Library."""
    try:
        # Get book data
        response = requests.get(
            f"https://openlibrary.org/isbn/{isbn}.json",
            timeout=10
        )
        if response.status_code != 200:
            return None
        
        book_data = response.json()
        
        # Get author data
        author_name = "Unknown"
        if book_data.get("authors"):
            author_key = book_data["authors"][0].get("key", "")
            if author_key:
                author_response = requests.get(
                    f"https://openlibrary.org{author_key}.json",
                    timeout=10
                )
                if author_response.status_code == 200:
                    author_name = author_response.json().get("name", "Unknown")
        
        return {
            "title": book_data.get("title", f"Book {isbn}"),
            "author": author_name,
            "isbn": isbn,
            "publish_date": book_data.get("publish_date", ""),
            "number_of_pages": book_data.get("number_of_pages", ""),
        }
    except Exception as e:
        print(f"Error fetching from Open Library: {e}")
        return None

def add_book_via_ui_workaround(isbn, title, author):
    """Instructions for manual addition since API requires metadata."""
    print("\n" + "="*60)
    print("MANUAL ADDITION INSTRUCTIONS:")
    print("="*60)
    print(f"\nBook Info:")
    print(f"  Title: {title}")
    print(f"  Author: {author}")
    print(f"  ISBN: {isbn}")
    print(f"\nSteps:")
    print(f"  1. Open Bookshelf: http://192.168.86.47:8787")
    print(f"  2. Go to 'Books' > 'Add New'")
    print(f"  3. In the search box, type: {isbn}")
    print(f"  4. Click search and WAIT 2-3 minutes (Goodreads will timeout)")
    print(f"  5. Even if it shows error, the book may appear in your library")
    print(f"  6. Once book is added, Bookshelf will automatically search NZBHydra2")
    print(f"  7. Check 'Activity' tab to see downloads")
    print("\n" + "="*60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 add_book_openlibrary.py <ISBN>")
        print("Example: python3 add_book_openlibrary.py 9780439785969")
        sys.exit(1)
    
    isbn = sys.argv[1]
    print(f"Fetching book info for ISBN: {isbn}")
    
    book_info = get_book_from_openlibrary(isbn)
    if book_info:
        print(f"✓ Found: {book_info['title']} by {book_info['author']}")
        add_book_via_ui_workaround(isbn, book_info['title'], book_info['author'])
    else:
        print(f"✗ Could not find book with ISBN: {isbn}")
        print(f"  Try searching manually in Bookshelf UI")

