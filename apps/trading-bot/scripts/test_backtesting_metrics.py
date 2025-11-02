#!/usr/bin/env python3
"""
Test Backtesting Metrics Calculator
====================================

Tests the performance metrics calculator with sample trade data.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, timedelta
import pandas as pd
from src.core.backtesting.metrics import MetricsCalculator, BacktestMetrics
from src.core.backtesting.parameter_space import ParameterRange, ParameterSpace

def create_sample_trades():
    """Create sample trade data for testing"""
    trades = []
    start_date = datetime(2024, 1, 1)
    
    # Simulate some winning and losing trades
    # Winning trades
    for i in range(15):
        trades.append({
            'pnl': 100.0 + i * 10,  # Increasing wins
            'timestamp': start_date + timedelta(days=i*2),
        })
    
    # Losing trades
    for i in range(10):
        trades.append({
            'pnl': -50.0 - i * 5,  # Increasing losses
            'timestamp': start_date + timedelta(days=30 + i*2),
        })
    
    # More winning trades
    for i in range(20):
        trades.append({
            'pnl': 75.0,
            'timestamp': start_date + timedelta(days=60 + i*2),
        })
    
    return trades


def test_metrics_calculation():
    """Test metrics calculation with sample trades"""
    print("="*60)
    print("Test 1: Metrics Calculation")
    print("="*60)
    
    calculator = MetricsCalculator(risk_free_rate=0.0)
    trades = create_sample_trades()
    
    initial_capital = 10000.0
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 3, 31)
    
    metrics = calculator.calculate(
        trades=trades,
        initial_capital=initial_capital,
        start_date=start_date,
        end_date=end_date,
        include_equity_curve=True
    )
    
    print(f"\n✅ Metrics calculated successfully")
    print(f"\nBasic Metrics:")
    print(f"  Initial Capital: ${metrics.initial_capital:,.2f}")
    print(f"  Final Capital: ${metrics.final_capital:,.2f}")
    print(f"  Total Return: ${metrics.total_return:,.2f} ({metrics.total_return_pct:.2f}%)")
    
    print(f"\nTrade Statistics:")
    print(f"  Total Trades: {metrics.total_trades}")
    print(f"  Winning Trades: {metrics.winning_trades}")
    print(f"  Losing Trades: {metrics.losing_trades}")
    print(f"  Win Rate: {metrics.win_rate:.2f}%")
    
    print(f"\nProfit/Loss Metrics:")
    print(f"  Total Profit: ${metrics.total_profit:,.2f}")
    print(f"  Total Loss: ${metrics.total_loss:,.2f}")
    print(f"  Profit Factor: {metrics.profit_factor:.2f}")
    print(f"  Average Win: ${metrics.average_win:,.2f}")
    print(f"  Average Loss: ${metrics.average_loss:,.2f}")
    print(f"  Largest Win: ${metrics.largest_win:,.2f}")
    print(f"  Largest Loss: ${metrics.largest_loss:,.2f}")
    
    print(f"\nRisk Metrics:")
    print(f"  Max Drawdown: ${metrics.max_drawdown:,.2f} ({metrics.max_drawdown_pct:.2f}%)")
    if metrics.max_drawdown_start:
        print(f"  Drawdown Start: {metrics.max_drawdown_start}")
    if metrics.max_drawdown_end:
        print(f"  Drawdown End: {metrics.max_drawdown_end}")
    if metrics.recovery_time_days:
        print(f"  Recovery Time: {metrics.recovery_time_days:.1f} days")
    
    print(f"\nRisk-Adjusted Returns:")
    print(f"  Sharpe Ratio: {metrics.sharpe_ratio:.4f}")
    print(f"  Sortino Ratio: {metrics.sortino_ratio:.4f}")
    print(f"  Calmar Ratio: {metrics.calmar_ratio:.4f}")
    
    print(f"\nAdditional Metrics:")
    print(f"  Average Trade Return: ${metrics.average_trade_return:,.2f}")
    print(f"  Expectancy: ${metrics.expectancy:,.2f}")
    
    # Validate calculations
    assert metrics.total_trades == len(trades), "Trade count mismatch"
    assert metrics.winning_trades + metrics.losing_trades == metrics.total_trades, "Win/loss count mismatch"
    assert metrics.final_capital == initial_capital + metrics.total_return, "Final capital calculation error"
    
    print("\n✅ All validations passed!")
    return True


def test_empty_trades():
    """Test metrics calculation with no trades"""
    print("\n" + "="*60)
    print("Test 2: Empty Trades (Edge Case)")
    print("="*60)
    
    calculator = MetricsCalculator()
    
    metrics = calculator.calculate(
        trades=[],
        initial_capital=10000.0,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 3, 31),
        include_equity_curve=False
    )
    
    assert metrics.total_trades == 0, "Should have 0 trades"
    assert metrics.final_capital == 10000.0, "Final capital should equal initial"
    assert metrics.total_return == 0.0, "Total return should be 0"
    
    print("✅ Empty trades handled correctly")
    return True


def test_parameter_space():
    """Test parameter space generation"""
    print("\n" + "="*60)
    print("Test 3: Parameter Space Generation")
    print("="*60)
    
    # Create parameter space for SMA strategy
    space = ParameterSpace({
        'sma_short': ParameterRange('sma_short', 10, 50, step=5, dtype=int),
        'sma_long': ParameterRange('sma_long', 50, 200, step=25, dtype=int),
        'entry_threshold': ParameterRange('entry_threshold', 0.001, 0.01, step=0.001, dtype=float),
    })
    
    total_combinations = space.get_total_combinations()
    print(f"\nTotal combinations: {total_combinations}")
    
    combinations = space.generate_combinations()
    print(f"Generated {len(combinations)} combinations")
    
    # Show first few combinations
    print("\nFirst 5 combinations:")
    for i, combo in enumerate(combinations[:5]):
        print(f"  {i+1}. {combo}")
    
    # Validate
    assert len(combinations) == total_combinations, "Combination count mismatch"
    assert all('sma_short' in c for c in combinations), "Missing sma_short parameter"
    assert all('sma_long' in c for c in combinations), "Missing sma_long parameter"
    
    print("\n✅ Parameter space generation working correctly")
    return True


def test_parameter_range_types():
    """Test different parameter range types"""
    print("\n" + "="*60)
    print("Test 4: Parameter Range Types")
    print("="*60)
    
    # Linear integer range
    int_range = ParameterRange('test_int', 10, 50, step=5, dtype=int)
    int_values = int_range.generate_values()
    print(f"\nInteger range (10-50, step=5): {len(int_values)} values")
    print(f"  Sample: {int_values[:5]}")
    assert all(isinstance(v, int) for v in int_values), "All values should be integers"
    
    # Linear float range
    float_range = ParameterRange('test_float', 0.1, 1.0, step=0.1, dtype=float)
    float_values = float_range.generate_values()
    print(f"\nFloat range (0.1-1.0, step=0.1): {len(float_values)} values")
    print(f"  Sample: {float_values[:5]}")
    assert all(isinstance(v, float) for v in float_values), "All values should be floats"
    
    # Logarithmic range
    log_range = ParameterRange('test_log', 10, 1000, step=2, log_scale=True, dtype=int)
    log_values = log_range.generate_values()
    print(f"\nLogarithmic range (10-1000): {len(log_values)} values")
    print(f"  Sample: {log_values[:10]}")
    
    print("\n✅ Parameter range types working correctly")
    return True


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("BACKTESTING METRICS CALCULATOR - TEST SUITE")
    print("="*60)
    
    all_passed = True
    
    try:
        all_passed = test_metrics_calculation() and all_passed
        all_passed = test_empty_trades() and all_passed
        all_passed = test_parameter_space() and all_passed
        all_passed = test_parameter_range_types() and all_passed
        
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        if all_passed:
            print("✅ ALL TESTS PASSED")
            return 0
        else:
            print("❌ SOME TESTS FAILED")
            return 1
            
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

