"""
Price data service.

Fetches historical price data from external APIs with caching support.
Supports multiple providers: Alpha Vantage (primary), yfinance (fallback), CoinGecko (crypto).
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
import httpx
import logging

# Helper to ensure timezone-naive datetime
def _naive_datetime(dt: datetime) -> datetime:
    """Convert timezone-aware datetime to naive, or return naive datetime as-is."""
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


def _is_regular_trading_hours(timestamp: datetime, timeframe: str) -> bool:
    """
    Check if timestamp is during regular trading hours (9:30 AM - 4:00 PM ET).
    
    For intraday timeframes, filters out pre-market and after-hours data.
    For daily timeframes, always returns True.
    
    Args:
        timestamp: Naive datetime to check
        timeframe: Timeframe string (1m, 5m, 15m, 1h, 1d)
    
    Returns:
        True if during regular trading hours or daily timeframe, False otherwise
    """
    # For daily data, include all timestamps
    if timeframe == "1d":
        return True
    
    # For intraday data, filter for regular trading hours
    # Regular trading hours: 9:30 AM - 4:00 PM ET
    # yfinance returns timestamps in ET timezone (naive, but represents ET)
    # However, we need to check if the hour is reasonable for ET market hours
    hour = timestamp.hour
    minute = timestamp.minute
    
    # Regular trading hours: 9:30 AM - 4:00 PM ET
    # Include: 9:30 AM to 3:59 PM (hour == 9 and minute >= 30) OR (hour >= 10 and hour < 16)
    # Exclude: before 9:30 AM or at/after 4:00 PM
    
    # Check if it's before 9:30 AM
    if hour < 9 or (hour == 9 and minute < 30):
        return False
    
    # Check if it's at or after 4:00 PM (16:00)
    if hour >= 16:
        return False
    
    # If we get here, it's between 9:30 AM and 3:59 PM
    return True

from app.models.price_cache import PriceCache
from app.schemas.charts import PriceDataPoint, PriceDataResponse
from app.config import settings

logger = logging.getLogger(__name__)

# Cache duration in hours
CACHE_DURATION_DAILY = 24  # 24 hours for daily data
CACHE_DURATION_INTRADAY = 1  # 1 hour for intraday data


async def get_price_data(
    db: AsyncSession,
    ticker: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    timeframe: str = "1h",
) -> PriceDataResponse:
    """
    Get price data for a ticker with caching.
    
    Args:
        db: Database session
        ticker: Ticker symbol
        start_date: Start date (default: 1 year ago)
        end_date: End date (default: now)
        timeframe: Timeframe (1m, 5m, 15m, 1h, 1d)
    
    Returns:
        PriceDataResponse with price data
    """
    # Set defaults (ensure timezone-naive)
    if end_date is None:
        end_date = _naive_datetime(datetime.now())
    else:
        end_date = _naive_datetime(end_date)
    if start_date is None:
        start_date = _naive_datetime(end_date - timedelta(days=365))
    else:
        start_date = _naive_datetime(start_date)
    
    # Normalize ticker (uppercase, strip)
    ticker = ticker.upper().strip()
    
    # Check cache first
    cached_data = await _get_cached_data(db, ticker, start_date, end_date, timeframe)
    
    # Filter cached data for regular trading hours (if intraday)
    if timeframe != "1d":
        cached_data = [point for point in cached_data if _is_regular_trading_hours(point.timestamp, timeframe)]
        logger.info(f"Filtered cached data: {len(cached_data)} points after trading hours filter")
    
    # Determine what data we need to fetch
    missing_ranges = _find_missing_ranges(cached_data, start_date, end_date, timeframe)
    
    # Fetch missing data (limit to reasonable ranges to avoid timeouts)
    if missing_ranges:
        # Limit the number of ranges to fetch at once (to avoid timeouts)
        # For large date ranges, we'll fetch in chunks
        max_ranges = 5  # Limit concurrent range fetches
        ranges_to_fetch = missing_ranges[:max_ranges]
        
        fetched_data = await _fetch_price_data(ticker, ranges_to_fetch, timeframe)
        
        # Cache the fetched data
        if fetched_data:
            await _cache_price_data(db, ticker, fetched_data, timeframe)
            # Merge with cached data
            cached_data = _merge_price_data(cached_data, fetched_data)
        
        # If there are more ranges, we'll fetch them on subsequent requests
        # This prevents timeouts on initial load
    
    # Sort by timestamp
    cached_data.sort(key=lambda x: x.timestamp)
    
    # Filter to requested range
    filtered_data = [
        point for point in cached_data
        if start_date <= point.timestamp <= end_date
    ]
    
    # If we have some data, return it even if not complete (to avoid timeout)
    # Subsequent requests will fill in the gaps
    if filtered_data:
        logger.info(f"Returning {len(filtered_data)} data points for {ticker} (may be incomplete)")
        return PriceDataResponse(
            ticker=ticker,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            data=filtered_data,
        )
    
    # If no data at all, return empty response
    return PriceDataResponse(
        ticker=ticker,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        data=[],
    )


async def _get_cached_data(
    db: AsyncSession,
    ticker: str,
    start_date: datetime,
    end_date: datetime,
    timeframe: str,
) -> List[PriceDataPoint]:
    """
    Get cached price data from database.
    
    Args:
        db: Database session
        ticker: Ticker symbol
        start_date: Start date
        end_date: End date
        timeframe: Timeframe
    
    Returns:
        List of cached price data points
    """
    # Determine cache expiration (ensure timezone-naive)
    cache_duration = CACHE_DURATION_DAILY if timeframe == "1d" else CACHE_DURATION_INTRADAY
    cache_expiry = _naive_datetime(datetime.now()) - timedelta(hours=cache_duration)
    
    # Ensure dates are timezone-naive for database comparison
    start_date_naive = _naive_datetime(start_date)
    end_date_naive = _naive_datetime(end_date)
    
    query = (
        select(PriceCache)
        .where(
            and_(
                PriceCache.ticker == ticker,
                PriceCache.timeframe == timeframe,
                PriceCache.timestamp >= start_date_naive,
                PriceCache.timestamp <= end_date_naive,
                PriceCache.cached_at >= cache_expiry,
            )
        )
        .order_by(PriceCache.timestamp)
    )
    
    result = await db.execute(query)
    cached_records = result.scalars().all()
    
    # Convert to PriceDataPoint
    data_points = []
    for record in cached_records:
        if record.close_price is not None:  # Only include records with valid data
            data_points.append(PriceDataPoint(
                timestamp=record.timestamp,
                open=record.open_price or record.close_price,
                high=record.high_price or record.close_price,
                low=record.low_price or record.close_price,
                close=record.close_price,
                volume=record.volume,
            ))
    
    return data_points


def _find_missing_ranges(
    cached_data: List[PriceDataPoint],
    start_date: datetime,
    end_date: datetime,
    timeframe: str,
) -> List[tuple[datetime, datetime]]:
    """
    Find date ranges that are missing from cache.
    
    Args:
        cached_data: List of cached data points
        start_date: Start date
        end_date: End date
        timeframe: Timeframe
    
    Returns:
        List of (start, end) tuples for missing ranges
    """
    if not cached_data:
        return [(start_date, end_date)]
    
    missing_ranges = []
    
    # Check if we have data at the start
    if cached_data[0].timestamp > start_date:
        missing_ranges.append((start_date, cached_data[0].timestamp))
    
    # Check for gaps in the middle
    for i in range(len(cached_data) - 1):
        gap_start = cached_data[i].timestamp
        gap_end = cached_data[i + 1].timestamp
        
        # Calculate expected interval based on timeframe
        interval = _get_timeframe_interval(timeframe)
        if (gap_end - gap_start) > interval * 2:  # More than 2 intervals = gap
            missing_ranges.append((gap_start + interval, gap_end - interval))
    
    # Check if we have data at the end
    if cached_data[-1].timestamp < end_date:
        missing_ranges.append((cached_data[-1].timestamp, end_date))
    
    return missing_ranges


def _get_timeframe_interval(timeframe: str) -> timedelta:
    """Get timedelta for a timeframe."""
    intervals = {
        "1m": timedelta(minutes=1),
        "5m": timedelta(minutes=5),
        "15m": timedelta(minutes=15),
        "1h": timedelta(hours=1),
        "1d": timedelta(days=1),
    }
    return intervals.get(timeframe, timedelta(hours=1))


async def _fetch_price_data(
    ticker: str,
    date_ranges: List[tuple[datetime, datetime]],
    timeframe: str,
) -> List[PriceDataPoint]:
    """
    Fetch price data from external APIs.
    
    Tries providers in order: Alpha Vantage -> yfinance -> CoinGecko (for crypto)
    
    Args:
        ticker: Ticker symbol
        date_ranges: List of (start, end) date ranges to fetch
        timeframe: Timeframe
    
    Returns:
        List of price data points
    """
    # Determine if this is crypto
    is_crypto = _is_crypto_ticker(ticker)
    
    # Try providers in order, but limit date range to avoid timeouts
    all_data = []
    for start_date, end_date in date_ranges:
        # Limit date range to 90 days max per request to avoid timeouts
        max_days = 90
        if (end_date - start_date).days > max_days:
            # Split large ranges into smaller chunks
            current_start = start_date
            while current_start < end_date:
                current_end = min(current_start + timedelta(days=max_days), end_date)
                chunk_data = await _fetch_from_providers(ticker, current_start, current_end, timeframe, is_crypto)
                if chunk_data:
                    all_data.extend(chunk_data)
                current_start = current_end
        else:
            chunk_data = await _fetch_from_providers(ticker, start_date, end_date, timeframe, is_crypto)
            if chunk_data:
                all_data.extend(chunk_data)
    
    return all_data


async def _fetch_from_providers(
    ticker: str,
    start_date: datetime,
    end_date: datetime,
    timeframe: str,
    is_crypto: bool,
) -> Optional[List[PriceDataPoint]]:
    """Fetch from providers in order with timeout handling."""
    # Try Alpha Vantage first (if API key available)
    if settings.alpha_vantage_api_key and not is_crypto:
        try:
            data = await _fetch_alpha_vantage(ticker, start_date, end_date, timeframe)
            if data:
                return data
        except Exception as e:
            logger.warning(f"Alpha Vantage fetch failed for {ticker}: {e}")
    
    # Try CoinGecko for crypto
    if is_crypto and settings.coingecko_api_key:
        try:
            data = await _fetch_coingecko(ticker, start_date, end_date, timeframe)
            if data:
                return data
        except Exception as e:
            logger.warning(f"CoinGecko fetch failed for {ticker}: {e}")
    
    # Fallback to yfinance (no API key needed)
    try:
        data = await _fetch_yfinance(ticker, start_date, end_date, timeframe)
        if data:
            return data
    except Exception as e:
        logger.warning(f"yfinance fetch failed for {ticker}: {e}")
    
    return None


def _is_crypto_ticker(ticker: str) -> bool:
    """Check if ticker is a crypto ticker."""
    # Common crypto patterns
    crypto_patterns = ["BTC", "ETH", "USDT", "USDC", "BNB", "ADA", "SOL", "XRP", "DOT", "DOGE"]
    return any(pattern in ticker.upper() for pattern in crypto_patterns)


async def _fetch_alpha_vantage(
    ticker: str,
    start_date: datetime,
    end_date: datetime,
    timeframe: str,
) -> Optional[List[PriceDataPoint]]:
    """
    Fetch price data from Alpha Vantage API.
    
    Args:
        ticker: Ticker symbol
        start_date: Start date
        end_date: End date
        timeframe: Timeframe
    
    Returns:
        List of price data points or None if failed
    """
    if not settings.alpha_vantage_api_key:
        return None
    
    # Map timeframe to Alpha Vantage function
    function_map = {
        "1m": "TIME_SERIES_INTRADAY",
        "5m": "TIME_SERIES_INTRADAY",
        "15m": "TIME_SERIES_INTRADAY",
        "1h": "TIME_SERIES_INTRADAY",
        "1d": "TIME_SERIES_DAILY_ADJUSTED",
    }
    
    function = function_map.get(timeframe, "TIME_SERIES_DAILY_ADJUSTED")
    
    # Build URL
    base_url = "https://www.alphavantage.co/query"
    params = {
        "function": function,
        "symbol": ticker,
        "apikey": settings.alpha_vantage_api_key,
    }
    
    if timeframe != "1d":
        interval_map = {
            "1m": "1min",
            "5m": "5min",
            "15m": "15min",
            "1h": "60min",
        }
        params["interval"] = interval_map.get(timeframe, "60min")
    
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
    
    # Parse response
    if "Error Message" in data or "Note" in data:
        logger.warning(f"Alpha Vantage API error: {data.get('Error Message', data.get('Note'))}")
        return None
    
    # Extract time series key
    time_series_key = None
    for key in data.keys():
        if "Time Series" in key:
            time_series_key = key
            break
    
    if not time_series_key:
        return None
    
    time_series = data[time_series_key]
    
    # Convert to PriceDataPoint list
    data_points = []
    for timestamp_str, values in time_series.items():
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S" if ":" in timestamp_str else "%Y-%m-%d")
        # Ensure timezone-naive
        timestamp = _naive_datetime(timestamp)
        
        # Filter by date range (ensure dates are naive)
        start_naive = _naive_datetime(start_date)
        end_naive = _naive_datetime(end_date)
        if start_naive <= timestamp <= end_naive:
            # Filter for regular trading hours only
            if not _is_regular_trading_hours(timestamp, timeframe):
                continue
            
            # Alpha Vantage uses different keys for daily vs intraday
                open_key = values.get("1. open")
                high_key = values.get("2. high")
                low_key = values.get("3. low")
                close_key = values.get("4. close")
            volume_key = values.get("5. volume") or values.get("6. volume", 0)
            
            data_points.append(PriceDataPoint(
                timestamp=_naive_datetime(timestamp),
                open=Decimal(str(open_key or "0")),
                high=Decimal(str(high_key or "0")),
                low=Decimal(str(low_key or "0")),
                close=Decimal(str(close_key or "0")),
                volume=int(volume_key) if volume_key else None,
            ))
    
    return sorted(data_points, key=lambda x: x.timestamp)


async def _fetch_yfinance(
    ticker: str,
    start_date: datetime,
    end_date: datetime,
    timeframe: str,
) -> Optional[List[PriceDataPoint]]:
    """
    Fetch price data using yfinance library (fallback).
    
    Args:
        ticker: Ticker symbol
        start_date: Start date
        end_date: End date
        timeframe: Timeframe
    
    Returns:
        List of price data points or None if failed
    """
    try:
        import yfinance as yf
    except ImportError:
        logger.warning("yfinance not installed, skipping yfinance fetch")
        return None
    
    # Map timeframe to yfinance interval
    interval_map = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "1h": "1h",
        "1d": "1d",
    }
    interval = interval_map.get(timeframe, "1h")
    
    # Fetch data
    # Note: yfinance intraday data (1m, 5m, 15m, 1h) is typically only available for the last 60 days
    # For intraday intervals, we need to ensure we're requesting a reasonable range
    max_yfinance_days = 60  # Limit to 60 days for yfinance
    if (end_date - start_date).days > max_yfinance_days:
        # Use a more recent date range
        start_date = end_date - timedelta(days=max_yfinance_days)
        logger.info(f"Limiting yfinance fetch to last {max_yfinance_days} days to avoid timeout")
    
    ticker_obj = yf.Ticker(ticker)
    # For intraday data, yfinance works better with period parameter
    # Intraday data (1m, 5m, 15m, 1h) is typically only available for the last 60 days
    if interval in ["1m", "5m", "15m", "1h"]:
        # For intraday, use period parameter (max 60 days for intraday)
        days_diff = (end_date - start_date).days
        if days_diff <= 60:
            # Use period parameter for intraday data - this gets more reliable results
            # Add extra days to account for weekends/holidays (multiply by ~1.4 to account for non-trading days)
            # For 2 days, request 3-4 days to ensure we get 2 full trading days
            period_days = max(min(int(days_diff * 1.5) + 2, 60), days_diff + 1)
            period = f"{period_days}d"
            logger.info(f"Fetching intraday data with period={period} for {ticker} (requested {days_diff} days)")
            hist = ticker_obj.history(period=period, interval=interval, timeout=20)
            # Filter to requested date range if needed
            if not hist.empty and len(hist) > 0:
                # Convert index to timezone-naive for comparison
                hist.index = hist.index.tz_localize(None) if hist.index.tz else hist.index
                # Filter to requested date range
                hist = hist[(hist.index >= start_date) & (hist.index <= end_date)]
                logger.info(f"Fetched {len(hist)} data points from yfinance for {ticker} (after date filtering)")
        else:
            hist = ticker_obj.history(start=start_date, end=end_date, interval=interval, timeout=20)
    else:
        hist = ticker_obj.history(start=start_date, end=end_date, interval=interval, timeout=20)
    
    if hist.empty:
        return None
    
    # Convert to PriceDataPoint list
    data_points = []
    total_points = 0
    filtered_out = 0
    
    for timestamp, row in hist.iterrows():
        total_points += 1
        # Convert to naive datetime
        timestamp_naive = _naive_datetime(timestamp.to_pydatetime())
        
        # Filter for regular trading hours only (9:30 AM - 4:00 PM ET)
        # For intraday data, only include data during market hours
        if not _is_regular_trading_hours(timestamp_naive, timeframe):
            filtered_out += 1
            logger.debug(f"Filtering out {timestamp_naive} (hour={timestamp_naive.hour}, minute={timestamp_naive.minute}) - outside trading hours")
            continue
        
        logger.debug(f"Including {timestamp_naive} (hour={timestamp_naive.hour}, minute={timestamp_naive.minute}) - within trading hours")
        
        volume = row["Volume"]
        volume_int = None
        try:
            if volume is not None and not (isinstance(volume, float) and volume != volume):  # Check for NaN
                volume_int = int(volume)
        except (ValueError, TypeError):
            pass
        
        data_points.append(PriceDataPoint(
            timestamp=timestamp_naive,
            open=Decimal(str(row["Open"])),
            high=Decimal(str(row["High"])),
            low=Decimal(str(row["Low"])),
            close=Decimal(str(row["Close"])),
            volume=volume_int,
        ))
    
    logger.info(f"yfinance filtering: {total_points} total points, {filtered_out} filtered out, {len(data_points)} included for {ticker}")
    if len(data_points) > 0:
        logger.info(f"First point: {data_points[0].timestamp}, Last point: {data_points[-1].timestamp}")
    
    return data_points


async def _fetch_coingecko(
    ticker: str,
    start_date: datetime,
    end_date: datetime,
    timeframe: str,
) -> Optional[List[PriceDataPoint]]:
    """
    Fetch crypto price data from CoinGecko API.
    
    Args:
        ticker: Crypto ticker symbol
        start_date: Start date
        end_date: End date
        timeframe: Timeframe
    
    Returns:
        List of price data points or None if failed
    """
    # CoinGecko uses coin IDs, not tickers
    # For now, we'll use a simple mapping (can be expanded)
    coin_id_map = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "USDT": "tether",
        "USDC": "usd-coin",
        "BNB": "binancecoin",
        "ADA": "cardano",
        "SOL": "solana",
        "XRP": "ripple",
        "DOT": "polkadot",
        "DOGE": "dogecoin",
    }
    
    coin_id = coin_id_map.get(ticker.upper(), ticker.lower())
    
    # Map timeframe to CoinGecko days
    days = (end_date - start_date).days
    if days > 365:
        days = 365
    
    base_url = "https://api.coingecko.com/api/v3/coins"
    url = f"{base_url}/{coin_id}/market_chart"
    
    params = {
        "vs_currency": "usd",
        "days": days,
    }
    
    if settings.coingecko_api_key:
        params["x_cg_demo_api_key"] = settings.coingecko_api_key
    
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    
    # Parse response (CoinGecko returns prices, market_caps, total_volumes)
    prices = data.get("prices", [])
    
    # Convert to PriceDataPoint list
    # Note: CoinGecko only provides close prices, so we'll use the same value for OHLC
    data_points = []
    for timestamp_ms, price in prices:
        timestamp = _naive_datetime(datetime.fromtimestamp(timestamp_ms / 1000))
        # Ensure dates are naive for comparison
        start_naive = _naive_datetime(start_date)
        end_naive = _naive_datetime(end_date)
        if start_naive <= timestamp <= end_naive:
            price_decimal = Decimal(str(price))
            data_points.append(PriceDataPoint(
                timestamp=_naive_datetime(timestamp),
                open=price_decimal,
                high=price_decimal,
                low=price_decimal,
                close=price_decimal,
                volume=None,  # CoinGecko doesn't provide volume in this endpoint
            ))
    
    return sorted(data_points, key=lambda x: x.timestamp)


async def _cache_price_data(
    db: AsyncSession,
    ticker: str,
    data_points: List[PriceDataPoint],
    timeframe: str,
) -> None:
    """
    Cache price data in database.
    
    Optimized to batch check existing entries and use bulk operations.
    
    Args:
        db: Database session
        ticker: Ticker symbol
        data_points: List of price data points to cache
        timeframe: Timeframe
    """
    if not data_points:
        return
    
    # Prepare timestamps
    timestamps = [_naive_datetime(point.timestamp) for point in data_points]
    now = _naive_datetime(datetime.now())
    
    # Batch check for existing entries
    query = (
        select(PriceCache)
        .where(
            and_(
                PriceCache.ticker == ticker,
                PriceCache.timeframe == timeframe,
                PriceCache.timestamp.in_(timestamps),
            )
        )
    )
    result = await db.execute(query)
    existing_entries = {entry.timestamp: entry for entry in result.scalars().all()}
    
    # Prepare updates and inserts
    to_update = []
    to_insert = []
    
    for point in data_points:
        point_timestamp_naive = _naive_datetime(point.timestamp)
        
        if point_timestamp_naive in existing_entries:
            # Update existing cache entry
            existing = existing_entries[point_timestamp_naive]
            existing.open_price = point.open
            existing.high_price = point.high
            existing.low_price = point.low
            existing.close_price = point.close
            existing.volume = point.volume
            existing.cached_at = now
            to_update.append(existing)
        else:
            # Create new cache entry
            cache_entry = PriceCache(
                ticker=ticker,
                timestamp=point_timestamp_naive,
                timeframe=timeframe,
                open_price=point.open,
                high_price=point.high,
                low_price=point.low,
                close_price=point.close,
                volume=point.volume,
                cached_at=now,
            )
            to_insert.append(cache_entry)
    
    # Bulk insert new entries
    if to_insert:
        db.add_all(to_insert)
    
    # Commit all changes (updates and inserts)
    await db.commit()


def _merge_price_data(
    cached: List[PriceDataPoint],
    fetched: List[PriceDataPoint],
) -> List[PriceDataPoint]:
    """
    Merge cached and fetched price data, removing duplicates.
    
    Args:
        cached: Cached data points
        fetched: Fetched data points
    
    Returns:
        Merged list of data points
    """
    # Create a dict keyed by timestamp for O(1) lookup
    merged_dict = {point.timestamp: point for point in cached}
    
    # Add fetched data (will overwrite cached if same timestamp)
    for point in fetched:
        merged_dict[point.timestamp] = point
    
    # Return sorted list
    return sorted(merged_dict.values(), key=lambda x: x.timestamp)

