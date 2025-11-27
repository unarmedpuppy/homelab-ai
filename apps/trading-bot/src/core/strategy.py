"""
Core Trading Strategy - Backward Compatibility
===============================================

This module provides backward compatibility for code that imports from
`src.core.strategy`. New code should import from `src.core.strategy.*` directly.

Example:
    # Old style (still works)
    from src.core.strategy import BaseStrategy, SignalType

    # New style (preferred)
    from src.core.strategy.base import BaseStrategy, SignalType
"""

# Re-export everything from the strategy package
from .strategy import (
    # Base classes and types
    BaseStrategy,
    TradingSignal,
    Position,
    SignalType,
    ExitReason,
    TechnicalIndicators,
    # Level support
    PriceLevel,
    LevelType,
    LevelDetector,
    # Concrete strategies
    LevelBasedStrategy,
    MomentumStrategy,
    RangeBoundStrategy,
)

# Also export the registry
from .strategy.registry import StrategyRegistry, get_registry

__all__ = [
    # Base classes and types
    'BaseStrategy',
    'TradingSignal',
    'Position',
    'SignalType',
    'ExitReason',
    'TechnicalIndicators',
    # Level support
    'PriceLevel',
    'LevelType',
    'LevelDetector',
    # Concrete strategies
    'LevelBasedStrategy',
    'MomentumStrategy',
    'RangeBoundStrategy',
    # Registry
    'StrategyRegistry',
    'get_registry',
]
