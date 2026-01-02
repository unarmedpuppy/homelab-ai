#!/usr/bin/env python3
"""
Database migration script to add Phase 2.2 metadata columns to conversations table.
"""
import sqlite3
import sys
from pathlib import Path

# Use same path as database.py - mounted volume at /data
import os
DB_PATH = Path(os.getenv("DATABASE_PATH", "/data/local-ai-router.db"))

def migrate_database():
    """Add username, source, and display_name columns to conversations table."""
    print(f"Connecting to database: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if columns already exist
    cursor.execute("PRAGMA table_info(conversations)")
    columns = {row[1] for row in cursor.fetchall()}

    print(f"Current columns: {columns}")

    # Add missing columns
    migrations_run = []

    if 'username' not in columns:
        print("Adding 'username' column...")
        cursor.execute("ALTER TABLE conversations ADD COLUMN username TEXT")
        migrations_run.append('username')

    if 'source' not in columns:
        print("Adding 'source' column...")
        cursor.execute("ALTER TABLE conversations ADD COLUMN source TEXT")
        migrations_run.append('source')

    if 'display_name' not in columns:
        print("Adding 'display_name' column...")
        cursor.execute("ALTER TABLE conversations ADD COLUMN display_name TEXT")
        migrations_run.append('display_name')

    if migrations_run:
        conn.commit()
        print(f"✅ Migration complete! Added columns: {', '.join(migrations_run)}")
    else:
        print("✅ No migration needed - all columns already exist")

    # Verify final schema
    cursor.execute("PRAGMA table_info(conversations)")
    print("\nFinal schema:")
    for row in cursor.fetchall():
        print(f"  - {row[1]} ({row[2]})")

    conn.close()
    print("\nDatabase connection closed")
    return len(migrations_run) > 0

if __name__ == "__main__":
    try:
        changed = migrate_database()
        sys.exit(0 if changed else 0)  # Always exit 0 for success
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
