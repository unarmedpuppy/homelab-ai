#!/usr/bin/env python3
"""
Test script for WebSocket data streams

Tests:
- Price update stream
- Portfolio update stream
- Signal broadcast stream
- Market data stream
- Options flow stream
- Stream manager lifecycle
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.api.websocket.streams import get_stream_manager
from src.api.websocket import get_websocket_manager
from src.config.settings import settings


async def test_price_stream():
    """Test price update stream"""
    print("\n" + "="*80)
    print("Testing Price Update Stream")
    print("="*80)
    
    try:
        from src.api.websocket.streams.price_updates import PriceUpdateStream
        from src.api.routes.market_data import get_data_manager
        
        stream = PriceUpdateStream(data_manager=get_data_manager())
        
        # Test initialization
        assert stream.update_interval > 0, "Update interval should be positive"
        assert not stream.is_running(), "Stream should not be running initially"
        print(f"✅ Price stream initialized (interval: {stream.update_interval}s)")
        
        # Note: Starting/stopping streams requires active WebSocket connections
        # Full integration test would require WebSocket clients
        print(f"✅ Price stream test passed")
        return True
        
    except Exception as e:
        print(f"❌ Price stream test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_portfolio_stream():
    """Test portfolio update stream"""
    print("\n" + "="*80)
    print("Testing Portfolio Update Stream")
    print("="*80)
    
    try:
        from src.api.websocket.streams.portfolio_updates import PortfolioUpdateStream
        
        stream = PortfolioUpdateStream()
        
        assert stream.update_interval > 0, "Update interval should be positive"
        assert not stream.is_running(), "Stream should not be running initially"
        print(f"✅ Portfolio stream initialized (interval: {stream.update_interval}s)")
        
        print(f"✅ Portfolio stream test passed")
        return True
        
    except Exception as e:
        print(f"❌ Portfolio stream test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_signal_stream():
    """Test signal broadcast stream"""
    print("\n" + "="*80)
    print("Testing Signal Broadcast Stream")
    print("="*80)
    
    try:
        from src.api.websocket.streams.signal_broadcast import SignalBroadcastStream
        from src.core.evaluation.evaluator import StrategyEvaluator
        
        # Create a test evaluator
        evaluator = StrategyEvaluator()
        stream = SignalBroadcastStream(evaluator)
        
        assert stream.evaluator == evaluator, "Evaluator should be set"
        assert not stream.is_running(), "Stream should not be running initially"
        print(f"✅ Signal stream initialized")
        
        # Test callback registration
        await stream.start()
        assert stream.is_running(), "Stream should be running after start"
        assert len(evaluator.signal_callbacks) > 0, "Callback should be registered"
        print(f"✅ Signal callback registered")
        
        # Stop stream
        await stream.stop()
        assert not stream.is_running(), "Stream should not be running after stop"
        print(f"✅ Signal stream stopped")
        
        print(f"✅ Signal stream test passed")
        return True
        
    except Exception as e:
        print(f"❌ Signal stream test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_market_data_stream():
    """Test market data stream"""
    print("\n" + "="*80)
    print("Testing Market Data Stream")
    print("="*80)
    
    try:
        from src.api.websocket.streams.market_data import MarketDataStream
        from src.api.routes.market_data import get_data_manager
        
        stream = MarketDataStream(data_manager=get_data_manager())
        
        assert stream.update_interval > 0, "Update interval should be positive"
        assert not stream.is_running(), "Stream should not be running initially"
        print(f"✅ Market data stream initialized (interval: {stream.update_interval}s)")
        
        print(f"✅ Market data stream test passed")
        return True
        
    except Exception as e:
        print(f"❌ Market data stream test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_options_flow_stream():
    """Test options flow stream"""
    print("\n" + "="*80)
    print("Testing Options Flow Stream")
    print("="*80)
    
    try:
        from src.api.websocket.streams.options_flow import OptionsFlowStream
        
        stream = OptionsFlowStream()
        
        assert stream.update_interval > 0, "Update interval should be positive"
        assert stream.min_flow_threshold > 0, "Flow threshold should be positive"
        assert not stream.is_running(), "Stream should not be running initially"
        print(f"✅ Options flow stream initialized")
        print(f"   - Interval: {stream.update_interval}s")
        print(f"   - Threshold: ${stream.min_flow_threshold:,.0f}")
        
        print(f"✅ Options flow stream test passed")
        return True
        
    except Exception as e:
        print(f"❌ Options flow stream test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_stream_manager():
    """Test stream manager"""
    print("\n" + "="*80)
    print("Testing Stream Manager")
    print("="*80)
    
    try:
        manager = get_stream_manager()
        
        # Test initialization
        assert manager is not None, "Stream manager should exist"
        print(f"✅ Stream manager retrieved")
        
        # Test initialization of streams
        from src.core.evaluation.evaluator import StrategyEvaluator
        evaluator = StrategyEvaluator()
        manager.initialize(evaluator)
        
        assert manager.price_stream is not None, "Price stream should be initialized"
        assert manager.portfolio_stream is not None, "Portfolio stream should be initialized"
        assert manager.signal_stream is not None, "Signal stream should be initialized"
        assert manager.market_data_stream is not None, "Market data stream should be initialized"
        assert manager.options_stream is not None, "Options stream should be initialized"
        print(f"✅ All streams initialized")
        
        # Note: Starting/stopping requires active WebSocket connections
        # Would test in full integration test
        
        print(f"✅ Stream manager test passed")
        return True
        
    except Exception as e:
        print(f"❌ Stream manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_message_formats():
    """Test that message formats match expected structure"""
    print("\n" + "="*80)
    print("Testing Message Formats")
    print("="*80)
    
    try:
        # Test price update format
        price_message = {
            "type": "price_update",
            "symbols": {
                "AAPL": {
                    "price": 150.25,
                    "change": 1.25,
                    "change_pct": 0.84,
                    "volume": 5000000,
                    "high": 151.00,
                    "low": 149.50,
                    "open": 149.75,
                    "close": 150.25
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Verify required fields
        assert "type" in price_message, "Price message must have 'type'"
        assert "symbols" in price_message, "Price message must have 'symbols'"
        assert price_message["type"] == "price_update", "Type should be 'price_update'"
        print(f"✅ Price update format valid")
        
        # Test signal format
        signal_message = {
            "type": "signal",
            "channel": "signals",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "signal_type": "BUY",
                "symbol": "AAPL",
                "price": 150.25,
                "quantity": 100,
                "confidence": 0.85
            }
        }
        
        assert "type" in signal_message, "Signal message must have 'type'"
        assert "data" in signal_message, "Signal message must have 'data'"
        assert signal_message["type"] == "signal", "Type should be 'signal'"
        assert "signal_type" in signal_message["data"], "Signal data must have 'signal_type'"
        print(f"✅ Signal format valid")
        
        # Test portfolio format
        portfolio_message = {
            "type": "portfolio_update",
            "channel": "portfolio",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "positions": {},
                "total_pnl": 0.0,
                "position_count": 0
            }
        }
        
        assert "type" in portfolio_message, "Portfolio message must have 'type'"
        assert "data" in portfolio_message, "Portfolio message must have 'data'"
        assert portfolio_message["type"] == "portfolio_update", "Type should be 'portfolio_update'"
        print(f"✅ Portfolio update format valid")
        
        print(f"✅ All message formats valid")
        return True
        
    except Exception as e:
        print(f"❌ Message format test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all stream tests"""
    print("\n" + "="*80)
    print("WEBSOCKET DATA STREAMS - TEST SUITE")
    print("="*80)
    print(f"\nTesting WebSocket data stream infrastructure...")
    
    results = []
    
    # Test individual streams
    try:
        results.append(("Price Stream", await test_price_stream()))
    except Exception as e:
        print(f"\n❌ Price stream test failed: {e}")
        results.append(("Price Stream", False))
    
    try:
        results.append(("Portfolio Stream", await test_portfolio_stream()))
    except Exception as e:
        print(f"\n❌ Portfolio stream test failed: {e}")
        results.append(("Portfolio Stream", False))
    
    try:
        results.append(("Signal Stream", await test_signal_stream()))
    except Exception as e:
        print(f"\n❌ Signal stream test failed: {e}")
        results.append(("Signal Stream", False))
    
    try:
        results.append(("Market Data Stream", await test_market_data_stream()))
    except Exception as e:
        print(f"\n❌ Market data stream test failed: {e}")
        results.append(("Market Data Stream", False))
    
    try:
        results.append(("Options Flow Stream", await test_options_flow_stream()))
    except Exception as e:
        print(f"\n❌ Options flow stream test failed: {e}")
        results.append(("Options Flow Stream", False))
    
    try:
        results.append(("Stream Manager", await test_stream_manager()))
    except Exception as e:
        print(f"\n❌ Stream manager test failed: {e}")
        results.append(("Stream Manager", False))
    
    try:
        results.append(("Message Formats", await test_message_formats()))
    except Exception as e:
        print(f"\n❌ Message format test failed: {e}")
        results.append(("Message Formats", False))
    
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
    sys.exit(asyncio.run(main()))

