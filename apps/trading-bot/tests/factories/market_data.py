"""
Market Data Factory Functions
==============================

Factory functions for creating market data for testing.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List

from src.core.strategy.levels import PriceLevel, LevelType


def create_ohlcv_data(
    start_date: str = '2024-01-01',
    periods: int = 100,
    freq: str = '5min',
    base_price: float = 100.0,
    volatility: float = 0.01,
    trend: float = 0.0
) -> pd.DataFrame:
    """
    Create sample OHLCV data for testing
    
    Args:
        start_date: Start date string
        periods: Number of periods
        freq: Frequency (e.g., '5min', '1h', '1d')
        base_price: Starting price
        volatility: Price volatility (std dev)
        trend: Price trend (mean return per period)
    
    Returns:
        DataFrame with OHLCV columns
    """
    dates = pd.date_range(start=start_date, periods=periods, freq=freq)
    
    # Generate realistic price data with trend
    np.random.seed(42)
    returns = np.random.randn(periods) * volatility + trend
    prices = base_price * (1 + returns).cumprod()
    
    data = pd.DataFrame({
        'open': prices * (1 + np.random.randn(periods) * 0.002),
        'high': prices * (1 + abs(np.random.randn(periods)) * 0.005),
        'low': prices * (1 - abs(np.random.randn(periods)) * 0.005),
        'close': prices,
        'volume': np.random.randint(100000, 1000000, periods)
    }, index=dates)
    
    # Ensure high >= close >= low and high >= open >= low
    data['high'] = data[['open', 'high', 'close', 'low']].max(axis=1)
    data['low'] = data[['open', 'high', 'close', 'low']].min(axis=1)
    
    return data


def create_price_level(
    price: float = 100.0,
    level_type: LevelType = LevelType.PREVIOUS_DAY_HIGH,
    strength: float = 0.9,
    timeframe: str = "1d",
    timestamp: Optional[datetime] = None,
    touches: int = 0,
    metadata: Optional[dict] = None
) -> PriceLevel:
    """
    Create a PriceLevel for testing
    
    Args:
        price: Level price
        level_type: Type of level
        strength: Level strength (0-1)
        timeframe: Timeframe
        timestamp: Level timestamp (defaults to now)
        touches: Number of touches
        metadata: Additional metadata
    
    Returns:
        PriceLevel instance
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    if metadata is None:
        metadata = {}
    
    return PriceLevel(
        price=price,
        level_type=level_type,
        strength=strength,
        timeframe=timeframe,
        timestamp=timestamp,
        touches=touches,
        metadata=metadata
    )


def create_price_levels(
    count: int = 2,
    base_price: float = 100.0,
    spacing: float = 5.0
) -> List[PriceLevel]:
    """
    Create a list of PriceLevels for testing
    
    Args:
        count: Number of levels to create
        base_price: Base price for levels
        spacing: Price spacing between levels
    
    Returns:
        List of PriceLevel instances
    """
    levels = []
    level_types = [LevelType.PREVIOUS_DAY_HIGH, LevelType.PREVIOUS_DAY_LOW]
    
    for i in range(count):
        level_type = level_types[i % len(level_types)]
        price = base_price + (i * spacing * (1 if i % 2 == 0 else -1))
        
        levels.append(create_price_level(
            price=price,
            level_type=level_type,
            strength=0.9 - (i * 0.1)
        ))
    
    return levels

