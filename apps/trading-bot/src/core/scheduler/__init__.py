"""
Trading Scheduler Module
========================

Background scheduler for automatic strategy evaluation and trade execution.
"""

import logging
from typing import Optional

from .trading_scheduler import TradingScheduler

logger = logging.getLogger(__name__)

_scheduler: Optional[TradingScheduler] = None

def get_scheduler() -> TradingScheduler:
    """
    Get the singleton TradingScheduler instance.
    Initializes it if it doesn't exist.
    """
    global _scheduler
    if _scheduler is None:
        _scheduler = TradingScheduler()
        logger.info("TradingScheduler instance created.")
    return _scheduler

__all__ = ["TradingScheduler", "get_scheduler"]

