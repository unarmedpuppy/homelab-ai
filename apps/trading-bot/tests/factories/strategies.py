"""
Strategy Factory Functions
===========================

Factory functions for creating strategy configurations and instances for testing.
"""

from typing import Dict, Any, Optional
from src.core.strategy.base import BaseStrategy


def create_strategy_config(
    symbol: str = "SPY",
    timeframe: str = "5m",
    entry_levels: Optional[list] = None,
    proximity_threshold: float = 0.001,
    stop_loss_pct: float = 0.005,
    take_profit_type: str = "opposite_level",
    volume_confirmation: bool = False,
    sentiment_enabled: bool = False,
    confluence_enabled: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a strategy configuration dict for testing
    
    Args:
        symbol: Trading symbol
        timeframe: Timeframe
        entry_levels: List of entry level types (defaults to PDH/PDL)
        proximity_threshold: Proximity threshold for entry
        stop_loss_pct: Stop loss percentage
        take_profit_type: Take profit type
        volume_confirmation: Enable volume confirmation
        sentiment_enabled: Enable sentiment filtering
        confluence_enabled: Enable confluence filtering
        **kwargs: Additional config keys
    
    Returns:
        Strategy configuration dictionary
    """
    if entry_levels is None:
        entry_levels = ["previous_day_high", "previous_day_low"]
    
    config = {
        "symbol": symbol,
        "timeframe": timeframe,
        "entry": {
            "levels": entry_levels,
            "proximity_threshold": proximity_threshold,
            "volume_confirmation": volume_confirmation
        },
        "exit": {
            "stop_loss_pct": stop_loss_pct,
            "take_profit_type": take_profit_type
        },
        "risk_management": {
            "max_position_size": 100,
            "risk_per_trade": 0.02,
            "default_qty": 10
        }
    }
    
    if sentiment_enabled:
        config["sentiment"] = {
            "enabled": True,
            "min_sentiment_for_buy": 0.3,
            "max_sentiment_for_sell": -0.3,
            "confidence_boost": 0.15
        }
    
    if confluence_enabled:
        config["confluence"] = {
            "enabled": True,
            "min_threshold": 0.6,
            "high_threshold": 0.8,
            "confidence_boost": 0.2
        }
    
    # Merge additional kwargs
    config.update(kwargs)
    
    return config


def create_test_strategy(
    strategy_class: type,
    config: Optional[Dict[str, Any]] = None,
    **config_overrides
) -> BaseStrategy:
    """
    Create a test strategy instance
    
    Args:
        strategy_class: Strategy class (must inherit from BaseStrategy)
        config: Strategy configuration (uses default if None)
        **config_overrides: Override config values
    
    Returns:
        Strategy instance
    """
    if config is None:
        config = create_strategy_config(**config_overrides)
    else:
        # Merge overrides
        for key, value in config_overrides.items():
            if key in config:
                if isinstance(config[key], dict) and isinstance(value, dict):
                    config[key].update(value)
                else:
                    config[key] = value
            else:
                config[key] = value
    
    return strategy_class(config)

