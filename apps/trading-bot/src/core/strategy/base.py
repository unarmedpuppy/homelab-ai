"""
Base Strategy Classes
=====================

Abstract base classes and core data structures for trading strategies.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING
from datetime import datetime
from enum import Enum
import pandas as pd
import numpy as np
import logging

from .levels import PriceLevel

if TYPE_CHECKING:
    from ...data.providers.sentiment.aggregator import AggregatedSentiment

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Trading signal types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class ExitReason(Enum):
    """Exit reason types"""
    TAKE_PROFIT = "take_profit"
    STOP_LOSS = "stop_loss"
    SMA_EXTENSION = "sma_extension"
    TIME_BASED = "time_based"
    MANUAL = "manual"
    LEVEL_REACHED = "level_reached"  # NEW: When a target level is reached
    TRAILING_STOP = "trailing_stop"  # NEW: Trailing stop activated


@dataclass
class TradingSignal:
    """Enhanced trading signal data structure"""
    signal_type: SignalType
    symbol: str
    price: float
    quantity: int
    timestamp: datetime
    confidence: float  # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    exit_reason: Optional[ExitReason] = None
    
    # Enhanced fields for level-based strategies
    entry_level: Optional[PriceLevel] = None  # Price level that triggered entry
    stop_loss: Optional[float] = None  # Calculated stop loss price
    take_profit: Optional[float] = None  # Calculated take profit price
    timeframe: Optional[str] = None  # Primary timeframe for this signal


@dataclass
class Position:
    """Position data structure"""
    symbol: str
    quantity: int
    entry_price: float
    entry_time: datetime
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    entry_level: Optional[PriceLevel] = None  # Level where entry occurred
    stop_loss: Optional[float] = None  # Current stop loss price
    take_profit: Optional[float] = None  # Current take profit price


class TechnicalIndicators:
    """Technical indicators calculation"""
    
    @staticmethod
    def sma(prices: pd.Series, window: int) -> pd.Series:
        """Simple Moving Average"""
        return prices.rolling(window=window).mean()
    
    @staticmethod
    def ema(prices: pd.Series, window: int) -> pd.Series:
        """Exponential Moving Average"""
        return prices.ewm(span=window).mean()
    
    @staticmethod
    def rsi(prices: pd.Series, window: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = prices.diff()
        gain = delta.clip(lower=0).ewm(alpha=1/window, adjust=False).mean()
        loss = -delta.clip(upper=0).ewm(alpha=1/window, adjust=False).mean()
        rs = gain / loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def obv(prices: pd.Series, volume: pd.Series) -> pd.Series:
        """On-Balance Volume"""
        price_change = prices.diff()
        obv = (np.sign(price_change) * volume).cumsum()
        return obv
    
    @staticmethod
    def obv_slope(obv: pd.Series, window: int = 5) -> pd.Series:
        """OBV slope calculation"""
        return obv.rolling(window).mean().diff()
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
        """Average True Range"""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window).mean()
    
    @staticmethod
    def bollinger_bands(prices: pd.Series, window: int = 20, num_std: float = 2.0) -> Dict[str, pd.Series]:
        """Bollinger Bands"""
        sma = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()
        
        return {
            'middle': sma,
            'upper': sma + (std * num_std),
            'lower': sma - (std * num_std)
        }


class BaseStrategy(ABC):
    """Abstract base class for trading strategies"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.indicators = TechnicalIndicators()
        self.symbol = config.get('symbol', 'UNKNOWN')
        self.timeframe = config.get('timeframe', '5m')
        
        # Sentiment configuration
        self.sentiment_config = config.get('sentiment', {})
        self.use_sentiment = self.sentiment_config.get('enabled', False)
        self.min_sentiment_for_buy = self.sentiment_config.get('min_sentiment_for_buy', -1.0)  # Default: no filter
        self.max_sentiment_for_sell = self.sentiment_config.get('max_sentiment_for_sell', 1.0)  # Default: no filter
        self.sentiment_confidence_boost = self.sentiment_config.get('confidence_boost', 0.1)  # Boost confidence by up to 10%
        
        # Confluence configuration
        self.confluence_config = config.get('confluence', {})
        self.use_confluence = self.confluence_config.get('enabled', False)
        self.min_confluence_threshold = self.confluence_config.get('min_threshold', 0.0)  # Minimum confluence required
        self.high_confluence_threshold = self.confluence_config.get('high_threshold', 0.7)  # High confluence threshold
        self.confluence_confidence_boost = self.confluence_config.get('confidence_boost', 0.15)  # Boost when high confluence
        
        # Earnings/Events configuration
        self.events_config = config.get('events', {})
        self.use_events_filter = self.events_config.get('enabled', False)
        self.avoid_earnings_days = self.events_config.get('avoid_earnings_days', 0)  # Days before/after earnings to avoid trades
    
    def _apply_sentiment_filter(
        self, 
        signal: TradingSignal, 
        sentiment: Optional['AggregatedSentiment']
    ) -> TradingSignal:
        """
        Apply sentiment-based filtering and confidence adjustment to a signal
        
        Args:
            signal: Trading signal to filter/adjust
            sentiment: Aggregated sentiment data
            
        Returns:
            Potentially modified signal (may be converted to HOLD if filtered out)
        """
        if not self.use_sentiment or sentiment is None:
            return signal
        
        # Store sentiment in metadata
        signal.metadata['sentiment'] = {
            'unified_sentiment': sentiment.unified_sentiment,
            'confidence': sentiment.confidence,
            'sentiment_level': sentiment.sentiment_level.value,
            'twitter_sentiment': sentiment.twitter_sentiment,
            'reddit_sentiment': sentiment.reddit_sentiment,
            'divergence_detected': sentiment.divergence_detected,
            'total_mention_count': sentiment.total_mention_count
        }
        
        # Apply sentiment filters
        if signal.signal_type == SignalType.BUY:
            # Filter out buys if sentiment is too negative
            if sentiment.unified_sentiment < self.min_sentiment_for_buy:
                logger.debug(
                    f"Signal filtered: BUY blocked due to negative sentiment "
                    f"({sentiment.unified_sentiment:.3f} < {self.min_sentiment_for_buy})"
                )
                return self._create_hold_signal(
                    signal.price,
                    reason=f"sentiment_too_negative_{sentiment.unified_sentiment:.3f}"
                )
            
            # Boost confidence if sentiment is positive and aligned with buy signal
            if sentiment.unified_sentiment > 0:
                sentiment_boost = min(
                    sentiment.unified_sentiment * self.sentiment_confidence_boost,
                    self.sentiment_confidence_boost
                )
                signal.confidence = min(1.0, signal.confidence + sentiment_boost)
                signal.metadata['sentiment_confidence_boost'] = sentiment_boost
        
        elif signal.signal_type == SignalType.SELL:
            # Filter out sells if sentiment is too positive (might want to hold)
            if sentiment.unified_sentiment > self.max_sentiment_for_sell:
                logger.debug(
                    f"Signal filtered: SELL blocked due to positive sentiment "
                    f"({sentiment.unified_sentiment:.3f} > {self.max_sentiment_for_sell})"
                )
                # Don't convert to HOLD, but reduce confidence significantly
                signal.confidence = max(0.0, signal.confidence * 0.5)
                signal.metadata['sentiment_filtered'] = True
            
            # Boost confidence if sentiment is negative and aligned with sell signal
            if sentiment.unified_sentiment < 0:
                sentiment_boost = min(
                    abs(sentiment.unified_sentiment) * self.sentiment_confidence_boost,
                    self.sentiment_confidence_boost
                )
                signal.confidence = min(1.0, signal.confidence + sentiment_boost)
                signal.metadata['sentiment_confidence_boost'] = sentiment_boost
        
        # Adjust for divergence (when sources disagree, reduce confidence)
        if sentiment.divergence_detected:
            divergence_penalty = sentiment.divergence_score * 0.2  # Up to 20% reduction
            signal.confidence = max(0.0, signal.confidence - divergence_penalty)
            signal.metadata['sentiment_divergence_penalty'] = divergence_penalty
        
        return signal
    
    def _apply_confluence_filter(
        self,
        signal: TradingSignal,
        confluence_score: Optional[Any] = None  # ConfluenceScore type
    ) -> TradingSignal:
        """
        Apply confluence-based filtering and confidence adjustment to a signal
        
        Args:
            signal: Trading signal to filter/adjust
            confluence_score: Optional ConfluenceScore object
            
        Returns:
            Potentially modified signal (may be converted to HOLD if filtered out)
        """
        if not self.use_confluence or confluence_score is None:
            return signal
        
        # Store confluence in metadata
        signal.metadata['confluence'] = {
            'confluence_score': confluence_score.confluence_score,
            'directional_bias': confluence_score.directional_bias,
            'confluence_level': confluence_score.confluence_level.value,
            'confidence': confluence_score.confidence,
            'meets_minimum_threshold': confluence_score.meets_minimum_threshold,
            'meets_high_threshold': confluence_score.meets_high_threshold,
            'components_used': confluence_score.components_used
        }
        
        # Check minimum threshold - filter out signals below threshold
        if not confluence_score.meets_minimum_threshold:
            logger.debug(
                f"Signal filtered: {signal.signal_type.value} blocked due to low confluence "
                f"({confluence_score.confluence_score:.3f} < {self.min_confluence_threshold})"
            )
            return self._create_hold_signal(
                signal.price,
                reason=f"confluence_below_threshold_{confluence_score.confluence_score:.3f}"
            )
        
        # Check directional alignment
        # For BUY signals, confluence directional_bias should be positive (bullish)
        # For SELL signals, confluence directional_bias should be negative (bearish)
        if signal.signal_type == SignalType.BUY:
            if confluence_score.directional_bias < -0.2:  # Strong bearish bias
                logger.debug(
                    f"Signal filtered: BUY blocked due to bearish confluence bias "
                    f"({confluence_score.directional_bias:.3f})"
                )
                return self._create_hold_signal(
                    signal.price,
                    reason=f"confluence_bearish_bias_{confluence_score.directional_bias:.3f}"
                )
            
            # Boost confidence if confluence aligns with signal
            if confluence_score.directional_bias > 0.3:  # Bullish alignment
                alignment_boost = min(
                    confluence_score.confluence_score * self.confluence_confidence_boost,
                    self.confluence_confidence_boost
                )
                signal.confidence = min(1.0, signal.confidence + alignment_boost)
                signal.metadata['confluence_confidence_boost'] = alignment_boost
        
        elif signal.signal_type == SignalType.SELL:
            if confluence_score.directional_bias > 0.2:  # Strong bullish bias
                logger.debug(
                    f"Signal filtered: SELL blocked due to bullish confluence bias "
                    f"({confluence_score.directional_bias:.3f})"
                )
                return self._create_hold_signal(
                    signal.price,
                    reason=f"confluence_bullish_bias_{confluence_score.directional_bias:.3f}"
                )
            
            # Boost confidence if confluence aligns with signal
            if confluence_score.directional_bias < -0.3:  # Bearish alignment
                alignment_boost = min(
                    confluence_score.confluence_score * self.confluence_confidence_boost,
                    self.confluence_confidence_boost
                )
                signal.confidence = min(1.0, signal.confidence + alignment_boost)
                signal.metadata['confluence_confidence_boost'] = alignment_boost
        
        # Additional boost if high confluence
        if confluence_score.meets_high_threshold:
            high_confluence_boost = 0.1  # Additional 10% boost for high confluence
            signal.confidence = min(1.0, signal.confidence + high_confluence_boost)
            signal.metadata['high_confluence_boost'] = high_confluence_boost
        
        return signal
    
    def _apply_events_filter(self, signal: TradingSignal) -> TradingSignal:
        """
        Apply events/earnings filtering to a signal
        
        Args:
            signal: Trading signal to filter
            
        Returns:
            Potentially modified signal (may be converted to HOLD if filtered out)
        """
        if not self.use_events_filter:
            return signal
        
        try:
            from ...data.providers.events.earnings_calendar import get_provider_instance
            
            # Use singleton provider instance
            provider = get_provider_instance()
            
            if not provider.is_available():
                return signal
            
            # Check if near earnings
            is_near = provider.is_near_earnings(
                self.symbol,
                days_threshold=self.avoid_earnings_days
            )
            
            if is_near:
                logger.debug(
                    f"Signal filtered: {signal.signal_type.value} blocked due to earnings within {self.avoid_earnings_days} days"
                )
                return self._create_hold_signal(
                    signal.price,
                    reason=f"near_earnings_avoidance"
                )
            
            # Store earnings info in metadata
            next_earnings = provider.get_next_earnings_date(self.symbol)
            if next_earnings:
                signal.metadata['next_earnings_date'] = next_earnings.isoformat()
                days_until = (next_earnings - datetime.now()).days
                signal.metadata['days_until_earnings'] = days_until
        
        except Exception as e:
            logger.warning(f"Error applying events filter: {e}")
        
        return signal
    
    @abstractmethod
    def generate_signal(
        self, 
        data: pd.DataFrame, 
        position: Optional[Position] = None,
        sentiment: Optional['AggregatedSentiment'] = None
    ) -> TradingSignal:
        """
        Generate trading signal based on market data
        
        Args:
            data: DataFrame with OHLCV data
            position: Current position (if any)
            sentiment: Optional aggregated sentiment data for the symbol
            
        Returns:
            TradingSignal object
        """
        pass
    
    @abstractmethod
    def should_exit(self, position: Position, data: pd.DataFrame) -> Tuple[bool, ExitReason]:
        """
        Determine if position should be exited
        
        Args:
            position: Current position
            data: Current market data
            
        Returns:
            Tuple of (should_exit: bool, reason: ExitReason)
        """
        pass
    
    def calculate_position_size(self, signal: TradingSignal, account_value: float) -> int:
        """Calculate position size based on risk management rules"""
        risk_per_trade = self.config.get('risk_management', {}).get('risk_per_trade', 0.02)  # 2% risk per trade
        stop_loss_pct = self.config.get('exit', {}).get('stop_loss_pct', 0.10)  # 10% stop loss
        
        # Use signal stop_loss if available, otherwise calculate from percentage
        if signal.stop_loss:
            price_risk = abs(signal.price - signal.stop_loss)
        else:
            price_risk = signal.price * stop_loss_pct
        
        risk_amount = account_value * risk_per_trade
        
        if price_risk > 0:
            position_size = int(risk_amount / price_risk)
            max_size = self.config.get('risk_management', {}).get('max_position_size', 1000)
            return min(position_size, max_size)
        
        default_qty = self.config.get('risk_management', {}).get('default_qty', 10)
        return default_qty
    
    def evaluate_entry_conditions(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Evaluate entry conditions and return detailed results
        
        Can be overridden by subclasses to provide more detailed condition evaluation
        
        Args:
            data: Market data
            
        Returns:
            Dictionary with condition evaluation results
        """
        return {
            'evaluated': True,
            'timestamp': datetime.now()
        }
    
    def evaluate_exit_conditions(self, position: Position, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Evaluate exit conditions and return detailed results
        
        Can be overridden by subclasses to provide more detailed condition evaluation
        
        Args:
            position: Current position
            data: Market data
            
        Returns:
            Dictionary with condition evaluation results
        """
        should_exit, reason = self.should_exit(position, data)
        return {
            'should_exit': should_exit,
            'reason': reason,
            'timestamp': datetime.now()
        }
    
    def _create_hold_signal(self, price: float, reason: str = "no_entry_conditions") -> TradingSignal:
        """Helper method to create a HOLD signal"""
        return TradingSignal(
            signal_type=SignalType.HOLD,
            symbol=self.symbol,
            price=price,
            quantity=0,
            timestamp=datetime.now(),
            confidence=0.0,
            metadata={'reason': reason},
            timeframe=self.timeframe
        )
    
    def _create_buy_signal(self, price: float, quantity: Optional[int] = None,
                          confidence: float = 0.5, entry_level: Optional[PriceLevel] = None,
                          stop_loss: Optional[float] = None, take_profit: Optional[float] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> TradingSignal:
        """Helper method to create a BUY signal"""
        if quantity is None:
            quantity = self.config.get('risk_management', {}).get('default_qty', 10)
        
        if metadata is None:
            metadata = {}
        
        return TradingSignal(
            signal_type=SignalType.BUY,
            symbol=self.symbol,
            price=price,
            quantity=quantity,
            timestamp=datetime.now(),
            confidence=confidence,
            metadata=metadata,
            entry_level=entry_level,
            stop_loss=stop_loss,
            take_profit=take_profit,
            timeframe=self.timeframe
        )
    
    def _create_sell_signal(self, price: float, quantity: Optional[int] = None,
                           confidence: float = 0.5, exit_reason: Optional[ExitReason] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> TradingSignal:
        """Helper method to create a SELL signal"""
        if quantity is None:
            quantity = self.config.get('risk_management', {}).get('default_qty', 10)
        
        if metadata is None:
            metadata = {}
        
        return TradingSignal(
            signal_type=SignalType.SELL,
            symbol=self.symbol,
            price=price,
            quantity=quantity,
            timestamp=datetime.now(),
            confidence=confidence,
            metadata=metadata,
            exit_reason=exit_reason,
            timeframe=self.timeframe
        )

