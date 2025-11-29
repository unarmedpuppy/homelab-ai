"""
Strategy Startup Configuration
==============================

Automatically register default strategies on application startup.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import os

from .registry import get_registry

logger = logging.getLogger(__name__)


@dataclass
class StrategyDefinition:
    """Definition for a strategy to be auto-registered"""
    strategy_type: str
    symbol: str
    enabled: bool = True
    timeframe: str = "5m"
    extra_config: Dict[str, Any] = None

    def __post_init__(self):
        if self.extra_config is None:
            self.extra_config = {}


# Default strategies to register on startup
# These can be overridden via environment variables
DEFAULT_STRATEGIES: List[StrategyDefinition] = [
    # Momentum strategies for major indices/stocks
    StrategyDefinition(
        strategy_type="momentum",
        symbol="SPY",
        enabled=True,
        timeframe="5m",
        extra_config={
            "rsi_period": 14,
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            "sma_short": 9,
            "sma_long": 21,
            "volume_threshold": 1.5,
        }
    ),
    StrategyDefinition(
        strategy_type="momentum",
        symbol="QQQ",
        enabled=True,
        timeframe="5m",
        extra_config={
            "rsi_period": 14,
            "rsi_oversold": 30,
            "rsi_overbought": 70,
        }
    ),
    # Range-bound strategy for SPY (PDH/PDL levels)
    StrategyDefinition(
        strategy_type="range_bound",
        symbol="SPY",
        enabled=True,
        timeframe="5m",
        extra_config={
            "stop_loss_pct": 0.005,  # 0.5% stop
            "volume_confirmation": True,
        }
    ),
]


def get_configured_strategies() -> List[StrategyDefinition]:
    """
    Get strategies to auto-register from environment or defaults.

    Environment variable format:
    TRADING_STRATEGIES=momentum:SPY:5m,momentum:QQQ:5m,range_bound:SPY:5m
    """
    env_strategies = os.getenv("TRADING_STRATEGIES", "").strip()

    if not env_strategies:
        return DEFAULT_STRATEGIES

    strategies = []
    for strategy_spec in env_strategies.split(","):
        parts = strategy_spec.strip().split(":")
        if len(parts) >= 2:
            strategy_type = parts[0]
            symbol = parts[1]
            timeframe = parts[2] if len(parts) > 2 else "5m"
            enabled = parts[3].lower() != "false" if len(parts) > 3 else True

            strategies.append(StrategyDefinition(
                strategy_type=strategy_type,
                symbol=symbol,
                timeframe=timeframe,
                enabled=enabled,
            ))

    return strategies if strategies else DEFAULT_STRATEGIES


def register_default_strategies(evaluator) -> int:
    """
    Register default strategies with the evaluator.

    Args:
        evaluator: StrategyEvaluator instance

    Returns:
        Number of strategies registered
    """
    registry = get_registry()
    strategies = get_configured_strategies()
    registered_count = 0

    for strategy_def in strategies:
        try:
            # Check if strategy type exists
            if not registry.is_registered(strategy_def.strategy_type):
                logger.warning(
                    f"Strategy type '{strategy_def.strategy_type}' not found in registry, skipping"
                )
                continue

            # Build strategy ID
            strategy_id = f"{strategy_def.strategy_type}_{strategy_def.symbol}"

            # Check if already registered
            if strategy_id in evaluator.list_strategies():
                logger.debug(f"Strategy {strategy_id} already registered, skipping")
                continue

            # Build config
            config = {
                "symbol": strategy_def.symbol,
                "timeframe": strategy_def.timeframe,
                **strategy_def.extra_config,
            }

            # Add to evaluator
            evaluator.add_strategy(
                strategy_type=strategy_def.strategy_type,
                config=config,
                enabled=strategy_def.enabled,
            )

            registered_count += 1
            logger.info(
                f"Auto-registered strategy: {strategy_id} "
                f"(type={strategy_def.strategy_type}, symbol={strategy_def.symbol}, "
                f"enabled={strategy_def.enabled})"
            )

        except Exception as e:
            logger.error(
                f"Failed to register strategy {strategy_def.strategy_type} "
                f"for {strategy_def.symbol}: {e}",
                exc_info=True
            )

    return registered_count


def initialize_strategies(evaluator) -> Dict[str, Any]:
    """
    Initialize all default strategies.

    Called during application startup to ensure strategies are ready.

    Returns:
        Status information about registered strategies
    """
    logger.info("Initializing default trading strategies...")

    # Ensure strategy modules are imported (triggers @register_strategy decorators)
    try:
        from . import momentum, range_bound
    except ImportError as e:
        logger.warning(f"Could not import all strategy modules: {e}")

    # Get registry info
    registry = get_registry()
    available_strategies = registry.list_strategies()

    # Register strategies with evaluator
    registered_count = register_default_strategies(evaluator)

    # Get final state
    active_strategies = evaluator.list_strategies()

    result = {
        "available_strategy_types": available_strategies,
        "registered_strategies": active_strategies,
        "registered_count": registered_count,
        "total_active": len(active_strategies),
    }

    logger.info(
        f"Strategy initialization complete: "
        f"{registered_count} registered, {len(active_strategies)} active"
    )

    return result
