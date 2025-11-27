"""
Trading Strategy Module
=======================

Core strategy implementations with support for level-based trading,
multi-timeframe analysis, and modular strategy composition.
"""

from .base import (
    BaseStrategy,
    TradingSignal,
    Position,
    SignalType,
    ExitReason,
    TechnicalIndicators
)

from .levels import (
    PriceLevel,
    LevelType,
    LevelDetector
)

from .level_based import LevelBasedStrategy
from .momentum import MomentumStrategy
from .range_bound import RangeBoundStrategy

__all__ = [
    'BaseStrategy',
    'TradingSignal',
    'Position',
    'SignalType',
    'ExitReason',
    'TechnicalIndicators',
    'PriceLevel',
    'LevelType',
    'LevelDetector',
    'LevelBasedStrategy',
    'MomentumStrategy',
    'RangeBoundStrategy',
]
