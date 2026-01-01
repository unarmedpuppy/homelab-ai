#!/usr/bin/env python3
"""Clean up duplicate n8n workflows from database."""
import sqlite3
import sys

DB_PATH = "/tmp/n8n-db.sqlite"

# Workflow IDs to delete (keeping only one of each type)
IDS_TO_DELETE = [
    # Duplicate Container Crash Agent Analysis (keep W8CtrLsdnhRSrUWR)
    "QHaWtWUpDdTzpSQM",
    "YGU6bQMjVl8hEKtr",
    "MkeQ6z8uZeZrPAgz",
    "JE4HisYbqLGRs2R2",
    "h11cvLmcHOMoNewH",
    # Test workflows (My workflow 2-12)
    "bVBEFqVgcrkcI4Yd",
    "nqJ8agmXwWs8bYpI",
    "ET9sZf4Oo0OXHUP2",
    "KaDCOmQKi4rupNIS",
    "nYTzDgQHLFZpSKQO",
    "eB2AVq0sHs5MypTB",
    "sRrJzq1hHQ0U2NOe",
    "UqdM9vQfYaXMNyIc",
    "CchQ1LuY9kIU1PcO",
    "Qdgf6BMBtb6F9vQS",
    "xwcIXp6xB0j7CrvR",
    # Duplicate monitors
    "VMmvZLRBlym0seeC",  # Docker Container Failure Monitor duplicate
    "FjkNcBPwPOPlnL24",  # Docker Build Failure Monitor duplicate
]

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # List workflows before
    print("=== Workflows BEFORE cleanup ===")
    cur.execute("SELECT id, name, active FROM workflow_entity ORDER BY name")
    for row in cur.fetchall():
        marker = " [TO DELETE]" if row[0] in IDS_TO_DELETE else ""
        print(f"  {row[0]}|{row[1]}|active={row[2]}{marker}")
    
    # Delete duplicates
    print(f"\n=== Deleting {len(IDS_TO_DELETE)} workflows ===")
    deleted = 0
    for wf_id in IDS_TO_DELETE:
        cur.execute("DELETE FROM workflow_entity WHERE id = ?", (wf_id,))
        if cur.rowcount > 0:
            print(f"  Deleted: {wf_id}")
            deleted += 1
        else:
            print(f"  Not found: {wf_id}")
    
    conn.commit()
    
    # List workflows after
    print(f"\n=== Workflows AFTER cleanup ({deleted} deleted) ===")
    cur.execute("SELECT id, name, active FROM workflow_entity ORDER BY name")
    for row in cur.fetchall():
        print(f"  {row[0]}|{row[1]}|active={row[2]}")
    
    conn.close()
    print("\nDone! Now copy database back to container:")
    print("  docker cp /tmp/n8n-db.sqlite n8n:/home/node/.n8n/database.sqlite")
    print("  docker restart n8n")

if __name__ == "__main__":
    main()
