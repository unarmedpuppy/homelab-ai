#!/usr/bin/env python3
"""
Add books directly to Bookshelf using ISBN, bypassing metadata lookup.
This works around the Goodreads timeout issue.
"""

import requests
import json
import sys
import time

BOOKSHELF_URL = "http://192.168.86.47:8787/api/v1"
API_KEY = "c51faf51b674418eba3a87fc8bb109b9"

def add_book_by_isbn_direct(isbn, title=None, author_name=None):
    """Add a book directly using minimal metadata."""
    # Try to get basic info from Open Library (free, no API key needed)
    try:
        ol_response = requests.get(
            f"https://openlibrary.org/isbn/{isbn}.json",
            timeout=10
        )
        if ol_response.status_code == 200:
            ol_data = ol_response.json()
            if not title:
                title = ol_data.get("title", f"Book {isbn}")
            if not author_name and ol_data.get("authors"):
                author_id = ol_data["authors"][0].get("key", "")
                if author_id:
                    author_response = requests.get(
                        f"https://openlibrary.org{author_id}.json",
                        timeout=10
                    )
                    if author_response.status_code == 200:
                        author_name = author_response.json().get("name", "Unknown")
    except:
        pass
    
    # Create a minimal book entry
    # Bookshelf/Readarr API structure for adding books
    book_data = {
        "title": title or f"Book {isbn}",
        "authorName": author_name or "Unknown Author",
        "isbn": isbn,
        "addOptions": {
            "searchForNewBook": True,
            "monitor": "all"
        }
    }
    
    # Try to add via author first (if we have author name)
    if author_name and author_name != "Unknown Author":
        # Search for author
        author_search = requests.get(
            f"{BOOKSHELF_URL}/author/lookup",
            headers={"X-Api-Key": API_KEY},
            params={"term": author_name},
            timeout=30
        )
        
        if author_search.status_code == 200:
            authors = author_search.json()
            if authors:
                author_id = authors[0].get("id")
                if author_id:
                    # Add book to existing author
                    book_data["authorId"] = author_id
                    add_response = requests.post(
                        f"{BOOKSHELF_URL}/book",
                        headers={"X-Api-Key": API_KEY, "Content-Type": "application/json"},
                        json=book_data,
                        timeout=30
                    )
                    if add_response.status_code in [200, 201]:
                        print(f"✓ Added '{title}' by {author_name} (ISBN: {isbn})")
                        return True
    
    # Fallback: try direct book add
    add_response = requests.post(
        f"{BOOKSHELF_URL}/book",
        headers={"X-Api-Key": API_KEY, "Content-Type": "application/json"},
        json=book_data,
        timeout=30
    )
    
    if add_response.status_code in [200, 201]:
        print(f"✓ Added '{title}' (ISBN: {isbn})")
        return True
    else:
        print(f"✗ Failed to add book: {add_response.status_code}")
        print(f"  Response: {add_response.text[:200]}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 add_book_direct.py <ISBN> [title] [author]")
        print("Example: python3 add_book_direct.py 9780439785969")
        print("Example: python3 add_book_direct.py 9780439785969 'Harry Potter' 'J.K. Rowling'")
        sys.exit(1)
    
    isbn = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else None
    author = sys.argv[3] if len(sys.argv) > 3 else None
    
    print(f"Adding book with ISBN: {isbn}")
    if add_book_by_isbn_direct(isbn, title, author):
        print("✓ Book added! Bookshelf will now search NZBHydra2 for downloads.")
    else:
        print("✗ Failed to add book. Try adding manually in the UI using ISBN search.")

