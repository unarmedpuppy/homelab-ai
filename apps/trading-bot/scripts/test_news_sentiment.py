#!/usr/bin/env python3
"""
Test Financial News Sentiment Integration
==========================================

Test script for financial news sentiment provider.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.providers.sentiment import NewsSentimentProvider
from src.config.settings import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_news_sentiment():
    """Test financial news sentiment provider"""
    print("=" * 60)
    print("Testing Financial News Sentiment Provider")
    print("=" * 60)
    print()
    
    # Check configuration
    print("📋 Configuration Check:")
    config = settings.news
    print(f"   News Provider Enabled: {config.enabled}")
    print(f"   NewsAPI Key: {'✅ Set' if config.newsapi_key else '❌ Not set'}")
    print(f"   RSS Feeds: {config.rss_feeds}")
    print(f"   Fetch Full Text: {config.fetch_full_text}")
    print(f"   Rate Limit Enabled: True")
    print(f"   Cache TTL: {config.cache_ttl}s")
    print(f"   Max Results: {config.max_results}")
    print()
    
    # Create provider
    print("🔧 Initializing News Sentiment Provider...")
    provider = NewsSentimentProvider()
    
    if not provider.is_available():
        print("❌ News provider not available")
        print("   Please configure NEWS_ENABLED=true and/or NEWS_RSS_FEEDS")
        print()
        print("   RSS feeds can be configured via NEWS_RSS_FEEDS environment variable")
        print("   NewsAPI key can be configured via NEWS_NEWSAPI_KEY (optional)")
        return False
    
    print("✅ News provider initialized")
    print()
    
    # Test symbol sentiment
    test_symbols = ["SPY", "AAPL", "TSLA"]
    
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
                print(f"   This might mean no recent news articles mention this symbol")
                print()
                
        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    print("=" * 60)
    print("✅ News sentiment test completed!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        success = test_news_sentiment()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
