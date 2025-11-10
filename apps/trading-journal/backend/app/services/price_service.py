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
    # Set defaults
    if end_date is None:
        end_date = datetime.now()
    if start_date is None:
        start_date = end_date - timedelta(days=365)
    
    # Normalize ticker (uppercase, strip)
    ticker = ticker.upper().strip()
    
    # Check cache first
    cached_data = await _get_cached_data(db, ticker, start_date, end_date, timeframe)
    
    # Determine what data we need to fetch
    missing_ranges = _find_missing_ranges(cached_data, start_date, end_date, timeframe)
    
    # Fetch missing data
    if missing_ranges:
        fetched_data = await _fetch_price_data(ticker, missing_ranges, timeframe)
        
        # Cache the fetched data
        if fetched_data:
            await _cache_price_data(db, ticker, fetched_data, timeframe)
            # Merge with cached data
            cached_data = _merge_price_data(cached_data, fetched_data)
    
    # Sort by timestamp
    cached_data.sort(key=lambda x: x.timestamp)
    
    # Filter to requested range
    filtered_data = [
        point for point in cached_data
        if start_date <= point.timestamp <= end_date
    ]
    
    return PriceDataResponse(
        ticker=ticker,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        data=filtered_data,
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
    # Determine cache expiration
    cache_duration = CACHE_DURATION_DAILY if timeframe == "1d" else CACHE_DURATION_INTRADAY
    cache_expiry = datetime.now() - timedelta(hours=cache_duration)
    
    query = (
        select(PriceCache)
        .where(
            and_(
                PriceCache.ticker == ticker,
                PriceCache.timeframe == timeframe,
                PriceCache.timestamp >= start_date,
                PriceCache.timestamp <= end_date,
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
    
    # Try providers in order
    for start_date, end_date in date_ranges:
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
    
    return []


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
    
    async with httpx.AsyncClient(timeout=30.0) as client:
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
        
        # Filter by date range
        if start_date <= timestamp <= end_date:
            # Alpha Vantage uses different keys for daily vs intraday
            open_key = values.get("1. open") or values.get("1. open")
            high_key = values.get("2. high") or values.get("2. high")
            low_key = values.get("3. low") or values.get("3. low")
            close_key = values.get("4. close") or values.get("4. close")
            volume_key = values.get("5. volume") or values.get("6. volume", 0)
            
            data_points.append(PriceDataPoint(
                timestamp=timestamp,
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
    ticker_obj = yf.Ticker(ticker)
    hist = ticker_obj.history(start=start_date, end=end_date, interval=interval)
    
    if hist.empty:
        return None
    
    # Convert to PriceDataPoint list
    data_points = []
    for timestamp, row in hist.iterrows():
        volume = row["Volume"]
        volume_int = None
        try:
            if volume is not None and not (isinstance(volume, float) and volume != volume):  # Check for NaN
                volume_int = int(volume)
        except (ValueError, TypeError):
            pass
        
        data_points.append(PriceDataPoint(
            timestamp=timestamp.to_pydatetime(),
            open=Decimal(str(row["Open"])),
            high=Decimal(str(row["High"])),
            low=Decimal(str(row["Low"])),
            close=Decimal(str(row["Close"])),
            volume=volume_int,
        ))
    
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
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    
    # Parse response (CoinGecko returns prices, market_caps, total_volumes)
    prices = data.get("prices", [])
    
    # Convert to PriceDataPoint list
    # Note: CoinGecko only provides close prices, so we'll use the same value for OHLC
    data_points = []
    for timestamp_ms, price in prices:
        timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
        if start_date <= timestamp <= end_date:
            price_decimal = Decimal(str(price))
            data_points.append(PriceDataPoint(
                timestamp=timestamp,
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
    
    Args:
        db: Database session
        ticker: Ticker symbol
        data_points: List of price data points to cache
        timeframe: Timeframe
    """
    for point in data_points:
        # Check if already cached
        query = (
            select(PriceCache)
            .where(
                and_(
                    PriceCache.ticker == ticker,
                    PriceCache.timestamp == point.timestamp,
                    PriceCache.timeframe == timeframe,
                )
            )
        )
        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing cache entry
            existing.open_price = point.open
            existing.high_price = point.high
            existing.low_price = point.low
            existing.close_price = point.close
            existing.volume = point.volume
            existing.cached_at = datetime.now()
        else:
            # Create new cache entry
            cache_entry = PriceCache(
                ticker=ticker,
                timestamp=point.timestamp,
                timeframe=timeframe,
                open_price=point.open,
                high_price=point.high,
                low_price=point.low,
                close_price=point.close,
                volume=point.volume,
                cached_at=datetime.now(),
            )
            db.add(cache_entry)
    
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

