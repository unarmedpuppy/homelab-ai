"""
Earnings Calendar Provider
==========================

Tracks earnings announcements and other corporate events using yfinance.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field

try:
    import yfinance as yf
    import pandas as pd
except ImportError:
    yf = None
    pd = None

from ...config.settings import settings
from ...utils.cache import get_cache_manager

logger = logging.getLogger(__name__)


@dataclass
class EarningsEvent:
    """Earnings announcement event"""
    symbol: str
    event_date: datetime
    event_type: str = "earnings"  # earnings, guidance, etc.
    confirmed: bool = True
    estimated: bool = False
    time_of_day: Optional[str] = None  # "BMO" (Before Market Open), "AMC" (After Market Close)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventCalendarEntry:
    """Calendar entry for a symbol"""
    symbol: str
    events: List[EarningsEvent] = field(default_factory=list)
    next_earnings_date: Optional[datetime] = None
    last_earnings_date: Optional[datetime] = None
    earnings_frequency: str = "quarterly"  # quarterly, annual
    metadata: Dict[str, Any] = field(default_factory=dict)


class EarningsCalendarProvider:
    """
    Earnings calendar provider using yfinance
    
    Tracks earnings announcements and upcoming events for symbols.
    """
    
    def __init__(self):
        """Initialize earnings calendar provider"""
        if yf is None:
            raise ImportError(
                "yfinance is required for earnings calendar. "
                "Install with: pip install yfinance"
            )
        
        self.config = settings.event_calendar
        self.cache = get_cache_manager()
        
        logger.info("EarningsCalendarProvider initialized")
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        return yf is not None and self.config.enabled
    
    def get_earnings_dates(self, symbol: str) -> Optional[List[datetime]]:
        """
        Get earnings dates for a symbol
        
        Args:
            symbol: Stock symbol (validated and uppercased)
            
        Returns:
            List of earnings dates or None
        """
        # Input validation
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        symbol = symbol.strip().upper()
        if not symbol:
            raise ValueError("Symbol cannot be empty after stripping")
        
        # Check cache
        cache_key = f"earnings:dates:{symbol}"
        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            logger.debug(f"Returning cached earnings dates for {symbol}")
            # Convert ISO strings back to datetime objects
            if cached_data and isinstance(cached_data, list):
                try:
                    return [pd.to_datetime(d).to_pydatetime() if isinstance(d, str) else d for d in cached_data]
                except Exception as e:
                    logger.warning(f"Error deserializing cached dates: {e}")
                    # Cache might be corrupted, continue to fetch fresh data
            else:
                return cached_data
        
        if not self.is_available():
            return None
        
        try:
            ticker = yf.Ticker(symbol)
            
            dates = []
            
            # Try getting earnings dates from ticker.info (most reliable)
            try:
                ticker_info = ticker.info
                
                # Check for next earnings date
                if 'earningsDate' in ticker_info:
                    earnings_date_list = ticker_info['earningsDate']
                    if isinstance(earnings_date_list, list):
                        for ed in earnings_date_list:
                            try:
                                if isinstance(ed, (int, float)):
                                    # Unix timestamp
                                    dt = datetime.fromtimestamp(ed)
                                else:
                                    dt = pd.to_datetime(ed).to_pydatetime()
                                dates.append(dt)
                            except (ValueError, TypeError, OSError) as e:
                                logger.debug(f"Could not parse earnings date {ed}: {e}")
                
                # Also check for next earnings date (single value)
                if 'nextEarningsDate' in ticker_info and ticker_info['nextEarningsDate']:
                    try:
                        next_date = ticker_info['nextEarningsDate']
                        if isinstance(next_date, (int, float)):
                            dt = datetime.fromtimestamp(next_date)
                        else:
                            dt = pd.to_datetime(next_date).to_pydatetime()
                        if dt not in dates:
                            dates.append(dt)
                    except (ValueError, TypeError, OSError) as e:
                        logger.debug(f"Could not parse nextEarningsDate: {e}")
                        
            except (KeyError, AttributeError, ValueError) as e:
                logger.debug(f"Error getting earnings dates from info: {e}")
            
            # Try calendar method as alternative
            try:
                earnings_calendar = ticker.calendar
                if earnings_calendar is not None and not earnings_calendar.empty:
                    # Calendar DataFrame has dates in index or as values
                    if hasattr(earnings_calendar, 'index'):
                        for idx in earnings_calendar.index:
                            try:
                                if hasattr(idx, 'to_pydatetime'):
                                    dt = idx.to_pydatetime()
                                    if dt not in dates:
                                        dates.append(dt)
                                elif isinstance(idx, datetime):
                                    if idx not in dates:
                                        dates.append(idx)
                            except (AttributeError, ValueError, TypeError) as e:
                                logger.debug(f"Error parsing calendar index {idx}: {e}")
            except (AttributeError, ValueError) as e:
                logger.debug(f"Error getting earnings dates from calendar: {e}")
            
            if not dates:
                logger.debug(f"No earnings dates found for {symbol}")
                return None
            
            # Cache result (convert datetime objects to ISO strings for JSON serialization)
            dates_serializable = [d.isoformat() if isinstance(d, datetime) else d for d in dates]
            self.cache.set(cache_key, dates_serializable, ttl=self.config.cache_ttl)
            
            logger.debug(f"Found {len(dates)} earnings dates for {symbol}")
            return dates
            
        except ValueError as e:
            logger.error(f"Invalid input for earnings dates query: {symbol}, error: {e}")
            raise
        except (KeyError, AttributeError) as e:
            logger.warning(f"Data structure error getting earnings dates for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting earnings dates for {symbol}: {e}", exc_info=True)
            return None
    
    def get_upcoming_earnings(
        self,
        symbol: str,
        days_ahead: Optional[int] = None
    ) -> Optional[List[EarningsEvent]]:
        # Input validation
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        if days_ahead is not None and (not isinstance(days_ahead, int) or days_ahead <= 0):
            raise ValueError("days_ahead must be a positive integer")
        
        symbol = symbol.strip().upper()
        days_ahead = days_ahead or self.config.lookahead_days
        
        dates = self.get_earnings_dates(symbol)
        
        if not dates:
            return None
        
        now = datetime.now()
        cutoff = now + timedelta(days=days_ahead)
        
        # Filter to upcoming dates
        upcoming = [d for d in dates if now <= d <= cutoff]
        upcoming.sort()  # Sort by date
        
        events = []
        for date in upcoming:
            events.append(EarningsEvent(
                symbol=symbol,
                event_date=date,
                event_type="earnings",
                confirmed=True,
                estimated=False
            ))
        
        return events if events else None
    
    def get_next_earnings_date(self, symbol: str) -> Optional[datetime]:
        """
        Get the next upcoming earnings date for a symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Next earnings date or None
        """
        upcoming = self.get_upcoming_earnings(symbol, days_ahead=self.config.lookahead_days)
        
        if not upcoming:
            return None
        
        return upcoming[0].event_date if upcoming else None
    
    def get_past_earnings(self, symbol: str, days_back: int = 365) -> Optional[List[EarningsEvent]]:
        """
        Get past earnings events
        
        Args:
            symbol: Stock symbol
            days_back: Days to look back
            
        Returns:
            List of past earnings events
        """
        symbol = symbol.upper()
        
        dates = self.get_earnings_dates(symbol)
        
        if not dates:
            return None
        
        now = datetime.now()
        cutoff = now - timedelta(days=days_back)
        
        # Filter to past dates
        past = [d for d in dates if cutoff <= d < now]
        past.sort(reverse=True)  # Most recent first
        
        events = []
        for date in past:
            events.append(EarningsEvent(
                symbol=symbol,
                event_date=date,
                event_type="earnings",
                confirmed=True,
                estimated=False
            ))
        
        return events if events else None
    
    def get_calendar(self, symbol: str) -> Optional[EventCalendarEntry]:
        """
        Get complete calendar entry for a symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            EventCalendarEntry with all events
        """
        symbol = symbol.upper()
        
        upcoming = self.get_upcoming_earnings(symbol)
        past = self.get_past_earnings(symbol)
        
        all_events = (past or []) + (upcoming or [])
        
        if not all_events:
            return None
        
        next_earnings = upcoming[0].event_date if upcoming else None
        last_earnings = past[0].event_date if past else None
        
        return EventCalendarEntry(
            symbol=symbol,
            events=all_events,
            next_earnings_date=next_earnings,
            last_earnings_date=last_earnings,
            earnings_frequency="quarterly"  # Default assumption
        )
    
    def get_earnings_calendar(
        self,
        symbols: List[str],
        days_ahead: Optional[int] = None
    ) -> Dict[str, List[EarningsEvent]]:
        """
        Get earnings calendar for multiple symbols
        
        Args:
            symbols: List of stock symbols
            days_ahead: Days ahead to look
            
        Returns:
            Dictionary mapping symbol -> list of earnings events
        """
        calendar = {}
        
        for symbol in symbols:
            upcoming = self.get_upcoming_earnings(symbol, days_ahead=days_ahead)
            if upcoming:
                calendar[symbol] = upcoming
        
        return calendar
    
    def is_near_earnings(self, symbol: str, days_threshold: int = 7) -> bool:
        # Input validation
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        if not isinstance(days_threshold, int) or days_threshold <= 0:
            raise ValueError("days_threshold must be a positive integer")
        
        symbol = symbol.strip().upper()
        next_date = self.get_next_earnings_date(symbol)
        
        if not next_date:
            return False
        
        days_until = (next_date - datetime.now()).days
        return 0 <= days_until <= days_threshold


# Module-level provider instance for singleton pattern
_provider_instance: Optional[EarningsCalendarProvider] = None


def get_provider_instance() -> EarningsCalendarProvider:
    """Get or create singleton provider instance"""
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = EarningsCalendarProvider()
    return _provider_instance

