"""
Unit Tests for Stop Loss Logic
==============================

Tests for stop loss calculation and execution logic.
Stop loss functionality is primarily in strategies, but we test it here as part of risk management.
"""

import pytest
from unittest.mock import Mock
from datetime import datetime
import pandas as pd

from src.core.strategy.base import Position, ExitReason
from src.core.strategy.levels import PriceLevel, LevelType
from src.core.strategy.range_bound import RangeBoundStrategy
from src.core.strategy.level_based import LevelBasedStrategy


class TestStopLossCalculation:
    """Test stop loss price calculation"""
    
    @pytest.fixture
    def strategy(self):
        """Create a test strategy"""
        config = {
            "symbol": "SPY",
            "timeframe": "5m",
            "entry": {
                "levels": ["previous_day_low"],
                "proximity_threshold": 0.001
            },
            "exit": {
                "stop_loss_pct": 0.005  # 0.5%
            }
        }
        return RangeBoundStrategy(config)
    
    @pytest.fixture
    def support_level(self):
        """Create a support level (PDL)"""
        return PriceLevel(
            price=100.0,
            level_type=LevelType.PREVIOUS_DAY_LOW,
            strength=0.9,
            timeframe="1d",
            timestamp=datetime.now()
        )
    
    @pytest.fixture
    def resistance_level(self):
        """Create a resistance level (PDH)"""
        return PriceLevel(
            price=105.0,
            level_type=LevelType.PREVIOUS_DAY_HIGH,
            strength=0.9,
            timeframe="1d",
            timestamp=datetime.now()
        )
    
    def test_calculate_stop_loss_from_support_level(self, strategy, support_level):
        """Test stop loss calculation from support level (PDL)"""
        entry_price = 100.0
        stop_loss_pct = 0.005  # 0.5%
        
        stop_loss = strategy.calculate_stop_loss_from_level(
            entry_price,
            support_level,
            stop_loss_pct
        )
        
        # Stop loss should be below the support level
        expected_stop_loss = support_level.price * (1 - stop_loss_pct)
        assert stop_loss == expected_stop_loss
        assert stop_loss < support_level.price
        assert abs(stop_loss - 99.5) < 0.01  # 100 * 0.995
    
    def test_calculate_stop_loss_from_resistance_level(self, strategy, resistance_level):
        """Test stop loss calculation from resistance level (PDH)"""
        entry_price = 105.0
        stop_loss_pct = 0.005  # 0.5%
        
        stop_loss = strategy.calculate_stop_loss_from_level(
            entry_price,
            resistance_level,
            stop_loss_pct
        )
        
        # Stop loss should be below entry price for resistance level entries
        expected_stop_loss = entry_price * (1 - stop_loss_pct)
        assert stop_loss == expected_stop_loss
        assert stop_loss < entry_price
        assert abs(stop_loss - 104.475) < 0.01  # 105 * 0.995
    
    def test_calculate_stop_loss_different_percentages(self, strategy, support_level):
        """Test stop loss with different percentage values"""
        entry_price = 100.0
        
        # Test 0.5% stop loss
        stop_loss_05 = strategy.calculate_stop_loss_from_level(
            entry_price, support_level, 0.005
        )
        assert abs(stop_loss_05 - 99.5) < 0.01
        
        # Test 1% stop loss
        stop_loss_1 = strategy.calculate_stop_loss_from_level(
            entry_price, support_level, 0.01
        )
        assert abs(stop_loss_1 - 99.0) < 0.01
        
        # Test 2% stop loss
        stop_loss_2 = strategy.calculate_stop_loss_from_level(
            entry_price, support_level, 0.02
        )
        assert abs(stop_loss_2 - 98.0) < 0.01
        
        # Wider stop loss should be lower
        assert stop_loss_2 < stop_loss_1 < stop_loss_05
    
    def test_calculate_stop_loss_zero_percentage(self, strategy, support_level):
        """Test stop loss with zero percentage (edge case)"""
        entry_price = 100.0
        stop_loss = strategy.calculate_stop_loss_from_level(
            entry_price, support_level, 0.0
        )
        
        # With 0%, stop loss should equal level/entry price
        assert stop_loss == support_level.price
    
    def test_calculate_stop_loss_large_percentage(self, strategy, support_level):
        """Test stop loss with large percentage (edge case)"""
        entry_price = 100.0
        stop_loss = strategy.calculate_stop_loss_from_level(
            entry_price, support_level, 0.10  # 10%
        )
        
        # Should still calculate correctly
        expected = support_level.price * 0.9
        assert abs(stop_loss - expected) < 0.01


class TestStopLossExecution:
    """Test stop loss execution/triggering"""
    
    @pytest.fixture
    def strategy(self):
        """Create a test strategy"""
        config = {
            "symbol": "SPY",
            "timeframe": "5m",
            "entry": {
                "levels": ["previous_day_low"],
                "proximity_threshold": 0.001
            },
            "exit": {
                "stop_loss_pct": 0.005
            }
        }
        return RangeBoundStrategy(config)
    
    @pytest.fixture
    def position_with_stop_loss(self):
        """Create a position with stop loss"""
        return Position(
            symbol="SPY",
            quantity=10,
            entry_price=100.0,
            entry_time=datetime.now(),
            current_price=99.0,
            unrealized_pnl=-10.0,
            unrealized_pnl_pct=-0.01,
            stop_loss=99.5
        )
    
    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data"""
        dates = pd.date_range(start='2024-01-01', periods=10, freq='5min')
        return pd.DataFrame({
            'open': [100.0] * 10,
            'high': [101.0] * 10,
            'low': [98.0] * 10,
            'close': [100.0] * 10,
            'volume': [1000000] * 10
        }, index=dates)
    
    def test_stop_loss_not_triggered_above_level(self, strategy, position_with_stop_loss, sample_data):
        """Test stop loss not triggered when price is above stop loss"""
        # Set price above stop loss
        sample_data.iloc[-1, sample_data.columns.get_loc('close')] = 100.0
        
        should_exit, reason = strategy.should_exit(position_with_stop_loss, sample_data)
        
        assert should_exit is False
        assert reason != ExitReason.STOP_LOSS
    
    def test_stop_loss_triggered_at_level(self, strategy, position_with_stop_loss, sample_data):
        """Test stop loss triggered when price hits stop loss"""
        # Set price exactly at stop loss
        sample_data.iloc[-1, sample_data.columns.get_loc('close')] = 99.5
        
        should_exit, reason = strategy.should_exit(position_with_stop_loss, sample_data)
        
        assert should_exit is True
        assert reason == ExitReason.STOP_LOSS
    
    def test_stop_loss_triggered_below_level(self, strategy, position_with_stop_loss, sample_data):
        """Test stop loss triggered when price goes below stop loss"""
        # Set price below stop loss
        sample_data.iloc[-1, sample_data.columns.get_loc('close')] = 99.0
        
        should_exit, reason = strategy.should_exit(position_with_stop_loss, sample_data)
        
        assert should_exit is True
        assert reason == ExitReason.STOP_LOSS
    
    def test_stop_loss_not_triggered_without_stop_loss(self, strategy, sample_data):
        """Test should_exit returns False when no stop loss set"""
        position = Position(
            symbol="SPY",
            quantity=10,
            entry_price=100.0,
            entry_time=datetime.now(),
            current_price=99.0,
            unrealized_pnl=-10.0,
            unrealized_pnl_pct=-0.01,
            stop_loss=None  # No stop loss
        )
        
        # Set price below entry (would trigger if stop loss existed)
        sample_data.iloc[-1, sample_data.columns.get_loc('close')] = 95.0
        
        should_exit, reason = strategy.should_exit(position, sample_data)
        
        # Should not exit due to stop loss (might exit for other reasons)
        assert reason != ExitReason.STOP_LOSS or should_exit is False
    
    def test_stop_loss_precedence_over_take_profit_when_both_triggered(self, strategy, sample_data):
        """Test that stop loss takes precedence when both stop loss and take profit are hit"""
        # This scenario is unlikely, but test edge case
        position = Position(
            symbol="SPY",
            quantity=10,
            entry_price=100.0,
            entry_time=datetime.now(),
            current_price=99.0,
            unrealized_pnl=-10.0,
            unrealized_pnl_pct=-0.01,
            stop_loss=99.5,
            take_profit=105.0
        )
        
        # Set price below stop loss (but take profit logic might also check)
        sample_data.iloc[-1, sample_data.columns.get_loc('close')] = 99.0
        
        should_exit, reason = strategy.should_exit(position, sample_data)
        
        # Stop loss should be checked first and triggered
        assert should_exit is True
        assert reason == ExitReason.STOP_LOSS


class TestStopLossEdgeCases:
    """Test edge cases for stop loss logic"""
    
    @pytest.fixture
    def strategy(self):
        """Create a test strategy"""
        config = {
            "symbol": "SPY",
            "timeframe": "5m",
            "entry": {
                "levels": ["previous_day_low"],
                "proximity_threshold": 0.001
            },
            "exit": {
                "stop_loss_pct": 0.005
            }
        }
        return RangeBoundStrategy(config)
    
    def test_stop_loss_with_very_small_price(self, strategy):
        """Test stop loss calculation with very small price"""
        support_level = PriceLevel(
            price=0.10,
            level_type=LevelType.PREVIOUS_DAY_LOW,
            strength=0.9,
            timeframe="1d",
            timestamp=datetime.now()
        )
        
        stop_loss = strategy.calculate_stop_loss_from_level(
            0.10, support_level, 0.005
        )
        
        # Should still calculate correctly even with small price
        assert stop_loss < support_level.price
        assert stop_loss > 0
    
    def test_stop_loss_with_very_large_price(self, strategy):
        """Test stop loss calculation with very large price"""
        support_level = PriceLevel(
            price=10000.0,
            level_type=LevelType.PREVIOUS_DAY_LOW,
            strength=0.9,
            timeframe="1d",
            timestamp=datetime.now()
        )
        
        stop_loss = strategy.calculate_stop_loss_from_level(
            10000.0, support_level, 0.005
        )
        
        # Should calculate correctly with large price
        assert stop_loss < support_level.price
        assert abs(stop_loss - 9950.0) < 1.0  # 10000 * 0.995
    
    def test_stop_loss_with_empty_data(self, strategy):
        """Test stop loss checking with empty data"""
        position = Position(
            symbol="SPY",
            quantity=10,
            entry_price=100.0,
            entry_time=datetime.now(),
            current_price=99.0,
            unrealized_pnl=-10.0,
            unrealized_pnl_pct=-0.01,
            stop_loss=99.5
        )
        
        empty_data = pd.DataFrame()
        
        # Should handle empty data gracefully
        try:
            should_exit, reason = strategy.should_exit(position, empty_data)
            # If it doesn't crash, should return a valid result
            assert isinstance(should_exit, bool)
        except (IndexError, KeyError):
            # Acceptable to raise error for empty data
            pass
    
    def test_stop_loss_calculation_with_different_level_types(self, strategy):
        """Test stop loss calculation with different level types"""
        entry_price = 100.0
        stop_loss_pct = 0.005
        
        # Test with SUPPORT level
        support_level = PriceLevel(
            price=100.0,
            level_type=LevelType.SUPPORT,
            strength=0.9,
            timeframe="1d",
            timestamp=datetime.now()
        )
        stop_loss_support = strategy.calculate_stop_loss_from_level(
            entry_price, support_level, stop_loss_pct
        )
        assert stop_loss_support == support_level.price * (1 - stop_loss_pct)
        
        # Test with RESISTANCE level
        resistance_level = PriceLevel(
            price=100.0,
            level_type=LevelType.RESISTANCE,
            strength=0.9,
            timeframe="1d",
            timestamp=datetime.now()
        )
        stop_loss_resistance = strategy.calculate_stop_loss_from_level(
            entry_price, resistance_level, stop_loss_pct
        )
        assert stop_loss_resistance == entry_price * (1 - stop_loss_pct)


@pytest.mark.unit
class TestStopLossIntegration:
    """Test stop loss integration with strategies"""
    
    def test_stop_loss_in_signal_metadata(self):
        """Test that stop loss is included in trading signal metadata"""
        config = {
            "symbol": "SPY",
            "timeframe": "5m",
            "entry": {
                "levels": ["previous_day_low"],
                "proximity_threshold": 0.001
            },
            "exit": {
                "stop_loss_pct": 0.005
            }
        }
        strategy = RangeBoundStrategy(config)
        
        # Create data near PDL
        dates = pd.date_range(start='2024-01-01', periods=100, freq='5min')
        data = pd.DataFrame({
            'open': [99.9] * 100,
            'high': [100.1] * 100,
            'low': [99.8] * 100,
            'close': [99.9] * 100,  # Near PDL
            'volume': [500000] * 100
        }, index=dates)
        
        # Set previous day low in earlier data
        data.iloc[50:60, data.columns.get_loc('low')] = 99.5
        data.iloc[50:60, data.columns.get_loc('close')] = 99.5
        
        signal = strategy.generate_signal(data)
        
        # Signal should have stop_loss if it's a buy signal
        if signal.signal_type.value == "BUY":
            assert signal.stop_loss is not None
            assert signal.stop_loss < signal.price
    
    def test_stop_loss_in_position_tracking(self):
        """Test that stop loss is tracked in position"""
        position = Position(
            symbol="SPY",
            quantity=10,
            entry_price=100.0,
            entry_time=datetime.now(),
            current_price=99.5,
            unrealized_pnl=-5.0,
            unrealized_pnl_pct=-0.005,
            stop_loss=99.5  # At current price
        )
        
        assert position.stop_loss == 99.5
        assert position.stop_loss <= position.entry_price

