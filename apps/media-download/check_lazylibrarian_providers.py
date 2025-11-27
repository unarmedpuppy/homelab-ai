#!/usr/bin/env python3
"""Check LazyLibrarian provider configuration in database."""

import sqlite3
import sys

DB_PATH = "/config/lazylibrarian.db"

try:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check newznab table
    try:
        c.execute("SELECT * FROM newznab")
        rows = c.fetchall()
        if rows:
            print("Newznab providers:")
            # Get column names
            c.execute("PRAGMA table_info(newznab)")
            cols = [col[1] for col in c.fetchall()]
            print(f"Columns: {cols}")
            for row in rows:
                print(f"  {dict(zip(cols, row))}")
        else:
            print("No newznab providers found")
    except Exception as e:
        print(f"Error reading newznab table: {e}")
        # Try to get schema
        try:
            c.execute("PRAGMA table_info(newznab)")
            print("Newznab table schema:")
            for col in c.fetchall():
                print(f"  {col}")
        except:
            print("Could not get newznab table info")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")















