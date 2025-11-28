"""
Trading Scheduler Module
========================

Background scheduler for automatic strategy evaluation and trade execution.
"""

import logging
from typing import Optional

from .trading_scheduler import TradingScheduler
from ...data.providers.market_data import get_default_data_provider

logger = logging.getLogger(__name__)

_scheduler: Optional[TradingScheduler] = None


def get_scheduler() -> TradingScheduler:
    """
    Get the singleton TradingScheduler instance.
    Initializes it with a default data provider if it doesn't exist.
    """
    global _scheduler
    if _scheduler is None:
        # Initialize with default Yahoo Finance data provider
        data_provider = get_default_data_provider()
        _scheduler = TradingScheduler(data_provider=data_provider)
        logger.info("TradingScheduler instance created with default data provider.")
    return _scheduler


__all__ = ["TradingScheduler", "get_scheduler"]

