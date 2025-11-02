#!/usr/bin/env python3
"""
Data Retention Cleanup Script
==============================

Script to clean up old data based on retention policies.
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database.retention import DataRetentionPolicy
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Clean up old data based on retention policies")
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )
    parser.add_argument(
        '--retention-days',
        type=int,
        default=None,
        help='Override default retention period (days) for all data types'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Data Retention Cleanup")
    print("=" * 60)
    print()
    
    if args.dry_run:
        print("⚠️  DRY RUN MODE - No data will be deleted")
        print()
    
    # Create retention policy
    retention_config = {}
    if args.retention_days:
        retention_config = {
            'tweets': args.retention_days,
            'tweet_sentiments': args.retention_days,
            'reddit_posts': args.retention_days,
            'reddit_sentiments': args.retention_days,
            'symbol_sentiments': args.retention_days,
            'aggregated_sentiments': args.retention_days,
            'confluence_scores': args.retention_days,
            'options_flow': args.retention_days
        }
    
    policy = DataRetentionPolicy(retention_days=retention_config if retention_config else None)
    
    # Show current data counts
    print("📊 Current Data Counts:")
    counts = policy.get_data_counts()
    for data_type, buckets in counts.items():
        print(f"  {data_type}:")
        for bucket, count in buckets.items():
            print(f"    {bucket}: {count:,} records")
    print()
    
    # Show retention policies
    print("📋 Retention Policies:")
    for data_type, days in policy.retention_days.items():
        print(f"  {data_type}: {days} days")
    print()
    
    # Perform cleanup
    print("🧹 Performing cleanup...")
    results = policy.cleanup_old_data(dry_run=args.dry_run)
    
    print()
    print("=" * 60)
    print("Cleanup Summary")
    print("=" * 60)
    
    total_deleted = 0
    for data_type, count in results.items():
        action = "Would delete" if args.dry_run else "Deleted"
        print(f"  {data_type}: {action} {count:,} records")
        total_deleted += count
    
    print(f"\nTotal: {action} {total_deleted:,} records")
    
    if args.dry_run:
        print("\n⚠️  This was a dry run. Use without --dry-run to actually delete data.")
    
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

