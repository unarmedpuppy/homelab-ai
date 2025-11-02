"""
Price Level Detection
=====================

Utilities for detecting and managing key price levels such as:
- Previous Day High/Low
- Support and Resistance levels
- Pivot Points
- Fibonacci levels
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class LevelType(Enum):
    """Types of price levels"""
    SUPPORT = "support"
    RESISTANCE = "resistance"
    PREVIOUS_DAY_HIGH = "previous_day_high"
    PREVIOUS_DAY_LOW = "previous_day_low"
    PIVOT_POINT = "pivot_point"
    FIBONACCI_RETRACEMENT = "fibonacci_retracement"
    FIBONACCI_EXTENSION = "fibonacci_extension"
    VOLUME_PROFILE = "volume_profile"

@dataclass
class PriceLevel:
    """Represents a significant price level"""
    price: float
    level_type: LevelType
    strength: float  # 0.0 to 1.0 - confidence/importance of level
    timeframe: str  # e.g., "5m", "1h", "1d"
    timestamp: datetime  # When this level was calculated
    touches: int = 0  # Number of times price has touched this level
    metadata: Optional[Dict] = None  # Additional level-specific data
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class LevelDetector:
    """Detects and manages price levels"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_previous_day_levels(self, df: pd.DataFrame, 
                                timeframe: Optional[str] = None) -> Dict[str, PriceLevel]:
        """
        Get Previous Day High (PDH) and Previous Day Low (PDL)
        
        Args:
            df: DataFrame with datetime index and OHLCV columns
            timeframe: Optional timeframe identifier
            
        Returns:
            Dictionary with 'previous_day_high' and 'previous_day_low' PriceLevels
        """
        if len(df) == 0:
            return {}
        
        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        # Get today's date
        last_timestamp = df.index[-1]
        today = last_timestamp.date()
        
        # Get previous trading day
        previous_day = today - timedelta(days=1)
        
        # Handle weekends - find most recent weekday
        while previous_day.weekday() >= 5:  # Saturday = 5, Sunday = 6
            previous_day -= timedelta(days=1)
        
        # Filter data for previous trading day
        previous_day_start = pd.Timestamp.combine(previous_day, pd.Timestamp.min.time())
        previous_day_end = pd.Timestamp.combine(previous_day, pd.Timestamp.max.time())
        
        previous_day_data = df[
            (df.index >= previous_day_start) & 
            (df.index <= previous_day_end)
        ]
        
        if len(previous_day_data) == 0:
            # If no data for previous day, look back further
            # Get the most recent complete day before today
            unique_dates = df.index.normalize().unique()
            if len(unique_dates) >= 2:
                previous_date = unique_dates[-2]
                previous_day_data = df[df.index.normalize() == previous_date]
        
        if len(previous_day_data) == 0:
            self.logger.warning("No previous day data found for PDH/PDL calculation")
            return {}
        
        # Calculate PDH and PDL
        pdh_price = float(previous_day_data['high'].max())
        pdl_price = float(previous_day_data['low'].min())
        
        # Find when these levels occurred
        pdh_idx = previous_day_data['high'].idxmax()
        pdl_idx = previous_day_data['low'].idxmin()
        
        pdh = PriceLevel(
            price=pdh_price,
            level_type=LevelType.PREVIOUS_DAY_HIGH,
            strength=0.9,  # High strength - daily level
            timeframe=timeframe or "1d",
            timestamp=pdh_idx if isinstance(pdh_idx, datetime) else datetime.now(),
            touches=0,
            metadata={
                'date': previous_day.isoformat(),
                'time': pdh_idx.isoformat() if hasattr(pdh_idx, 'isoformat') else str(pdh_idx)
            }
        )
        
        pdl = PriceLevel(
            price=pdl_price,
            level_type=LevelType.PREVIOUS_DAY_LOW,
            strength=0.9,  # High strength - daily level
            timeframe=timeframe or "1d",
            timestamp=pdl_idx if isinstance(pdl_idx, datetime) else datetime.now(),
            touches=0,
            metadata={
                'date': previous_day.isoformat(),
                'time': pdl_idx.isoformat() if hasattr(pdl_idx, 'isoformat') else str(pdl_idx)
            }
        )
        
        return {
            'previous_day_high': pdh,
            'previous_day_low': pdl
        }
    
    def detect_support_resistance(self, df: pd.DataFrame, 
                                  lookback: int = 20,
                                  tolerance: float = 0.002,  # 0.2% tolerance
                                  min_touches: int = 2) -> List[PriceLevel]:
        """
        Detect support and resistance levels based on price reversals
        
        Args:
            df: DataFrame with OHLCV data
            lookback: Number of periods to look back
            tolerance: Price tolerance for grouping similar levels (%)
            min_touches: Minimum number of touches to consider a level valid
            
        Returns:
            List of PriceLevel objects (support and resistance)
        """
        if len(df) < lookback:
            return []
        
        # Get recent data
        recent_data = df.tail(lookback).copy()
        
        # Find local highs (potential resistance) and lows (potential support)
        highs = recent_data['high'].values
        lows = recent_data['low'].values
        
        # Detect local maxima and minima
        from scipy.signal import argrelextrema
        
        try:
            # Find local highs (resistance candidates)
            high_indices = argrelextrema(highs, np.greater, order=2)[0]
            # Find local lows (support candidates)
            low_indices = argrelextrema(lows, np.less, order=2)[0]
        except ImportError:
            # Fallback if scipy not available
            self.logger.warning("scipy not available, using simple local extrema detection")
            high_indices = []
            low_indices = []
            
            for i in range(1, len(highs) - 1):
                if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                    high_indices.append(i)
                if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                    low_indices.append(i)
        
        levels = []
        
        # Group similar price levels and count touches
        def group_levels(price_values, indices, level_type: LevelType):
            if len(price_values) == 0:
                return []
            
            grouped = {}
            
            for idx in indices:
                price = price_values[idx]
                
                # Find existing group within tolerance
                matched = False
                for key_price in grouped.keys():
                    if abs(price - key_price) / key_price <= tolerance:
                        grouped[key_price].append(idx)
                        matched = True
                        break
                
                if not matched:
                    grouped[price] = [idx]
            
            # Create PriceLevel objects for groups with enough touches
            result = []
            for price, touches_list in grouped.items():
                if len(touches_list) >= min_touches:
                    strength = min(1.0, len(touches_list) / 5.0)  # Max strength at 5+ touches
                    
                    level = PriceLevel(
                        price=float(price),
                        level_type=level_type,
                        strength=strength,
                        timeframe="unknown",
                        timestamp=recent_data.index[touches_list[-1]],
                        touches=len(touches_list),
                        metadata={'detection_method': 'local_extrema', 'touches_indices': touches_list}
                    )
                    result.append(level)
            
            return result
        
        # Detect resistance (local highs)
        resistance_levels = group_levels(highs, high_indices, LevelType.RESISTANCE)
        levels.extend(resistance_levels)
        
        # Detect support (local lows)
        support_levels = group_levels(lows, low_indices, LevelType.SUPPORT)
        levels.extend(support_levels)
        
        # Sort by strength (descending)
        levels.sort(key=lambda x: x.strength, reverse=True)
        
        return levels
    
    def calculate_pivot_points(self, df: pd.DataFrame) -> Dict[str, PriceLevel]:
        """
        Calculate standard pivot points (PP, R1, R2, S1, S2)
        
        Uses previous day's high, low, and close
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary with pivot point levels
        """
        if len(df) == 0:
            return {}
        
        # Get previous day data
        pd_levels = self.get_previous_day_levels(df)
        
        if not pd_levels:
            # Fall back to last available data
            prev_high = float(df['high'].iloc[-1])
            prev_low = float(df['low'].iloc[-1])
            prev_close = float(df['close'].iloc[-1])
        else:
            prev_high = pd_levels['previous_day_high'].price
            prev_low = pd_levels['previous_day_low'].price
            
            # Get previous day close
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
            
            last_timestamp = df.index[-1]
            today = last_timestamp.date()
            previous_day = today - timedelta(days=1)
            
            while previous_day.weekday() >= 5:
                previous_day -= timedelta(days=1)
            
            previous_day_start = pd.Timestamp.combine(previous_day, pd.Timestamp.min.time())
            previous_day_end = pd.Timestamp.combine(previous_day, pd.Timestamp.max.time())
            
            previous_day_data = df[
                (df.index >= previous_day_start) & 
                (df.index <= previous_day_end)
            ]
            
            if len(previous_day_data) > 0:
                prev_close = float(previous_day_data['close'].iloc[-1])
            else:
                prev_close = float(df['close'].iloc[-1])
        
        # Calculate pivot point
        pp = (prev_high + prev_low + prev_close) / 3.0
        
        # Calculate resistance levels
        r1 = 2 * pp - prev_low
        r2 = pp + (prev_high - prev_low)
        
        # Calculate support levels
        s1 = 2 * pp - prev_high
        s2 = pp - (prev_high - prev_low)
        
        timestamp = datetime.now()
        
        pivot_levels = {
            'pivot_point': PriceLevel(
                price=pp,
                level_type=LevelType.PIVOT_POINT,
                strength=0.8,
                timeframe="1d",
                timestamp=timestamp,
                metadata={'calculation': 'standard', 'prev_high': prev_high, 'prev_low': prev_low, 'prev_close': prev_close}
            ),
            'resistance_1': PriceLevel(
                price=r1,
                level_type=LevelType.RESISTANCE,
                strength=0.7,
                timeframe="1d",
                timestamp=timestamp,
                metadata={'level': 'R1'}
            ),
            'resistance_2': PriceLevel(
                price=r2,
                level_type=LevelType.RESISTANCE,
                strength=0.6,
                timeframe="1d",
                timestamp=timestamp,
                metadata={'level': 'R2'}
            ),
            'support_1': PriceLevel(
                price=s1,
                level_type=LevelType.SUPPORT,
                strength=0.7,
                timeframe="1d",
                timestamp=timestamp,
                metadata={'level': 'S1'}
            ),
            'support_2': PriceLevel(
                price=s2,
                level_type=LevelType.SUPPORT,
                strength=0.6,
                timeframe="1d",
                timestamp=timestamp,
                metadata={'level': 'S2'}
            ),
        }
        
        return pivot_levels
    
    def check_level_proximity(self, price: float, level: PriceLevel, 
                             threshold: float = 0.001) -> bool:
        """
        Check if price is within threshold of a level
        
        Args:
            price: Current price
            level: PriceLevel to check against
            threshold: Proximity threshold as decimal (0.001 = 0.1%)
            
        Returns:
            True if price is within threshold of level
        """
        if level.price == 0:
            return False
        
        distance = abs(price - level.price) / level.price
        return distance <= threshold
    
    def get_nearest_level(self, price: float, levels: List[PriceLevel],
                         threshold: Optional[float] = None) -> Optional[PriceLevel]:
        """
        Get the nearest price level to the current price
        
        Args:
            price: Current price
            levels: List of PriceLevel objects
            threshold: Optional maximum distance threshold
            
        Returns:
            Nearest PriceLevel or None if no level within threshold
        """
        if not levels:
            return None
        
        nearest = None
        min_distance = float('inf')
        
        for level in levels:
            if level.price == 0:
                continue
            
            distance = abs(price - level.price) / level.price
            
            if threshold and distance > threshold:
                continue
            
            if distance < min_distance:
                min_distance = distance
                nearest = level
        
        return nearest

