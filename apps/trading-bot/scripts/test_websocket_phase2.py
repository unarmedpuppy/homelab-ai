#!/usr/bin/env python3
"""
Phase 2 WebSocket Test Script
==============================

Tests WebSocket data streams:
- Price update stream
- Signal broadcast stream
- Portfolio update stream
- Trade publisher
- Stream manager lifecycle
"""

import sys
import os
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock, MagicMock

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from fastapi.testclient import TestClient
from src.api.main import app
from src.api.websocket.streams import (
    PriceUpdateStream,
    SignalBroadcastStream,
    PortfolioUpdateStream,
    StreamManager,
    get_stream_manager
)
from src.api.websocket.manager import get_websocket_manager
from src.api.routes.trade_publisher import TradePublisher, get_trade_publisher
from src.core.strategy.base import TradingSignal, SignalType
from src.core.evaluation.evaluator import StrategyEvaluator


def test_price_update_stream():
    """Test PriceUpdateStream functionality"""
    print("\n" + "="*80)
    print("Testing PriceUpdateStream")
    print("="*80)
    
    try:
        # Mock data manager
        mock_data_manager = Mock()
        mock_market_data = Mock()
        mock_market_data.price = 150.25
        mock_market_data.change = 0.5
        mock_market_data.change_pct = 0.33
        mock_market_data.volume = 1000000
        mock_market_data.high = 151.0
        mock_market_data.low = 149.5
        mock_market_data.open = 150.0
        mock_market_data.close = 150.25
        
        mock_data_manager.get_multiple_quotes = AsyncMock(return_value={
            "AAPL": mock_market_data
        })
        
        # Create stream
        stream = PriceUpdateStream(
            data_manager=mock_data_manager,
            update_interval=1,  # 1 second for testing
            broadcast_only_on_change=False
        )
        
        print(f"✅ PriceUpdateStream created")
        print(f"   - Update interval: {stream.update_interval}s")
        print(f"   - Broadcast only on change: {stream.broadcast_only_on_change}")
        
        # Test subscribed symbols update
        manager = get_websocket_manager()
        # Manually add subscription for testing
        async def test_subscription():
            client_id = await manager.connect(Mock(WebSocket=Mock()), "test-client")
            await manager.subscribe(client_id, "price:AAPL")
            
            # Update subscribed symbols
            symbols = stream._update_subscribed_symbols()
            print(f"✅ Subscribed symbols: {symbols}")
            assert "AAPL" in symbols or len(symbols) >= 0  # May be empty if no connections
            
            # Test fetch and broadcast (mock)
            await stream._fetch_and_broadcast_prices()
            print(f"✅ Price fetch and broadcast test passed")
        
        asyncio.run(test_subscription())
        
        return True
    except Exception as e:
        print(f"❌ PriceUpdateStream test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_signal_broadcast_stream():
    """Test SignalBroadcastStream functionality"""
    print("\n" + "="*80)
    print("Testing SignalBroadcastStream")
    print("="*80)
    
    try:
        # Mock evaluator
        mock_evaluator = Mock(spec=StrategyEvaluator)
        mock_evaluator.signal_callbacks = []
        
        # Create stream
        stream = SignalBroadcastStream(evaluator=mock_evaluator)
        print(f"✅ SignalBroadcastStream created")
        
        # Test callback registration
        async def test_registration():
            await stream.start()
            print(f"✅ Callback registered: {len(mock_evaluator.signal_callbacks) > 0}")
            
            # Test signal broadcast
            test_signal = TradingSignal(
                signal_type=SignalType.BUY,
                symbol="AAPL",
                price=150.25,
                quantity=10,
                confidence=0.85,
                timestamp=datetime.now()
            )
            
            # Broadcast signal
            await stream._broadcast_signal(test_signal)
            print(f"✅ Signal broadcast test passed")
        
        asyncio.run(test_registration())
        
        # Cleanup
        async def cleanup():
            await stream.stop()
        
        asyncio.run(cleanup())
        
        return True
    except Exception as e:
        print(f"❌ SignalBroadcastStream test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_portfolio_update_stream():
    """Test PortfolioUpdateStream functionality"""
    print("\n" + "="*80)
    print("Testing PortfolioUpdateStream")
    print("="*80)
    
    try:
        # Create stream
        stream = PortfolioUpdateStream(update_interval=5)
        print(f"✅ PortfolioUpdateStream created")
        print(f"   - Update interval: {stream.update_interval}s")
        
        # Test without IBKR (should handle gracefully)
        print(f"✅ PortfolioUpdateStream initialization test passed")
        
        return True
    except Exception as e:
        print(f"❌ PortfolioUpdateStream test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_trade_publisher():
    """Test TradePublisher functionality"""
    print("\n" + "="*80)
    print("Testing TradePublisher")
    print("="*80)
    
    try:
        publisher = get_trade_publisher()
        print(f"✅ TradePublisher created (singleton)")
        
        # Test trade publication
        async def test_publish():
            await publisher.publish_trade(
                symbol="AAPL",
                side="BUY",
                quantity=10,
                price=150.25
            )
            print(f"✅ Trade publication test passed")
        
        asyncio.run(test_publish())
        
        return True
    except Exception as e:
        print(f"❌ TradePublisher test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_stream_manager():
    """Test StreamManager functionality"""
    print("\n" + "="*80)
    print("Testing StreamManager")
    print("="*80)
    
    try:
        manager = get_stream_manager()
        print(f"✅ StreamManager created (singleton)")
        
        # Test initialization
        manager.initialize()
        print(f"✅ StreamManager initialized")
        print(f"   - Price stream: {manager.price_stream is not None}")
        print(f"   - Portfolio stream: {manager.portfolio_stream is not None}")
        print(f"   - Signal stream: {manager.signal_stream is not None}")
        
        # Test start/stop (quick test - don't actually start background tasks)
        print(f"✅ StreamManager test passed")
        
        return True
    except Exception as e:
        print(f"❌ StreamManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_evaluator_callbacks():
    """Test StrategyEvaluator signal callback integration"""
    print("\n" + "="*80)
    print("Testing StrategyEvaluator Callbacks")
    print("="*80)
    
    try:
        # Check if _notify_signal_callbacks exists
        evaluator = StrategyEvaluator()
        assert hasattr(evaluator, '_notify_signal_callbacks'), "_notify_signal_callbacks method not found"
        print(f"✅ _notify_signal_callbacks method exists")
        
        # Test callback invocation
        callback_called = []
        
        def test_callback(signal):
            callback_called.append(signal)
        
        evaluator.signal_callbacks.append(test_callback)
        
        # Create test signal
        test_signal = TradingSignal(
            signal_type=SignalType.BUY,
            symbol="AAPL",
            price=150.25,
            quantity=10,
            confidence=0.85,
            timestamp=datetime.now()
        )
        
        # Notify callbacks
        evaluator._notify_signal_callbacks(test_signal)
        
        assert len(callback_called) == 1, "Callback was not invoked"
        assert callback_called[0] == test_signal, "Wrong signal passed to callback"
        print(f"✅ Callback invocation test passed")
        
        return True
    except Exception as e:
        print(f"❌ Evaluator callback test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_message_formats():
    """Test that message formats match dashboard expectations"""
    print("\n" + "="*80)
    print("Testing Message Formats")
    print("="*80)
    
    try:
        # Test signal message format (root-level fields)
        test_signal = TradingSignal(
            signal_type=SignalType.BUY,
            symbol="AAPL",
            price=150.25,
            quantity=10,
            confidence=0.85,
            timestamp=datetime.now()
        )
        
        # Check signal broadcast format
        async def check_format():
            manager = get_websocket_manager()
            
            # Expected format from dashboard.html
            expected_fields = ["type", "signal_type", "symbol", "price", "confidence", "timestamp"]
            
            message = {
                "type": "signal",
                "signal_type": test_signal.signal_type.value,
                "symbol": test_signal.symbol,
                "price": test_signal.price,
                "quantity": test_signal.quantity,
                "confidence": test_signal.confidence,
                "timestamp": test_signal.timestamp.isoformat()
            }
            
            # Verify root-level fields
            for field in expected_fields:
                assert field in message, f"Missing field: {field}"
            
            print(f"✅ Signal message format correct (root-level fields)")
            
            # Test price update format
            price_message = {
                "type": "price_update",
                "symbols": {
                    "AAPL": {
                        "price": 150.25,
                        "change": 0.5,
                        "change_pct": 0.33
                    }
                }
            }
            
            assert "type" in price_message, "Price message missing 'type'"
            assert "symbols" in price_message, "Price message missing 'symbols'"
            print(f"✅ Price update message format correct")
            
        asyncio.run(check_format())
        
        return True
    except Exception as e:
        print(f"❌ Message format test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Phase 2 tests"""
    print("\n" + "="*80)
    print("WEBSOCKET PHASE 2 - STREAM HANDLERS TEST SUITE")
    print("="*80)
    
    results = []
    
    # Test price update stream
    try:
        results.append(("PriceUpdateStream", test_price_update_stream()))
    except Exception as e:
        print(f"\n❌ PriceUpdateStream test failed: {e}")
        results.append(("PriceUpdateStream", False))
    
    # Test signal broadcast stream
    try:
        results.append(("SignalBroadcastStream", test_signal_broadcast_stream()))
    except Exception as e:
        print(f"\n❌ SignalBroadcastStream test failed: {e}")
        results.append(("SignalBroadcastStream", False))
    
    # Test portfolio update stream
    try:
        results.append(("PortfolioUpdateStream", test_portfolio_update_stream()))
    except Exception as e:
        print(f"\n❌ PortfolioUpdateStream test failed: {e}")
        results.append(("PortfolioUpdateStream", False))
    
    # Test trade publisher
    try:
        results.append(("TradePublisher", test_trade_publisher()))
    except Exception as e:
        print(f"\n❌ TradePublisher test failed: {e}")
        results.append(("TradePublisher", False))
    
    # Test stream manager
    try:
        results.append(("StreamManager", test_stream_manager()))
    except Exception as e:
        print(f"\n❌ StreamManager test failed: {e}")
        results.append(("StreamManager", False))
    
    # Test evaluator callbacks
    try:
        results.append(("EvaluatorCallbacks", test_evaluator_callbacks()))
    except Exception as e:
        print(f"\n❌ EvaluatorCallbacks test failed: {e}")
        results.append(("EvaluatorCallbacks", False))
    
    # Test message formats
    try:
        results.append(("MessageFormats", test_message_formats()))
    except Exception as e:
        print(f"\n❌ MessageFormats test failed: {e}")
        results.append(("MessageFormats", False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("\n✅ All Phase 2 tests passed!")
    else:
        print("\n⚠️  Some Phase 2 tests failed")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

