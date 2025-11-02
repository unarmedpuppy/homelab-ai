"""
Level-Based Strategy Base Class
================================

Base class for strategies that trade around key price levels
(e.g., support/resistance, previous day high/low, pivot points).
"""

from abc import abstractmethod
from typing import Dict, List, Optional, Tuple
import pandas as pd
from datetime import datetime

from .base import BaseStrategy, TradingSignal, Position, ExitReason
from .levels import PriceLevel, LevelDetector, LevelType


class LevelBasedStrategy(BaseStrategy):
    """Base class for strategies that use price levels"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.level_detector = LevelDetector()
        
        # Level detection configuration
        self.level_config = config.get('entry', {}).get('levels', [])
        self.proximity_threshold = config.get('entry', {}).get('proximity_threshold', 0.001)  # 0.1%
    
    def identify_levels(self, data: pd.DataFrame) -> Dict[str, PriceLevel]:
        """
        Identify all relevant price levels for this strategy
        
        Args:
            data: Market data DataFrame
            
        Returns:
            Dictionary mapping level names to PriceLevel objects
        """
        levels = {}
        
        # Detect Previous Day High/Low if requested
        if 'previous_day_high' in self.level_config or 'previous_day_low' in self.level_config:
            pd_levels = self.level_detector.get_previous_day_levels(data, self.timeframe)
            levels.update(pd_levels)
        
        # Detect support/resistance if requested
        if 'support' in self.level_config or 'resistance' in self.level_config:
            sr_levels = self.level_detector.detect_support_resistance(data)
            for level in sr_levels:
                if level.level_type == LevelType.SUPPORT:
                    levels[f'support_{len([l for l in levels.values() if l.level_type == LevelType.SUPPORT])}'] = level
                elif level.level_type == LevelType.RESISTANCE:
                    levels[f'resistance_{len([l for l in levels.values() if l.level_type == LevelType.RESISTANCE])}'] = level
        
        # Calculate pivot points if requested
        if 'pivot_point' in self.level_config:
            pivot_levels = self.level_detector.calculate_pivot_points(data)
            levels.update(pivot_levels)
        
        return levels
    
    def get_entry_levels(self, data: pd.DataFrame) -> List[PriceLevel]:
        """
        Get levels that are valid for entry
        
        Args:
            data: Market data
            
        Returns:
            List of PriceLevel objects that can trigger entries
        """
        all_levels = self.identify_levels(data)
        
        # Filter to only entry-relevant levels
        entry_levels = []
        for level_name, level in all_levels.items():
            if any(ltype in level_name.lower() for ltype in self.level_config):
                entry_levels.append(level)
        
        return entry_levels
    
    def get_exit_levels(self, data: pd.DataFrame) -> List[PriceLevel]:
        """
        Get levels that are valid for exit (take profit targets)
        
        Args:
            data: Market data
            
        Returns:
            List of PriceLevel objects that can trigger exits
        """
        # Default: use same level detection
        # Override in subclasses for different exit level logic
        return self.get_entry_levels(data)
    
    def check_level_proximity(self, price: float, level: PriceLevel, 
                             threshold: Optional[float] = None) -> bool:
        """
        Check if price is near a level
        
        Args:
            price: Current price
            level: PriceLevel to check
            threshold: Proximity threshold (uses default if None)
            
        Returns:
            True if price is within threshold of level
        """
        if threshold is None:
            threshold = self.proximity_threshold
        
        return self.level_detector.check_level_proximity(price, level, threshold)
    
    def get_nearest_entry_level(self, price: float, data: pd.DataFrame,
                               threshold: Optional[float] = None) -> Optional[PriceLevel]:
        """
        Get the nearest entry level to current price
        
        Args:
            price: Current price
            data: Market data
            threshold: Maximum distance threshold
            
        Returns:
            Nearest PriceLevel or None
        """
        entry_levels = self.get_entry_levels(data)
        
        if threshold is None:
            threshold = self.proximity_threshold
        
        return self.level_detector.get_nearest_level(price, entry_levels, threshold)
    
    @abstractmethod
    def generate_signal(
        self, 
        data: pd.DataFrame, 
        position: Optional[Position] = None,
        sentiment = None
    ) -> TradingSignal:
        """
        Generate trading signal based on market data and price levels
        
        Must be implemented by subclasses.
        
        Args:
            data: Market data DataFrame
            position: Current position (if any)
            sentiment: Optional aggregated sentiment data
        """
        pass
    
    def calculate_stop_loss_from_level(self, entry_price: float, entry_level: PriceLevel,
                                      stop_loss_pct: float) -> float:
        """
        Calculate stop loss price based on entry level and percentage
        
        Args:
            entry_price: Entry price
            entry_level: Entry level
            stop_loss_pct: Stop loss as percentage (e.g., 0.005 for 0.5%)
            
        Returns:
            Stop loss price
        """
        # Stop loss is calculated from entry level
        # For long entries at support/PDL: stop below entry level
        # For long entries at resistance/PDH: stop below entry level (from level)
        
        if entry_level.level_type in [LevelType.SUPPORT, LevelType.PREVIOUS_DAY_LOW]:
            # Entry at support level - stop loss below the level
            stop_loss = entry_level.price * (1 - stop_loss_pct)
        else:
            # Entry at resistance level or other - stop loss below entry price
            stop_loss = entry_price * (1 - stop_loss_pct)
        
        return stop_loss
    
    def calculate_take_profit_opposite_level(self, entry_level: PriceLevel, 
                                            data: pd.DataFrame) -> Optional[PriceLevel]:
        """
        Get the opposite level for take profit target
        
        For example, if entry is at PDL, take profit is at PDH
        
        Args:
            entry_level: Level where entry occurred
            data: Market data
            
        Returns:
            Opposite PriceLevel for take profit, or None if not found
        """
        all_levels = self.identify_levels(data)
        
        # Find opposite level
        if entry_level.level_type == LevelType.PREVIOUS_DAY_LOW:
            return all_levels.get('previous_day_high')
        elif entry_level.level_type == LevelType.PREVIOUS_DAY_HIGH:
            return all_levels.get('previous_day_low')
        elif entry_level.level_type == LevelType.SUPPORT:
            # Find nearest resistance level
            resistances = [l for l in all_levels.values() if l.level_type == LevelType.RESISTANCE]
            if resistances:
                # Return highest resistance
                return max(resistances, key=lambda x: x.price)
        elif entry_level.level_type == LevelType.RESISTANCE:
            # Find nearest support level
            supports = [l for l in all_levels.values() if l.level_type == LevelType.SUPPORT]
            if supports:
                # Return lowest support
                return min(supports, key=lambda x: x.price)
        
        return None
    
    def should_exit(self, position: Position, data: pd.DataFrame) -> Tuple[bool, ExitReason]:
        """
        Check if position should be exited based on level-based exit conditions
        
        Args:
            position: Current position
            data: Market data
            
        Returns:
            Tuple of (should_exit: bool, reason: ExitReason)
        """
        if not position:
            return False, ExitReason.MANUAL
        
        current_price = float(data['close'].iloc[-1])
        
        # Check stop loss
        if position.stop_loss and current_price <= position.stop_loss:
            return True, ExitReason.STOP_LOSS
        
        # Check take profit level
        if position.take_profit and current_price >= position.take_profit:
            return True, ExitReason.TAKE_PROFIT
        
        # Check if opposite level reached (for range-bound strategies)
        if position.entry_level:
            opposite_level = self.calculate_take_profit_opposite_level(position.entry_level, data)
            
            if opposite_level:
                # Check proximity to opposite level
                exit_threshold = self.config.get('exit', {}).get('take_profit_threshold', 0.002)  # 0.2%
                
                if self.check_level_proximity(current_price, opposite_level, exit_threshold):
                    return True, ExitReason.LEVEL_REACHED
        
        return False, ExitReason.MANUAL

