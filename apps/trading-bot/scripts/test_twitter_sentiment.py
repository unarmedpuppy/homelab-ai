#!/usr/bin/env python3
"""
Test Twitter Sentiment Integration
==================================

Test script for Twitter/X sentiment provider.
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.providers.sentiment import TwitterSentimentProvider
from src.data.providers.sentiment.repository import SentimentRepository
from src.data.database import SessionLocal
from src.config.settings import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_twitter_sentiment():
    """Test Twitter sentiment provider"""
    print("=" * 60)
    print("Testing Twitter/X Sentiment Provider")
    print("=" * 60)
    print()
    
    # Check configuration
    print("📋 Configuration Check:")
    print(f"   Twitter API Key: {'✅ Set' if settings.twitter.api_key else '❌ Not set'}")
    print(f"   Bearer Token: {'✅ Set' if settings.twitter.bearer_token else '❌ Not set'}")
    print(f"   Rate Limit Enabled: {settings.twitter.rate_limit_enabled}")
    print(f"   Cache TTL: {settings.twitter.cache_ttl}s")
    print()
    
    # Create provider
    print("🔧 Initializing Twitter Sentiment Provider...")
    # Test with database persistence enabled
    provider = TwitterSentimentProvider(persist_to_db=True)
    
    if not provider.is_available():
        print("❌ Twitter provider not available")
        print("   Please configure TWITTER_BEARER_TOKEN in your .env file")
        print()
        print("   Get API keys from: https://developer.twitter.com/en/portal/dashboard")
        return False
    
    print("✅ Twitter provider initialized")
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
            
            # Test retrieving tweets
            tweets = repository.get_tweets_for_symbol(test_symbol, hours=24, limit=10)
            print(f"✅ Retrieved {len(tweets)} tweets from database")
            
            # Test retrieving influencers
            influencers = repository.get_influencers(active_only=True)
            print(f"✅ Retrieved {len(influencers)} influencers from database")
            
            db.close()
            print()
            
        except Exception as e:
            print(f"❌ Error testing database persistence: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    print("=" * 60)
    print("✅ Twitter sentiment test completed!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_twitter_sentiment())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

