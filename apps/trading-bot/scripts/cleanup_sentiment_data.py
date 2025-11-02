#!/usr/bin/env python3
"""
Sentiment Data Cleanup Script
==============================

Scheduled cleanup script for old sentiment and confluence data.
Can be run via cron or scheduled task.

Usage:
    python scripts/cleanup_sentiment_data.py [--dry-run] [--days TWEETS,REDDIT,SYMBOL,AGGREGATED,CONFLUENCE]
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.providers.sentiment.repository import SentimentRepository
from src.config.settings import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main cleanup function"""
    parser = argparse.ArgumentParser(description='Clean up old sentiment data')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )
    parser.add_argument(
        '--days',
        type=str,
        default='90,90,365,730,730',
        help='Retention days: tweets,reddit_posts,symbol_sentiments,aggregated_sentiments,confluence_scores'
    )
    
    args = parser.parse_args()
    
    # Parse retention days
    try:
        days_list = [int(d.strip()) for d in args.days.split(',')]
        if len(days_list) != 5:
            raise ValueError("Must provide 5 comma-separated values")
        tweets_days, reddit_days, symbol_days, aggregated_days, confluence_days = days_list
    except ValueError as e:
        logger.error(f"Invalid days format: {e}")
        logger.error("Expected format: --days TWEETS,REDDIT,SYMBOL,AGGREGATED,CONFLUENCE")
        return False
    
    print("=" * 60)
    print("Sentiment Data Cleanup")
    print("=" * 60)
    print()
    
    if args.dry_run:
        print("⚠️  DRY RUN MODE - No data will be deleted")
        print()
    
    print("📋 Retention Periods:")
    print(f"   Tweets: {tweets_days} days")
    print(f"   Reddit Posts: {reddit_days} days")
    print(f"   Symbol Sentiments: {symbol_days} days")
    print(f"   Aggregated Sentiments: {aggregated_days} days")
    print(f"   Confluence Scores: {confluence_days} days")
    print()
    
    # Initialize repository
    repository = SentimentRepository()
    
    if args.dry_run:
        # In dry-run mode, we'd need to count without deleting
        # For now, just show the configuration
        print("ℹ️  Dry-run mode: Use without --dry-run to actually delete data")
        print()
        print("To run cleanup:")
        print("  python scripts/cleanup_sentiment_data.py")
        return True
    
    # Perform cleanup
    try:
        results = repository.cleanup_all_old_data(
            tweets_days=tweets_days,
            reddit_posts_days=reddit_days,
            symbol_sentiments_days=symbol_days,
            aggregated_sentiments_days=aggregated_days,
            confluence_scores_days=confluence_days
        )
        
        print("=" * 60)
        print("✅ Cleanup Complete!")
        print("=" * 60)
        print()
        print("📊 Deletion Summary:")
        print(f"   Tweets: {results['tweets']}")
        print(f"   Reddit Posts: {results['reddit_posts']}")
        print(f"   Symbol Sentiments: {results['symbol_sentiments']}")
        print(f"   Aggregated Sentiments: {results['aggregated_sentiments']}")
        print(f"   Confluence Scores: {results['confluence_scores']}")
        print()
        
        total = sum(results.values())
        print(f"   Total Records Deleted: {total}")
        print()
        
        return True
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Cleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

