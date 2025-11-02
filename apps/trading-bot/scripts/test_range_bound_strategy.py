#!/usr/bin/env python3
"""
Test Range-Bound Strategy
==========================

Example script demonstrating how to use the RangeBoundStrategy for SPY PDH/PDL trading.
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import strategy components
from src.core.strategies import RangeBoundStrategy
from src.core.strategy.registry import get_registry

def create_sample_data():
    """Create sample OHLCV data for testing"""
    # Create a simple dataset with clear PDH/PDL
    dates = pd.date_range(start='2024-01-01 09:30', end='2024-01-01 16:00', freq='5min')
    
    # Simulate price action with PDH around 500 and PDL around 490
    n = len(dates)
    base_price = 495
    price_variation = pd.Series(range(n)) * 0.1
    
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

def test_range_bound_strategy():
    """Test the range-bound strategy"""
    print("=" * 60)
    print("Testing Range-Bound Strategy (SPY PDH/PDL)")
    print("=" * 60)
    print()
    
    # Strategy configuration
    config = {
        "name": "SPY_PDH_PDL_Range",
        "symbol": "SPY",
        "timeframe": "5m",
        "entry": {
            "levels": ["previous_day_high", "previous_day_low"],
            "proximity_threshold": 0.001,  # 0.1%
            "volume_confirmation": False  # Disable for testing
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
    
    # Create strategy instance
    print("Creating strategy instance...")
    strategy = RangeBoundStrategy(config)
    print(f"✅ Strategy created: {strategy.symbol} on {strategy.timeframe}")
    print()
    
    # Get sample data
    print("Loading sample data...")
    data = create_sample_data()
    print(f"✅ Loaded {len(data)} bars")
    print(f"   Date range: {data.index[0]} to {data.index[-1]}")
    print()
    
    # Identify levels
    print("Identifying price levels...")
    levels = strategy.identify_levels(data)
    print(f"✅ Found {len(levels)} levels:")
    for level_name, level in levels.items():
        print(f"   {level_name}: ${level.price:.2f} (strength: {level.strength:.2f})")
    print()
    
    # Generate signals
    print("Generating trading signals...")
    print("-" * 60)
    
    position = None
    signals_generated = 0
    
    # Test signal generation at different price points
    test_prices = [490.1, 490.0, 495.0, 499.9, 500.0, 500.1]
    
    for test_price in test_prices:
        # Update last close price
        test_data = data.copy()
        test_data.iloc[-1, test_data.columns.get_loc('close')] = test_price
        
        signal = strategy.generate_signal(test_data, position)
        
        if signal.signal_type.value != "HOLD":
            signals_generated += 1
            print(f"\n💰 SIGNAL at ${test_price:.2f}:")
            print(f"   Type: {signal.signal_type.value}")
            print(f"   Price: ${signal.price:.2f}")
            print(f"   Quantity: {signal.quantity}")
            print(f"   Confidence: {signal.confidence:.2%}")
            
            if signal.entry_level:
                print(f"   Entry Level: {signal.entry_level.level_type.value} @ ${signal.entry_level.price:.2f}")
            
            if signal.stop_loss:
                print(f"   Stop Loss: ${signal.stop_loss:.2f}")
            
            if signal.take_profit:
                print(f"   Take Profit: ${signal.take_profit:.2f}")
            
            if signal.metadata:
                print(f"   Metadata: {signal.metadata}")
            
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
                print(f"   ✅ Position opened: {position.quantity} shares @ ${position.entry_price:.2f}")
        else:
            print(f"   No signal at ${test_price:.2f}: {signal.metadata.get('reason', 'unknown')}")
    
    print()
    print("-" * 60)
    print(f"✅ Generated {signals_generated} entry signals")
    print()
    
    # Test exit conditions if we have a position
    if position:
        print("Testing exit conditions...")
        print("-" * 60)
        
        exit_scenarios = [
            (position.stop_loss - 0.1, "Below stop loss"),
            (position.take_profit + 0.1, "Above take profit"),
            (position.entry_price + 1.0, "Near opposite level"),
            (position.entry_price + 0.5, "Holding position")
        ]
        
        for exit_price, scenario in exit_scenarios:
            test_data = data.copy()
            test_data.iloc[-1, test_data.columns.get_loc('close')] = exit_price
            
            should_exit, reason = strategy.should_exit(position, test_data)
            
            status = "✅ EXIT" if should_exit else "⏸ HOLD"
            print(f"{status} at ${exit_price:.2f} ({scenario}): {reason.value}")
    
    print()
    print("=" * 60)
    print("✅ Strategy test completed!")
    print("=" * 60)

def test_registry():
    """Test the strategy registry"""
    print("\n" + "=" * 60)
    print("Testing Strategy Registry")
    print("=" * 60)
    print()
    
    registry = get_registry()
    
    # List all strategies
    strategies = registry.list_strategies()
    print(f"Registered strategies: {strategies}")
    print()
    
    # Get strategy info
    for strategy_name in strategies:
        info = registry.get_strategy_info(strategy_name)
        print(f"Strategy: {strategy_name}")
        print(f"  Description: {info.get('description', 'N/A')}")
        print(f"  Supports Levels: {info.get('supports_levels', False)}")
        print()

if __name__ == "__main__":
    try:
        # Import strategies to trigger auto-registration
        import src.core.strategies
        
        test_range_bound_strategy()
        test_registry()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

