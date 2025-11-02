"""
Trading Strategies
==================

Concrete strategy implementations.

Strategies are automatically registered when this module is imported.
"""

from ..strategy.registry import get_registry

# Import strategies (this will happen before registration)
from .range_bound_strategy import RangeBoundStrategy
from ..strategy.momentum import MomentumStrategy

# Register strategies manually
_registry = get_registry()

# Register RangeBoundStrategy
_registry.register(
    'range_bound',
    RangeBoundStrategy,
    {
        'description': 'Range-bound strategy using Previous Day High/Low',
        'supports_levels': True,
        'example_config': {
            'symbol': 'SPY',
            'timeframe': '5m',
            'entry': {
                'levels': ['previous_day_high', 'previous_day_low'],
                'proximity_threshold': 0.001
            },
            'exit': {
                'stop_loss_pct': 0.005,
                'take_profit_type': 'opposite_level'
            }
        }
    }
)

# Register MomentumStrategy
_registry.register(
    'momentum',
    MomentumStrategy,
    {
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
    }
)

__all__ = [
    'RangeBoundStrategy',
    'MomentumStrategy',
]

