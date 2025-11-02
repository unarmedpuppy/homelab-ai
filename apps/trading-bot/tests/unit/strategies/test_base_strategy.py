"""
Unit Tests for BaseStrategy
============================

Comprehensive unit tests for the BaseStrategy abstract base class.
Tests strategy initialization, configuration, signal generation, and utilities.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import pandas as pd

from src.core.strategy.base import (
    BaseStrategy,
    TradingSignal,
    SignalType,
    Position,
    ExitReason,
    TechnicalIndicators
)
from typing import Tuple, Optional, Any


class TestStrategy(BaseStrategy):
    """Concrete implementation of BaseStrategy for testing"""
    
    def generate_signal(self, data: pd.DataFrame, position: Optional[Position] = None, sentiment: Optional[Any] = None) -> TradingSignal:
        """Generate a test signal"""
        if len(data) == 0:
            return self._create_hold_signal(100.0, "no_data")
        
        current_price = float(data['close'].iloc[-1])
        
        # Simple test logic: buy if price > 100
        if current_price > 100.0:
            return self._create_buy_signal(current_price, quantity=10)
        else:
            return self._create_hold_signal(current_price, "price_too_low")
    
    def should_exit(self, position: Position, data: pd.DataFrame) -> Tuple[bool, ExitReason]:
        """Determine if position should be exited"""
        if not position:
            return False, ExitReason.MANUAL
        
        current_price = float(data['close'].iloc[-1]) if len(data) > 0 else position.current_price
        
        # Check stop loss
        if position.stop_loss and current_price <= position.stop_loss:
            return True, ExitReason.STOP_LOSS
        
        # Check take profit
        if position.take_profit and current_price >= position.take_profit:
            return True, ExitReason.TAKE_PROFIT
        
        return False, ExitReason.MANUAL
    
    def evaluate_entry_conditions(self, data: pd.DataFrame) -> dict:
        """Evaluate entry conditions"""
        return {"can_enter": True, "reason": "test"}
    
    def evaluate_exit_conditions(self, position: Position, data: pd.DataFrame) -> dict:
        """Evaluate exit conditions"""
        return {"should_exit": False, "reason": "test"}


class TestBaseStrategyInitialization:
    """Test BaseStrategy initialization"""
    
    def test_strategy_initialization_basic(self):
        """Test basic strategy initialization"""
        config = {
            "symbol": "SPY",
            "timeframe": "5m"
        }
        
        strategy = TestStrategy(config)
        
        assert strategy.symbol == "SPY"
        assert strategy.timeframe == "5m"
        assert strategy.config == config
        assert strategy.indicators is not None
    
    def test_strategy_initialization_with_sentiment(self):
        """Test strategy initialization with sentiment config"""
        config = {
            "symbol": "SPY",
            "timeframe": "5m",
            "sentiment": {
                "enabled": True,
                "min_sentiment_for_buy": 0.5,
                "max_sentiment_for_sell": -0.5,
                "confidence_boost": 0.15
            }
        }
        
        strategy = TestStrategy(config)
        
        assert strategy.use_sentiment is True
        assert strategy.min_sentiment_for_buy == 0.5
        assert strategy.max_sentiment_for_sell == -0.5
        assert strategy.sentiment_confidence_boost == 0.15
    
    def test_strategy_initialization_with_confluence(self):
        """Test strategy initialization with confluence config"""
        config = {
            "symbol": "SPY",
            "timeframe": "5m",
            "confluence": {
                "enabled": True,
                "min_threshold": 0.6,
                "high_threshold": 0.8,
                "confidence_boost": 0.2
            }
        }
        
        strategy = TestStrategy(config)
        
        assert strategy.use_confluence is True
        assert strategy.min_confluence_threshold == 0.6
        assert strategy.high_confluence_threshold == 0.8
        assert strategy.confluence_confidence_boost == 0.2
    
    def test_strategy_initialization_with_events(self):
        """Test strategy initialization with events config"""
        config = {
            "symbol": "SPY",
            "timeframe": "5m",
            "events": {
                "enabled": True,
                "avoid_earnings_days": 2
            }
        }
        
        strategy = TestStrategy(config)
        
        assert strategy.use_events_filter is True
        assert strategy.avoid_earnings_days == 2


# Note: Technical indicators tests moved to separate file test_technical_indicators.py


class TestBaseStrategySignalGeneration:
    """Test signal generation methods"""
    
    @pytest.fixture
    def strategy(self):
        """Create a test strategy"""
        config = {
            "symbol": "SPY",
            "timeframe": "5m"
        }
        return TestStrategy(config)
    
    def test_create_buy_signal(self, strategy):
        """Test creating a buy signal"""
        signal = strategy._create_buy_signal(100.0, quantity=10)
        
        assert signal.signal_type == SignalType.BUY
        assert signal.symbol == "SPY"
        assert signal.price == 100.0
        assert signal.quantity == 10
        assert signal.confidence > 0
        assert isinstance(signal.timestamp, datetime)
    
    def test_create_sell_signal(self, strategy):
        """Test creating a sell signal"""
        signal = strategy._create_sell_signal(105.0, quantity=10)
        
        assert signal.signal_type == SignalType.SELL
        assert signal.symbol == "SPY"
        assert signal.price == 105.0
        assert signal.quantity == 10
        assert signal.confidence > 0
    
    def test_create_hold_signal(self, strategy):
        """Test creating a hold signal"""
        signal = strategy._create_hold_signal(100.0, "no_entry_conditions")
        
        assert signal.signal_type == SignalType.HOLD
        assert signal.symbol == "SPY"
        assert signal.price == 100.0
        assert signal.metadata.get("reason") == "no_entry_conditions"
    
    def test_generate_signal_with_data(self, strategy, sample_ohlcv_data):
        """Test generating signal with market data"""
        signal = strategy.generate_signal(sample_ohlcv_data)
        
        assert signal is not None
        assert isinstance(signal, TradingSignal)
        assert signal.symbol == "SPY"
        assert signal.price > 0
    
    def test_generate_signal_with_empty_data(self, strategy):
        """Test generating signal with empty data"""
        empty_data = pd.DataFrame()
        signal = strategy.generate_signal(empty_data)
        
        assert signal is not None
        assert signal.signal_type == SignalType.HOLD


class TestBaseStrategyPositionSizing:
    """Test position sizing calculations"""
    
    @pytest.fixture
    def strategy(self):
        """Create a test strategy"""
        config = {
            "symbol": "SPY",
            "timeframe": "5m",
            "risk_management": {
                "max_position_size": 100,
                "default_qty": 10
            }
        }
        return TestStrategy(config)
    
    def test_calculate_position_size_default(self, strategy):
        """Test position sizing with default quantity"""
        signal = strategy._create_buy_signal(100.0)
        account_value = 100000.0
        
        qty = strategy.calculate_position_size(signal, account_value)
        
        # Should use default_qty from config
        assert qty == 10
    
    def test_calculate_position_size_with_quantity(self, strategy):
        """Test position sizing with signal quantity"""
        signal = strategy._create_buy_signal(100.0, quantity=20)
        account_value = 100000.0
        
        qty = strategy.calculate_position_size(signal, account_value)
        
        # Should use signal quantity if provided
        assert qty == 20
    
    def test_calculate_position_size_respects_max(self, strategy):
        """Test position sizing respects max position size"""
        signal = strategy._create_buy_signal(100.0, quantity=200)  # Exceeds max
        account_value = 100000.0
        
        qty = strategy.calculate_position_size(signal, account_value)
        
        # Should be capped at max_position_size
        assert qty <= 100


class TestBaseStrategyEntryExitConditions:
    """Test entry and exit condition evaluation"""
    
    @pytest.fixture
    def strategy(self):
        """Create a test strategy"""
        return TestStrategy({"symbol": "SPY", "timeframe": "5m"})
    
    @pytest.fixture
    def sample_position(self):
        """Create a sample position"""
        return Position(
            symbol="SPY",
            quantity=10,
            entry_price=100.0,
            entry_time=datetime.now(),
            current_price=102.0,
            unrealized_pnl=20.0,
            unrealized_pnl_pct=0.02
        )
    
    def test_evaluate_entry_conditions(self, strategy, sample_ohlcv_data):
        """Test entry condition evaluation"""
        conditions = strategy.evaluate_entry_conditions(sample_ohlcv_data)
        
        assert isinstance(conditions, dict)
        assert "can_enter" in conditions
    
    def test_evaluate_exit_conditions(self, strategy, sample_ohlcv_data, sample_position):
        """Test exit condition evaluation"""
        conditions = strategy.evaluate_exit_conditions(sample_position, sample_ohlcv_data)
        
        assert isinstance(conditions, dict)
        assert "should_exit" in conditions
    
    def test_should_exit_no_exit(self, strategy, sample_ohlcv_data, sample_position):
        """Test should_exit returns False when no exit conditions met"""
        should_exit, reason = strategy.should_exit(sample_position, sample_ohlcv_data)
        
        assert should_exit is False
        assert reason == ExitReason.MANUAL
    
    def test_should_exit_stop_loss(self, strategy, sample_ohlcv_data):
        """Test should_exit returns True when stop loss is hit"""
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
        
        # Create data with price below stop loss
        data = sample_ohlcv_data.copy()
        data.iloc[-1, data.columns.get_loc('close')] = 99.0
        
        should_exit, reason = strategy.should_exit(position, data)
        
        assert should_exit is True
        assert reason == ExitReason.STOP_LOSS
    
    def test_should_exit_take_profit(self, strategy, sample_ohlcv_data):
        """Test should_exit returns True when take profit is hit"""
        position = Position(
            symbol="SPY",
            quantity=10,
            entry_price=100.0,
            entry_time=datetime.now(),
            current_price=105.0,
            unrealized_pnl=50.0,
            unrealized_pnl_pct=0.05,
            take_profit=105.0
        )
        
        # Create data with price at take profit
        data = sample_ohlcv_data.copy()
        data.iloc[-1, data.columns.get_loc('close')] = 105.0
        
        should_exit, reason = strategy.should_exit(position, data)
        
        assert should_exit is True
        assert reason == ExitReason.TAKE_PROFIT
    
    def test_should_exit_empty_data(self, strategy, sample_position):
        """Test should_exit handles empty data gracefully"""
        empty_data = pd.DataFrame()
        
        # Should use position's current_price when data is empty
        should_exit, reason = strategy.should_exit(sample_position, empty_data)
        
        assert isinstance(should_exit, bool)
        assert isinstance(reason, ExitReason)


@pytest.mark.unit
class TestBaseStrategySentimentFilter:
    """Test sentiment filtering"""
    
    @pytest.fixture
    def strategy_with_sentiment(self):
        """Create strategy with sentiment enabled"""
        config = {
            "symbol": "SPY",
            "timeframe": "5m",
            "sentiment": {
                "enabled": True,
                "min_sentiment_for_buy": 0.3,
                "max_sentiment_for_sell": -0.3
            }
        }
        return TestStrategy(config)
    
    @pytest.fixture
    def bullish_sentiment(self):
        """Create bullish sentiment"""
        from unittest.mock import Mock
        sentiment = Mock()
        sentiment.unified_sentiment = 0.6  # Bullish
        sentiment.confidence = 0.8
        return sentiment
    
    @pytest.fixture
    def bearish_sentiment(self):
        """Create bearish sentiment"""
        from unittest.mock import Mock
        sentiment = Mock()
        sentiment.unified_sentiment = -0.6  # Bearish
        sentiment.confidence = 0.8
        return sentiment
    
    def test_sentiment_filter_allows_bullish_buy(self, strategy_with_sentiment, bullish_sentiment):
        """Test sentiment filter allows buy with bullish sentiment"""
        signal = strategy_with_sentiment._create_buy_signal(100.0)
        filtered = strategy_with_sentiment._apply_sentiment_filter(signal, bullish_sentiment)
        
        assert filtered.signal_type == SignalType.BUY
    
    def test_sentiment_filter_blocks_buy_with_bearish_sentiment(
        self, strategy_with_sentiment, bearish_sentiment
    ):
        """Test sentiment filter blocks buy with bearish sentiment"""
        signal = strategy_with_sentiment._create_buy_signal(100.0)
        filtered = strategy_with_sentiment._apply_sentiment_filter(signal, bearish_sentiment)
        
        # Should be converted to HOLD
        assert filtered.signal_type == SignalType.HOLD


@pytest.mark.unit
class TestBaseStrategyMetadata:
    """Test signal metadata handling"""
    
    @pytest.fixture
    def strategy(self):
        """Create a test strategy"""
        return TestStrategy({"symbol": "SPY", "timeframe": "5m"})
    
    def test_signal_metadata_initialized(self, strategy):
        """Test signal metadata is initialized"""
        signal = strategy._create_buy_signal(100.0)
        
        assert isinstance(signal.metadata, dict)
    
    def test_signal_metadata_can_be_updated(self, strategy):
        """Test signal metadata can be updated"""
        signal = strategy._create_buy_signal(100.0)
        signal.metadata["custom_key"] = "custom_value"
        
        assert signal.metadata["custom_key"] == "custom_value"


@pytest.mark.unit
class TestBaseStrategyErrorHandling:
    """Test error handling in BaseStrategy"""
    
    @pytest.fixture
    def strategy(self):
        """Create a test strategy"""
        return TestStrategy({"symbol": "SPY", "timeframe": "5m"})
    
    def test_generate_signal_handles_invalid_data(self, strategy):
        """Test generate_signal handles invalid data gracefully"""
        # Data with missing columns
        invalid_data = pd.DataFrame({'invalid': [1, 2, 3]})
        
        # Should not crash, may return hold signal or raise helpful error
        try:
            signal = strategy.generate_signal(invalid_data)
            assert signal is not None
            assert isinstance(signal, TradingSignal)
        except (KeyError, IndexError):
            # Acceptable to raise errors for invalid data
            pass
    
    def test_generate_signal_with_nan_values(self, strategy):
        """Test generate_signal handles NaN values"""
        import numpy as np
        data = pd.DataFrame({
            'close': [100.0, 101.0, np.nan, 103.0],
            'open': [99.0, 100.0, 102.0, 102.0],
            'high': [101.0, 102.0, 103.0, 104.0],
            'low': [98.0, 99.0, 101.0, 101.0],
            'volume': [1000, 1100, 1200, 1300]
        })
        
        # Should handle NaN gracefully
        try:
            signal = strategy.generate_signal(data)
            assert signal is not None
        except (ValueError, TypeError):
            # Acceptable to raise errors for invalid data
            pass
    
    def test_calculate_position_size_with_zero_account_value(self, strategy):
        """Test position sizing with zero account value"""
        signal = strategy._create_buy_signal(100.0, quantity=10)
        
        # Should handle zero account value gracefully
        qty = strategy.calculate_position_size(signal, 0.0)
        
        # Should return at least 0, possibly capped at 0 or default
        assert qty >= 0
    
    def test_calculate_position_size_with_negative_account_value(self, strategy):
        """Test position sizing with negative account value"""
        signal = strategy._create_buy_signal(100.0, quantity=10)
        
        # Should handle negative account value gracefully
        qty = strategy.calculate_position_size(signal, -1000.0)
        
        # Should return at least 0
        assert qty >= 0
    
    def test_should_exit_with_none_position(self, strategy, sample_ohlcv_data):
        """Test should_exit handles None position"""
        # Should handle None gracefully or raise appropriate error
        try:
            should_exit, reason = strategy.should_exit(None, sample_ohlcv_data)
            assert isinstance(should_exit, bool)
        except (TypeError, AttributeError):
            # Acceptable to raise error for None position
            pass


@pytest.mark.unit
class TestBaseStrategyConfigurationValidation:
    """Test configuration validation"""
    
    def test_strategy_with_minimal_config(self):
        """Test strategy works with minimal configuration"""
        config = {"symbol": "SPY"}
        strategy = TestStrategy(config)
        
        assert strategy.symbol == "SPY"
        assert strategy.timeframe == "5m"  # Default
    
    def test_strategy_with_defaults(self):
        """Test strategy uses sensible defaults"""
        config = {"symbol": "AAPL"}
        strategy = TestStrategy(config)
        
        assert strategy.symbol == "AAPL"
        assert strategy.timeframe == "5m"
        assert strategy.indicators is not None
        assert strategy.use_sentiment is False  # Default
        assert strategy.use_confluence is False  # Default
    
    def test_strategy_sentiment_config_defaults(self):
        """Test sentiment config uses sensible defaults"""
        config = {
            "symbol": "SPY",
            "sentiment": {"enabled": True}
        }
        strategy = TestStrategy(config)
        
        assert strategy.use_sentiment is True
        # Check default values
        assert strategy.min_sentiment_for_buy == -1.0  # Default: no filter
        assert strategy.max_sentiment_for_sell == 1.0  # Default: no filter
    
    def test_strategy_confluence_config_defaults(self):
        """Test confluence config uses sensible defaults"""
        config = {
            "symbol": "SPY",
            "confluence": {"enabled": True}
        }
        strategy = TestStrategy(config)
        
        assert strategy.use_confluence is True
        # Check default values
        assert strategy.min_confluence_threshold == 0.0  # Default
        assert strategy.high_confluence_threshold == 0.7  # Default

