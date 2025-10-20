#!/usr/bin/env python3
"""
Yahoo Finance Data Provider Test
================================

Test script for Yahoo Finance data provider.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.data.providers.market_data import (
    DataProviderManager, 
    DataProviderType,
    YahooFinanceProvider
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_yahoo_finance_provider():
    """Test Yahoo Finance provider"""
    logger.info("Testing Yahoo Finance Provider...")
    
    # Create provider
    provider = YahooFinanceProvider()
    
    # Test symbols
    test_symbols = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"]
    
    try:
        # Test single quote
        logger.info("Testing single quote...")
        quote = await provider.get_quote("AAPL")
        logger.info(f"AAPL Quote: ${quote.price:.2f} ({quote.change:+.2f}, {quote.change_pct:+.2%})")
        
        # Test multiple quotes
        logger.info("Testing multiple quotes...")
        quotes = await provider.get_multiple_quotes(test_symbols)
        for symbol, quote in quotes.items():
            logger.info(f"{symbol}: ${quote.price:.2f} ({quote.change:+.2f})")
        
        # Test historical data
        logger.info("Testing historical data...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        historical_data = await provider.get_historical_data(
            "AAPL", start_date, end_date, "1d"
        )
        
        logger.info(f"Got {len(historical_data)} days of historical data")
        if historical_data:
            latest = historical_data[-1]
            logger.info(f"Latest AAPL data: ${latest.close:.2f} (Volume: {latest.volume:,})")
        
        logger.info("✅ Yahoo Finance provider test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Yahoo Finance provider test failed: {e}")
        return False

async def test_data_provider_manager():
    """Test data provider manager with fallback"""
    logger.info("Testing Data Provider Manager...")
    
    # Create manager with multiple providers
    providers = [
        (DataProviderType.YAHOO_FINANCE, None),
        # Add more providers here when you have API keys
        # (DataProviderType.ALPHA_VANTAGE, "your_api_key"),
        # (DataProviderType.POLYGON, "your_api_key"),
    ]
    
    manager = DataProviderManager(providers)
    
    try:
        # Test quote with fallback
        logger.info("Testing quote with fallback...")
        quote = await manager.get_quote("AAPL")
        logger.info(f"AAPL Quote: ${quote.price:.2f} ({quote.change:+.2f})")
        
        # Test historical data with fallback
        logger.info("Testing historical data with fallback...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        historical_data = await manager.get_historical_data(
            "AAPL", start_date, end_date, "1d"
        )
        
        logger.info(f"Got {len(historical_data)} days of historical data")
        
        # Test multiple quotes
        logger.info("Testing multiple quotes...")
        quotes = await manager.get_multiple_quotes(["AAPL", "MSFT", "NVDA"])
        for symbol, quote in quotes.items():
            logger.info(f"{symbol}: ${quote.price:.2f}")
        
        logger.info("✅ Data Provider Manager test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Data Provider Manager test failed: {e}")
        return False

async def test_error_handling():
    """Test error handling"""
    logger.info("Testing error handling...")
    
    provider = YahooFinanceProvider()
    
    try:
        # Test invalid symbol
        logger.info("Testing invalid symbol...")
        try:
            quote = await provider.get_quote("INVALID_SYMBOL_XYZ")
            logger.warning(f"Unexpected success for invalid symbol: {quote}")
        except Exception as e:
            logger.info(f"✅ Correctly handled invalid symbol: {e}")
        
        # Test empty symbol list
        logger.info("Testing empty symbol list...")
        quotes = await provider.get_multiple_quotes([])
        logger.info(f"✅ Empty symbol list handled: {len(quotes)} quotes")
        
        logger.info("✅ Error handling test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error handling test failed: {e}")
        return False

async def main():
    """Main test function"""
    logger.info("Starting Yahoo Finance Data Provider Tests...")
    
    tests = [
        ("Yahoo Finance Provider", test_yahoo_finance_provider),
        ("Data Provider Manager", test_data_provider_manager),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed!")
        return True
    else:
        logger.error("💥 Some tests failed!")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
