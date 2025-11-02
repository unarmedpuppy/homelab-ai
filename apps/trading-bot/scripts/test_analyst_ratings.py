#!/usr/bin/env python3
"""
Test Analyst Ratings Sentiment Integration
==========================================

Tests the Analyst Ratings sentiment provider functionality.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.providers.sentiment.analyst_ratings import (
    AnalystRatingsClient,
    AnalystRatingsSentimentProvider,
    AnalystRating
)
from src.config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_client():
    """Test Analyst Ratings client"""
    print("="*60)
    print("Test 1: Analyst Ratings Client")
    print("="*60)
    
    try:
        client = AnalystRatingsClient()
    except ImportError as e:
        print(f"⚠️  Analyst Ratings client not available: {e}")
        print("   Install yfinance: pip install yfinance")
        return False
    
    if not client.is_available():
        print("⚠️  Client not enabled in configuration")
        return False
    
    print("✅ Client initialized")
    
    # Test getting analyst rating
    test_symbols = ["AAPL", "MSFT", "TSLA"]
    
    for symbol in test_symbols:
        print(f"\n📊 Testing analyst rating for {symbol}...")
        try:
            rating = client.get_analyst_rating(symbol)
            
            if rating:
                print(f"✅ Rating retrieved:")
                print(f"   Rating: {rating.rating} ({rating.rating_numeric:.2f})")
                print(f"   Analysts: {rating.number_of_analysts}")
                print(f"   Price Target: ${rating.price_target:.2f}" if rating.price_target else "   Price Target: N/A")
                print(f"   Current Price: ${rating.current_price:.2f}" if rating.current_price else "   Current Price: N/A")
                if rating.price_target_upside is not None:
                    print(f"   Upside/Downside: {rating.price_target_upside:.2f}%")
            else:
                print(f"⚠️  No rating data for {symbol}")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    return True


def test_sentiment_provider():
    """Test sentiment provider"""
    print("\n" + "="*60)
    print("Test 2: Analyst Ratings Sentiment Provider")
    print("="*60)
    
    try:
        provider = AnalystRatingsSentimentProvider(persist_to_db=False)
    except Exception as e:
        print(f"⚠️  Provider not available: {e}")
        return False
    
    if not provider.is_available():
        print("⚠️  Provider not enabled")
        return False
    
    print("✅ Provider initialized")
    
    # Test sentiment calculation
    test_symbols = ["AAPL", "MSFT", "TSLA"]
    
    for symbol in test_symbols:
        print(f"\n📈 Testing sentiment for {symbol}...")
        try:
            sentiment = provider.get_sentiment(symbol, hours=24)
            
            if sentiment:
                print(f"✅ Sentiment calculated:")
                print(f"   Score: {sentiment.average_sentiment:.3f}")
                print(f"   Level: {sentiment.sentiment_level.value}")
                print(f"   Confidence: {sentiment.confidence:.3f}")
                print(f"   Analyst Count: {sentiment.mention_count}")
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
        
        if 'analyst_ratings' in aggregator.get_available_sources():
            print("✅ Analyst Ratings provider registered in aggregator")
            
            # Test aggregated sentiment
            print("\n📊 Testing aggregated sentiment with Analyst Ratings...")
            aggregated = aggregator.get_aggregated_sentiment("AAPL", hours=24)
            
            if aggregated:
                print(f"✅ Aggregated sentiment calculated:")
                print(f"   Unified Score: {aggregated.unified_sentiment:.3f}")
                print(f"   Providers Used: {', '.join(aggregated.providers_used)}")
                if 'analyst_ratings' in aggregated.sources:
                    print(f"   Analyst Ratings Contribution: {aggregated.source_breakdown.get('analyst_ratings', 0):.1f}%")
            else:
                print("⚠️  No aggregated sentiment (may need other providers)")
        else:
            print("⚠️  Analyst Ratings not available in aggregator")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    """Run all tests"""
    print("Analyst Ratings Sentiment Integration Tests")
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
        print("\nNote: Analyst ratings require yfinance and may depend on Yahoo Finance availability.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
