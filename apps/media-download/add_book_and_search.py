#!/usr/bin/env python3
"""
Add a book to Bookshelf and trigger a search.
This bypasses the metadata search issue.
"""

import requests
import json
import sys

BOOKSHELF_URL = "http://192.168.86.47:8787/api/v1"
API_KEY = "c51faf51b674418eba3a87fc8bb109b9"

def add_book_by_isbn(isbn, title=None, author=None):
    """Add a book by ISBN and trigger search."""
    # First, try to lookup by ISBN
    lookup_url = f"{BOOKSHELF_URL}/book/lookup"
    params = {"term": f"isbn:{isbn}"}
    
    response = requests.get(
        lookup_url,
        headers={"X-Api-Key": API_KEY},
        params=params,
        timeout=30
    )
    
    if response.status_code == 200:
        results = response.json()
        if results:
            book = results[0]
            print(f"✓ Found book: {book.get('title', 'N/A')}")
            
            # Add the book
            add_url = f"{BOOKSHELF_URL}/book"
            add_data = {
                "title": book.get("title"),
                "authorId": book.get("author", {}).get("id") if book.get("author") else None,
                "foreignBookId": book.get("foreignBookId"),
                "addOptions": {
                    "searchForNewBook": True,
                    "monitor": "all"
                }
            }
            
            add_response = requests.post(
                add_url,
                headers={"X-Api-Key": API_KEY, "Content-Type": "application/json"},
                json=add_data,
                timeout=30
            )
            
            if add_response.status_code in [200, 201]:
                print("✓ Book added and search triggered!")
                return True
    
    print("✗ Could not find book by ISBN")
    return False

def trigger_manual_search(book_id=None):
    """Trigger a manual search for books."""
    if book_id:
        url = f"{BOOKSHELF_URL}/command"
        data = {
            "name": "BookSearch",
            "bookIds": [book_id]
        }
    else:
        url = f"{BOOKSHELF_URL}/command"
        data = {
            "name": "SearchMissing"
        }
    
    response = requests.post(
        url,
        headers={"X-Api-Key": API_KEY, "Content-Type": "application/json"},
        json=data,
        timeout=30
    )
    
    if response.status_code in [200, 201, 202]:
        print("✓ Search triggered!")
        return True
    else:
        print(f"✗ Failed to trigger search: {response.status_code}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 add_book_and_search.py <ISBN>")
        print("Example: python3 add_book_and_search.py 9780439785969")
        sys.exit(1)
    
    isbn = sys.argv[1]
    print(f"Adding book with ISBN: {isbn}")
    if add_book_by_isbn(isbn):
        print("✓ Book added successfully!")
    else:
        print("✗ Failed to add book")

