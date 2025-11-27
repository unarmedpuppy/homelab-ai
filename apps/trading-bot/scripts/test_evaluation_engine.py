#!/usr/bin/env python3
"""
Test Strategy Evaluation Engine
================================

Example script demonstrating how to use the StrategyEvaluator
to evaluate strategies in real-time.
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import required modules
from src.core.evaluation import StrategyEvaluator
from src.core.strategy.range_bound import RangeBoundStrategy
from src.core.strategy.registry import get_registry

def create_sample_data():
    """Create sample OHLCV data for testing"""
    # Create a simple dataset with clear PDH/PDL
    dates = pd.date_range(start='2024-01-01 09:30', end='2024-01-01 16:00', freq='5min')
    
    # Simulate price action with PDH around 500 and PDL around 490
    n = len(dates)
    base_price = 495
    
    # Create price that touches PDH and PDL
    highs = []
    lows = []
    closes = []
    
    for i in range(n):
        # Vary price between 490 and 500
        variation = 5 * (i % 20) / 20  # Oscillate
        close = base_price + variation
        high = close + 0.5
        low = close - 0.5
        
        # Set PDH and PDL on previous day
        if i < 20:  # Previous day simulation
            high = 500  # PDH
            low = 490   # PDL
            close = 495
        
        highs.append(high)
        lows.append(low)
        closes.append(close)
    
    df = pd.DataFrame({
        'open': closes,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': [1000000] * n
    }, index=dates)
    
    return df

def test_evaluation_engine():
    """Test the strategy evaluation engine"""
    print("=" * 60)
    print("Testing Strategy Evaluation Engine")
    print("=" * 60)
    print()
    
    # Create evaluator
    print("Creating StrategyEvaluator...")
    evaluator = StrategyEvaluator()
    print("✅ Evaluator created")
    print()
    
    # Add range-bound strategy
    print("Adding RangeBoundStrategy for SPY...")
    config = {
        "name": "SPY_PDH_PDL_Range",
        "symbol": "SPY",
        "timeframe": "5m",
        "entry": {
            "levels": ["previous_day_high", "previous_day_low"],
            "proximity_threshold": 0.001,  # 0.1%
            "volume_confirmation": False
        },
        "exit": {
            "stop_loss_pct": 0.005,  # 0.5%
            "take_profit_type": "opposite_level",
            "take_profit_threshold": 0.002  # 0.2%
        },
        "risk_management": {
            "max_position_size": 100,
            "risk_per_trade": 0.02,
            "default_qty": 10
        }
    }
    
    state = evaluator.add_strategy('range_bound', config, enabled=True)
    print(f"✅ Strategy added: range_bound_SPY")
    print(f"   Enabled: {state.enabled}")
    print()
    
    # Get sample data
    print("Loading sample market data...")
    data = create_sample_data()
    print(f"✅ Loaded {len(data)} bars")
    print()
    
    # Test signal callback
    signals_received = []
    
    def signal_callback(signal):
        signals_received.append(signal)
        print(f"📡 Signal received: {signal.signal_type.value} {signal.symbol} @ ${signal.price:.2f}")
    
    evaluator.add_signal_callback(signal_callback)
    print("✅ Signal callback registered")
    print()
    
    # Evaluate strategy at different price points
    print("Evaluating strategy at different price points...")
    print("-" * 60)
    
    strategy_id = "range_bound_SPY"
    test_prices = [490.1, 490.0, 495.0, 499.9, 500.0]
    
    for test_price in test_prices:
        # Update last close price
        test_data = data.copy()
        test_data.iloc[-1, test_data.columns.get_loc('close')] = test_price
        
        signal = evaluator.evaluate_strategy(strategy_id, test_data)
        
        if signal:
            print(f"\n💰 SIGNAL at ${test_price:.2f}:")
            print(f"   Type: {signal.signal_type.value}")
            print(f"   Price: ${signal.price:.2f}")
            print(f"   Confidence: {signal.confidence:.2%}")
            
            # Simulate position entry
            if signal.signal_type.value == "BUY":
                from src.core.strategy.base import Position
                position = Position(
                    symbol="SPY",
                    quantity=signal.quantity,
                    entry_price=signal.price,
                    entry_time=datetime.now(),
                    current_price=signal.price,
                    unrealized_pnl=0.0,
                    unrealized_pnl_pct=0.0,
                    entry_level=signal.entry_level,
                    stop_loss=signal.stop_loss,
                    take_profit=signal.take_profit
                )
                evaluator.update_position(strategy_id, position)
                print(f"   ✅ Position opened: {position.quantity} shares @ ${position.entry_price:.2f}")
        else:
            print(f"   No signal at ${test_price:.2f}")
    
    print()
    print("-" * 60)
    print(f"✅ Received {len(signals_received)} signals via callback")
    print()
    
    # Test exit conditions
    print("Testing exit conditions...")
    print("-" * 60)
    
    state = evaluator.get_strategy_state(strategy_id)
    if state and state.current_position:
        position = state.current_position
        
        exit_scenarios = [
            (position.stop_loss - 0.1, "Below stop loss"),
            (position.take_profit + 0.1, "Above take profit"),
            (position.entry_price + 0.5, "Holding")
        ]
        
        for exit_price, scenario in exit_scenarios:
            test_data = data.copy()
            test_data.iloc[-1, test_data.columns.get_loc('close')] = exit_price
            
            exit_signal = evaluator.check_exit_conditions(strategy_id, test_data)
            
            if exit_signal:
                print(f"✅ EXIT SIGNAL at ${exit_price:.2f} ({scenario}):")
                print(f"   Reason: {exit_signal.exit_reason.value if exit_signal.exit_reason else 'unknown'}")
    
    print()
    
    # Get evaluation statistics
    print("Evaluation Statistics:")
    print("-" * 60)
    stats = evaluator.get_evaluation_stats()
    print(f"Total strategies: {stats['total_strategies']}")
    print(f"Enabled strategies: {stats['enabled_strategies']}")
    print(f"Total evaluations: {stats['total_evaluations']}")
    print(f"Total signals generated: {stats['total_signals']}")
    print()
    
    for strategy_id, strategy_stats in stats['strategies'].items():
        print(f"Strategy: {strategy_id}")
        print(f"  Enabled: {strategy_stats['enabled']}")
        print(f"  Evaluations: {strategy_stats['evaluations']}")
        print(f"  Signals: {strategy_stats['signals']}")
        print()
    
    print("=" * 60)
    print("✅ Evaluation engine test completed!")
    print("=" * 60)

def test_multiple_strategies():
    """Test evaluating multiple strategies"""
    print("\n" + "=" * 60)
    print("Testing Multiple Strategies")
    print("=" * 60)
    print()
    
    evaluator = StrategyEvaluator()
    
    # Add multiple strategies
    strategies = [
        ('range_bound', 'SPY', {
            "symbol": "SPY",
            "timeframe": "5m",
            "entry": {"levels": ["previous_day_high", "previous_day_low"]},
            "exit": {"stop_loss_pct": 0.005}
        }),
        ('range_bound', 'QQQ', {
            "symbol": "QQQ",
            "timeframe": "5m",
            "entry": {"levels": ["previous_day_high", "previous_day_low"]},
            "exit": {"stop_loss_pct": 0.005}
        }),
    ]
    
    for strategy_type, symbol, config in strategies:
        evaluator.add_strategy(strategy_type, config, enabled=True)
        print(f"✅ Added {strategy_type} for {symbol}")
    
    print()
    print(f"Active strategies: {evaluator.list_strategies()}")
    print()
    
    # Get stats
    stats = evaluator.get_evaluation_stats()
    print(f"Total strategies: {stats['total_strategies']}")
    print(f"Enabled: {stats['enabled_strategies']}")

if __name__ == "__main__":
    try:
        # Import strategies to trigger auto-registration
        import src.core.strategies
        
        test_evaluation_engine()
        test_multiple_strategies()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

