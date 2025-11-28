"""
Data Providers - Multiple Sources for Stock Data
===============================================

Comprehensive data provider system supporting multiple sources:
- Alpha Vantage (free tier: 5 calls/minute, 500 calls/day)
- Polygon.io (free tier: 5 calls/minute)
- Yahoo Finance (via yfinance - free, no API key needed)
- IEX Cloud (free tier: 50,000 calls/month)
- Twelve Data (free tier: 800 calls/day)
- Finnhub (free tier: 60 calls/minute)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
import asyncio
import aiohttp
import yfinance as yf
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class DataProviderType(Enum):
    """Available data provider types"""
    ALPHA_VANTAGE = "alpha_vantage"
    POLYGON = "polygon"
    YAHOO_FINANCE = "yahoo_finance"
    IEX_CLOUD = "iex_cloud"
    TWELVE_DATA = "twelve_data"
    FINNHUB = "finnhub"
    IBKR = "ibkr"  # Interactive Brokers

@dataclass
class MarketData:
    """Standardized market data structure"""
    symbol: str
    price: float
    change: float
    change_pct: float
    volume: int
    timestamp: datetime
    high: Optional[float] = None
    low: Optional[float] = None
    open: Optional[float] = None
    close: Optional[float] = None

@dataclass
class OHLCVData:
    """OHLCV data structure"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

class BaseDataProvider(ABC):
    """Abstract base class for data providers"""
    
    def __init__(self, api_key: Optional[str] = None, rate_limit: int = 60):
        self.api_key = api_key
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.request_count = 0
    
    @abstractmethod
    async def get_quote(self, symbol: str) -> MarketData:
        """Get current quote for a symbol"""
        pass
    
    @abstractmethod
    async def get_historical_data(self, symbol: str, start_date: datetime, 
                                end_date: datetime, interval: str = "1d") -> List[OHLCVData]:
        """Get historical OHLCV data"""
        pass
    
    @abstractmethod
    async def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Get quotes for multiple symbols"""
        pass
    
    async def _rate_limit_check(self):
        """Implement rate limiting"""
        current_time = datetime.now().timestamp()
        if current_time - self.last_request_time < (60 / self.rate_limit):
            await asyncio.sleep((60 / self.rate_limit) - (current_time - self.last_request_time))
        self.last_request_time = datetime.now().timestamp()

class YahooFinanceProvider(BaseDataProvider):
    """Yahoo Finance data provider (free, no API key required)"""
    
    def __init__(self):
        super().__init__(rate_limit=100)  # Conservative rate limit
    
    async def get_quote(self, symbol: str) -> MarketData:
        """Get current quote from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return MarketData(
                symbol=symbol,
                price=info.get('currentPrice', info.get('regularMarketPrice', 0)),
                change=info.get('regularMarketChange', 0),
                change_pct=info.get('regularMarketChangePercent', 0) / 100,
                volume=info.get('volume', 0),
                timestamp=datetime.now(),
                high=info.get('dayHigh'),
                low=info.get('dayLow'),
                open=info.get('open'),
                close=info.get('previousClose')
            )
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {e}")
            raise
    
    async def get_historical_data(self, symbol: str, start_date: datetime, 
                                end_date: datetime, interval: str = "1d") -> List[OHLCVData]:
        """Get historical data from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, interval=interval)
            
            data = []
            for timestamp, row in df.iterrows():
                data.append(OHLCVData(
                    symbol=symbol,
                    timestamp=timestamp,
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume'])
                ))
            
            return data
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            raise
    
    async def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Get quotes for multiple symbols"""
        quotes = {}
        for symbol in symbols:
            try:
                quotes[symbol] = await self.get_quote(symbol)
                await asyncio.sleep(0.1)  # Small delay between requests
            except Exception as e:
                logger.error(f"Error getting quote for {symbol}: {e}")
                continue
        return quotes

class AlphaVantageProvider(BaseDataProvider):
    """Alpha Vantage data provider"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key, rate_limit=5)  # 5 calls/minute free tier
        self.base_url = "https://www.alphavantage.co/query"
    
    async def get_quote(self, symbol: str) -> MarketData:
        """Get current quote from Alpha Vantage"""
        await self._rate_limit_check()
        
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=params) as response:
                data = await response.json()
                
                if "Global Quote" in data:
                    quote = data["Global Quote"]
                    return MarketData(
                        symbol=symbol,
                        price=float(quote["05. price"]),
                        change=float(quote["09. change"]),
                        change_pct=float(quote["10. change percent"].replace("%", "")) / 100,
                        volume=int(quote["06. volume"]),
                        timestamp=datetime.now(),
                        high=float(quote["03. high"]),
                        low=float(quote["04. low"]),
                        open=float(quote["02. open"]),
                        close=float(quote["08. previous close"])
                    )
                else:
                    raise ValueError(f"No data returned for {symbol}")
    
    async def get_historical_data(self, symbol: str, start_date: datetime, 
                                end_date: datetime, interval: str = "1d") -> List[OHLCVData]:
        """Get historical data from Alpha Vantage"""
        await self._rate_limit_check()
        
        function = "TIME_SERIES_DAILY" if interval == "1d" else "TIME_SERIES_INTRADAY"
        params = {
            "function": function,
            "symbol": symbol,
            "apikey": self.api_key,
            "outputsize": "full"
        }
        
        if interval != "1d":
            params["interval"] = interval
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=params) as response:
                data = await response.json()
                
                time_series_key = "Time Series (Daily)" if interval == "1d" else f"Time Series ({interval})"
                
                if time_series_key in data:
                    time_series = data[time_series_key]
                    ohlcv_data = []
                    
                    for date_str, values in time_series.items():
                        date = datetime.strptime(date_str, "%Y-%m-%d")
                        if start_date <= date <= end_date:
                            ohlcv_data.append(OHLCVData(
                                symbol=symbol,
                                timestamp=date,
                                open=float(values["1. open"]),
                                high=float(values["2. high"]),
                                low=float(values["3. low"]),
                                close=float(values["4. close"]),
                                volume=int(values["5. volume"])
                            ))
                    
                    return sorted(ohlcv_data, key=lambda x: x.timestamp)
                else:
                    raise ValueError(f"No historical data returned for {symbol}")
    
    async def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Get quotes for multiple symbols (rate limited)"""
        quotes = {}
        for symbol in symbols:
            try:
                quotes[symbol] = await self.get_quote(symbol)
            except Exception as e:
                logger.error(f"Error getting quote for {symbol}: {e}")
                continue
        return quotes

class PolygonProvider(BaseDataProvider):
    """Polygon.io data provider"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key, rate_limit=5)  # 5 calls/minute free tier
        self.base_url = "https://api.polygon.io"
    
    async def get_quote(self, symbol: str) -> MarketData:
        """Get current quote from Polygon"""
        await self._rate_limit_check()
        
        url = f"{self.base_url}/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}"
        params = {"apikey": self.api_key}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()
                
                if "ticker" in data:
                    ticker_data = data["ticker"]
                    day_data = ticker_data.get("day", {})
                    
                    return MarketData(
                        symbol=symbol,
                        price=day_data.get("c", 0),  # close price
                        change=day_data.get("c", 0) - day_data.get("o", 0),  # close - open
                        change_pct=day_data.get("c", 0) / day_data.get("o", 1) - 1 if day_data.get("o") else 0,
                        volume=day_data.get("v", 0),
                        timestamp=datetime.now(),
                        high=day_data.get("h"),
                        low=day_data.get("l"),
                        open=day_data.get("o"),
                        close=day_data.get("c")
                    )
                else:
                    raise ValueError(f"No data returned for {symbol}")
    
    async def get_historical_data(self, symbol: str, start_date: datetime, 
                                end_date: datetime, interval: str = "1d") -> List[OHLCVData]:
        """Get historical data from Polygon"""
        await self._rate_limit_check()
        
        # Convert interval to Polygon format
        timespan_map = {
            "1d": "day",
            "1h": "hour",
            "5m": "minute",
            "1m": "minute"
        }
        
        multiplier_map = {
            "1d": 1,
            "1h": 1,
            "5m": 5,
            "1m": 1
        }
        
        timespan = timespan_map.get(interval, "day")
        multiplier = multiplier_map.get(interval, 1)
        
        url = f"{self.base_url}/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        params = {"apikey": self.api_key}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()
                
                if "results" in data:
                    ohlcv_data = []
                    for result in data["results"]:
                        timestamp = datetime.fromtimestamp(result["t"] / 1000)
                        ohlcv_data.append(OHLCVData(
                            symbol=symbol,
                            timestamp=timestamp,
                            open=result["o"],
                            high=result["h"],
                            low=result["l"],
                            close=result["c"],
                            volume=result["v"]
                        ))
                    
                    return sorted(ohlcv_data, key=lambda x: x.timestamp)
                else:
                    raise ValueError(f"No historical data returned for {symbol}")
    
    async def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Get quotes for multiple symbols"""
        quotes = {}
        for symbol in symbols:
            try:
                quotes[symbol] = await self.get_quote(symbol)
            except Exception as e:
                logger.error(f"Error getting quote for {symbol}: {e}")
                continue
        return quotes

class DataProviderFactory:
    """Factory for creating data provider instances"""
    
    @staticmethod
    def create_provider(provider_type: DataProviderType, api_key: Optional[str] = None) -> BaseDataProvider:
        """Create data provider instance"""
        providers = {
            DataProviderType.YAHOO_FINANCE: YahooFinanceProvider,
            DataProviderType.ALPHA_VANTAGE: AlphaVantageProvider,
            DataProviderType.POLYGON: PolygonProvider,
        }
        
        if provider_type not in providers:
            raise ValueError(f"Unknown provider type: {provider_type}")
        
        if provider_type == DataProviderType.YAHOO_FINANCE:
            return providers[provider_type]()
        else:
            if not api_key:
                raise ValueError(f"API key required for {provider_type}")
            return providers[provider_type](api_key)

class DataProviderManager:
    """Manages multiple data providers with fallback"""
    
    def __init__(self, providers: List[Tuple[DataProviderType, Optional[str]]]):
        self.providers = []
        for provider_type, api_key in providers:
            try:
                provider = DataProviderFactory.create_provider(provider_type, api_key)
                self.providers.append(provider)
            except Exception as e:
                logger.warning(f"Failed to initialize {provider_type}: {e}")
    
    async def get_quote(self, symbol: str) -> MarketData:
        """Get quote with fallback to other providers"""
        for provider in self.providers:
            try:
                return await provider.get_quote(symbol)
            except Exception as e:
                logger.warning(f"Provider {provider.__class__.__name__} failed for {symbol}: {e}")
                continue
        
        raise RuntimeError(f"All providers failed for {symbol}")
    
    async def get_historical_data(self, symbol: str, start_date: datetime, 
                                end_date: datetime, interval: str = "1d") -> List[OHLCVData]:
        """Get historical data with fallback"""
        for provider in self.providers:
            try:
                return await provider.get_historical_data(symbol, start_date, end_date, interval)
            except Exception as e:
                logger.warning(f"Provider {provider.__class__.__name__} failed for {symbol}: {e}")
                continue
        
        raise RuntimeError(f"All providers failed for {symbol}")
    
    async def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Get multiple quotes with fallback"""
        quotes = {}
        failed_symbols = symbols.copy()

        for provider in self.providers:
            if not failed_symbols:
                break

            try:
                provider_quotes = await provider.get_multiple_quotes(failed_symbols)
                quotes.update(provider_quotes)
                failed_symbols = [s for s in failed_symbols if s not in provider_quotes]
            except Exception as e:
                logger.warning(f"Provider {provider.__class__.__name__} failed: {e}")
                continue

        return quotes

    async def get_historical_data_df(
        self,
        symbol: str,
        timeframe: str = "5m",
        lookback_bars: int = 100
    ) -> pd.DataFrame:
        """
        Get historical data as a DataFrame with lookback_bars interface.

        This is the interface expected by the TradingScheduler and StrategyEvaluator.

        Args:
            symbol: Stock symbol
            timeframe: Timeframe string (1m, 5m, 15m, 1h, 1d)
            lookback_bars: Number of bars to fetch

        Returns:
            DataFrame with columns: open, high, low, close, volume
        """
        # Convert timeframe to interval and calculate date range
        interval_map = {
            "1m": ("1m", timedelta(minutes=lookback_bars)),
            "5m": ("5m", timedelta(minutes=5 * lookback_bars)),
            "15m": ("15m", timedelta(minutes=15 * lookback_bars)),
            "30m": ("30m", timedelta(minutes=30 * lookback_bars)),
            "1h": ("1h", timedelta(hours=lookback_bars)),
            "1d": ("1d", timedelta(days=lookback_bars)),
        }

        interval, lookback_delta = interval_map.get(timeframe, ("1d", timedelta(days=lookback_bars)))

        end_date = datetime.now()
        start_date = end_date - lookback_delta

        try:
            ohlcv_data = await self.get_historical_data(symbol, start_date, end_date, interval)

            if not ohlcv_data:
                return pd.DataFrame()

            # Convert to DataFrame
            df = pd.DataFrame([
                {
                    'timestamp': d.timestamp,
                    'open': d.open,
                    'high': d.high,
                    'low': d.low,
                    'close': d.close,
                    'volume': d.volume
                }
                for d in ohlcv_data
            ])

            if not df.empty:
                df.set_index('timestamp', inplace=True)
                df.sort_index(inplace=True)

            return df

        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()


def get_default_data_provider() -> DataProviderManager:
    """
    Create a default DataProviderManager with Yahoo Finance (free, no API key).

    This is used by the TradingScheduler when no data provider is specified.
    """
    return DataProviderManager([
        (DataProviderType.YAHOO_FINANCE, None),
    ])
