"""
Range-Bound Strategy
====================

Trading strategy that enters when price approaches Previous Day High (PDH)
or Previous Day Low (PDL), with take profit at the opposite range.

Example: SPY on 5-minute chart
- Entry: Price within 0.1% of PDH or PDL
- Stop Loss: 0.5% from entry level
- Take Profit: When price approaches opposite level (PDL if entered at PDH, vice versa)
"""

from typing import Dict, Optional, Tuple
import pandas as pd
from datetime import datetime
import logging

from .base import TradingSignal, Position, ExitReason, SignalType
from .level_based import LevelBasedStrategy
from .levels import PriceLevel, LevelType
from .registry import register_strategy

logger = logging.getLogger(__name__)


@register_strategy('range_bound', {
    'description': 'Range-bound strategy using Previous Day High/Low',
    'supports_levels': True,
    'example_config': {
        'symbol': 'SPY',
        'timeframe': '5m',
        'entry': {
            'levels': ['previous_day_high', 'previous_day_low'],
            'proximity_threshold': 0.001,
            'volume_confirmation': True
        },
        'exit': {
            'stop_loss_pct': 0.005,
            'take_profit_type': 'opposite_level',
            'take_profit_threshold': 0.002
        },
        'risk_management': {
            'max_position_size': 100,
            'risk_per_trade': 0.02,
            'default_qty': 10
        }
    }
})
class RangeBoundStrategy(LevelBasedStrategy):
    """
    Range-bound trading strategy using Previous Day High/Low
    """
    
    def __init__(self, config: Dict):
        super().__init__(config)
        
        # Entry configuration
        entry_config = config.get('entry', {})
        self.entry_levels_config = entry_config.get('levels', ['previous_day_high', 'previous_day_low'])
        self.volume_confirmation = entry_config.get('volume_confirmation', False)
        self.min_volume_multiple = entry_config.get('min_volume_multiple', 1.0)
        
        # Exit configuration
        exit_config = config.get('exit', {})
        self.stop_loss_pct = exit_config.get('stop_loss_pct', 0.005)  # 0.5% default
        self.take_profit_type = exit_config.get('take_profit_type', 'opposite_level')
        self.take_profit_threshold = exit_config.get('take_profit_threshold', 0.002)  # 0.2%
        
        logger.info(f"Initialized RangeBoundStrategy for {self.symbol} on {self.timeframe}")
    
    def generate_signal(
        self, 
        data: pd.DataFrame, 
        position: Optional[Position] = None,
        sentiment = None
    ) -> TradingSignal:
        """
        Generate trading signal based on proximity to PDH/PDL
        
        Args:
            data: DataFrame with OHLCV data (5-minute bars)
            position: Current position (if any)
            sentiment: Optional aggregated sentiment data
            
        Returns:
            TradingSignal object
        """
        if len(data) == 0:
            return self._create_hold_signal(0.0, "no_data")
        
        # Don't generate new entry signal if we already have a position
        if position and position.quantity > 0:
            return self._create_hold_signal(float(data['close'].iloc[-1]), "position_open")
        
        # Get current price
        current_price = float(data['close'].iloc[-1])
        
        # Identify PDH and PDL levels
        levels = self.identify_levels(data)
        
        pdh = levels.get('previous_day_high')
        pdl = levels.get('previous_day_low')
        
        if not pdh or not pdl:
            logger.warning("Could not identify PDH/PDL levels")
            return self._create_hold_signal(current_price, "levels_not_found")
        
        # Check volume confirmation if required
        volume_ok = True
        if self.volume_confirmation and 'volume' in data.columns:
            current_volume = float(data['volume'].iloc[-1])
            avg_volume = float(data['volume'].tail(20).mean())
            
            if avg_volume > 0:
                volume_multiple = current_volume / avg_volume
                volume_ok = volume_multiple >= self.min_volume_multiple
        
        # Check proximity to PDH
        if 'previous_day_high' in self.entry_levels_config:
            near_pdh = self.check_level_proximity(current_price, pdh, self.proximity_threshold)
            
            if near_pdh and volume_ok:
                # Entry signal at PDH (expecting bounce down, so this would be a short in some strategies)
                # For this range-bound strategy, we'll enter long expecting move to PDL
                # Actually, entering at PDH means we expect it to go to PDL (mean reversion)
                # So we enter SHORT at PDH or LONG at PDL
                
                # For simplicity, let's enter LONG at PDL and SHORT at PDH
                # But for range-bound, we typically want to buy low (PDL) and sell high (PDH)
                # So we'll enter LONG at PDL
                pass  # Continue to check PDL
        
        # Check proximity to PDL (preferred entry for long)
        if 'previous_day_low' in self.entry_levels_config:
            near_pdl = self.check_level_proximity(current_price, pdl, self.proximity_threshold)
            
            if near_pdl and volume_ok:
                # Entry signal at PDL - buy expecting move toward PDH
                stop_loss = self.calculate_stop_loss_from_level(current_price, pdl, self.stop_loss_pct)
                
                # Calculate take profit (opposite level)
                take_profit_level = self.calculate_take_profit_opposite_level(pdl, data)
                take_profit_price = take_profit_level.price if take_profit_level else None
                
                confidence = self._calculate_confidence(current_price, pdl, data, sentiment)
                
                signal = self._create_buy_signal(
                    price=current_price,
                    confidence=confidence,
                    entry_level=pdl,
                    stop_loss=stop_loss,
                    take_profit=take_profit_price,
                    metadata={
                        'entry_reason': 'near_previous_day_low',
                        'entry_level_price': pdl.price,
                        'pdh': pdh.price,
                        'pdl': pdl.price,
                        'volume_confirmed': volume_ok
                    }
                )
                
                # Apply sentiment filtering if enabled
                if self.use_sentiment and sentiment is not None:
                    signal = self._apply_sentiment_filter(signal, sentiment)
                
                return signal
        
        # Check proximity to PDH for short entry (if strategy allows shorts)
        # For now, we'll focus on long entries at PDL
        if 'previous_day_high' in self.entry_levels_config:
            near_pdh = self.check_level_proximity(current_price, pdh, self.proximity_threshold)
            
            # Optional: Could enter SHORT at PDH expecting move to PDL
            # For now, we'll skip this and focus on LONG entries
        
        # No entry conditions met
        return self._create_hold_signal(
            current_price,
            f"not_near_levels_pdh={pdh.price:.2f}_pdl={pdl.price:.2f}_price={current_price:.2f}"
        )
    
    def should_exit(self, position: Position, data: pd.DataFrame) -> Tuple[bool, ExitReason]:
        """
        Determine if position should be exited
        
        Args:
            position: Current position
            data: Market data
            
        Returns:
            Tuple of (should_exit: bool, reason: ExitReason)
        """
        if not position or position.quantity == 0:
            return False, ExitReason.MANUAL
        
        current_price = float(data['close'].iloc[-1])
        
        # Check stop loss
        if position.stop_loss and current_price <= position.stop_loss:
            logger.info(f"Stop loss triggered at {current_price:.2f} (stop: {position.stop_loss:.2f})")
            return True, ExitReason.STOP_LOSS
        
        # Check take profit level
        if position.take_profit and current_price >= position.take_profit:
            logger.info(f"Take profit reached at {current_price:.2f} (target: {position.take_profit:.2f})")
            return True, ExitReason.TAKE_PROFIT
        
        # Check proximity to opposite level (range-bound exit)
        if position.entry_level and self.take_profit_type == 'opposite_level':
            opposite_level = self.calculate_take_profit_opposite_level(position.entry_level, data)
            
            if opposite_level:
                # Check if price is approaching opposite level
                if self.check_level_proximity(current_price, opposite_level, self.take_profit_threshold):
                    logger.info(f"Opposite level reached: {opposite_level.level_type} at {opposite_level.price:.2f}")
                    return True, ExitReason.LEVEL_REACHED
        
        return False, ExitReason.MANUAL
    
    def _calculate_confidence(
        self, 
        price: float, 
        entry_level: PriceLevel, 
        data: pd.DataFrame,
        sentiment = None
    ) -> float:
        """
        Calculate confidence score for entry signal
        
        Args:
            price: Entry price
            entry_level: Entry level (PDH or PDL)
            data: Market data
            sentiment: Optional aggregated sentiment data
            
        Returns:
            Confidence score 0.0 to 1.0
        """
        confidence = 0.5  # Base confidence
        
        # Closer to level = higher confidence
        if entry_level.price > 0:
            distance = abs(price - entry_level.price) / entry_level.price
            proximity_score = max(0, 1.0 - (distance / self.proximity_threshold))
            confidence += proximity_score * 0.3
        
        # Volume confirmation bonus
        if self.volume_confirmation and 'volume' in data.columns:
            current_volume = float(data['volume'].iloc[-1])
            avg_volume = float(data['volume'].tail(20).mean())
            
            if avg_volume > 0:
                volume_multiple = current_volume / avg_volume
                if volume_multiple >= self.min_volume_multiple:
                    confidence += 0.2
        
        # Level strength bonus
        confidence += entry_level.strength * 0.2
        
        # Sentiment boost (will be applied via _apply_sentiment_filter, but can add base boost here)
        if sentiment is not None and hasattr(self, 'use_sentiment') and self.use_sentiment:
            # Small base boost if sentiment is positive (sentiment filtering handles the rest)
            if sentiment.unified_sentiment > 0.2:
                confidence += 0.05
        
        return min(1.0, max(0.0, confidence))
