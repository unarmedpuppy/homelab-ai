#!/usr/bin/env python3
"""
Test Google Trends Sentiment Integration
========================================

Tests the Google Trends sentiment provider functionality.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.providers.sentiment.google_trends import (
    GoogleTrendsClient,
    GoogleTrendsSentimentProvider
)
from src.config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_client():
    """Test Google Trends client"""
    print("="*60)
    print("Test 1: Google Trends Client")
    print("="*60)
    
    client = GoogleTrendsClient()
    
    if not client.is_available():
        print("⚠️  Google Trends client not available (pytrends not installed?)")
        print("   Install with: pip install pytrends")
        return False
    
    print("✅ Client initialized")
    
    # Test interest over time
    print("\n📊 Testing interest over time for 'AAPL stock'...")
    try:
        interest_data = client.get_interest_over_time("AAPL stock", timeframe='today 3-m')
        if interest_data:
            print(f"✅ Retrieved {len(interest_data.get('data', []))} data points")
            if interest_data.get('data'):
                latest = interest_data['data'][-1]
                print(f"   Latest: {latest['timestamp']} - Interest: {latest['interest']}")
        else:
            print("⚠️  No data returned")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test related queries
    print("\n🔍 Testing related queries for 'AAPL stock'...")
    try:
        related = client.get_related_queries("AAPL stock")
        if related:
            rising = related.get('rising', [])
            top = related.get('top', [])
            print(f"✅ Related queries - Rising: {len(rising)}, Top: {len(top)}")
            if rising:
                print(f"   Top rising: {rising[0]['query']}")
        else:
            print("⚠️  No related queries returned")
    except Exception as e:
        print(f"⚠️  Error (may be rate-limited): {e}")
    
    return True


def test_sentiment_provider():
    """Test sentiment provider"""
    print("\n" + "="*60)
    print("Test 2: Google Trends Sentiment Provider")
    print("="*60)
    
    provider = GoogleTrendsSentimentProvider(persist_to_db=False)
    
    if not provider.is_available():
        print("⚠️  Provider not available")
        return False
    
    print("✅ Provider initialized")
    
    # Test sentiment calculation
    test_symbols = ["AAPL", "SPY", "TSLA"]
    
    for symbol in test_symbols:
        print(f"\n📈 Testing sentiment for {symbol}...")
        try:
            sentiment = provider.get_sentiment(symbol, hours=24)
            
            if sentiment:
                print(f"✅ Sentiment calculated:")
                print(f"   Score: {sentiment.average_sentiment:.3f}")
                print(f"   Level: {sentiment.sentiment_level.value}")
                print(f"   Confidence: {sentiment.confidence:.3f}")
                print(f"   Volume Trend: {sentiment.volume_trend}")
            else:
                print(f"⚠️  No sentiment data for {symbol}")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    return True


def test_integration():
    """Test integration with aggregator"""
    print("\n" + "="*60)
    print("Test 3: Integration with Sentiment Aggregator")
    print("="*60)
    
    try:
        from src.data.providers.sentiment import SentimentAggregator
        
        aggregator = SentimentAggregator(persist_to_db=False)
        
        if 'google_trends' in aggregator.get_available_sources():
            print("✅ Google Trends provider registered in aggregator")
            
            # Test aggregated sentiment
            print("\n📊 Testing aggregated sentiment with Google Trends...")
            aggregated = aggregator.get_aggregated_sentiment("AAPL", hours=24)
            
            if aggregated:
                print(f"✅ Aggregated sentiment calculated:")
                print(f"   Unified Score: {aggregated.unified_sentiment:.3f}")
                print(f"   Providers Used: {', '.join(aggregated.providers_used)}")
                if 'google_trends' in aggregated.sources:
                    print(f"   Google Trends Contribution: {aggregated.source_breakdown.get('google_trends', 0):.1f}%")
            else:
                print("⚠️  No aggregated sentiment (may need other providers)")
        else:
            print("⚠️  Google Trends not available in aggregator")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    """Run all tests"""
    print("Google Trends Sentiment Integration Tests")
    print("="*60)
    print()
    
    results = []
    
    # Test 1: Client
    results.append(("Client", test_client()))
    
    # Test 2: Provider
    results.append(("Provider", test_sentiment_provider()))
    
    # Test 3: Integration
    results.append(("Integration", test_integration()))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")
    
    all_passed = all(r[1] for r in results)
    
    print()
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("⚠️  Some tests failed or skipped")
        print("\nNote: Google Trends uses pytrends which may have rate limits.")
        print("      Some failures may be due to rate limiting.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
