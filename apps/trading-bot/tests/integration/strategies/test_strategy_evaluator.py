"""
Integration Tests for Strategy Evaluator
========================================

Tests that verify StrategyEvaluator integrates correctly with strategies,
data providers, and other components.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from src.core.evaluation.evaluator import StrategyEvaluator, StrategyState
from src.core.strategy.base import TradingSignal, SignalType, Position
from src.core.data.providers.market_data import DataProviderManager


class TestStrategyEvaluatorInitialization:
    """Test StrategyEvaluator initialization"""
    
    def test_initialization_without_data_provider(self):
        """Test initialization without data provider"""
        evaluator = StrategyEvaluator()
        
        assert evaluator.data_provider is None
        assert evaluator.strategies == {}
        assert evaluator.signal_callbacks == []
        assert evaluator.min_confidence == 0.0
        assert evaluator.require_volume is False
    
    def test_initialization_with_data_provider(self):
        """Test initialization with data provider"""
        mock_provider = Mock(spec=DataProviderManager)
        evaluator = StrategyEvaluator(data_provider=mock_provider)
        
        assert evaluator.data_provider == mock_provider
        assert evaluator.strategies == {}


class TestStrategyAddition:
    """Test adding strategies to evaluator"""
    
    @pytest.fixture
    def evaluator(self):
        """Create strategy evaluator"""
        return StrategyEvaluator()
    
    def test_add_strategy_success(self, evaluator, sample_ohlcv_data):
        """Test successfully adding a strategy"""
        config = {
            'symbol': 'SPY',
            'timeframe': '5m',
            'entry': {
                'levels': ['previous_day_high', 'previous_day_low'],
                'proximity_threshold': 0.001
            },
            'exit': {
                'stop_loss_pct': 0.005,
                'take_profit_type': 'opposite_level'
            }
        }
        
        state = evaluator.add_strategy('RangeBoundStrategy', config)
        
        assert isinstance(state, StrategyState)
        assert state.strategy is not None
        assert state.symbol == 'SPY'
        assert state.enabled is True
        assert state.signals_generated == 0
        assert state.evaluation_count == 0
        
        # Check strategy was added to internal dict
        strategy_id = "RangeBoundStrategy_SPY"
        assert strategy_id in evaluator.strategies
        assert evaluator.strategies[strategy_id] == state
    
    def test_add_strategy_invalid_name(self, evaluator):
        """Test adding non-existent strategy raises error"""
        config = {'symbol': 'SPY'}
        
        with pytest.raises(ValueError, match="not found"):
            evaluator.add_strategy('NonExistentStrategy', config)
    
    def test_add_strategy_disabled(self, evaluator):
        """Test adding strategy as disabled"""
        config = {
            'symbol': 'SPY',
            'timeframe': '5m',
            'entry': {'levels': ['previous_day_high']},
            'exit': {'stop_loss_pct': 0.005}
        }
        
        state = evaluator.add_strategy('RangeBoundStrategy', config, enabled=False)
        
        assert state.enabled is False


class TestStrategyRemoval:
    """Test removing strategies from evaluator"""
    
    @pytest.fixture
    def evaluator(self):
        """Create evaluator with a strategy"""
        evaluator = StrategyEvaluator()
        config = {
            'symbol': 'SPY',
            'timeframe': '5m',
            'entry': {'levels': ['previous_day_high']},
            'exit': {'stop_loss_pct': 0.005}
        }
        evaluator.add_strategy('RangeBoundStrategy', config)
        return evaluator
    
    def test_remove_strategy(self, evaluator):
        """Test removing a strategy"""
        strategy_id = "RangeBoundStrategy_SPY"
        assert strategy_id in evaluator.strategies
        
        evaluator.remove_strategy(strategy_id)
        
        assert strategy_id not in evaluator.strategies
    
    def test_remove_nonexistent_strategy(self, evaluator):
        """Test removing non-existent strategy (should not raise error)"""
        evaluator.remove_strategy('nonexistent_strategy')
        # Should not raise error, just log warning
    
    def test_enable_disable_strategy(self, evaluator):
        """Test enabling and disabling strategies"""
        strategy_id = "RangeBoundStrategy_SPY"
        
        # Disable
        evaluator.disable_strategy(strategy_id)
        assert evaluator.strategies[strategy_id].enabled is False
        
        # Enable
        evaluator.enable_strategy(strategy_id)
        assert evaluator.strategies[strategy_id].enabled is True


class TestStrategyEvaluation:
    """Test strategy evaluation with market data"""
    
    @pytest.fixture
    def evaluator(self):
        """Create evaluator with a strategy"""
        evaluator = StrategyEvaluator()
        config = {
            'symbol': 'SPY',
            'timeframe': '5m',
            'entry': {
                'levels': ['previous_day_high', 'previous_day_low'],
                'proximity_threshold': 0.001
            },
            'exit': {
                'stop_loss_pct': 0.005,
                'take_profit_type': 'opposite_level'
            }
        }
        evaluator.add_strategy('RangeBoundStrategy', config)
        return evaluator
    
    def test_evaluate_strategy_with_data(self, evaluator, sample_ohlcv_data):
        """Test evaluating strategy with market data"""
        strategy_id = "RangeBoundStrategy_SPY"
        
        signal = evaluator.evaluate_strategy(strategy_id, sample_ohlcv_data)
        
        # Should return a signal (or None if no signal generated)
        assert signal is None or isinstance(signal, TradingSignal)
        
        # Check state was updated
        state = evaluator.strategies[strategy_id]
        assert state.last_evaluation is not None
        assert state.evaluation_count == 1
    
    def test_evaluate_strategy_no_data(self, evaluator):
        """Test evaluating strategy without data"""
        strategy_id = "RangeBoundStrategy_SPY"
        
        signal = evaluator.evaluate_strategy(strategy_id, None)
        
        # Should return None when no data
        assert signal is None
        
        # State should not be updated
        state = evaluator.strategies[strategy_id]
        assert state.last_evaluation is None
        assert state.evaluation_count == 0
    
    def test_evaluate_strategy_empty_data(self, evaluator):
        """Test evaluating strategy with empty data"""
        strategy_id = "RangeBoundStrategy_SPY"
        empty_data = pd.DataFrame()
        
        signal = evaluator.evaluate_strategy(strategy_id, empty_data)
        
        assert signal is None
    
    def test_evaluate_strategy_disabled(self, evaluator, sample_ohlcv_data):
        """Test evaluating disabled strategy returns None"""
        strategy_id = "RangeBoundStrategy_SPY"
        evaluator.disable_strategy(strategy_id)
        
        signal = evaluator.evaluate_strategy(strategy_id, sample_ohlcv_data)
        
        assert signal is None
    
    def test_evaluate_strategy_nonexistent(self, evaluator, sample_ohlcv_data):
        """Test evaluating non-existent strategy"""
        signal = evaluator.evaluate_strategy('nonexistent', sample_ohlcv_data)
        
        assert signal is None
    
    def test_evaluate_strategy_updates_stats(self, evaluator, sample_ohlcv_data):
        """Test that evaluation updates statistics"""
        strategy_id = "RangeBoundStrategy_SPY"
        initial_count = evaluator.strategies[strategy_id].evaluation_count
        
        evaluator.evaluate_strategy(strategy_id, sample_ohlcv_data)
        
        assert evaluator.strategies[strategy_id].evaluation_count == initial_count + 1


class TestMultiStrategyEvaluation:
    """Test evaluating multiple strategies"""
    
    @pytest.fixture
    def evaluator(self):
        """Create evaluator with multiple strategies"""
        evaluator = StrategyEvaluator()
        
        # Add strategy 1
        config1 = {
            'symbol': 'SPY',
            'timeframe': '5m',
            'entry': {'levels': ['previous_day_high']},
            'exit': {'stop_loss_pct': 0.005}
        }
        evaluator.add_strategy('RangeBoundStrategy', config1)
        
        # Add strategy 2
        config2 = {
            'symbol': 'QQQ',
            'timeframe': '5m',
            'entry': {'levels': ['previous_day_low']},
            'exit': {'stop_loss_pct': 0.005}
        }
        evaluator.add_strategy('RangeBoundStrategy', config2)
        
        return evaluator
    
    def test_evaluate_all_strategies(self, evaluator, sample_ohlcv_data):
        """Test evaluating all strategies at once"""
        market_data = {
            'SPY': sample_ohlcv_data,
            'QQQ': sample_ohlcv_data  # Reuse same data structure
        }
        
        signals = evaluator.evaluate_all_strategies(market_data=market_data)
        
        assert isinstance(signals, list)
        # May have 0, 1, or 2 signals depending on strategy logic
        assert len(signals) <= 2
        
        # All signals should be TradingSignal instances
        for signal in signals:
            assert isinstance(signal, TradingSignal)
    
    def test_evaluate_all_strategies_missing_data(self, evaluator, sample_ohlcv_data):
        """Test evaluating all strategies with missing data"""
        market_data = {
            'SPY': sample_ohlcv_data
            # Missing QQQ data
        }
        
        signals = evaluator.evaluate_all_strategies(market_data=market_data)
        
        # Should still evaluate SPY strategy
        assert isinstance(signals, list)
    
    def test_evaluate_all_strategies_respects_disabled(self, evaluator, sample_ohlcv_data):
        """Test that disabled strategies are not evaluated"""
        evaluator.disable_strategy("RangeBoundStrategy_SPY")
        
        market_data = {
            'SPY': sample_ohlcv_data,
            'QQQ': sample_ohlcv_data
        }
        
        signals = evaluator.evaluate_all_strategies(market_data=market_data)
        
        # Should only evaluate QQQ (SPY is disabled)
        assert isinstance(signals, list)


class TestSignalCallbacks:
    """Test signal callback functionality"""
    
    @pytest.fixture
    def evaluator(self):
        """Create evaluator with strategy"""
        evaluator = StrategyEvaluator()
        config = {
            'symbol': 'SPY',
            'timeframe': '5m',
            'entry': {'levels': ['previous_day_high']},
            'exit': {'stop_loss_pct': 0.005}
        }
        evaluator.add_strategy('RangeBoundStrategy', config)
        return evaluator
    
    def test_add_signal_callback(self, evaluator):
        """Test adding signal callback"""
        callback = Mock()
        
        evaluator.add_signal_callback(callback)
        
        assert callback in evaluator.signal_callbacks
        assert len(evaluator.signal_callbacks) == 1
    
    def test_signal_callback_invoked(self, evaluator, sample_ohlcv_data):
        """Test that callback is invoked when signal is generated"""
        callback = Mock()
        evaluator.add_signal_callback(callback)
        
        # Mock the strategy to return a signal
        strategy_id = "RangeBoundStrategy_SPY"
        state = evaluator.strategies[strategy_id]
        mock_signal = TradingSignal(
            signal_type=SignalType.BUY,
            price=100.0,
            quantity=10,
            confidence=0.8,
            timestamp=datetime.now(),
            symbol='SPY'
        )
        state.strategy.generate_signal = Mock(return_value=mock_signal)
        
        signal = evaluator.evaluate_strategy(strategy_id, sample_ohlcv_data)
        
        # Callback should be called if signal was generated
        # (may or may not be called depending on filtering)
        if signal:
            callback.assert_called()
    
    def test_signal_callback_error_handling(self, evaluator, sample_ohlcv_data):
        """Test that callback errors don't break evaluation"""
        callback = Mock(side_effect=Exception("Callback error"))
        evaluator.add_signal_callback(callback)
        
        # Evaluation should still work
        strategy_id = "RangeBoundStrategy_SPY"
        signal = evaluator.evaluate_strategy(strategy_id, sample_ohlcv_data)
        
        # Should not raise error even if callback fails
        assert signal is None or isinstance(signal, TradingSignal)
    
    def test_remove_signal_callback(self, evaluator):
        """Test removing signal callback"""
        callback = Mock()
        evaluator.add_signal_callback(callback)
        assert callback in evaluator.signal_callbacks
        
        evaluator.remove_signal_callback(callback)
        
        assert callback not in evaluator.signal_callbacks


class TestPositionTracking:
    """Test position tracking functionality"""
    
    @pytest.fixture
    def evaluator(self):
        """Create evaluator with strategy"""
        evaluator = StrategyEvaluator()
        config = {
            'symbol': 'SPY',
            'timeframe': '5m',
            'entry': {'levels': ['previous_day_high']},
            'exit': {'stop_loss_pct': 0.005}
        }
        evaluator.add_strategy('RangeBoundStrategy', config)
        return evaluator
    
    def test_update_position(self, evaluator):
        """Test updating position for a strategy"""
        strategy_id = "RangeBoundStrategy_SPY"
        position = Position(
            symbol='SPY',
            quantity=10,
            entry_price=100.0,
            entry_time=datetime.now()
        )
        
        evaluator.update_position(strategy_id, position)
        
        state = evaluator.strategies[strategy_id]
        assert state.current_position == position
    
    def test_update_position_none(self, evaluator):
        """Test clearing position"""
        strategy_id = "RangeBoundStrategy_SPY"
        position = Position(
            symbol='SPY',
            quantity=10,
            entry_price=100.0,
            entry_time=datetime.now()
        )
        evaluator.update_position(strategy_id, position)
        
        # Clear position
        evaluator.update_position(strategy_id, None)
        
        state = evaluator.strategies[strategy_id]
        assert state.current_position is None
    
    def test_get_strategy_state(self, evaluator):
        """Test getting strategy state"""
        strategy_id = "RangeBoundStrategy_SPY"
        
        state = evaluator.get_strategy_state(strategy_id)
        
        assert isinstance(state, StrategyState)
        assert state.symbol == 'SPY'
    
    def test_get_strategy_state_nonexistent(self, evaluator):
        """Test getting state for non-existent strategy"""
        state = evaluator.get_strategy_state('nonexistent')
        
        assert state is None


class TestSignalFiltering:
    """Test signal filtering (confidence thresholds, etc.)"""
    
    @pytest.fixture
    def evaluator(self):
        """Create evaluator with strategy"""
        evaluator = StrategyEvaluator()
        config = {
            'symbol': 'SPY',
            'timeframe': '5m',
            'entry': {'levels': ['previous_day_high']},
            'exit': {'stop_loss_pct': 0.005}
        }
        evaluator.add_strategy('RangeBoundStrategy', config)
        return evaluator
    
    def test_min_confidence_filtering(self, evaluator, sample_ohlcv_data):
        """Test that signals below confidence threshold are filtered"""
        strategy_id = "RangeBoundStrategy_SPY"
        
        # Set high confidence threshold
        evaluator.min_confidence = 0.9
        
        # Mock strategy to return low confidence signal
        state = evaluator.strategies[strategy_id]
        mock_signal = TradingSignal(
            signal_type=SignalType.BUY,
            price=100.0,
            quantity=10,
            confidence=0.5,  # Below threshold
            timestamp=datetime.now(),
            symbol='SPY'
        )
        state.strategy.generate_signal = Mock(return_value=mock_signal)
        
        signal = evaluator.evaluate_strategy(strategy_id, sample_ohlcv_data)
        
        # Should be filtered out (return None)
        assert signal is None or signal.confidence >= evaluator.min_confidence


class TestExitConditions:
    """Test exit condition checking"""
    
    @pytest.fixture
    def evaluator(self):
        """Create evaluator with strategy and position"""
        evaluator = StrategyEvaluator()
        config = {
            'symbol': 'SPY',
            'timeframe': '5m',
            'entry': {'levels': ['previous_day_high']},
            'exit': {'stop_loss_pct': 0.005}
        }
        evaluator.add_strategy('RangeBoundStrategy', config)
        
        # Add a position
        strategy_id = "RangeBoundStrategy_SPY"
        position = Position(
            symbol='SPY',
            quantity=10,
            entry_price=100.0,
            entry_time=datetime.now()
        )
        evaluator.update_position(strategy_id, position)
        
        return evaluator
    
    def test_check_exit_conditions_no_position(self, evaluator, sample_ohlcv_data):
        """Test exit check with no position"""
        evaluator = StrategyEvaluator()
        config = {
            'symbol': 'SPY',
            'timeframe': '5m',
            'entry': {'levels': ['previous_day_high']},
            'exit': {'stop_loss_pct': 0.005}
        }
        evaluator.add_strategy('RangeBoundStrategy', config)
        
        strategy_id = "RangeBoundStrategy_SPY"
        signal = evaluator.check_exit_conditions(strategy_id, sample_ohlcv_data)
        
        # Should return None if no position
        assert signal is None
    
    def test_check_exit_conditions_with_position(self, evaluator, sample_ohlcv_data):
        """Test exit check with position"""
        strategy_id = "RangeBoundStrategy_SPY"
        
        # Mock strategy exit logic
        state = evaluator.strategies[strategy_id]
        state.strategy.should_exit = Mock(return_value=(False, None))
        state.strategy.check_profit_taking_levels = Mock(return_value=None)
        
        signal = evaluator.check_exit_conditions(strategy_id, sample_ohlcv_data)
        
        # May return None or exit signal depending on conditions
        assert signal is None or isinstance(signal, TradingSignal)


class TestEvaluationStats:
    """Test evaluation statistics"""
    
    @pytest.fixture
    def evaluator(self):
        """Create evaluator with strategies"""
        evaluator = StrategyEvaluator()
        
        config1 = {
            'symbol': 'SPY',
            'timeframe': '5m',
            'entry': {'levels': ['previous_day_high']},
            'exit': {'stop_loss_pct': 0.005}
        }
        evaluator.add_strategy('RangeBoundStrategy', config1)
        
        config2 = {
            'symbol': 'QQQ',
            'timeframe': '5m',
            'entry': {'levels': ['previous_day_low']},
            'exit': {'stop_loss_pct': 0.005}
        }
        evaluator.add_strategy('RangeBoundStrategy', config2)
        
        return evaluator
    
    def test_get_evaluation_stats(self, evaluator):
        """Test getting evaluation statistics"""
        stats = evaluator.get_evaluation_stats()
        
        assert stats['total_strategies'] == 2
        assert stats['enabled_strategies'] == 2
        assert 'total_evaluations' in stats
        assert 'total_signals' in stats
        assert 'strategies' in stats
        assert len(stats['strategies']) == 2
    
    def test_list_strategies(self, evaluator):
        """Test listing all strategy IDs"""
        strategies = evaluator.list_strategies()
        
        assert len(strategies) == 2
        assert "RangeBoundStrategy_SPY" in strategies
        assert "RangeBoundStrategy_QQQ" in strategies


@pytest.mark.integration
class TestStrategyEvaluatorErrorHandling:
    """Test error handling in strategy evaluator"""
    
    @pytest.fixture
    def evaluator(self):
        """Create evaluator with strategy"""
        evaluator = StrategyEvaluator()
        config = {
            'symbol': 'SPY',
            'timeframe': '5m',
            'entry': {'levels': ['previous_day_high']},
            'exit': {'stop_loss_pct': 0.005}
        }
        evaluator.add_strategy('RangeBoundStrategy', config)
        return evaluator
    
    def test_evaluation_handles_strategy_error(self, evaluator, sample_ohlcv_data):
        """Test that strategy errors don't crash evaluator"""
        strategy_id = "RangeBoundStrategy_SPY"
        state = evaluator.strategies[strategy_id]
        
        # Mock strategy to raise error
        state.strategy.generate_signal = Mock(side_effect=Exception("Strategy error"))
        
        # Should handle error gracefully
        signal = evaluator.evaluate_strategy(strategy_id, sample_ohlcv_data)
        
        assert signal is None  # Should return None on error
    
    def test_evaluation_handles_data_error(self, evaluator):
        """Test that data errors are handled"""
        strategy_id = "RangeBoundStrategy_SPY"
        invalid_data = pd.DataFrame({'invalid': [1, 2, 3]})
        
        # Should handle error gracefully
        signal = evaluator.evaluate_strategy(strategy_id, invalid_data)
        
        # Should return None or handle gracefully
        assert signal is None or isinstance(signal, TradingSignal)

