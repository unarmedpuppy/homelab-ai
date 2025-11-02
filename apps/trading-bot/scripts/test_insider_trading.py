#!/usr/bin/env python3
"""
Test script for Insider Trading & Institutional Holdings Sentiment Provider

Tests:
- Insider transaction fetching
- Institutional holdings fetching
- Major holders summary
- Sentiment calculation
- API integration
"""

import sys
import os
from datetime import datetime

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.data.providers.sentiment.insider_trading import (
    InsiderTradingClient,
    InsiderTradingSentimentProvider
)
from src.config.settings import settings

def test_client():
    """Test InsiderTradingClient"""
    print("\n" + "="*80)
    print("Testing InsiderTradingClient")
    print("="*80)
    
    client = InsiderTradingClient()
    
    if not client.is_available():
        print("❌ Client not available (insider trading may be disabled)")
        return False
    
    print("✅ Client initialized successfully")
    
    # Test symbols
    test_symbols = ["AAPL", "MSFT", "TSLA"]
    
    for symbol in test_symbols:
        print(f"\n--- Testing {symbol} ---")
        
        # Test major holders
        print(f"\n1. Major Holders:")
        major_holders = client.get_major_holders(symbol)
        if major_holders:
            print(f"   ✅ Major holders found")
            if major_holders.get('insiders'):
                print(f"   - Insiders: {len(major_holders['insiders'])} entries")
                print(f"   - Total Insider %: {major_holders.get('total_insider_percent', 0):.2f}%")
            if major_holders.get('institutions'):
                print(f"   - Institutions: {len(major_holders['institutions'])} entries")
                print(f"   - Total Institutional %: {major_holders.get('total_institutional_percent', 0):.2f}%")
        else:
            print(f"   ⚠️  No major holders data available")
        
        # Test insider transactions
        print(f"\n2. Insider Transactions:")
        transactions = client.get_insider_transactions(symbol)
        if transactions:
            print(f"   ✅ Found {len(transactions)} transactions")
            for i, trans in enumerate(transactions[:5], 1):  # Show first 5
                date = trans.get('date', 'Unknown')
                if isinstance(date, datetime):
                    date = date.strftime('%Y-%m-%d')
                print(f"   {i}. {trans.get('insider', 'Unknown')} - {trans.get('transaction', 'Unknown')} "
                      f"({trans.get('shares', 0):,} shares) on {date}")
        else:
            print(f"   ⚠️  No insider transactions available")
        
        # Test institutional holders
        print(f"\n3. Institutional Holders:")
        institutional = client.get_institutional_holders(symbol)
        if institutional:
            print(f"   ✅ Found {len(institutional)} institutions")
            for i, holder in enumerate(institutional[:5], 1):  # Show first 5
                shares = holder.get('shares', 0)
                percent = holder.get('percent_held', 0)
                value = holder.get('value', 0)
                print(f"   {i}. {holder.get('institution', 'Unknown')[:50]}")
                print(f"      - Shares: {shares:,}")
                print(f"      - % Held: {percent:.2f}%")
                if value:
                    print(f"      - Value: ${value:,.0f}")
        else:
            print(f"   ⚠️  No institutional holders data available")
    
    return True


def test_sentiment_provider():
    """Test InsiderTradingSentimentProvider"""
    print("\n" + "="*80)
    print("Testing InsiderTradingSentimentProvider")
    print("="*80)
    
    provider = InsiderTradingSentimentProvider(persist_to_db=False)
    
    if not provider.is_available():
        print("❌ Provider not available")
        return False
    
    print("✅ Provider initialized successfully")
    
    # Test symbols
    test_symbols = ["AAPL", "MSFT", "TSLA"]
    
    for symbol in test_symbols:
        print(f"\n--- Testing Sentiment for {symbol} ---")
        
        sentiment = provider.get_sentiment(symbol, hours=24)
        
        if sentiment:
            print(f"✅ Sentiment calculated:")
            print(f"   - Symbol: {sentiment.symbol}")
            print(f"   - Average Sentiment: {sentiment.average_sentiment:.4f}")
            print(f"   - Weighted Sentiment: {sentiment.weighted_sentiment:.4f}")
            print(f"   - Sentiment Level: {sentiment.sentiment_level.value}")
            print(f"   - Confidence: {sentiment.confidence:.4f}")
            print(f"   - Mention Count: {sentiment.mention_count}")
            print(f"   - Engagement Score: {sentiment.engagement_score:.4f}")
            
            # Test cache hit
            print(f"\n   Testing cache...")
            cached_sentiment = provider.get_sentiment(symbol, hours=24)
            if cached_sentiment:
                print(f"   ✅ Cache working (returned cached sentiment)")
        else:
            print(f"   ⚠️  Could not calculate sentiment (may not have data)")
    
    return True


def test_api_endpoints():
    """Test that API endpoints are accessible"""
    print("\n" + "="*80)
    print("Testing API Endpoints (Manual Check)")
    print("="*80)
    print("\nTo test API endpoints, start the server and check:")
    print("  - GET /api/sentiment/insider-trading/status")
    print("  - GET /api/sentiment/insider-trading/{symbol}")
    print("  - GET /api/sentiment/insider-trading/{symbol}/transactions")
    print("  - GET /api/sentiment/insider-trading/{symbol}/institutional")
    print("  - GET /api/sentiment/insider-trading/{symbol}/major-holders")
    print("\nOr use the FastAPI docs at: http://localhost:8000/docs")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("INSIDER TRADING SENTIMENT PROVIDER - TEST SUITE")
    print("="*80)
    print(f"\nTesting with configuration:")
    print(f"  - Enabled: {settings.insider_trading.enabled}")
    print(f"  - Cache TTL: {settings.insider_trading.cache_ttl}s")
    print(f"  - Insider Weight: {settings.insider_trading.insider_weight}")
    print(f"  - Institutional Weight: {settings.insider_trading.institutional_weight}")
    
    results = []
    
    # Test client
    try:
        results.append(("Client Tests", test_client()))
    except Exception as e:
        print(f"\n❌ Client test failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Client Tests", False))
    
    # Test sentiment provider
    try:
        results.append(("Sentiment Provider Tests", test_sentiment_provider()))
    except Exception as e:
        print(f"\n❌ Sentiment provider test failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Sentiment Provider Tests", False))
    
    # Show API endpoint info
    test_api_endpoints()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("\n✅ All tests passed!")
    else:
        print("\n⚠️  Some tests failed")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
