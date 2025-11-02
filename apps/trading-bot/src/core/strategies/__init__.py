"""
Trading Strategies
==================

Concrete strategy implementations.

Strategies are automatically registered when this module is imported.
"""

from ..strategy.registry import get_registry

# Import strategies (this will happen before registration)
from .range_bound_strategy import RangeBoundStrategy

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

__all__ = [
    'RangeBoundStrategy',
]

