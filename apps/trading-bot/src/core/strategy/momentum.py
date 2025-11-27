"""
Momentum Strategy
================

Trading strategy that identifies and trades strong price momentum trends.
Uses RSI, MACD, Rate of Change (ROC), and volume to detect momentum.
"""

from typing import Dict, Optional, Tuple, Any, TYPE_CHECKING
import pandas as pd
import numpy as np
from datetime import datetime
import logging

from .base import BaseStrategy, TradingSignal, Position, SignalType, ExitReason
from .registry import register_strategy

if TYPE_CHECKING:
    from ...data.providers.sentiment.aggregator import AggregatedSentiment

logger = logging.getLogger(__name__)


@register_strategy('momentum', {
    'description': 'Momentum trading strategy using RSI, MACD, ROC, and volume',
    'supports_levels': False,
    'example_config': {
        'symbol': 'SPY',
        'timeframe': '5m',
        'momentum': {
            'rsi_period': 14,
            'rsi_overbought': 70,
            'rsi_oversold': 30,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'roc_period': 10,
            'min_volume_increase': 1.2
        },
        'stop_loss': {
            'pct': 0.02
        },
        'take_profit': {
            'pct': 0.05
        }
    }
})
class MomentumStrategy(BaseStrategy):
    """
    Momentum trading strategy
    
    Identifies strong price momentum using:
    - RSI: Relative Strength Index (overbought/oversold with momentum)
    - MACD: Moving Average Convergence Divergence (trend direction)
    - ROC: Rate of Change (price momentum)
    - Volume: Confirms momentum with increased volume
    
    Entry Signals:
    - Strong uptrend: RSI > overbought threshold, MACD bullish, increasing volume
    - Strong downtrend: RSI < oversold threshold, MACD bearish, increasing volume
    
    Exit Signals:
    - Momentum exhaustion (RSI divergence)
    - Trend reversal (MACD crossover opposite direction)
    - Stop loss / take profit
    """
    
    def __init__(self, config: Dict):
        super().__init__(config)
        
        # Momentum configuration
        momentum_config = config.get('momentum', {})
        
        # RSI configuration
        self.rsi_period = momentum_config.get('rsi_period', 14)
        self.rsi_overbought = momentum_config.get('rsi_overbought', 70)
        self.rsi_oversold = momentum_config.get('rsi_oversold', 30)
        self.rsi_momentum_threshold = momentum_config.get('rsi_momentum_threshold', 65)  # Minimum for strong momentum
        
        # MACD configuration
        self.macd_fast = momentum_config.get('macd_fast', 12)
        self.macd_slow = momentum_config.get('macd_slow', 26)
        self.macd_signal = momentum_config.get('macd_signal', 9)
        
        # ROC (Rate of Change) configuration
        self.roc_period = momentum_config.get('roc_period', 10)
        self.min_roc = momentum_config.get('min_roc', 0.02)  # Minimum 2% change
        
        # Volume configuration
        self.min_volume_increase = momentum_config.get('min_volume_increase', 1.2)  # 20% increase
        self.volume_lookback = momentum_config.get('volume_lookback', 20)  # Days for average volume
        
        # Risk management
        self.stop_loss_pct = config.get('stop_loss', {}).get('pct', 0.02)  # 2%
        self.take_profit_pct = config.get('take_profit', {}).get('pct', 0.05)  # 5%
        
        logger.info(
            f"MomentumStrategy initialized for {self.symbol}: "
            f"RSI({self.rsi_period}), MACD({self.macd_fast},{self.macd_slow},{self.macd_signal}), "
            f"ROC({self.roc_period})"
        )
    
    def _calculate_macd(self, prices: pd.Series) -> Dict[str, pd.Series]:
        """
        Calculate MACD indicator
        
        Args:
            prices: Price series
            
        Returns:
            Dictionary with 'macd', 'signal', 'histogram' series
        """
        ema_fast = self.indicators.ema(prices, self.macd_fast)
        ema_slow = self.indicators.ema(prices, self.macd_slow)
        macd_line = ema_fast - ema_slow
        signal_line = self.indicators.ema(macd_line, self.macd_signal)
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def _calculate_roc(self, prices: pd.Series) -> pd.Series:
        """
        Calculate Rate of Change (ROC)
        
        Args:
            prices: Price series
            
        Returns:
            ROC series (percentage change)
        """
        roc = ((prices - prices.shift(self.roc_period)) / prices.shift(self.roc_period)) * 100
        return roc
    
    def _check_volume_confirmation(self, data: pd.DataFrame) -> bool:
        """
        Check if volume confirms momentum
        
        Args:
            data: Market data DataFrame
            
        Returns:
            True if volume is above threshold
        """
        if 'volume' not in data.columns:
            return True  # Skip volume check if not available
        
        current_volume = data['volume'].iloc[-1]
        avg_volume = data['volume'].tail(self.volume_lookback).mean()
        
        if avg_volume == 0:
            return True  # Skip if no volume data
        
        volume_ratio = current_volume / avg_volume
        return volume_ratio >= self.min_volume_increase
    
    def _detect_momentum_direction(self, data: pd.DataFrame) -> Tuple[Optional[SignalType], float]:
        """
        Detect momentum direction and strength
        
        Args:
            data: Market data DataFrame
            
        Returns:
            Tuple of (signal_type, confidence)
        """
        if len(data) < max(self.macd_slow, self.rsi_period, self.roc_period) + 10:
            return None, 0.0
        
        close_prices = data['close']
        
        # Calculate indicators
        rsi = self.indicators.rsi(close_prices, self.rsi_period)
        macd_data = self._calculate_macd(close_prices)
        roc = self._calculate_roc(close_prices)
        
        # Get latest values
        current_rsi = rsi.iloc[-1]
        current_macd = macd_data['macd'].iloc[-1]
        current_signal = macd_data['signal'].iloc[-1]
        current_histogram = macd_data['histogram'].iloc[-1]
        prev_histogram = macd_data['histogram'].iloc[-2] if len(macd_data['histogram']) > 1 else 0
        current_roc = roc.iloc[-1]
        
        # Check volume confirmation
        volume_confirmed = self._check_volume_confirmation(data)
        
        # Bullish momentum signals
        bullish_signals = 0
        bullish_confidence = 0.0
        
        # RSI momentum (strong but not overbought)
        if current_rsi > self.rsi_momentum_threshold and current_rsi < 85:
            bullish_signals += 1
            bullish_confidence += 0.3
        elif current_rsi >= 70 and current_rsi < 80:  # Overbought but not extreme
            bullish_signals += 1
            bullish_confidence += 0.2
        
        # MACD bullish crossover or positive histogram
        if current_macd > current_signal and current_histogram > prev_histogram:
            bullish_signals += 1
            bullish_confidence += 0.3
        elif current_macd > current_signal:
            bullish_signals += 1
            bullish_confidence += 0.2
        
        # Positive ROC
        if current_roc > self.min_roc:
            bullish_signals += 1
            bullish_confidence += 0.2
        elif current_roc > 0:
            bullish_signals += 1
            bullish_confidence += 0.1
        
        # Volume confirmation
        if volume_confirmed:
            bullish_confidence += 0.2
        
        # Bearish momentum signals
        bearish_signals = 0
        bearish_confidence = 0.0
        
        # RSI momentum (strong but not oversold)
        if current_rsi < (100 - self.rsi_momentum_threshold) and current_rsi > 15:
            bearish_signals += 1
            bearish_confidence += 0.3
        elif current_rsi <= 30 and current_rsi > 20:  # Oversold but not extreme
            bearish_signals += 1
            bearish_confidence += 0.2
        
        # MACD bearish crossover or negative histogram
        if current_macd < current_signal and current_histogram < prev_histogram:
            bearish_signals += 1
            bearish_confidence += 0.3
        elif current_macd < current_signal:
            bearish_signals += 1
            bearish_confidence += 0.2
        
        # Negative ROC
        if current_roc < -self.min_roc:
            bearish_signals += 1
            bearish_confidence += 0.2
        elif current_roc < 0:
            bearish_signals += 1
            bearish_confidence += 0.1
        
        # Volume confirmation
        if volume_confirmed:
            bearish_confidence += 0.2
        
        # Determine signal
        min_signals_required = 2  # Need at least 2 confirmations
        
        if bullish_signals >= min_signals_required and bullish_confidence > bearish_confidence:
            confidence = min(0.95, 0.5 + (bullish_confidence / 2.0))
            return SignalType.BUY, confidence
        
        elif bearish_signals >= min_signals_required and bearish_confidence > bullish_confidence:
            confidence = min(0.95, 0.5 + (bearish_confidence / 2.0))
            return SignalType.SELL, confidence
        
        return SignalType.HOLD, 0.0
    
    def generate_signal(
        self,
        data: pd.DataFrame,
        position: Optional[Position] = None,
        sentiment: Optional[Any] = None
    ) -> TradingSignal:
        """
        Generate trading signal based on momentum indicators
        
        Args:
            data: DataFrame with OHLCV data
            position: Current position (if any)
            sentiment: Optional aggregated sentiment data
            
        Returns:
            TradingSignal object
        """
        if position:
            # If we have a position, check exit conditions instead
            should_exit, reason = self.should_exit(position, data)
            if should_exit:
                current_price = float(data['close'].iloc[-1])
                return TradingSignal(
                    signal_type=SignalType.SELL if position.quantity > 0 else SignalType.BUY,
                    symbol=self.symbol,
                    price=current_price,
                    quantity=abs(position.quantity),
                    confidence=0.8,  # High confidence for exit signals
                    timestamp=datetime.now(),
                    exit_reason=reason,
                    metadata={'strategy': 'momentum', 'exit': True}
                )
        
        # Check data requirements
        if len(data) < max(self.macd_slow, self.rsi_period, self.roc_period) + 10:
            current_price = float(data['close'].iloc[-1])
            return TradingSignal(
                signal_type=SignalType.HOLD,
                symbol=self.symbol,
                price=current_price,
                quantity=0,
                confidence=0.0,
                timestamp=datetime.now(),
                metadata={'strategy': 'momentum', 'reason': 'insufficient_data'}
            )
        
        current_price = float(data['close'].iloc[-1])
        
        # Detect momentum
        signal_type, confidence = self._detect_momentum_direction(data)
        
        if signal_type == SignalType.HOLD:
            return TradingSignal(
                signal_type=SignalType.HOLD,
                symbol=self.symbol,
                price=current_price,
                quantity=0,
                confidence=0.0,
                timestamp=datetime.now(),
                metadata={'strategy': 'momentum', 'reason': 'no_momentum_detected'}
            )
        
        # Calculate stop loss and take profit
        stop_loss = None
        take_profit = None
        
        if signal_type == SignalType.BUY:
            stop_loss = current_price * (1 - self.stop_loss_pct)
            take_profit = current_price * (1 + self.take_profit_pct)
        elif signal_type == SignalType.SELL:
            stop_loss = current_price * (1 + self.stop_loss_pct)
            take_profit = current_price * (1 - self.take_profit_pct)
        
        # Calculate indicators for metadata
        close_prices = data['close']
        rsi = self.indicators.rsi(close_prices, self.rsi_period)
        macd_data = self._calculate_macd(close_prices)
        roc = self._calculate_roc(close_prices)
        
        # Create signal
        signal = TradingSignal(
            signal_type=signal_type,
            symbol=self.symbol,
            price=current_price,
            quantity=0,  # Will be calculated by position sizing
            confidence=confidence,
            timestamp=datetime.now(),
            stop_loss=stop_loss,
            take_profit=take_profit,
            timeframe=self.timeframe,
            metadata={
                'strategy': 'momentum',
                'rsi': float(rsi.iloc[-1]),
                'macd': float(macd_data['macd'].iloc[-1]),
                'macd_signal': float(macd_data['signal'].iloc[-1]),
                'macd_histogram': float(macd_data['histogram'].iloc[-1]),
                'roc': float(roc.iloc[-1]),
                'volume_confirmed': self._check_volume_confirmation(data)
            }
        )
        
        return signal
    
    def should_exit(self, position: Position, data: pd.DataFrame) -> Tuple[bool, ExitReason]:
        """
        Determine if position should be exited
        
        Args:
            position: Current position
            data: Current market data
            
        Returns:
            Tuple of (should_exit: bool, reason: ExitReason)
        """
        if not position:
            return False, ExitReason.MANUAL
        
        current_price = float(data['close'].iloc[-1])
        
        # Check stop loss
        if position.stop_loss:
            if position.quantity > 0:  # Long position
                if current_price <= position.stop_loss:
                    return True, ExitReason.STOP_LOSS
            else:  # Short position
                if current_price >= position.stop_loss:
                    return True, ExitReason.STOP_LOSS
        
        # Check take profit
        if position.take_profit:
            if position.quantity > 0:  # Long position
                if current_price >= position.take_profit:
                    return True, ExitReason.TAKE_PROFIT
            else:  # Short position
                if current_price <= position.take_profit:
                    return True, ExitReason.TAKE_PROFIT
        
        # Check for momentum exhaustion (RSI divergence)
        if len(data) >= self.rsi_period + 5:
            close_prices = data['close']
            rsi = self.indicators.rsi(close_prices, self.rsi_period)
            macd_data = self._calculate_macd(close_prices)
            
            current_rsi = rsi.iloc[-1]
            current_macd = macd_data['macd'].iloc[-1]
            current_signal = macd_data['signal'].iloc[-1]
            current_histogram = macd_data['histogram'].iloc[-1]
            prev_histogram = macd_data['histogram'].iloc[-2] if len(macd_data['histogram']) > 1 else 0
            
            # Long position: exit if momentum reversing
            if position.quantity > 0:
                # RSI overbought and MACD bearish crossover
                if current_rsi > 80 and current_macd < current_signal and current_histogram < prev_histogram:
                    return True, ExitReason.TRAILING_STOP  # Momentum exhaustion
                
                # RSI divergence (price higher but RSI lower)
                if len(rsi) >= 5:
                    recent_rsi_trend = rsi.iloc[-5:].diff().mean()
                    recent_price_trend = close_prices.iloc[-5:].diff().mean()
                    if recent_price_trend > 0 and recent_rsi_trend < -2:  # Price up but RSI down
                        return True, ExitReason.TRAILING_STOP
            
            # Short position: exit if momentum reversing
            elif position.quantity < 0:
                # RSI oversold and MACD bullish crossover
                if current_rsi < 20 and current_macd > current_signal and current_histogram > prev_histogram:
                    return True, ExitReason.TRAILING_STOP  # Momentum exhaustion
                
                # RSI divergence (price lower but RSI higher)
                if len(rsi) >= 5:
                    recent_rsi_trend = rsi.iloc[-5:].diff().mean()
                    recent_price_trend = close_prices.iloc[-5:].diff().mean()
                    if recent_price_trend < 0 and recent_rsi_trend > 2:  # Price down but RSI up
                        return True, ExitReason.TRAILING_STOP
        
        return False, ExitReason.MANUAL
