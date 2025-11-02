#!/usr/bin/env python3
"""
Test script for Dark Pool & Institutional Flow Sentiment Provider

Tests:
- Provider initialization
- Status checks
- API endpoint structure
- Integration with aggregator

Note: This provider requires a paid API key (FlowAlgo, Cheddar Flow, etc.)
Without an API key, the provider will be unavailable but the structure is ready.
"""

import sys
import os
from datetime import datetime

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.data.providers.data.dark_pool import (
    DarkPoolClient,
    DarkPoolSentimentProvider,
    DarkPoolTrade,
    InstitutionalFlow,
    DarkPoolSnapshot,
    TradeType
)
from src.config.settings import settings


def test_client():
    """Test DarkPoolClient"""
    print("\n" + "="*80)
    print("Testing DarkPoolClient")
    print("="*80)
    
    try:
        client = DarkPoolClient()
        
        is_available = client.is_available()
        print(f"✅ Client initialized successfully")
        print(f"   - Available: {is_available}")
        
        if is_available:
            print("   - API key configured")
        else:
            print("   - API key not configured (this is expected)")
            print("   - To enable: Set DARK_POOL_API_KEY and DARK_POOL_BASE_URL")
        
        return True
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_provider():
    """Test DarkPoolSentimentProvider"""
    print("\n" + "="*80)
    print("Testing DarkPoolSentimentProvider")
    print("="*80)
    
    try:
        provider = DarkPoolSentimentProvider(persist_to_db=False)
        
        is_available = provider.is_available()
        print(f"✅ Provider initialized successfully")
        print(f"   - Available: {is_available}")
        print(f"   - Cache TTL: {provider.cache_ttl}s")
        
        if is_available:
            print("   - Ready to fetch dark pool data")
            
            # Test with a symbol (will return None without API key)
            print(f"\n   Testing sentiment fetch for AAPL...")
            sentiment = provider.get_sentiment("AAPL", hours=24)
            
            if sentiment:
                print(f"   ✅ Sentiment calculated:")
                print(f"      - Symbol: {sentiment.symbol}")
                print(f"      - Sentiment: {sentiment.average_sentiment:.4f}")
                print(f"      - Level: {sentiment.sentiment_level.value}")
                print(f"      - Confidence: {sentiment.confidence:.4f}")
            else:
                print(f"   ⚠️  No data returned (API not implemented or no API key)")
        else:
            print("   - Provider structure ready, awaiting API key configuration")
            print("   - Configure DARK_POOL_API_KEY and DARK_POOL_BASE_URL to enable")
        
        return True
    except Exception as e:
        print(f"❌ Provider initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_models():
    """Test data models"""
    print("\n" + "="*80)
    print("Testing Data Models")
    print("="*80)
    
    try:
        # Test DarkPoolTrade
        trade = DarkPoolTrade(
            symbol="AAPL",
            timestamp=datetime.now(),
            volume=10000,
            price=150.0,
            trade_type=TradeType.BUY,
            dark_pool_name="ATS-1",
            block_size=True
        )
        print(f"✅ DarkPoolTrade model created:")
        print(f"   - Symbol: {trade.symbol}")
        print(f"   - Volume: {trade.volume:,}")
        print(f"   - Type: {trade.trade_type.value}")
        print(f"   - Block trade: {trade.block_size}")
        
        # Test InstitutionalFlow
        flow = InstitutionalFlow(
            symbol="AAPL",
            timestamp=datetime.now(),
            net_flow=500000.0,
            buy_volume=1000000,
            sell_volume=500000,
            dark_pool_volume=200000,
            block_trades=5,
            institutional_percentage=65.0
        )
        print(f"\n✅ InstitutionalFlow model created:")
        print(f"   - Net flow: ${flow.net_flow:,.0f}")
        print(f"   - Buy volume: {flow.buy_volume:,}")
        print(f"   - Sell volume: {flow.sell_volume:,}")
        print(f"   - Institutional %: {flow.institutional_percentage:.1f}%")
        
        # Test DarkPoolSnapshot
        snapshot = DarkPoolSnapshot(
            symbol="AAPL",
            timestamp=datetime.now(),
            total_dark_pool_volume=1000000,
            dark_pool_percentage=15.5,
            net_dark_pool_flow=250000.0,
            block_trades=[trade]
        )
        print(f"\n✅ DarkPoolSnapshot model created:")
        print(f"   - Total volume: {snapshot.total_dark_pool_volume:,}")
        print(f"   - Dark pool %: {snapshot.dark_pool_percentage:.1f}%")
        print(f"   - Net flow: ${snapshot.net_dark_pool_flow:,.0f}")
        print(f"   - Block trades: {len(snapshot.block_trades)}")
        
        return True
    except Exception as e:
        print(f"❌ Model creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration():
    """Test configuration"""
    print("\n" + "="*80)
    print("Testing Configuration")
    print("="*80)
    
    try:
        print(f"✅ Dark Pool Settings:")
        print(f"   - Enabled: {settings.dark_pool.enabled}")
        print(f"   - API Key configured: {settings.dark_pool.api_key is not None}")
        print(f"   - Base URL: {settings.dark_pool.base_url or 'Not set'}")
        print(f"   - Cache TTL: {settings.dark_pool.cache_ttl}s")
        
        return True
    except Exception as e:
        print(f"❌ Configuration check failed: {e}")
        return False


def test_api_endpoints():
    """Test that API endpoints are accessible"""
    print("\n" + "="*80)
    print("Testing API Endpoints (Manual Check)")
    print("="*80)
    print("\nTo test API endpoints, start the server and check:")
    print("  - GET /api/sentiment/dark-pool/status")
    print("  - GET /api/sentiment/dark-pool/{symbol}")
    print("\nOr use the FastAPI docs at: http://localhost:8000/docs")
    print("\nNote: Endpoints will return 503 (Service Unavailable) without API key.")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("DARK POOL & INSTITUTIONAL FLOW SENTIMENT PROVIDER - TEST SUITE")
    print("="*80)
    print(f"\nTesting with configuration:")
    print(f"  - Enabled: {settings.dark_pool.enabled}")
    print(f"  - Cache TTL: {settings.dark_pool.cache_ttl}s")
    print(f"\nNote: This provider requires a paid API subscription.")
    print(f"      Without an API key, the structure is ready but unavailable.")
    
    results = []
    
    # Test configuration
    try:
        results.append(("Configuration Tests", test_configuration()))
    except Exception as e:
        print(f"\n❌ Configuration test failed: {e}")
        results.append(("Configuration Tests", False))
    
    # Test models
    try:
        results.append(("Model Tests", test_models()))
    except Exception as e:
        print(f"\n❌ Model test failed: {e}")
        results.append(("Model Tests", False))
    
    # Test client
    try:
        results.append(("Client Tests", test_client()))
    except Exception as e:
        print(f"\n❌ Client test failed: {e}")
        results.append(("Client Tests", False))
    
    # Test provider
    try:
        results.append(("Provider Tests", test_provider()))
    except Exception as e:
        print(f"\n❌ Provider test failed: {e}")
        results.append(("Provider Tests", False))
    
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
        print("\n✅ All structural tests passed!")
        print("⚠️  Note: Provider requires API key to fetch actual data.")
    else:
        print("\n⚠️  Some tests failed")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

