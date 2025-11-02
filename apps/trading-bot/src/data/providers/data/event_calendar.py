"""
Earnings & Event Calendar Provider
===================================

Integration with yfinance and other sources for earnings announcements,
economic events, and Fed meetings.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial

try:
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type
    )
except ImportError:
    # Fallback if tenacity not available
    def retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    stop_after_attempt = None
    wait_exponential = None
    retry_if_exception_type = None

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    import pandas as pd
except ImportError:
    pd = None

from ....config.settings import settings
from ....utils.cache import get_cache_manager
from ....utils.rate_limiter import get_rate_limiter

logger = logging.getLogger(__name__)

# Constants for impact score calculation
MARKET_CAP_THRESHOLDS = {
    'mega': 100_000_000_000,  # > $100B
    'large': 10_000_000_000,   # > $10B
    'mid': 1_000_000_000,      # > $1B
}

MARKET_CAP_SCORES = {
    'mega': 0.3,
    'large': 0.2,
    'mid': 0.1,
}

VOLUME_THRESHOLDS = {
    'high': 10_000_000,  # > 10M daily volume
    'medium': 1_000_000,  # > 1M
}

VOLUME_SCORES = {
    'high': 0.2,
    'medium': 0.1,
}

# Fed meeting dates by year (typically 8 meetings per year)
# Format: (month, day) tuples
# Note: These are approximate - actual dates vary slightly year to year
FED_MEETING_PATTERNS = {
    # Standard pattern: last week of Jan/Mar/May/Jun/Jul/Sep/Nov, mid-Dec
    'january_last': (1, 31),
    'march_mid': (3, 20),
    'may_first': (5, 1),
    'june_mid': (6, 12),
    'july_last': (7, 31),
    'september_mid': (9, 18),
    'november_first': (11, 7),
    'december_mid': (12, 18),
}


class EventType(Enum):
    """Event type enumeration"""
    EARNINGS = "earnings"
    ECONOMIC = "economic"
    FED_MEETING = "fed_meeting"
    CPI = "cpi"
    GDP = "gdp"
    UNEMPLOYMENT = "unemployment"
    OTHER = "other"


class EventImpact(Enum):
    """Event impact level"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class EarningsEvent:
    """Earnings announcement event"""
    symbol: str
    event_date: datetime
    estimated_eps: Optional[float] = None
    actual_eps: Optional[float] = None
    estimated_revenue: Optional[float] = None
    actual_revenue: Optional[float] = None
    fiscal_period: Optional[str] = None  # e.g., "Q1 2024"
    impact_score: float = 0.5  # 0.0 to 1.0
    is_confirmed: bool = False
    conference_call_time: Optional[datetime] = None
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class EconomicEvent:
    """Economic event (CPI, Fed meeting, etc.)"""
    event_type: EventType
    event_name: str
    event_date: datetime
    expected_value: Optional[float] = None
    actual_value: Optional[float] = None
    previous_value: Optional[float] = None
    impact_score: float = 0.5  # 0.0 to 1.0
    description: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class EventCalendar:
    """Calendar of events for a date range"""
    start_date: datetime
    end_date: datetime
    earnings_events: List[EarningsEvent] = field(default_factory=list)
    economic_events: List[EconomicEvent] = field(default_factory=list)
    
    def get_upcoming_events(self, days: int = 7) -> List[Any]:
        """Get all upcoming events in the next N days"""
        cutoff = datetime.now(timezone.utc) + timedelta(days=days)
        all_events = []
        
        for event in self.earnings_events:
            if event.event_date <= cutoff:
                all_events.append(('earnings', event))
        
        for event in self.economic_events:
            if event.event_date <= cutoff:
                all_events.append(('economic', event))
        
        # Sort by date
        all_events.sort(key=lambda x: x[1].event_date)
        return all_events


class EarningsCalendarProvider:
    """
    Earnings calendar provider using yfinance
    
    Fetches earnings dates and information from Yahoo Finance.
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
        self.cache_ttl = self.config.cache_ttl
        self.rate_limiter = get_rate_limiter("earnings_calendar")
        
        logger.info("EarningsCalendarProvider initialized")
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        return yf is not None and self.config.enabled
    
    def _calculate_impact_score(
        self,
        market_cap: Optional[float] = None,
        avg_volume: Optional[float] = None,
        historical_volatility: Optional[float] = None
    ) -> float:
        """
        Calculate impact score for earnings event (0.0 to 1.0)
        
        Factors:
        - Market cap (larger = higher impact)
        - Average volume (higher = higher impact)
        - Historical volatility (higher = higher impact)
        """
        score = 0.5  # Base score
        
        # Market cap impact (normalize to 0-0.3)
        if market_cap:
            if market_cap > MARKET_CAP_THRESHOLDS['mega']:
                score += MARKET_CAP_SCORES['mega']
            elif market_cap > MARKET_CAP_THRESHOLDS['large']:
                score += MARKET_CAP_SCORES['large']
            elif market_cap > MARKET_CAP_THRESHOLDS['mid']:
                score += MARKET_CAP_SCORES['mid']
        
        # Volume impact (normalize to 0-0.2)
        if avg_volume:
            if avg_volume > VOLUME_THRESHOLDS['high']:
                score += VOLUME_SCORES['high']
            elif avg_volume > VOLUME_THRESHOLDS['medium']:
                score += VOLUME_SCORES['medium']
        
        # Cap at 1.0
        return min(score, 1.0)
    
    def get_earnings_date(self, symbol: str, only_future: bool = True) -> Optional[datetime]:
        """
        Get next earnings announcement date for a symbol
        
        Args:
            symbol: Stock symbol
            only_future: If True, only return dates in the future (default: True)
            
        Returns:
            Earnings date as datetime or None
        """
        symbol = symbol.upper()
        cache_key = f"earnings_date_{symbol}"
        
        # Check cache
        cached = self.cache.get(cache_key)
        if cached:
            if only_future and cached < datetime.now(timezone.utc):
                # Clear stale cache entry
                self.cache.delete(cache_key)
                cached = None
            else:
                return cached
        
        # Apply retry logic for transient failures
        max_retries = getattr(self.config, 'retry_attempts', 3)
        backoff_multiplier = getattr(self.config, 'retry_backoff_multiplier', 1.0)
        
        info = None
        for attempt in range(max_retries):
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                break  # Success, exit retry loop
            except (ConnectionError, TimeoutError, KeyError) as e:
                if attempt < max_retries - 1:
                    wait_time = min(backoff_multiplier * (2 ** attempt), 10)  # Cap at 10 seconds
                    logger.debug(f"Transient error fetching ticker info for {symbol} (attempt {attempt + 1}/{max_retries}): {e}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.warning(f"Failed to fetch ticker info for {symbol} after {max_retries} attempts: {e}")
                    return None
        
        if info is None:
            logger.error(f"Unexpected: info is None after retry loop for {symbol}")
            return None
        
        try:
            # Try different field names for earnings date
            earnings_date = None
            for field in ['earningsDate', 'nextEarningsDate', 'nextFiscalDate']:
                if field in info and info[field]:
                    earnings_date = info[field]
                    break
            
            if earnings_date:
                # Handle different date formats
                if isinstance(earnings_date, list) and len(earnings_date) > 0:
                    earnings_date = earnings_date[0]
                
                # Convert timestamp to datetime
                if isinstance(earnings_date, (int, float)):
                    earnings_date = datetime.fromtimestamp(earnings_date, tz=timezone.utc)
                elif isinstance(earnings_date, str):
                    try:
                        earnings_date = datetime.fromisoformat(earnings_date.replace('Z', '+00:00'))
                    except:
                        # Try parsing other formats
                        try:
                            from dateutil.parser import parse
                            earnings_date = parse(earnings_date)
                        except ImportError:
                            logger.warning(f"dateutil not available, cannot parse: {earnings_date}")
                            return None
                        except Exception:
                            logger.warning(f"Could not parse earnings date: {earnings_date}")
                            return None
                
                # Ensure timezone awareness
                if earnings_date.tzinfo is None:
                    earnings_date = earnings_date.replace(tzinfo=timezone.utc)
                
                # Filter out past dates if requested
                if only_future and earnings_date < datetime.now(timezone.utc):
                    logger.debug(f"Earnings date {earnings_date} is in the past, skipping")
                    return None
                
                # Cache result
                self.cache.set(cache_key, earnings_date, ttl=self.cache_ttl)
                return earnings_date
            else:
                logger.debug(f"No earnings date found for {symbol}")
                return None
        
        except (KeyError, AttributeError, TypeError, ValueError) as e:
            logger.debug(f"Error parsing earnings date for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting earnings date for {symbol}: {e}", exc_info=True)
            return None
    
    def get_earnings_event(self, symbol: str) -> Optional[EarningsEvent]:
        """
        Get detailed earnings event information for a symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            EarningsEvent object or None
        """
        symbol = symbol.upper()
        cache_key = f"earnings_event_{symbol}"
        
        # Check cache
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        # Apply rate limiting (yfinance has no official limit, but be conservative: 100/min)
        # Note: rate_limit_enabled doesn't exist in EventCalendarSettings, but we check anyway for safety
        if self.rate_limiter and getattr(self.config, 'rate_limit_enabled', True):
            is_allowed, rate_status = self.rate_limiter.check_rate_limit(limit=100, window_seconds=60)
            if not is_allowed:
                logger.debug(f"Rate limit approaching for {symbol}, waiting...")
                self.rate_limiter.wait_if_needed(limit=100, window_seconds=60)
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get earnings date
            event_date = self.get_earnings_date(symbol)
            if not event_date:
                return None
            
            # Extract earnings estimates
            # Try multiple fields for EPS estimates
            estimated_eps = (
                info.get('forwardEps') or 
                info.get('trailingEps') or 
                info.get('revenuePerShare') or 
                None
            )
            # Try to get actual EPS from quarterly earnings
            actual_eps = None
            fiscal_period = None
            
            try:
                if pd is not None:
                    earnings = ticker.quarterly_earnings
                    if earnings is not None and not earnings.empty:
                        # Get most recent quarter
                        latest_quarter = earnings.iloc[0]
                        if 'Diluted EPS' in latest_quarter:
                            actual_eps = float(latest_quarter['Diluted EPS'])
                        # Try to get date for fiscal period
                        if hasattr(earnings.index[0], 'month') and hasattr(earnings.index[0], 'year'):
                            quarter = (earnings.index[0].month - 1) // 3 + 1
                            fiscal_period = f"{earnings.index[0].year}-Q{quarter}"
            except Exception as e:
                logger.debug(f"Could not get quarterly earnings: {e}")
            
            # Calculate impact score
            market_cap = info.get('marketCap')
            avg_volume = info.get('averageVolume')
            impact_score = self._calculate_impact_score(
                market_cap=market_cap,
                avg_volume=avg_volume
            )
            
            event = EarningsEvent(
                symbol=symbol,
                event_date=event_date,
                estimated_eps=estimated_eps,
                actual_eps=actual_eps,
                fiscal_period=fiscal_period,
                impact_score=impact_score,
                is_confirmed=True,  # If we have a date, it's confirmed
                raw_data=info
            )
            
            # Cache result
            self.cache.set(cache_key, event, ttl=self.cache_ttl)
            return event
        
        except (KeyError, AttributeError, TypeError) as e:
            logger.debug(f"Error getting earnings event for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting earnings event for {symbol}: {e}", exc_info=True)
            return None
    
    def get_upcoming_earnings(
        self,
        symbols: List[str],
        days: int = 30,
        max_workers: Optional[int] = None
    ) -> List[EarningsEvent]:
        """
        Get upcoming earnings events for multiple symbols (with concurrent processing)
        
        Args:
            symbols: List of stock symbols
            days: Number of days to look ahead
            max_workers: Maximum number of worker threads (default: min(10, len(symbols)))
            
        Returns:
            List of EarningsEvent objects, sorted by date
        """
        cutoff_date = datetime.now(timezone.utc) + timedelta(days=days)
        upcoming_events = []
        
        if not symbols:
            return []
        
        # Determine optimal worker count from config
        if max_workers is None:
            max_workers = min(
                getattr(self.config, 'max_concurrent_workers', 10),
                len(symbols)
            )
        
        # Use ThreadPoolExecutor for concurrent processing (yfinance is synchronous)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_symbol = {
                executor.submit(self.get_earnings_event, symbol): symbol
                for symbol in symbols
            }
            
            # Process completed tasks
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    event = future.result()
                    if event and event.event_date <= cutoff_date:
                        upcoming_events.append(event)
                except Exception as e:
                    logger.debug(f"Error getting earnings for {symbol}: {e}")
                    continue
        
        # Sort by date
        upcoming_events.sort(key=lambda x: x.event_date)
        return upcoming_events


class EconomicEventProvider:
    """
    Economic event provider
    
    Provides information about economic events like CPI, Fed meetings, GDP, etc.
    Currently provides basic structure - can be extended with external APIs.
    """
    
    def __init__(self):
        """Initialize economic event provider"""
        self.config = settings.event_calendar
        self.cache = get_cache_manager()
        self.cache_ttl = self.config.cache_ttl  # Use config TTL for consistency
        
        logger.info("EconomicEventProvider initialized")
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        return True  # Basic implementation always available
    
    def get_fed_meeting_schedule(
        self, 
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> List[EconomicEvent]:
        """
        Get Federal Reserve meeting schedule for a range of years
        
        Args:
            start_year: Start year (default: current year)
            end_year: End year (default: current year + 1)
            
        Returns:
            List of EconomicEvent objects (sorted by date)
        """
        now = datetime.now(timezone.utc)
        if start_year is None:
            start_year = now.year
        if end_year is None:
            end_year = start_year + 1
        
        events = []
        
        # Generate Fed meeting dates for each year in range
        for year in range(start_year, end_year + 1):
            # Use the pattern to generate dates for this year
            # Adjust dates slightly based on weekday (Fed typically meets Tue-Wed)
            for pattern_name, (month, day) in FED_MEETING_PATTERNS.items():
                try:
                    date = datetime(year, month, day, tzinfo=timezone.utc)
                    
                    # Adjust to nearest Tuesday (Fed typically meets Tue-Wed)
                    # If the day falls on weekend, move to next Tuesday
                    weekday = date.weekday()
                    if weekday >= 5:  # Saturday (5) or Sunday (6)
                        days_to_add = (1 - weekday) % 7  # Days to next Monday
                        date += timedelta(days=days_to_add + 1)  # Then add 1 for Tuesday
                    elif weekday == 0:  # Monday
                        date += timedelta(days=1)  # Move to Tuesday
                    
                    # Only add future events
                    if date >= now:
                        events.append(EconomicEvent(
                            event_type=EventType.FED_MEETING,
                            event_name=f"Federal Reserve FOMC Meeting - {date.strftime('%B %Y')}",
                            event_date=date,
                            impact_score=0.9,  # High impact
                            description="Federal Open Market Committee meeting to set interest rates"
                        ))
                except ValueError:
                    # Handle invalid dates (e.g., Feb 29 in non-leap years)
                    logger.debug(f"Invalid date for Fed meeting: {year}-{month}-{day}")
                    continue
        
        # Sort by date
        events.sort(key=lambda x: x.event_date)
        return events
    
    def get_cpi_schedule(self, year: int = None) -> List[EconomicEvent]:
        """
        Get CPI release schedule
        
        CPI is typically released around the 10th-15th of each month
        
        Args:
            year: Year to get schedule for (default: current year)
            
        Returns:
            List of EconomicEvent objects
        """
        if year is None:
            year = datetime.now(timezone.utc).year
        
        events = []
        now = datetime.now(timezone.utc)
        # CPI typically released around 10th-15th of each month
        for month in range(1, 13):
            # Approximate date (actual varies by month - should use actual BLS calendar)
            cpi_date = datetime(year, month, 12, tzinfo=timezone.utc)
            if cpi_date >= now:
                events.append(EconomicEvent(
                    event_type=EventType.CPI,
                    event_name=f"Consumer Price Index (CPI) - {cpi_date.strftime('%B %Y')}",
                    event_date=cpi_date,
                    impact_score=0.7,  # Medium-high impact
                    description="Monthly CPI data release by Bureau of Labor Statistics"
                ))
        
        return events


class EventCalendarProvider:
    """
    Unified event calendar provider
    
    Combines earnings and economic events into a single calendar.
    """
    
    def __init__(self):
        """Initialize event calendar provider"""
        self.earnings_provider = EarningsCalendarProvider()
        self.economic_provider = EconomicEventProvider()
        self.cache = get_cache_manager()
        
        logger.info("EventCalendarProvider initialized")
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        return self.earnings_provider.is_available() and self.economic_provider.is_available()
    
    def get_calendar(
        self,
        symbols: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_economic: bool = True
    ) -> EventCalendar:
        """
        Get comprehensive event calendar
        
        Args:
            symbols: List of symbols to get earnings for (None = no earnings)
            start_date: Start date for calendar (default: now)
            end_date: End date for calendar (default: 30 days from now)
            include_economic: Whether to include economic events
            
        Returns:
            EventCalendar object
        """
        if start_date is None:
            start_date = datetime.now(timezone.utc)
        if end_date is None:
            end_date = start_date + timedelta(days=30)
        
        # Validate date range
        if start_date >= end_date:
            raise ValueError(f"Invalid date range: start_date ({start_date}) must be before end_date ({end_date})")
        
        calendar = EventCalendar(
            start_date=start_date,
            end_date=end_date
        )
        
        # Get earnings events
        if symbols:
            days_ahead = (end_date - start_date).days
            calendar.earnings_events = self.earnings_provider.get_upcoming_earnings(
                symbols=symbols,
                days=days_ahead
            )
            # Filter by date range
            calendar.earnings_events = [
                e for e in calendar.earnings_events
                if start_date <= e.event_date <= end_date
            ]
        
        # Get economic events
        if include_economic:
            # Get Fed meetings for current year and next year to cover date range
            start_year = start_date.year
            end_year = end_date.year + 1  # Include next year to be safe
            fed_meetings = self.economic_provider.get_fed_meeting_schedule(
                start_year=start_year,
                end_year=end_year
            )
            # Get CPI for all years in range
            cpi_releases = []
            for year in range(start_year, end_year + 1):
                cpi_releases.extend(self.economic_provider.get_cpi_schedule(year))
            
            calendar.economic_events = fed_meetings + cpi_releases
            # Filter by date range
            calendar.economic_events = [
                e for e in calendar.economic_events
                if start_date <= e.event_date <= end_date
            ]
        
        return calendar
    
    def get_events_for_symbol(
        self,
        symbol: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get all events (earnings + economic) relevant to a symbol
        
        Args:
            symbol: Stock symbol
            days: Number of days to look ahead
            
        Returns:
            Dictionary with earnings and relevant economic events
        """
        earnings_event = self.earnings_provider.get_earnings_event(symbol)
        
        # Get economic events
        end_date = datetime.now(timezone.utc) + timedelta(days=days)
        calendar = self.get_calendar(
            symbols=[symbol],
            end_date=end_date,
            include_economic=True
        )
        
        return {
            'symbol': symbol,
            'earnings_event': earnings_event,
            'economic_events': calendar.economic_events,
            'upcoming_events': calendar.get_upcoming_events(days=days)
        }
