#!/usr/bin/env python3
"""
Test StockTwits Sentiment Provider
===================================

Test script for StockTwits sentiment integration.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.providers.sentiment.stocktwits import StockTwitsSentimentProvider
from src.utils.cache import get_cache_manager
from src.utils.rate_limiter import get_rate_limiter
from src.utils.monitoring import get_usage_monitor
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_provider_availability():
    """Test provider availability"""
    print("\n" + "=" * 60)
    print("Test 1: Provider Availability")
    print("=" * 60)
    
    provider = StockTwitsSentimentProvider()
    available = provider.is_available()
    
    print(f"✅ StockTwits provider available: {available}")
    
    if not available:
        print("\n⚠️  StockTwits provider not available.")
        print("   Make sure 'requests' is installed: pip install requests")
        return False
    
    return True


def test_rate_limiting():
    """Test rate limiting"""
    print("\n" + "=" * 60)
    print("Test 2: Rate Limiting")
    print("=" * 60)
    
    limiter = get_rate_limiter("stocktwits")
    
    # Test rate limit check (200 requests per hour)
    is_allowed, status = limiter.check_rate_limit(limit=200, window_seconds=3600)
    
    print(f"✅ Rate limit check: {is_allowed}")
    print(f"   Status: {status.used}/{status.allowed} used, {status.remaining} remaining")
    print(f"   Reset at: {status.reset_at}")
    
    return True


def test_caching():
    """Test caching"""
    print("\n" + "=" * 60)
    print("Test 3: Caching")
    print("=" * 60)
    
    cache = get_cache_manager()
    
    # Test cache
    test_key = "test:stocktwits:cache"
    test_data = {"symbol": "AAPL", "sentiment": 0.5}
    
    cache.set(test_key, test_data, ttl=60)
    cached_data = cache.get(test_key)
    
    print(f"✅ Cache test: {cached_data == test_data}")
    print(f"   Redis available: {cache.is_available()}")
    print(f"   Using Redis: {cache.redis_client is not None}")
    
    # Cleanup
    cache.delete(test_key)
    
    return True


def test_sentiment_retrieval():
    """Test sentiment retrieval for a symbol"""
    print("\n" + "=" * 60)
    print("Test 4: Sentiment Retrieval")
    print("=" * 60)
    
    provider = StockTwitsSentimentProvider()
    
    if not provider.is_available():
        print("⚠️  Skipping: Provider not available")
        return False
    
    # Test with a popular symbol
    symbol = "AAPL"
    print(f"\nFetching sentiment for {symbol}...")
    
    try:
        sentiment = provider.get_sentiment(symbol, hours=24)
        
        if sentiment:
            print(f"\n✅ Sentiment retrieved successfully!")
            print(f"   Symbol: {sentiment.symbol}")
            print(f"   Weighted Sentiment: {sentiment.weighted_sentiment:.3f}")
            print(f"   Sentiment Level: {sentiment.sentiment_level.value}")
            print(f"   Mention Count: {sentiment.mention_count}")
            print(f"   Confidence: {sentiment.confidence:.3f}")
            return True
        else:
            print(f"⚠️  No sentiment data returned for {symbol}")
            return False
            
    except Exception as e:
        print(f"❌ Error retrieving sentiment: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_trending_symbols():
    """Test trending symbols"""
    print("\n" + "=" * 60)
    print("Test 5: Trending Symbols")
    print("=" * 60)
    
    provider = StockTwitsSentimentProvider()
    
    if not provider.is_available():
        print("⚠️  Skipping: Provider not available")
        return False
    
    try:
        trending = provider.get_trending_symbols()
        
        if trending:
            print(f"\n✅ Found {len(trending)} trending symbols")
            print("\nTop 5 trending symbols:")
            for i, symbol_data in enumerate(trending[:5], 1):
                print(f"   {i}. {symbol_data.get('symbol')} - {symbol_data.get('title', 'N/A')}")
            return True
        else:
            print("⚠️  No trending symbols returned")
            return False
            
    except Exception as e:
        print(f"❌ Error retrieving trending symbols: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_usage_monitoring():
    """Test usage monitoring"""
    print("\n" + "=" * 60)
    print("Test 6: Usage Monitoring")
    print("=" * 60)
    
    monitor = get_usage_monitor()
    
    # Record some test requests
    monitor.record_request("stocktwits", success=True, cached=True)
    monitor.record_request("stocktwits", success=True, cached=False)
    monitor.record_request("stocktwits", success=False)
    
    # Get metrics
    metrics = monitor.get_source_metrics("stocktwits")
    
    if metrics:
        print(f"✅ Usage monitoring working")
        print(f"   Requests today: {metrics.requests_today}")
        print(f"   Cache hits: {metrics.cache_hits}")
        print(f"   Cache misses: {metrics.cache_misses}")
        print(f"   Cache hit rate: {metrics.cache_hit_rate:.2%}")
        print(f"   Errors: {metrics.errors}")
        return True
    else:
        print("⚠️  No metrics available")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("StockTwits Sentiment Provider Test Suite")
    print("=" * 60)
    
    results = {
        "Provider Availability": test_provider_availability(),
        "Rate Limiting": test_rate_limiting(),
        "Caching": test_caching(),
        "Sentiment Retrieval": test_sentiment_retrieval(),
        "Trending Symbols": test_trending_symbols(),
        "Usage Monitoring": test_usage_monitoring(),
    }
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
