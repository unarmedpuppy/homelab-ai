"""
Unit Tests for LevelBasedStrategy
==================================

Tests for the LevelBasedStrategy base class.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import pandas as pd

from src.core.strategy.level_based import LevelBasedStrategy
from src.core.strategy.base import TradingSignal, SignalType
from src.core.strategy.levels import PriceLevel, LevelType


class TestLevelBasedStrategy(LevelBasedStrategy):
    """Concrete implementation for testing"""
    
    def generate_signal(self, data: pd.DataFrame) -> TradingSignal:
        """Generate a test signal"""
        current_price = float(data['close'].iloc[-1]) if len(data) > 0 else 100.0
        return self._create_hold_signal(current_price, "test")


class TestLevelBasedStrategyInitialization:
    """Test LevelBasedStrategy initialization"""
    
    def test_initialization_with_level_config(self):
        """Test initialization with level configuration"""
        config = {
            "symbol": "SPY",
            "timeframe": "5m",
            "entry": {
                "levels": ["previous_day_high", "previous_day_low"],
                "proximity_threshold": 0.001
            }
        }
        
        strategy = TestLevelBasedStrategy(config)
        
        assert strategy.symbol == "SPY"
        assert strategy.level_detector is not None
        assert strategy.proximity_threshold == 0.001
    
    def test_proximity_threshold_default(self):
        """Test default proximity threshold"""
        config = {
            "symbol": "SPY",
            "timeframe": "5m",
            "entry": {"levels": ["previous_day_high"]}
        }
        
        strategy = TestLevelBasedStrategy(config)
        
        assert strategy.proximity_threshold == 0.001  # 0.1% default


class TestLevelDetection:
    """Test level detection methods"""
    
    @pytest.fixture
    def strategy(self):
        """Create test strategy"""
        config = {
            "symbol": "SPY",
            "timeframe": "5m",
            "entry": {
                "levels": ["previous_day_high", "previous_day_low"],
                "proximity_threshold": 0.001
            }
        }
        return TestLevelBasedStrategy(config)
    
    def test_identify_levels_pdh_pdl(self, strategy, sample_ohlcv_data):
        """Test identifying Previous Day High/Low levels"""
        levels = strategy.identify_levels(sample_ohlcv_data)
        
        # Should detect PDH/PDL if data spans multiple days
        assert isinstance(levels, dict)
    
    def test_get_entry_levels(self, strategy, sample_ohlcv_data):
        """Test getting entry-relevant levels"""
        entry_levels = strategy.get_entry_levels(sample_ohlcv_data)
        
        assert isinstance(entry_levels, list)
        # All should be PriceLevel objects
        for level in entry_levels:
            assert isinstance(level, PriceLevel)
    
    def test_entry_levels_filtering(self, strategy, sample_price_levels):
        """Test that only configured levels are returned"""
        # Mock identify_levels to return known levels
        strategy.identify_levels = Mock(return_value={
            'previous_day_high': sample_price_levels[0],
            'previous_day_low': sample_price_levels[1]
        })
        
        data = pd.DataFrame({'close': [100.0]})
        entry_levels = strategy.get_entry_levels(data)
        
        # Should return both PDH and PDL since both are in config
        assert len(entry_levels) == 2


class TestLevelProximity:
    """Test level proximity checking"""
    
    @pytest.fixture
    def strategy(self):
        """Create test strategy"""
        config = {
            "symbol": "SPY",
            "timeframe": "5m",
            "entry": {
                "levels": ["previous_day_high"],
                "proximity_threshold": 0.001  # 0.1%
            }
        }
        return TestLevelBasedStrategy(config)
    
    @pytest.fixture
    def pdh_level(self):
        """Create PDH level"""
        return PriceLevel(
            price=100.0,
            level_type=LevelType.PREVIOUS_DAY_HIGH,
            strength=0.9,
            timeframe="1d",
            timestamp=datetime.now()
        )
    
    def test_price_near_level(self, strategy, pdh_level):
        """Test price within proximity threshold"""
        price = 100.09  # 0.09% away (within 0.1% threshold)
        
        is_near = strategy.level_detector.check_level_proximity(
            price, pdh_level, threshold=strategy.proximity_threshold
        )
        
        assert is_near is True
    
    def test_price_far_from_level(self, strategy, pdh_level):
        """Test price outside proximity threshold"""
        price = 101.0  # 1% away (outside 0.1% threshold)
        
        is_near = strategy.level_detector.check_level_proximity(
            price, pdh_level, threshold=strategy.proximity_threshold
        )
        
        assert is_near is False
    
    def test_price_at_exact_level(self, strategy, pdh_level):
        """Test price exactly at level"""
        price = 100.0  # Exactly at level
        
        is_near = strategy.level_detector.check_level_proximity(
            price, pdh_level, threshold=strategy.proximity_threshold
        )
        
        assert is_near is True
    
    def test_get_nearest_level(self, strategy, sample_price_levels):
        """Test getting nearest level to price"""
        price = 103.0  # Closer to PDH (105.0) than PDL (95.0)
        
        nearest = strategy.level_detector.get_nearest_level(
            price, sample_price_levels
        )
        
        assert nearest is not None
        assert nearest.price == 105.0  # PDH
    
    def test_get_nearest_level_with_threshold(self, strategy, sample_price_levels):
        """Test getting nearest level with distance threshold"""
        price = 200.0  # Very far from both levels
        
        nearest = strategy.level_detector.get_nearest_level(
            price, sample_price_levels, threshold=0.1  # 10% max distance
        )
        
        # Should return None since price is > 10% away from nearest level
        assert nearest is None


@pytest.mark.unit
class TestLevelBasedStrategyEdgeCases:
    """Test edge cases for level-based strategy"""
    
    @pytest.fixture
    def strategy(self):
        """Create test strategy"""
        return TestLevelBasedStrategy({
            "symbol": "SPY",
            "timeframe": "5m",
            "entry": {"levels": ["previous_day_high"]}
        })
    
    def test_identify_levels_with_empty_data(self, strategy):
        """Test level identification with empty data"""
        empty_data = pd.DataFrame()
        levels = strategy.identify_levels(empty_data)
        
        # Should return empty dict or handle gracefully
        assert isinstance(levels, dict)
    
    def test_identify_levels_with_single_bar(self, strategy):
        """Test level identification with single bar"""
        single_bar = pd.DataFrame({
            'open': [100.0],
            'high': [101.0],
            'low': [99.0],
            'close': [100.5],
            'volume': [100000]
        })
        
        levels = strategy.identify_levels(single_bar)
        
        # Should handle gracefully (may not detect levels)
        assert isinstance(levels, dict)
    
    def test_proximity_check_with_zero_price(self, strategy):
        """Test proximity check with zero price level"""
        level = PriceLevel(
            price=0.0,
            level_type=LevelType.SUPPORT,
            strength=0.5,
            timeframe="1d",
            timestamp=datetime.now()
        )
        
        is_near = strategy.level_detector.check_level_proximity(100.0, level)
        
        # Should return False for zero price
        assert is_near is False

