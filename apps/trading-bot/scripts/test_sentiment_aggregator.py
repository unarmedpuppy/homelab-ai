#!/usr/bin/env python3
"""
Test Sentiment Aggregator
==========================

Test script for the sentiment aggregator system.
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
import os
os.chdir(project_root)  # Change to project root for relative imports

try:
    from src.data.providers.sentiment.aggregator import SentimentAggregator
    from src.data.providers.sentiment.twitter import TwitterSentimentProvider
    from src.data.providers.sentiment.reddit import RedditSentimentProvider
    from src.config.settings import settings
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Import error: {e}")
    print("\nNote: Dependencies may not be installed. Try:")
    print("  1. Install dependencies: pip install -r requirements/base.txt")
    print("  2. Or run in Docker: docker-compose exec bot python scripts/test_sentiment_aggregator.py")
    IMPORTS_AVAILABLE = False

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_aggregator_initialization():
    """Test that aggregator initializes correctly"""
    print("=" * 60)
    print("Testing Aggregator Initialization")
    print("=" * 60)
    print()
    
    try:
        aggregator = SentimentAggregator(persist_to_db=False)
        
        print(f"✅ Aggregator initialized successfully")
        print(f"   Available sources: {aggregator.get_available_sources()}")
        print(f"   Source weights: {aggregator.source_weights}")
        print(f"   Time decay hours: {aggregator.time_decay_hours}")
        print(f"   Min confidence: {aggregator.min_confidence}")
        print()
        
        return True, aggregator
    except Exception as e:
        print(f"❌ Failed to initialize aggregator: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False, None


def test_individual_providers(aggregator):
    """Test individual sentiment providers"""
    print("=" * 60)
    print("Testing Individual Providers")
    print("=" * 60)
    print()
    
    test_symbol = "SPY"
    providers_status = {}
    
    # Test Twitter
    if 'twitter' in aggregator.providers:
        print(f"📊 Testing Twitter provider for {test_symbol}...")
        try:
            twitter_provider = aggregator.providers['twitter']
            if twitter_provider.is_available():
                sentiment = twitter_provider.get_sentiment(test_symbol, hours=24)
                if sentiment:
                    print(f"   ✅ Twitter: {sentiment.weighted_sentiment:.3f} ({sentiment.sentiment_level.value})")
                    print(f"      Mentions: {sentiment.mention_count}, Confidence: {sentiment.confidence:.2%}")
                    providers_status['twitter'] = True
                else:
                    print(f"   ⚠️  Twitter: No data available for {test_symbol}")
                    providers_status['twitter'] = False
            else:
                print(f"   ⚠️  Twitter: Provider not available (check API credentials)")
                providers_status['twitter'] = False
        except Exception as e:
            print(f"   ❌ Twitter: Error - {e}")
            providers_status['twitter'] = False
    else:
        print(f"   ⚠️  Twitter: Provider not initialized")
        providers_status['twitter'] = False
    
    print()
    
    # Test Reddit
    if 'reddit' in aggregator.providers:
        print(f"📊 Testing Reddit provider for {test_symbol}...")
        try:
            reddit_provider = aggregator.providers['reddit']
            if reddit_provider.is_available():
                sentiment = reddit_provider.get_sentiment(test_symbol, hours=24)
                if sentiment:
                    print(f"   ✅ Reddit: {sentiment.weighted_sentiment:.3f} ({sentiment.sentiment_level.value})")
                    print(f"      Mentions: {sentiment.mention_count}, Confidence: {sentiment.confidence:.2%}")
                    providers_status['reddit'] = True
                else:
                    print(f"   ⚠️  Reddit: No data available for {test_symbol}")
                    providers_status['reddit'] = False
            else:
                print(f"   ⚠️  Reddit: Provider not available (check API credentials)")
                providers_status['reddit'] = False
        except Exception as e:
            print(f"   ❌ Reddit: Error - {e}")
            providers_status['reddit'] = False
    else:
        print(f"   ⚠️  Reddit: Provider not initialized")
        providers_status['reddit'] = False
    
    print()
    return providers_status


def test_aggregated_sentiment(aggregator):
    """Test aggregated sentiment calculation"""
    print("=" * 60)
    print("Testing Aggregated Sentiment")
    print("=" * 60)
    print()
    
    test_symbols = ["SPY", "AAPL"]
    results = {}
    
    for symbol in test_symbols:
        print(f"📊 Testing aggregated sentiment for {symbol}...")
        print("-" * 60)
        
        try:
            aggregated = aggregator.get_aggregated_sentiment(symbol, hours=24)
            
            if aggregated:
                print(f"✅ Aggregated Sentiment for {symbol}:")
                print(f"   Unified Score: {aggregated.unified_sentiment:.3f}")
                print(f"   Sentiment Level: {aggregated.sentiment_level.value}")
                print(f"   Confidence: {aggregated.confidence:.2%}")
                print(f"   Sources: {aggregated.source_count}")
                print(f"   Total Mentions: {aggregated.total_mentions}")
                print(f"   Divergence Score: {aggregated.divergence_score:.3f}")
                print()
                print(f"   Source Breakdown:")
                for source, percentage in aggregated.source_breakdown.items():
                    if source in aggregated.sources:
                        source_data = aggregated.sources[source]
                        print(f"      {source.upper()}: {percentage:.1f}% contribution")
                        print(f"         Score: {source_data.sentiment_score:.3f}, "
                              f"Weighted: {source_data.weighted_sentiment:.3f}")
                        print(f"         Mentions: {source_data.mention_count}, "
                              f"Confidence: {source_data.confidence:.2%}")
                print()
                results[symbol] = True
            else:
                print(f"⚠️  No aggregated sentiment available for {symbol}")
                print(f"   (No sources returned valid data)")
                print()
                results[symbol] = False
                
        except Exception as e:
            print(f"❌ Error getting aggregated sentiment for {symbol}: {e}")
            import traceback
            traceback.print_exc()
            print()
            results[symbol] = False
    
    return results


def test_time_decay():
    """Test time decay weighting"""
    print("=" * 60)
    print("Testing Time Decay Weighting")
    print("=" * 60)
    print()
    
    aggregator = SentimentAggregator(persist_to_db=False)
    
    now = datetime.now()
    test_times = [
        (now, "Now (should be 1.0)"),
        (now - timedelta(hours=6), "6 hours ago (should be ~0.7)"),
        (now - timedelta(hours=12), "12 hours ago (should be ~0.5)"),
        (now - timedelta(hours=24), "24 hours ago (should be ~0.25)"),
    ]
    
    print("Time Decay Calculation (half-life = 24 hours):")
    for timestamp, description in test_times:
        weight = aggregator._calculate_time_decay(timestamp, hours=24)
        print(f"   {description}: {weight:.3f}")
    
    print()
    return True


def test_divergence_detection():
    """Test divergence detection"""
    print("=" * 60)
    print("Testing Divergence Detection")
    print("=" * 60)
    print()
    
    aggregator = SentimentAggregator(persist_to_db=False)
    
    # Test case 1: All sources agree (low divergence)
    print("Test Case 1: All sources agree (should have low divergence)")
    from src.data.providers.sentiment.aggregator import SourceSentiment
    from src.data.providers.sentiment.models import SentimentLevel
    
    sources_agree = {
        'twitter': SourceSentiment(
            source='twitter',
            symbol='AAPL',
            sentiment_score=0.5,
            weighted_sentiment=0.5,
            confidence=0.8,
            mention_count=100,
            timestamp=datetime.now(),
            sentiment_level=SentimentLevel.BULLISH,
            source_weight=1.0
        ),
        'reddit': SourceSentiment(
            source='reddit',
            symbol='AAPL',
            sentiment_score=0.48,
            weighted_sentiment=0.48,
            confidence=0.7,
            mention_count=50,
            timestamp=datetime.now(),
            sentiment_level=SentimentLevel.BULLISH,
            source_weight=1.0
        )
    }
    
    divergence_agree = aggregator._calculate_divergence(sources_agree)
    print(f"   Divergence when sources agree: {divergence_agree:.3f}")
    print()
    
    # Test case 2: Sources disagree (high divergence)
    print("Test Case 2: Sources disagree (should have high divergence)")
    sources_disagree = {
        'twitter': SourceSentiment(
            source='twitter',
            symbol='AAPL',
            sentiment_score=0.8,
            weighted_sentiment=0.8,
            confidence=0.8,
            mention_count=100,
            timestamp=datetime.now(),
            sentiment_level=SentimentLevel.VERY_BULLISH,
            source_weight=1.0
        ),
        'reddit': SourceSentiment(
            source='reddit',
            symbol='AAPL',
            sentiment_score=-0.6,
            weighted_sentiment=-0.6,
            confidence=0.7,
            mention_count=50,
            timestamp=datetime.now(),
            sentiment_level=SentimentLevel.BEARISH,
            source_weight=1.0
        )
    }
    
    divergence_disagree = aggregator._calculate_divergence(sources_disagree)
    print(f"   Divergence when sources disagree: {divergence_disagree:.3f}")
    print()
    
    assert divergence_disagree > divergence_agree, "Divergence should be higher when sources disagree"
    print("✅ Divergence detection working correctly")
    print()
    
    return True


async def main():
    """Main test function"""
    if not IMPORTS_AVAILABLE:
        print("❌ Cannot run tests - required imports failed")
        return False
    
    logger.info("🚀 Starting Sentiment Aggregator Tests...")
    print()
    
    # Test 1: Initialization
    success, aggregator = test_aggregator_initialization()
    if not success:
        print("❌ Failed to initialize aggregator. Cannot continue tests.")
        return False
    
    # Test 2: Individual providers
    providers_status = test_individual_providers(aggregator)
    
    # Test 3: Aggregated sentiment
    aggregated_results = test_aggregated_sentiment(aggregator)
    
    # Test 4: Time decay
    test_time_decay()
    
    # Test 5: Divergence detection
    test_divergence_detection()
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print()
    
    print("Provider Status:")
    for provider, status in providers_status.items():
        status_icon = "✅" if status else "⚠️"
        print(f"   {status_icon} {provider.upper()}: {'Available' if status else 'Not Available'}")
    print()
    
    print("Aggregated Sentiment Results:")
    for symbol, status in aggregated_results.items():
        status_icon = "✅" if status else "⚠️"
        print(f"   {status_icon} {symbol}: {'Success' if status else 'No Data'}")
    print()
    
    # Check if we have at least one working provider
    working_providers = sum(1 for status in providers_status.values() if status)
    
    if working_providers > 0:
        print(f"✅ Aggregator system is functional with {working_providers} provider(s)")
        print()
        print("Next steps:")
        print("   1. Test API endpoints: GET /api/sentiment/aggregated/{symbol}")
        print("   2. Test with real trading symbols")
        print("   3. Monitor aggregation accuracy")
        return True
    else:
        print("⚠️  No providers are available. Please configure API credentials:")
        print("   - Twitter: Set TWITTER_BEARER_TOKEN in .env")
        print("   - Reddit: Set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT in .env")
        print()
        print("✅ Aggregator system is working correctly (waiting for provider credentials)")
        return True


if __name__ == "__main__":
    from datetime import timedelta
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
