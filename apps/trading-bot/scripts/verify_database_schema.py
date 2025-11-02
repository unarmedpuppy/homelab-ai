#!/usr/bin/env python3
"""
Database Schema Verification Script
===================================

Verify database schema matches models and check for missing tables/indexes.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database.migrations import MigrationManager
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    print("=" * 60)
    print("Database Schema Verification")
    print("=" * 60)
    print()
    
    manager = MigrationManager()
    
    # Get table information
    print("📊 Database Tables:")
    table_info = manager.get_table_info()
    if table_info:
        for table_name, info in table_info.items():
            print(f"  ✓ {table_name}")
            print(f"    Columns: {len(info['columns'])}")
            print(f"    Indexes: {len(info['indexes'])}")
    else:
        print("  No tables found")
    print()
    
    # Check for missing tables
    print("🔍 Checking for missing tables...")
    missing_tables = manager.check_missing_tables()
    if missing_tables:
        print(f"  ⚠️  Missing tables: {', '.join(missing_tables)}")
    else:
        print("  ✅ All expected tables exist")
    print()
    
    # Check for missing indexes
    print("🔍 Checking for missing indexes...")
    missing_indexes = manager.check_missing_indexes()
    if missing_indexes:
        print("  ⚠️  Missing indexes:")
        for table, indexes in missing_indexes.items():
            print(f"    {table}: {', '.join(indexes)}")
    else:
        print("  ✅ All expected indexes exist")
    print()
    
    # Verify schema
    print("✅ Verifying schema...")
    verification = manager.verify_schema()
    
    if verification['valid']:
        print("  ✅ Schema is valid!")
    else:
        print("  ❌ Schema validation failed:")
        if verification['missing_tables']:
            print(f"    Missing tables: {', '.join(verification['missing_tables'])}")
    
    if verification['warnings']:
        for warning in verification['warnings']:
            print(f"  ⚠️  {warning}")
    
    # Get schema version
    print()
    print("📋 Schema Version:")
    version = manager.get_schema_version()
    if version:
        print(f"  Current version: {version}")
    else:
        print("  No version information available")
    
    print()
    print("=" * 60)
    
    if not verification['valid']:
        print("❌ Schema verification failed. Run migrations to fix.")
        sys.exit(1)
    else:
        print("✅ Schema verification passed!")
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

