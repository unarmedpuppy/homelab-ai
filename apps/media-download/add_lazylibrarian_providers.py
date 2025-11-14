#!/usr/bin/env python3
"""
Add providers directly to LazyLibrarian database.
This script modifies the database file directly.
"""

import sqlite3
import sys
import os

# Database path (on server)
DB_PATH = "lazylibrarian/config/lazylibrarian.db"
SERVER_DB_PATH = "~/server/apps/media-download/lazylibrarian/config/lazylibrarian.db"

def add_providers(db_path):
    """Add NZBHydra2 and Jackett providers to LazyLibrarian database."""
    if not os.path.exists(db_path):
        print(f"✗ Database not found at: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Add NZBHydra2 (Newznab)
        print("Adding NZBHydra2 provider...")
        cursor.execute("""
            INSERT OR REPLACE INTO newznab 
            (Name, Host, Apipath, Apikey, Enabled, Priority, Types)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            'NZBHydra2',
            'http://media-download-nzbhydra2:5076',
            '/api',
            '2SQ42T9209NUIQCAJTPBMTLBJF',
            1,  # Enabled
            0,  # Priority
            'E,A'  # Types: Ebooks, Audiobooks
        ))
        
        # Add Jackett (Torznab)
        print("Adding Jackett provider...")
        cursor.execute("""
            INSERT OR REPLACE INTO torznab 
            (Name, Host, Apipath, Apikey, Enabled, Priority, Seeders, Types)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'Jackett',
            'http://media-download-jackett:9117',
            '/api/v2.0/indexers/all/results/torznab',
            'orjbnk0p7ar5s2u521emxrwb8cjvrz8c',
            1,  # Enabled
            0,  # Priority
            0,  # Min seeders
            'E,A'  # Types: Ebooks, Audiobooks
        ))
        
        conn.commit()
        conn.close()
        
        print("✓ Providers added successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    # Try local path first
    if os.path.exists(DB_PATH):
        add_providers(DB_PATH)
    else:
        # Try server path
        import subprocess
        print("Database not found locally. Trying to modify on server...")
        
        script = f"""
import sqlite3
conn = sqlite3.connect('{SERVER_DB_PATH.replace('~', '/home/unarmedpuppy')}')
cursor = conn.cursor()

# Add NZBHydra2
cursor.execute('''
    INSERT OR REPLACE INTO newznab 
    (Name, Host, Apipath, Apikey, Enabled, Priority, Types)
    VALUES (?, ?, ?, ?, ?, ?, ?)
''', ('NZBHydra2', 'http://media-download-nzbhydra2:5076', '/api', 
      '2SQ42T9209NUIQCAJTPBMTLBJF', 1, 0, 'E,A'))

# Add Jackett
cursor.execute('''
    INSERT OR REPLACE INTO torznab 
    (Name, Host, Apipath, Apikey, Enabled, Priority, Seeders, Types)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
''', ('Jackett', 'http://media-download-jackett:9117', 
      '/api/v2.0/indexers/all/results/torznab',
      'orjbnk0p7ar5s2u521emxrwb8cjvrz8c', 1, 0, 0, 'E,A'))

conn.commit()
conn.close()
print('✓ Providers added successfully!')
"""
        
        result = subprocess.run(
            ["bash", "scripts/connect-server.sh", f"cd ~/server/apps/media-download && python3 -c \"{script}\""],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)

if __name__ == "__main__":
    main()

