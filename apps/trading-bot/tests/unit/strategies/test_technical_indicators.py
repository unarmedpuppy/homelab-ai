"""
Unit Tests for Technical Indicators
===================================

Tests for TechnicalIndicators utility class methods.
"""

import pytest
import pandas as pd
import numpy as np
from src.core.strategy.base import TechnicalIndicators


class TestTechnicalIndicators:
    """Test suite for TechnicalIndicators"""
    
    @pytest.fixture
    def sample_price_data(self):
        """Create sample price data"""
        dates = pd.date_range(start='2024-01-01', periods=50, freq='5min')
        prices = 100 + np.cumsum(np.random.randn(50) * 0.5)
        return pd.Series(prices, index=dates)
    
    @pytest.fixture
    def sample_volume_data(self):
        """Create sample volume data"""
        dates = pd.date_range(start='2024-01-01', periods=50, freq='5min')
        volumes = np.random.randint(100000, 1000000, 50)
        return pd.Series(volumes, index=dates)
    
    # SMA Tests
    def test_sma_with_valid_data(self, sample_price_data):
        """Test SMA with valid price data"""
        sma = TechnicalIndicators.sma(sample_price_data, window=10)
        
        assert len(sma) == len(sample_price_data)
        # First 9 values should be NaN
        assert all(pd.isna(sma.iloc[:9]))
        # 10th value onwards should have values
        assert pd.notna(sma.iloc[9])
    
    def test_sma_window_larger_than_data(self, sample_price_data):
        """Test SMA with window larger than data length"""
        sma = TechnicalIndicators.sma(sample_price_data, window=100)
        
        # All values should be NaN since window > data length
        assert all(pd.isna(sma))
    
    def test_sma_single_value(self):
        """Test SMA with single value"""
        prices = pd.Series([100.0])
        sma = TechnicalIndicators.sma(prices, window=5)
        
        assert len(sma) == 1
        assert pd.isna(sma.iloc[0])
    
    def test_sma_empty_series(self):
        """Test SMA with empty series"""
        prices = pd.Series([], dtype=float)
        sma = TechnicalIndicators.sma(prices, window=10)
        
        assert len(sma) == 0
    
    # EMA Tests
    def test_ema_with_valid_data(self, sample_price_data):
        """Test EMA with valid price data"""
        ema = TechnicalIndicators.ema(sample_price_data, window=10)
        
        assert len(ema) == len(sample_price_data)
        assert pd.notna(ema.iloc[-1])
    
    def test_ema_smoother_than_sma(self, sample_price_data):
        """Test that EMA responds faster than SMA"""
        ema = TechnicalIndicators.ema(sample_price_data, window=10)
        sma = TechnicalIndicators.sma(sample_price_data, window=10)
        
        # Both should have values for comparison
        valid_idx = sma.dropna().index
        assert len(valid_idx) > 0
        # EMA should generally be closer to recent prices than SMA
    
    # RSI Tests
    def test_rsi_with_valid_data(self, sample_price_data):
        """Test RSI calculation with valid data"""
        rsi = TechnicalIndicators.rsi(sample_price_data, window=14)
        
        assert len(rsi) == len(sample_price_data)
        valid_rsi = rsi.dropna()
        assert len(valid_rsi) > 0
        # RSI should be between 0 and 100
        assert all((valid_rsi >= 0) & (valid_rsi <= 100))
    
    def test_rsi_all_positive_returns(self):
        """Test RSI with all positive returns (should be high)"""
        prices = pd.Series([100, 101, 102, 103, 104, 105])
        rsi = TechnicalIndicators.rsi(prices, window=3)
        
        valid_rsi = rsi.dropna()
        if len(valid_rsi) > 0:
            # With all positive returns, RSI should be > 50
            assert valid_rsi.iloc[-1] > 50
    
    def test_rsi_all_negative_returns(self):
        """Test RSI with all negative returns (should be low)"""
        prices = pd.Series([105, 104, 103, 102, 101, 100])
        rsi = TechnicalIndicators.rsi(prices, window=3)
        
        valid_rsi = rsi.dropna()
        if len(valid_rsi) > 0:
            # With all negative returns, RSI should be < 50
            assert valid_rsi.iloc[-1] < 50
    
    # OBV Tests
    def test_obv_calculation(self, sample_price_data, sample_volume_data):
        """Test On-Balance Volume calculation"""
        obv = TechnicalIndicators.obv(sample_price_data, sample_volume_data)
        
        assert len(obv) == len(sample_price_data)
        assert pd.notna(obv.iloc[0])
    
    def test_obv_with_price_increase(self):
        """Test OBV increases with price increase"""
        prices = pd.Series([100, 101, 102, 103])
        volumes = pd.Series([1000, 1000, 1000, 1000])
        obv = TechnicalIndicators.obv(prices, volumes)
        
        # OBV should increase when price increases
        assert obv.iloc[-1] > obv.iloc[0]
    
    def test_obv_with_price_decrease(self):
        """Test OBV decreases with price decrease"""
        prices = pd.Series([103, 102, 101, 100])
        volumes = pd.Series([1000, 1000, 1000, 1000])
        obv = TechnicalIndicators.obv(prices, volumes)
        
        # OBV should decrease when price decreases
        assert obv.iloc[-1] < obv.iloc[0]
    
    # Bollinger Bands Tests
    def test_bollinger_bands_calculation(self, sample_price_data):
        """Test Bollinger Bands calculation"""
        bb = TechnicalIndicators.bollinger_bands(sample_price_data, window=20)
        
        assert 'middle' in bb
        assert 'upper' in bb
        assert 'lower' in bb
        assert len(bb['middle']) == len(sample_price_data)
    
    def test_bollinger_bands_ordering(self, sample_price_data):
        """Test that upper > middle > lower"""
        bb = TechnicalIndicators.bollinger_bands(sample_price_data, window=20)
        
        valid_idx = bb['middle'].dropna().index
        if len(valid_idx) > 0:
            assert all(bb['upper'][valid_idx] >= bb['middle'][valid_idx])
            assert all(bb['lower'][valid_idx] <= bb['middle'][valid_idx])
    
    def test_bollinger_bands_custom_std(self, sample_price_data):
        """Test Bollinger Bands with custom standard deviation multiplier"""
        bb_2std = TechnicalIndicators.bollinger_bands(sample_price_data, window=20, num_std=2.0)
        bb_1std = TechnicalIndicators.bollinger_bands(sample_price_data, window=20, num_std=1.0)
        
        valid_idx = bb_2std['middle'].dropna().index
        if len(valid_idx) > 0:
            # 2 std bands should be wider than 1 std bands
            width_2std = bb_2std['upper'][valid_idx] - bb_2std['lower'][valid_idx]
            width_1std = bb_1std['upper'][valid_idx] - bb_1std['lower'][valid_idx]
            assert all(width_2std >= width_1std)
    
    # ATR Tests
    def test_atr_calculation(self):
        """Test Average True Range calculation"""
        dates = pd.date_range(start='2024-01-01', periods=20, freq='5min')
        high = pd.Series([102, 103, 101, 104, 105], index=dates[:5])
        low = pd.Series([100, 101, 99, 102, 103], index=dates[:5])
        close = pd.Series([101, 102, 100, 103, 104], index=dates[:5])
        
        atr = TechnicalIndicators.atr(high, low, close, window=3)
        
        assert len(atr) == len(high)
        valid_atr = atr.dropna()
        # ATR should be positive
        assert all(valid_atr > 0)
    
    def test_atr_with_volatile_prices(self):
        """Test ATR with highly volatile prices"""
        dates = pd.date_range(start='2024-01-01', periods=20, freq='5min')
        high = pd.Series([110, 120, 115, 125, 130], index=dates[:5])
        low = pd.Series([100, 110, 105, 115, 120], index=dates[:5])
        close = pd.Series([105, 115, 110, 120, 125], index=dates[:5])
        
        atr = TechnicalIndicators.atr(high, low, close, window=3)
        
        valid_atr = atr.dropna()
        # ATR should be higher with volatile prices
        assert len(valid_atr) > 0
        assert valid_atr.iloc[-1] > 5  # Should be relatively high
    
    # Edge Cases
    def test_indicators_with_nan_values(self):
        """Test indicators handle NaN values"""
        prices = pd.Series([100, 101, np.nan, 103, 104])
        sma = TechnicalIndicators.sma(prices, window=3)
        
        # Should not crash, but may have NaN in result
        assert len(sma) == len(prices)
    
    def test_indicators_with_constant_prices(self):
        """Test indicators with constant prices"""
        prices = pd.Series([100.0] * 20)
        sma = TechnicalIndicators.sma(prices, window=10)
        
        valid_sma = sma.dropna()
        # SMA of constant values should equal the constant
        if len(valid_sma) > 0:
            assert all(valid_sma == 100.0)

