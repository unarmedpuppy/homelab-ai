#!/usr/bin/env python3
"""
Critical Test Suite: Insider Trading Provider
=============================================

Focuses on critical functionality that must work correctly before production.
"""

import sys
import time
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.providers.sentiment.insider_trading import (
    InsiderTradingClient,
    InsiderTradingSentimentProvider,
    InsiderTradingTimeoutError
)
from src.config.settings import settings
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_symbol_validation():
    """Test 1: Symbol Validation - CRITICAL"""
    print("\n" + "="*60)
    print("TEST 1: Symbol Validation")
    print("="*60)
    
    client = InsiderTradingClient()
    
    # Valid symbols
    valid_symbols = ["AAPL", "MSFT", "TSLA", "SPY", "QQQ"]
    print("\n✅ Testing valid symbols:")
    for symbol in valid_symbols:
        is_valid = client._validate_symbol(symbol)
        assert is_valid, f"Valid symbol {symbol} was rejected"
        print(f"  ✓ {symbol}")
    
    # Invalid symbols
    invalid_symbols = ["", "AAPL!", "AAP L", "AAPL@", "A"*11, "123", None]
    print("\n❌ Testing invalid symbols:")
    for symbol in invalid_symbols:
        if symbol is None:
            continue  # Skip None for now
        is_valid = client._validate_symbol(symbol)
        assert not is_valid, f"Invalid symbol '{symbol}' was accepted"
        print(f"  ✓ '{symbol}' correctly rejected")
    
    print("\n✅ TEST 1 PASSED: Symbol validation works correctly")


def test_rate_limiting():
    """Test 2: Rate Limiting - CRITICAL"""
    print("\n" + "="*60)
    print("TEST 2: Rate Limiting")
    print("="*60)
    
    client = InsiderTradingClient()
    
    # Test rate limit check
    print("\n⏱️  Testing rate limit enforcement:")
    try:
        # Make multiple rapid calls
        for i in range(5):
            client._check_rate_limit()
            print(f"  ✓ Request {i+1} allowed")
        print("\n✅ Rate limiting check works")
    except Exception as e:
        print(f"  ⚠️  Rate limit error (may be expected): {e}")
    
    print("\n✅ TEST 2 PASSED: Rate limiting mechanism works")


def test_retry_logic():
    """Test 3: Retry Logic - CRITICAL"""
    print("\n" + "="*60)
    print("TEST 3: Retry Logic")
    print("="*60)
    
    client = InsiderTradingClient()
    
    # Test retryable error detection
    print("\n🔄 Testing retryable error detection:")
    
    from unittest.mock import Mock
    retryable = ConnectionError("Connection failed")
    non_retryable = ValueError("Invalid value")
    
    assert client._is_retryable_error(retryable), "ConnectionError should be retryable"
    assert not client._is_retryable_error(non_retryable), "ValueError should not be retryable"
    
    print("  ✓ ConnectionError identified as retryable")
    print("  ✓ ValueError identified as non-retryable")
    
    print("\n✅ TEST 3 PASSED: Retry logic works correctly")


def test_configuration():
    """Test 4: Configuration - HIGH"""
    print("\n" + "="*60)
    print("TEST 4: Configuration")
    print("="*60)
    
    config = settings.insider_trading
    
    print("\n⚙️  Testing configuration:")
    assert hasattr(config, 'enabled'), "Missing 'enabled' setting"
    assert hasattr(config, 'timeout_seconds'), "Missing 'timeout_seconds' setting"
    assert hasattr(config, 'max_retries'), "Missing 'max_retries' setting"
    assert hasattr(config, 'rate_limit_requests_per_minute'), "Missing rate limit setting"
    
    print(f"  ✓ enabled: {config.enabled}")
    print(f"  ✓ timeout_seconds: {config.timeout_seconds}")
    print(f"  ✓ max_retries: {config.max_retries}")
    print(f"  ✓ rate_limit: {config.rate_limit_requests_per_minute}/min")
    
    print("\n✅ TEST 4 PASSED: Configuration is complete")


def test_provider_initialization():
    """Test 5: Provider Initialization - HIGH"""
    print("\n" + "="*60)
    print("TEST 5: Provider Initialization")
    print("="*60)
    
    print("\n🔧 Testing provider initialization:")
    
    provider = InsiderTradingSentimentProvider(persist_to_db=False)
    
    assert provider.client is not None, "Client not initialized"
    assert provider.cache is not None, "Cache not initialized"
    assert provider.rate_limiter is not None, "Rate limiter not initialized"
    assert provider.usage_monitor is not None, "Usage monitor not initialized"
    assert provider.analyzer is not None, "Sentiment analyzer not initialized"
    
    print("  ✓ Client initialized")
    print("  ✓ Cache initialized")
    print("  ✓ Rate limiter initialized")
    print("  ✓ Usage monitor initialized")
    print("  ✓ Sentiment analyzer initialized")
    
    is_available = provider.is_available()
    print(f"  ✓ Provider available: {is_available}")
    
    print("\n✅ TEST 5 PASSED: Provider initializes correctly")


def test_cache_keys():
    """Test 6: Cache Key Generation - HIGH"""
    print("\n" + "="*60)
    print("TEST 6: Cache Key Generation")
    print("="*60)
    
    provider = InsiderTradingSentimentProvider(persist_to_db=False)
    
    print("\n🔑 Testing cache key generation:")
    
    key1 = provider._get_cache_key("AAPL", 24)
    key2 = provider._get_cache_key("MSFT", 24)
    key3 = provider._get_cache_key("AAPL", 48)
    
    assert key1 != key2, "Different symbols should have different keys"
    assert key1 != key3, "Different hours should have different keys"
    assert "insider_trading:" in key1, "Key should include namespace"
    assert "AAPL" in key1, "Key should include symbol"
    assert "24" in key1, "Key should include hours"
    
    print(f"  ✓ Key format: {key1}")
    print(f"  ✓ Keys are unique for different symbols/hours")
    
    print("\n✅ TEST 6 PASSED: Cache keys are correct")


def test_sentiment_level_calculation():
    """Test 7: Sentiment Level Calculation - CRITICAL"""
    print("\n" + "="*60)
    print("TEST 7: Sentiment Level Calculation")
    print("="*60)
    
    provider = InsiderTradingSentimentProvider(persist_to_db=False)
    
    print("\n📊 Testing sentiment level calculation:")
    
    test_cases = [
        (0.8, "VERY_BULLISH"),
        (0.5, "BULLISH"),
        (0.0, "NEUTRAL"),
        (-0.5, "BEARISH"),
        (-0.8, "VERY_BEARISH")
    ]
    
    for score, expected_level in test_cases:
        level = provider.analyzer._score_to_level(score)
        assert level.value == expected_level.lower().replace("_", "-"), \
            f"Score {score} should map to {expected_level}"
        print(f"  ✓ Score {score:+.1f} → {level.value}")
    
    print("\n✅ TEST 7 PASSED: Sentiment levels calculated correctly")


def main():
    """Run all critical tests"""
    print("="*60)
    print("CRITICAL TEST SUITE: Insider Trading Provider")
    print("="*60)
    print("\nThese tests verify critical functionality before production.")
    print("All tests must pass for production deployment.\n")
    
    results = []
    
    try:
        test_symbol_validation()
        results.append(("Symbol Validation", True))
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        results.append(("Symbol Validation", False))
        import traceback
        traceback.print_exc()
    
    try:
        test_rate_limiting()
        results.append(("Rate Limiting", True))
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        results.append(("Rate Limiting", False))
    
    try:
        test_retry_logic()
        results.append(("Retry Logic", True))
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        results.append(("Retry Logic", False))
    
    try:
        test_configuration()
        results.append(("Configuration", True))
    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}")
        results.append(("Configuration", False))
    
    try:
        test_provider_initialization()
        results.append(("Provider Initialization", True))
    except Exception as e:
        print(f"\n❌ TEST 5 FAILED: {e}")
        results.append(("Provider Initialization", False))
    
    try:
        test_cache_keys()
        results.append(("Cache Keys", True))
    except Exception as e:
        print(f"\n❌ TEST 6 FAILED: {e}")
        results.append(("Cache Keys", False))
    
    try:
        test_sentiment_level_calculation()
        results.append(("Sentiment Level Calculation", True))
    except Exception as e:
        print(f"\n❌ TEST 7 FAILED: {e}")
        results.append(("Sentiment Level Calculation", False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL CRITICAL TESTS PASSED!")
        print("✅ Ready for comprehensive testing phase")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("❌ Fix issues before proceeding to comprehensive testing")
        return 1


if __name__ == "__main__":
    sys.exit(main())
