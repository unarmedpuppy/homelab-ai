"""
Volume Trend Calculator
=======================

Utility functions for calculating volume trends by comparing current mention counts
with historical data.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from ...database.models import SymbolSentiment as SymbolSentimentModel
from ...database import SessionLocal

logger = logging.getLogger(__name__)


def calculate_volume_trend(
    symbol: str,
    current_mention_count: int,
    hours: int = 24,
    db: Optional[Session] = None,
    threshold_percent: float = 0.2  # 20% change = trend
) -> str:
    """
    Calculate volume trend by comparing current mention count with historical baseline
    
    Args:
        symbol: Stock symbol
        current_mention_count: Current period mention count
        hours: Hours in current period (default: 24)
        db: Database session (if None, creates new session)
        threshold_percent: Percentage change threshold for trend detection (default: 20%)
                          Values above this = "up", below = "down", within = "stable"
    
    Returns:
        "up", "down", or "stable"
    """
    if current_mention_count == 0:
        return "stable"
    
    session = db
    session_created = False
    
    if session is None:
        session = SessionLocal()
        session_created = True
    
    try:
        # Get baseline: mentions in the previous period of same length
        baseline_start = datetime.now() - timedelta(hours=hours * 2)  # Previous period
        baseline_end = datetime.now() - timedelta(hours=hours)  # End of previous period
        
        baseline_count = session.query(func.count(SymbolSentimentModel.id)).filter(
            and_(
                SymbolSentimentModel.symbol == symbol.upper(),
                SymbolSentimentModel.timestamp >= baseline_start,
                SymbolSentimentModel.timestamp < baseline_end
            )
        ).scalar() or 0
        
        # If no baseline data, try using a longer lookback period
        if baseline_count == 0:
            # Try 7-day average as fallback
            week_ago = datetime.now() - timedelta(days=7)
            week_count = session.query(func.count(SymbolSentimentModel.id)).filter(
                and_(
                    SymbolSentimentModel.symbol == symbol.upper(),
                    SymbolSentimentModel.timestamp >= week_ago,
                    SymbolSentimentModel.timestamp < datetime.now() - timedelta(hours=hours)
                )
            ).scalar() or 0
            
            if week_count > 0:
                # Average mentions per hour, then multiply by current period hours
                baseline_count = (week_count / (7 * 24 - hours)) * hours
            else:
                # No historical data - can't determine trend
                return "stable"
        
        # Calculate percentage change
        if baseline_count == 0:
            # Any mentions when baseline is 0 = up
            return "up" if current_mention_count > 0 else "stable"
        
        percent_change = (current_mention_count - baseline_count) / baseline_count
        
        # Determine trend
        if percent_change > threshold_percent:
            return "up"
        elif percent_change < -threshold_percent:
            return "down"
        else:
            return "stable"
    
    except Exception as e:
        logger.warning(
            f"Error calculating volume trend for {symbol}: {e}",
            extra={
                'symbol': symbol,
                'current_mentions': current_mention_count,
                'hours': hours,
                'operation': 'calculate_volume_trend'
            }
        )
        return "stable"  # Default to stable on error
    
    finally:
        if session_created:
            session.close()


def calculate_volume_trend_from_repository(
    repository,
    symbol: str,
    current_mention_count: int,
    hours: int = 24,
    threshold_percent: float = 0.2
) -> str:
    """
    Calculate volume trend using repository (alternative interface)
    
    Args:
        repository: SentimentRepository instance
        symbol: Stock symbol
        current_mention_count: Current period mention count
        hours: Hours in current period
        threshold_percent: Percentage change threshold
    
    Returns:
        "up", "down", or "stable"
    """
    # Use repository's database session if available
    db = repository.db if hasattr(repository, 'db') else None
    return calculate_volume_trend(
        symbol=symbol,
        current_mention_count=current_mention_count,
        hours=hours,
        db=db,
        threshold_percent=threshold_percent
    )

