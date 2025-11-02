"""
Core Trading Strategy Implementation
====================================

Clean, testable trading strategy with proper separation of concerns.

NOTE: This module maintains backward compatibility. New strategies should use
the modular strategy system in src.core.strategy.*
"""

# Import from new modular structure for backward compatibility
from .strategy.base import (
    BaseStrategy,
    TradingSignal,
    Position,
    SignalType,
    ExitReason,
    TechnicalIndicators
)
from .strategy.levels import PriceLevel, LevelType

# Re-export for backward compatibility
__all__ = [
    'BaseStrategy',
    'TradingSignal',
    'Position',
    'SignalType',
    'ExitReason',
    'TechnicalIndicators',
    'PriceLevel',
    'LevelType',
]

# Keep old imports for any code that directly imports from here
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import pandas as pd
import numpy as np
from enum import Enum

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

@dataclass
class TradingSignal:
    """Trading signal data structure"""
    signal_type: SignalType
    symbol: str
    price: float
    quantity: int
    timestamp: datetime
    confidence: float  # 0.0 to 1.0
    metadata: Dict[str, Any]
    exit_reason: Optional[ExitReason] = None

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

class BaseStrategy(ABC):
    """Abstract base class for trading strategies"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.indicators = TechnicalIndicators()
    
    @abstractmethod
    def generate_signal(self, data: pd.DataFrame, position: Optional[Position] = None) -> TradingSignal:
        """Generate trading signal based on market data"""
        pass
    
    @abstractmethod
    def should_exit(self, position: Position, data: pd.DataFrame) -> Tuple[bool, ExitReason]:
        """Determine if position should be exited"""
        pass
    
    def calculate_position_size(self, signal: TradingSignal, account_value: float) -> int:
        """Calculate position size based on risk management rules"""
        risk_per_trade = self.config.get('risk_per_trade', 0.02)  # 2% risk per trade
        stop_loss_pct = self.config.get('stop_loss_pct', 0.10)   # 10% stop loss
        
        risk_amount = account_value * risk_per_trade
        price_risk = signal.price * stop_loss_pct
        
        if price_risk > 0:
            position_size = int(risk_amount / price_risk)
            return min(position_size, self.config.get('max_position_size', 1000))
        
        return self.config.get('default_qty', 10)

class SMAStrategy(BaseStrategy):
    """SMA-based trading strategy"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.sma_short_window = config.get('sma_short_window', 20)
        self.sma_long_window = config.get('sma_long_window', 200)
        self.entry_threshold = config.get('entry_threshold', 0.005)  # 0.5%
        self.exit_threshold = config.get('exit_threshold', 0.03)    # 3%
        self.take_profit = config.get('take_profit', 0.20)           # 20%
        self.stop_loss = config.get('stop_loss', 0.10)              # 10%
        self.rsi_oversold = config.get('rsi_oversold', 45)
        self.rsi_overbought = config.get('rsi_overbought', 55)
    
    def generate_signal(self, data: pd.DataFrame, position: Optional[Position] = None) -> TradingSignal:
        """Generate SMA-based trading signal"""
        if len(data) < self.sma_long_window:
            return TradingSignal(
                signal_type=SignalType.HOLD,
                symbol=self.config.get('symbol', 'UNKNOWN'),
                price=float(data['close'].iloc[-1]),
                quantity=0,
                timestamp=datetime.now(),
                confidence=0.0,
                metadata={'reason': 'insufficient_data'}
            )
        
        # Calculate indicators
        sma_short = self.indicators.sma(data['close'], self.sma_short_window)
        sma_long = self.indicators.sma(data['close'], self.sma_long_window)
        rsi = self.indicators.rsi(data['close'])
        
        # Calculate OBV if volume data available
        obv_slope = 0.0
        if 'volume' in data.columns:
            obv = self.indicators.obv(data['close'], data['volume'])
            obv_slope = float(self.indicators.obv_slope(obv).iloc[-1])
        
        current_price = float(data['close'].iloc[-1])
        current_sma_short = float(sma_short.iloc[-1])
        current_sma_long = float(sma_long.iloc[-1])
        current_rsi = float(rsi.iloc[-1])
        
        # Entry conditions
        within_sma_short = abs(current_price - current_sma_short) / current_sma_short <= self.entry_threshold
        within_sma_long = abs(current_price - current_sma_long) / current_sma_long <= self.entry_threshold
        rsi_ok = self.rsi_oversold <= current_rsi <= self.rsi_overbought
        obv_ok = obv_slope > 0
        
        # Generate signal
        if (within_sma_short or within_sma_long) and rsi_ok and obv_ok:
            confidence = self._calculate_confidence(
                current_price, current_sma_short, current_sma_long, 
                current_rsi, obv_slope
            )
            
            return TradingSignal(
                signal_type=SignalType.BUY,
                symbol=self.config.get('symbol', 'UNKNOWN'),
                price=current_price,
                quantity=self.config.get('default_qty', 10),
                timestamp=datetime.now(),
                confidence=confidence,
                metadata={
                    'sma_short': current_sma_short,
                    'sma_long': current_sma_long,
                    'rsi': current_rsi,
                    'obv_slope': obv_slope,
                    'within_sma_short': within_sma_short,
                    'within_sma_long': within_sma_long
                }
            )
        
        return TradingSignal(
            signal_type=SignalType.HOLD,
            symbol=self.config.get('symbol', 'UNKNOWN'),
            price=current_price,
            quantity=0,
            timestamp=datetime.now(),
            confidence=0.0,
            metadata={
                'reason': 'entry_conditions_not_met',
                'within_sma_short': within_sma_short,
                'within_sma_long': within_sma_long,
                'rsi_ok': rsi_ok,
                'obv_ok': obv_ok
            }
        )
    
    def should_exit(self, position: Position, data: pd.DataFrame) -> Tuple[bool, ExitReason]:
        """Determine if position should be exited"""
        if len(data) < self.sma_short_window:
            return False, ExitReason.MANUAL
        
        current_price = float(data['close'].iloc[-1])
        sma_short = self.indicators.sma(data['close'], self.sma_short_window)
        current_sma_short = float(sma_short.iloc[-1])
        
        # Take profit
        pnl_pct = (current_price - position.entry_price) / position.entry_price
        if pnl_pct >= self.take_profit:
            return True, ExitReason.TAKE_PROFIT
        
        # Stop loss
        if pnl_pct <= -self.stop_loss:
            return True, ExitReason.STOP_LOSS
        
        # SMA extension
        sma_extension = abs(current_price - current_sma_short) / current_sma_short
        if sma_extension >= self.exit_threshold:
            return True, ExitReason.SMA_EXTENSION
        
        return False, ExitReason.MANUAL
    
    def _calculate_confidence(self, price: float, sma_short: float, sma_long: float, 
                            rsi: float, obv_slope: float) -> float:
        """Calculate signal confidence score"""
        confidence = 0.0
        
        # SMA alignment bonus
        if sma_short > sma_long:  # Uptrend
            confidence += 0.3
        elif sma_short < sma_long:  # Downtrend
            confidence -= 0.2
        
        # RSI bonus (closer to 50 is better)
        rsi_score = 1.0 - abs(rsi - 50) / 50
        confidence += rsi_score * 0.3
        
        # OBV slope bonus
        if obv_slope > 0:
            confidence += 0.2
        
        # Price proximity to SMA bonus
        sma_proximity = min(abs(price - sma_short) / sma_short, 
                           abs(price - sma_long) / sma_long)
        proximity_score = max(0, 1.0 - sma_proximity / self.entry_threshold)
        confidence += proximity_score * 0.2
        
        return max(0.0, min(1.0, confidence))

class StrategyFactory:
    """Factory for creating strategy instances"""
    
    @staticmethod
    def create_strategy(strategy_type: str, config: Dict[str, Any]) -> BaseStrategy:
        """
        Create strategy instance based on type
        
        First checks the registry, then falls back to legacy strategies
        """
        # Try registry first
        try:
            from .strategy.registry import get_registry
            registry = get_registry()
            if registry.is_registered(strategy_type):
                return registry.get_strategy(strategy_type, config)
        except ImportError:
            pass
        
        # Fall back to legacy strategies
        strategies = {
            'sma': SMAStrategy,
            # Add more legacy strategies here
        }
        
        if strategy_type not in strategies:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        
        return strategies[strategy_type](config)
