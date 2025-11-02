"""
End-to-End Test: Strategy Evaluation Workflow
==============================================

Tests complete strategy evaluation workflow including signal generation,
filtering, and multi-strategy coordination.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from src.core.evaluation.evaluator import StrategyEvaluator
from src.core.strategy.range_bound import RangeBoundStrategy
from src.core.strategy.level_based import LevelBasedStrategy
from src.core.strategy.base import SignalType
from src.data.providers.market_data import MarketData
from tests.factories.market_data import create_ohlcv_data


@pytest.fixture
def mock_data_provider():
    """Create mock data provider"""
    provider = Mock()
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5)
    
    historical_data = create_ohlcv_data(
        symbol="SPY",
        days=5,
        base_price=450.0,
        start_date=start_date
    )
    
    provider.get_historical_data = AsyncMock(return_value=historical_data)
    provider.get_quote = AsyncMock(return_value=MarketData(
        symbol="SPY",
        price=450.0,
        change=2.5,
        change_pct=0.56,
        volume=1000000,
        timestamp=datetime.now(),
        high=452.0,
        low=448.0,
        open=449.5,
        close=450.0
    ))
    
    return provider


@pytest.mark.asyncio
@pytest.mark.e2e
class TestStrategyEvaluationWorkflow:
    """Test complete strategy evaluation workflow"""
    
    async def test_single_strategy_evaluation(
        self,
        mock_data_provider
    ):
        """Test evaluating a single strategy"""
        
        # Create strategy
        strategy = RangeBoundStrategy(
            name="test_range_bound",
            config={
                "levels": ["previous_day_high", "previous_day_low"],
                "proximity_threshold": 0.005
            }
        )
        
        # Create evaluator
        evaluator = StrategyEvaluator(data_provider=mock_data_provider)
        evaluator.add_strategy(strategy)
        
        # Evaluate
        result = await evaluator.evaluate_strategy(
            strategy_name="test_range_bound",
            symbol="SPY",
            timeframe="5m"
        )
        
        # Verify result
        assert result is not None
        assert result.strategy_name == "test_range_bound"
        assert result.symbol == "SPY"
        
        # Signal may be HOLD if conditions not met
        if result.signal:
            assert result.signal.symbol == "SPY"
            assert result.signal.signal_type in [SignalType.BUY, SignalType.SELL, SignalType.HOLD]
    
    async def test_multi_strategy_evaluation(
        self,
        mock_data_provider
    ):
        """Test evaluating multiple strategies for same symbol"""
        
        # Create multiple strategies
        range_bound = RangeBoundStrategy(
            name="range_bound",
            config={"proximity_threshold": 0.005}
        )
        
        level_based = LevelBasedStrategy(
            name="level_based",
            config={"levels": ["previous_day_high", "previous_day_low"]}
        )
        
        # Create evaluator
        evaluator = StrategyEvaluator(data_provider=mock_data_provider)
        evaluator.add_strategy(range_bound)
        evaluator.add_strategy(level_based)
        
        # Evaluate both strategies
        results = []
        for strategy_name in ["range_bound", "level_based"]:
            result = await evaluator.evaluate_strategy(
                strategy_name=strategy_name,
                symbol="SPY",
                timeframe="5m"
            )
            if result:
                results.append(result)
        
        # Verify both strategies were evaluated
        assert len(results) == 2
        assert all(r.symbol == "SPY" for r in results)
        assert all(r.strategy_name in ["range_bound", "level_based"] for r in results)
    
    async def test_signal_filtering_by_confidence(
        self,
        mock_data_provider
    ):
        """Test filtering signals by confidence threshold"""
        
        strategy = RangeBoundStrategy(
            name="test_strategy",
            config={"proximity_threshold": 0.005}
        )
        
        evaluator = StrategyEvaluator(
            data_provider=mock_data_provider,
            min_confidence=0.7  # High confidence threshold
        )
        evaluator.add_strategy(strategy)
        
        # Evaluate
        result = await evaluator.evaluate_strategy(
            strategy_name="test_strategy",
            symbol="SPY",
            timeframe="5m"
        )
        
        # If signal generated, it should meet confidence threshold
        if result and result.signal and result.signal.signal_type != SignalType.HOLD:
            assert result.signal.confidence is None or result.signal.confidence >= 0.7
    
    async def test_strategy_evaluation_with_position(
        self,
        mock_data_provider
    ):
        """Test strategy evaluation when position exists"""
        
        strategy = RangeBoundStrategy(
            name="test_strategy",
            config={"proximity_threshold": 0.005}
        )
        
        evaluator = StrategyEvaluator(data_provider=mock_data_provider)
        evaluator.add_strategy(strategy)
        
        # Set existing position
        evaluator.update_position(
            symbol="SPY",
            quantity=10,
            entry_price=450.0
        )
        
        # Evaluate (should check exit conditions)
        result = await evaluator.evaluate_strategy(
            strategy_name="test_strategy",
            symbol="SPY",
            timeframe="5m"
        )
        
        # Should generate HOLD or exit signal
        if result and result.signal:
            assert result.signal.signal_type in [SignalType.HOLD, SignalType.SELL]
    
    async def test_evaluation_statistics_tracking(
        self,
        mock_data_provider
    ):
        """Test that evaluation statistics are tracked"""
        
        strategy = RangeBoundStrategy(
            name="test_strategy",
            config={"proximity_threshold": 0.005}
        )
        
        evaluator = StrategyEvaluator(data_provider=mock_data_provider)
        evaluator.add_strategy(strategy)
        
        # Evaluate multiple times
        for _ in range(5):
            await evaluator.evaluate_strategy(
                strategy_name="test_strategy",
                symbol="SPY",
                timeframe="5m"
            )
        
        # Get statistics
        stats = evaluator.get_evaluation_stats(strategy_name="test_strategy")
        
        # Verify statistics
        assert stats is not None
        assert stats["evaluation_count"] >= 5
    
    async def test_strategy_enable_disable(
        self,
        mock_data_provider
    ):
        """Test enabling/disabling strategies"""
        
        strategy = RangeBoundStrategy(
            name="test_strategy",
            config={"proximity_threshold": 0.005}
        )
        
        evaluator = StrategyEvaluator(data_provider=mock_data_provider)
        evaluator.add_strategy(strategy)
        
        # Disable strategy
        evaluator.disable_strategy("test_strategy")
        
        # Evaluate (should return None or indicate disabled)
        result = await evaluator.evaluate_strategy(
            strategy_name="test_strategy",
            symbol="SPY",
            timeframe="5m"
        )
        
        # Strategy should be disabled
        assert result is None or not result.enabled
        
        # Re-enable
        evaluator.enable_strategy("test_strategy")
        
        # Evaluate again (should work)
        result = await evaluator.evaluate_strategy(
            strategy_name="test_strategy",
            symbol="SPY",
            timeframe="5m"
        )
        
        assert result is not None


@pytest.mark.asyncio
@pytest.mark.e2e
class TestStrategyEvaluationErrorHandling:
    """Test error handling in strategy evaluation"""
    
    async def test_missing_data_handling(
        self,
        mock_data_provider
    ):
        """Test handling when data provider fails"""
        
        # Configure provider to fail
        mock_data_provider.get_historical_data = AsyncMock(side_effect=Exception("Data unavailable"))
        
        strategy = RangeBoundStrategy(
            name="test_strategy",
            config={"proximity_threshold": 0.005}
        )
        
        evaluator = StrategyEvaluator(data_provider=mock_data_provider)
        evaluator.add_strategy(strategy)
        
        # Evaluate (should handle error gracefully)
        result = await evaluator.evaluate_strategy(
            strategy_name="test_strategy",
            symbol="SPY",
            timeframe="5m"
        )
        
        # Should return None or error result
        assert result is None or result.error is not None
    
    async def test_invalid_strategy_name(
        self,
        mock_data_provider
    ):
        """Test handling of invalid strategy name"""
        
        evaluator = StrategyEvaluator(data_provider=mock_data_provider)
        
        # Try to evaluate non-existent strategy
        result = await evaluator.evaluate_strategy(
            strategy_name="non_existent_strategy",
            symbol="SPY",
            timeframe="5m"
        )
        
        # Should return None or error
        assert result is None or result.error is not None
    
    async def test_strategy_exception_handling(
        self,
        mock_data_provider
    ):
        """Test handling when strategy raises exception"""
        
        # Create strategy that will fail
        strategy = Mock()
        strategy.name = "failing_strategy"
        strategy.generate_signal = Mock(side_effect=Exception("Strategy error"))
        
        evaluator = StrategyEvaluator(data_provider=mock_data_provider)
        evaluator.add_strategy(strategy)
        
        # Evaluate (should handle exception)
        result = await evaluator.evaluate_strategy(
            strategy_name="failing_strategy",
            symbol="SPY",
            timeframe="5m"
        )
        
        # Should return None or error result
        assert result is None or result.error is not None

