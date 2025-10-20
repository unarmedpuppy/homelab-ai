#!/usr/bin/env python3
"""
Quick Start Script
==================

Script to quickly test the trading bot setup.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.data.providers.market_data import YahooFinanceProvider, DataProviderManager, DataProviderType
from src.config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_yahoo_finance():
    """Test Yahoo Finance provider"""
    logger.info("Testing Yahoo Finance provider...")
    
    try:
        provider = YahooFinanceProvider()
        
        # Test single quote
        quote = await provider.get_quote("AAPL")
        logger.info(f"✅ AAPL Quote: ${quote.price:.2f} ({quote.change:+.2f})")
        
        # Test multiple quotes
        quotes = await provider.get_multiple_quotes(["AAPL", "MSFT", "NVDA"])
        logger.info(f"✅ Multiple quotes: {len(quotes)} symbols")
        for symbol, quote in quotes.items():
            logger.info(f"   {symbol}: ${quote.price:.2f}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Yahoo Finance test failed: {e}")
        return False

async def test_data_manager():
    """Test data provider manager"""
    logger.info("Testing Data Provider Manager...")
    
    try:
        providers = [(DataProviderType.YAHOO_FINANCE, None)]
        manager = DataProviderManager(providers)
        
        quote = await manager.get_quote("AAPL")
        logger.info(f"✅ Manager Quote: ${quote.price:.2f}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Data Manager test failed: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    logger.info("Testing configuration...")
    
    try:
        logger.info(f"✅ Database URL: {settings.database.url}")
        logger.info(f"✅ API Host: {settings.api.host}")
        logger.info(f"✅ API Port: {settings.api.port}")
        logger.info(f"✅ Environment: {settings.environment}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        return False

async def main():
    """Main test function"""
    logger.info("🚀 Starting Trading Bot Quick Test...")
    
    tests = [
        ("Configuration", test_configuration),
        ("Yahoo Finance", test_yahoo_finance),
        ("Data Manager", test_data_manager),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("QUICK TEST SUMMARY")
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
        logger.info("🎉 All tests passed! Ready to start the API server.")
        logger.info("\nNext steps:")
        logger.info("1. Run: python main.py")
        logger.info("2. Open: http://localhost:8000")
        logger.info("3. Test the market data endpoints")
        return True
    else:
        logger.error("💥 Some tests failed! Please check the errors above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
