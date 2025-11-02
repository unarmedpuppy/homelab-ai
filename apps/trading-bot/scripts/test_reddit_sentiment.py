#!/usr/bin/env python3
"""
Test Reddit Sentiment Integration
==================================

Test script for Reddit sentiment provider.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.providers.sentiment.reddit import RedditSentimentProvider
from src.data.providers.sentiment.repository import SentimentRepository
from src.data.database import SessionLocal
from src.config.settings import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_reddit_sentiment():
    """Test Reddit sentiment provider"""
    print("=" * 60)
    print("Testing Reddit Sentiment Provider")
    print("=" * 60)
    print()
    
    # Check configuration
    print("📋 Configuration Check:")
    print(f"   Reddit Client ID: {'✅ Set' if settings.reddit.client_id else '❌ Not set'}")
    print(f"   Reddit Client Secret: {'✅ Set' if settings.reddit.client_secret else '❌ Not set'}")
    print(f"   User Agent: {settings.reddit.user_agent}")
    print(f"   Subreddits: {settings.reddit.subreddits}")
    print(f"   Rate Limit Enabled: {settings.reddit.rate_limit_enabled}")
    print(f"   Cache TTL: {settings.reddit.cache_ttl}s")
    print(f"   Min Score: {settings.reddit.min_score}")
    print(f"   Min Length: {settings.reddit.min_length}")
    print()
    
    # Create provider
    print("🔧 Initializing Reddit Sentiment Provider...")
    # Test with database persistence enabled
    provider = RedditSentimentProvider(persist_to_db=True)
    
    if not provider.is_available():
        print("❌ Reddit provider not available")
        print("   Please configure REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in your .env file")
        print()
        print("   Get API credentials from: https://www.reddit.com/prefs/apps")
        print("   Create a 'script' type application")
        return False
    
    print("✅ Reddit provider initialized")
    print(f"   Database Persistence: {'✅ Enabled' if provider.persist_to_db else '❌ Disabled'}")
    print()
    
    # Test symbol sentiment
    test_symbols = ["SPY", "AAPL"]
    
    for symbol in test_symbols:
        print(f"📊 Analyzing sentiment for {symbol}...")
        print("-" * 60)
        
        try:
            sentiment = provider.get_sentiment(symbol, hours=24)
            
            if sentiment:
                print(f"✅ Sentiment Analysis for {symbol}:")
                print(f"   Mentions: {sentiment.mention_count}")
                print(f"   Average Sentiment: {sentiment.average_sentiment:.3f}")
                print(f"   Weighted Sentiment: {sentiment.weighted_sentiment:.3f}")
                print(f"   Sentiment Level: {sentiment.sentiment_level.value}")
                print(f"   Confidence: {sentiment.confidence:.2%}")
                print(f"   Engagement Score: {sentiment.engagement_score:.3f}")
                
                if sentiment.influencer_sentiment is not None:
                    print(f"   Influencer Sentiment: {sentiment.influencer_sentiment:.3f}")
                
                print()
            else:
                print(f"⚠️  No sentiment data available for {symbol}")
                print()
                
        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    # Test trending symbols
    print("=" * 60)
    print("📈 Testing Trending Symbols Detection...")
    print("=" * 60)
    print()
    
    try:
        trending = provider.get_trending_symbols(min_mentions=5)
        
        if trending:
            print(f"✅ Found {len(trending)} trending symbols:")
            for i, item in enumerate(trending[:10], 1):  # Show top 10
                print(f"   {i}. {item['symbol']}: {item['mentions']} mentions")
            print()
        else:
            print("⚠️  No trending symbols found (may need more data)")
            print()
            
    except Exception as e:
        print(f"❌ Error getting trending symbols: {e}")
        import traceback
        traceback.print_exc()
        print()
    
    # Test database persistence
    if provider.persist_to_db:
        print("💾 Testing Database Persistence...")
        print("-" * 60)
        
        try:
            db = SessionLocal()
            repository = SentimentRepository(db=db)
            
            # Test retrieving recent sentiment from database
            test_symbol = test_symbols[0] if test_symbols else "SPY"
            recent_sentiments = repository.get_recent_sentiment(test_symbol, hours=24, limit=10)
            
            print(f"✅ Retrieved {len(recent_sentiments)} sentiment records from database")
            
            # Test retrieving Reddit posts (filtered by "reddit_" prefix)
            tweets = repository.get_tweets_for_symbol(test_symbol, hours=24, limit=20)
            reddit_posts = [t for t in tweets if t.tweet_id.startswith("reddit_")]
            print(f"✅ Retrieved {len(reddit_posts)} Reddit posts from database")
            
            db.close()
            print()
            
        except Exception as e:
            print(f"❌ Error testing database persistence: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    print("=" * 60)
    print("✅ Reddit sentiment test completed!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        success = test_reddit_sentiment()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
