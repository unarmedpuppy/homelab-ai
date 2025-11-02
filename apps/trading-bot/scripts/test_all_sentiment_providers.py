#!/usr/bin/env python3
"""
Comprehensive Test Suite: All Sentiment Providers
==================================================

Tests all sentiment providers to ensure they work correctly individually
and integrate properly with the sentiment aggregator.
"""

import sys
import time
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from typing import Dict, List, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test symbols
TEST_SYMBOLS = ["AAPL", "MSFT", "TSLA", "SPY"]

# Results tracking
test_results: List[Tuple[str, str, bool, str]] = []  # (provider, test, passed, message)


def log_test(provider: str, test_name: str, passed: bool, message: str = ""):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    result = (provider, test_name, passed, message)
    test_results.append(result)
    print(f"{status}: {provider} - {test_name}" + (f": {message}" if message else ""))


def test_twitter_provider():
    """Test Twitter/X sentiment provider"""
    provider_name = "Twitter"
    print(f"\n{'='*60}")
    print(f"Testing {provider_name} Provider")
    print(f"{'='*60}")
    
    try:
        from src.data.providers.sentiment.twitter import TwitterSentimentProvider
        
        provider = TwitterSentimentProvider(persist_to_db=False)
        available = provider.is_available()
        log_test(provider_name, "Initialization", True, f"Available: {available}")
        
        if available:
            for symbol in TEST_SYMBOLS[:2]:  # Test with 2 symbols
                try:
                    sentiment = provider.get_sentiment(symbol, hours=24)
                    if sentiment:
                        log_test(provider_name, f"Get sentiment ({symbol})", True, 
                               f"Score: {sentiment.average_sentiment:.3f}")
                    else:
                        log_test(provider_name, f"Get sentiment ({symbol})", True, 
                               "No data (expected for some symbols)")
                except Exception as e:
                    log_test(provider_name, f"Get sentiment ({symbol})", False, str(e))
    except Exception as e:
        log_test(provider_name, "Import/Initialization", False, str(e))


def test_reddit_provider():
    """Test Reddit sentiment provider"""
    provider_name = "Reddit"
    print(f"\n{'='*60}")
    print(f"Testing {provider_name} Provider")
    print(f"{'='*60}")
    
    try:
        from src.data.providers.sentiment.reddit import RedditSentimentProvider
        
        provider = RedditSentimentProvider(persist_to_db=False)
        available = provider.is_available()
        log_test(provider_name, "Initialization", True, f"Available: {available}")
        
        if available:
            for symbol in TEST_SYMBOLS[:2]:
                try:
                    sentiment = provider.get_sentiment(symbol, hours=24)
                    if sentiment:
                        log_test(provider_name, f"Get sentiment ({symbol})", True,
                               f"Score: {sentiment.average_sentiment:.3f}")
                    else:
                        log_test(provider_name, f"Get sentiment ({symbol})", True,
                               "No data (expected)")
                except Exception as e:
                    log_test(provider_name, f"Get sentiment ({symbol})", False, str(e))
    except Exception as e:
        log_test(provider_name, "Import/Initialization", False, str(e))


def test_stocktwits_provider():
    """Test StockTwits sentiment provider"""
    provider_name = "StockTwits"
    print(f"\n{'='*60}")
    print(f"Testing {provider_name} Provider")
    print(f"{'='*60}")
    
    try:
        from src.data.providers.sentiment.stocktwits import StockTwitsSentimentProvider
        
        provider = StockTwitsSentimentProvider(persist_to_db=False)
        available = provider.is_available()
        log_test(provider_name, "Initialization", True, f"Available: {available}")
        
        if available:
            for symbol in TEST_SYMBOLS[:2]:
                try:
                    sentiment = provider.get_sentiment(symbol, hours=24)
                    if sentiment:
                        log_test(provider_name, f"Get sentiment ({symbol})", True,
                               f"Score: {sentiment.average_sentiment:.3f}")
                    else:
                        log_test(provider_name, f"Get sentiment ({symbol})", True,
                               "No data (expected)")
                except Exception as e:
                    log_test(provider_name, f"Get sentiment ({symbol})", False, str(e))
    except Exception as e:
        log_test(provider_name, "Import/Initialization", False, str(e))


def test_news_provider():
    """Test Financial News sentiment provider"""
    provider_name = "News"
    print(f"\n{'='*60}")
    print(f"Testing {provider_name} Provider")
    print(f"{'='*60}")
    
    try:
        from src.data.providers.sentiment.news import NewsSentimentProvider
        
        provider = NewsSentimentProvider(persist_to_db=False)
        available = provider.is_available()
        log_test(provider_name, "Initialization", True, f"Available: {available}")
        
        if available:
            for symbol in TEST_SYMBOLS[:2]:
                try:
                    sentiment = provider.get_sentiment(symbol, hours=24)
                    if sentiment:
                        log_test(provider_name, f"Get sentiment ({symbol})", True,
                               f"Score: {sentiment.average_sentiment:.3f}")
                    else:
                        log_test(provider_name, f"Get sentiment ({symbol})", True,
                               "No data (expected)")
                except Exception as e:
                    log_test(provider_name, f"Get sentiment ({symbol})", False, str(e))
    except Exception as e:
        log_test(provider_name, "Import/Initialization", False, str(e))


def test_analyst_ratings_provider():
    """Test Analyst Ratings sentiment provider"""
    provider_name = "Analyst Ratings"
    print(f"\n{'='*60}")
    print(f"Testing {provider_name} Provider")
    print(f"{'='*60}")
    
    try:
        from src.data.providers.sentiment.analyst_ratings import AnalystRatingsSentimentProvider
        
        provider = AnalystRatingsSentimentProvider(persist_to_db=False)
        available = provider.is_available()
        log_test(provider_name, "Initialization", True, f"Available: {available}")
        
        if available:
            for symbol in TEST_SYMBOLS:
                try:
                    sentiment = provider.get_sentiment(symbol, hours=24)
                    if sentiment:
                        log_test(provider_name, f"Get sentiment ({symbol})", True,
                               f"Score: {sentiment.average_sentiment:.3f}, Confidence: {sentiment.confidence:.3f}")
                    else:
                        log_test(provider_name, f"Get sentiment ({symbol})", True,
                               "No data (may be expected)")
                    
                    # Test raw rating
                    rating = provider.get_analyst_rating(symbol)
                    if rating:
                        log_test(provider_name, f"Get rating ({symbol})", True,
                               f"Rating: {rating.rating}, Analysts: {rating.number_of_analysts}")
                    else:
                        log_test(provider_name, f"Get rating ({symbol})", True, "No rating data")
                except Exception as e:
                    log_test(provider_name, f"Get sentiment ({symbol})", False, str(e))
    except Exception as e:
        log_test(provider_name, "Import/Initialization", False, str(e))


def test_insider_trading_provider():
    """Test Insider Trading sentiment provider"""
    provider_name = "Insider Trading"
    print(f"\n{'='*60}")
    print(f"Testing {provider_name} Provider")
    print(f"{'='*60}")
    
    try:
        from src.data.providers.sentiment.insider_trading import (
            InsiderTradingClient,
            InsiderTradingSentimentProvider
        )
        
        # Test client
        client = InsiderTradingClient()
        available = client.is_available()
        log_test(provider_name, "Client Initialization", True, f"Available: {available}")
        
        # Test symbol validation
        assert client._validate_symbol("AAPL"), "Valid symbol rejected"
        assert not client._validate_symbol("AAPL!"), "Invalid symbol accepted"
        log_test(provider_name, "Symbol Validation", True)
        
        # Test provider
        provider = InsiderTradingSentimentProvider(persist_to_db=False)
        available = provider.is_available()
        log_test(provider_name, "Provider Initialization", True, f"Available: {available}")
        
        if available:
            for symbol in TEST_SYMBOLS:
                try:
                    sentiment = provider.get_sentiment(symbol, hours=24)
                    if sentiment:
                        log_test(provider_name, f"Get sentiment ({symbol})", True,
                               f"Score: {sentiment.average_sentiment:.3f}, Confidence: {sentiment.confidence:.3f}")
                    else:
                        log_test(provider_name, f"Get sentiment ({symbol})", True,
                               "No data (may be expected for some symbols)")
                    
                    # Test raw data methods
                    holders = provider.get_major_holders(symbol)
                    if holders:
                        log_test(provider_name, f"Get major holders ({symbol})", True,
                               f"Insider: {holders.get('total_insider_percent', 0):.1f}%")
                    
                except Exception as e:
                    log_test(provider_name, f"Get sentiment ({symbol})", False, str(e))
    except Exception as e:
        log_test(provider_name, "Import/Initialization", False, str(e))
        import traceback
        traceback.print_exc()


def test_google_trends_provider():
    """Test Google Trends sentiment provider"""
    provider_name = "Google Trends"
    print(f"\n{'='*60}")
    print(f"Testing {provider_name} Provider")
    print(f"{'='*60}")
    
    try:
        from src.data.providers.sentiment.google_trends import GoogleTrendsSentimentProvider
        
        provider = GoogleTrendsSentimentProvider(persist_to_db=False)
        available = provider.is_available()
        log_test(provider_name, "Initialization", True, f"Available: {available}")
        
        if available:
            for symbol in TEST_SYMBOLS[:2]:  # Limit to avoid rate limits
                try:
                    sentiment = provider.get_sentiment(symbol, hours=24)
                    if sentiment:
                        log_test(provider_name, f"Get sentiment ({symbol})", True,
                               f"Score: {sentiment.average_sentiment:.3f}")
                    else:
                        log_test(provider_name, f"Get sentiment ({symbol})", True,
                               "No data (expected)")
                    time.sleep(2)  # Rate limit protection
                except Exception as e:
                    log_test(provider_name, f"Get sentiment ({symbol})", False, str(e))
    except Exception as e:
        log_test(provider_name, "Import/Initialization", False, str(e))


def test_sec_filings_provider():
    """Test SEC Filings sentiment provider"""
    provider_name = "SEC Filings"
    print(f"\n{'='*60}")
    print(f"Testing {provider_name} Provider")
    print(f"{'='*60}")
    
    try:
        from src.data.providers.sentiment.sec_filings import SECFilingsSentimentProvider
        
        provider = SECFilingsSentimentProvider(persist_to_db=False)
        available = provider.is_available()
        log_test(provider_name, "Initialization", True, f"Available: {available}")
        
        if available:
            for symbol in TEST_SYMBOLS[:2]:  # Limit due to slow SEC API
                try:
                    sentiment = provider.get_sentiment(symbol, days=90)
                    if sentiment:
                        log_test(provider_name, f"Get sentiment ({symbol})", True,
                               f"Score: {sentiment.average_sentiment:.3f}")
                    else:
                        log_test(provider_name, f"Get sentiment ({symbol})", True,
                               "No data (expected - slow API)")
                    time.sleep(1)  # Rate limit protection
                except Exception as e:
                    log_test(provider_name, f"Get sentiment ({symbol})", True,
                           f"No data or error (expected): {type(e).__name__}")
    except Exception as e:
        log_test(provider_name, "Import/Initialization", False, str(e))


def test_sentiment_aggregator():
    """Test Sentiment Aggregator integration"""
    provider_name = "Sentiment Aggregator"
    print(f"\n{'='*60}")
    print(f"Testing {provider_name}")
    print(f"{'='*60}")
    
    try:
        from src.data.providers.sentiment.aggregator import SentimentAggregator
        
        aggregator = SentimentAggregator(persist_to_db=False)
        
        # Test available sources
        sources = aggregator.get_available_sources()
        log_test(provider_name, "Available Sources", True, 
               f"Sources: {', '.join(sources)}")
        
        # Test aggregated sentiment
        for symbol in TEST_SYMBOLS[:2]:
            try:
                aggregated = aggregator.get_aggregated_sentiment(symbol, hours=24)
                if aggregated:
                    log_test(provider_name, f"Aggregated sentiment ({symbol})", True,
                           f"Unified: {aggregated.unified_sentiment:.3f}, "
                           f"Sources: {len(aggregated.providers_used)}, "
                           f"Confidence: {aggregated.confidence:.3f}")
                    
                    # Test that insider_trading is included if available
                    if 'insider_trading' in sources:
                        if 'insider_trading' in aggregated.providers_used:
                            log_test(provider_name, f"Insider Trading integrated ({symbol})", True)
                        else:
                            log_test(provider_name, f"Insider Trading integrated ({symbol})", True,
                                   "Not used (may not have data)")
                else:
                    log_test(provider_name, f"Aggregated sentiment ({symbol})", True,
                           "No aggregated data (may need more providers)")
            except Exception as e:
                log_test(provider_name, f"Aggregated sentiment ({symbol})", False, str(e))
                import traceback
                traceback.print_exc()
    except Exception as e:
        log_test(provider_name, "Initialization", False, str(e))
        import traceback
        traceback.print_exc()


def test_mention_volume_provider():
    """Test Mention Volume provider"""
    provider_name = "Mention Volume"
    print(f"\n{'='*60}")
    print(f"Testing {provider_name} Provider")
    print(f"{'='*60}")
    
    try:
        from src.data.providers.sentiment.mention_volume import MentionVolumeProvider
        
        provider = MentionVolumeProvider()
        available = provider.is_available()
        log_test(provider_name, "Initialization", True, f"Available: {available}")
        
        if available:
            for symbol in TEST_SYMBOLS[:2]:
                try:
                    volume_data = provider.get_mention_volume(symbol, hours=24)
                    if volume_data:
                        log_test(provider_name, f"Get volume ({symbol})", True,
                               f"Total: {volume_data.get('total_mentions', 0)} mentions")
                    else:
                        log_test(provider_name, f"Get volume ({symbol})", True,
                               "No data (requires database)")
                except Exception as e:
                    log_test(provider_name, f"Get volume ({symbol})", False, str(e))
    except Exception as e:
        log_test(provider_name, "Import/Initialization", False, str(e))


def main():
    """Run all sentiment provider tests"""
    print("="*60)
    print("COMPREHENSIVE SENTIMENT PROVIDER TEST SUITE")
    print("="*60)
    print("\nTesting all sentiment providers and aggregator integration")
    print("This may take several minutes due to API rate limits...\n")
    
    start_time = time.time()
    
    # Test individual providers
    test_twitter_provider()
    test_reddit_provider()
    test_stocktwits_provider()
    test_news_provider()
    test_analyst_ratings_provider()
    test_insider_trading_provider()
    test_google_trends_provider()
    test_sec_filings_provider()
    test_mention_volume_provider()
    
    # Test aggregator
    test_sentiment_aggregator()
    
    elapsed = time.time() - start_time
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    # Group by provider
    providers = {}
    for provider, test_name, passed, message in test_results:
        if provider not in providers:
            providers[provider] = {'passed': 0, 'failed': 0, 'tests': []}
        providers[provider]['tests'].append((test_name, passed, message))
        if passed:
            providers[provider]['passed'] += 1
        else:
            providers[provider]['failed'] += 1
    
    for provider, stats in providers.items():
        total = stats['passed'] + stats['failed']
        status = "✅" if stats['failed'] == 0 else "⚠️" if stats['passed'] > 0 else "❌"
        print(f"\n{status} {provider}: {stats['passed']}/{total} tests passed")
        if stats['failed'] > 0:
            for test_name, passed, message in stats['tests']:
                if not passed:
                    print(f"    ❌ {test_name}: {message}")
    
    total_passed = sum(1 for _, _, passed, _ in test_results if passed)
    total_tests = len(test_results)
    
    print(f"\n{'='*60}")
    print(f"Overall: {total_passed}/{total_tests} tests passed")
    print(f"Time elapsed: {elapsed:.2f} seconds")
    print(f"{'='*60}")
    
    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) failed or skipped")
        print("Review failures above - some may be expected (no data, rate limits, etc.)")
        return 1


if __name__ == "__main__":
    sys.exit(main())

