"""
Unusual Whales Scraper Cache
============================

File-based caching for persistence across container restarts.
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import aiofiles
import aiofiles.os

from .models import MarketTideSnapshot, TickerFlowData, ScraperStatus
from .config import get_settings

logger = logging.getLogger(__name__)


class UWScraperCache:
    """
    File-based cache for Unusual Whales scraper data.

    Persists data to JSON files to survive container restarts.
    """

    MARKET_TIDE_FILE = "market_tide.json"
    TICKER_FLOW_PREFIX = "ticker_flow_"
    STATUS_FILE = "scraper_status.json"
    SESSION_FILE = "session.json"

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the cache.

        Args:
            cache_dir: Directory for cache files. Uses settings default if not specified.
        """
        settings = get_settings()
        self.cache_dir = cache_dir or settings.cache_dir
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Create cache directory if it doesn't exist"""
        try:
            await aiofiles.os.makedirs(self.cache_dir, exist_ok=True)
            logger.info(f"Cache directory initialized: {self.cache_dir}")
        except Exception as e:
            logger.error(f"Failed to create cache directory: {e}")
            raise

    def _get_file_path(self, filename: str) -> Path:
        """Get full path for a cache file"""
        return self.cache_dir / filename

    async def _read_json(self, filename: str) -> Optional[Dict[str, Any]]:
        """Read and parse a JSON cache file"""
        file_path = self._get_file_path(filename)
        try:
            if not file_path.exists():
                return None
            async with aiofiles.open(file_path, "r") as f:
                content = await f.read()
                return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in cache file {filename}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading cache file {filename}: {e}")
            return None

    async def _write_json(self, filename: str, data: Dict[str, Any]):
        """Write data to a JSON cache file"""
        file_path = self._get_file_path(filename)
        try:
            async with self._lock:
                async with aiofiles.open(file_path, "w") as f:
                    await f.write(json.dumps(data, indent=2, default=str))
            logger.debug(f"Cache file written: {filename}")
        except Exception as e:
            logger.error(f"Error writing cache file {filename}: {e}")
            raise

    # Market Tide Cache Methods

    async def save_market_tide(self, data: MarketTideSnapshot):
        """Save market tide data to cache"""
        await self._write_json(self.MARKET_TIDE_FILE, data.to_dict())
        logger.info(
            f"Market tide cached: {len(data.data_points)} points, "
            f"sentiment={data.overall_sentiment:.2f}"
        )

    async def load_market_tide(self) -> Optional[MarketTideSnapshot]:
        """Load market tide data from cache"""
        data = await self._read_json(self.MARKET_TIDE_FILE)
        if data is None:
            return None
        try:
            return MarketTideSnapshot.from_dict(data)
        except Exception as e:
            logger.error(f"Error parsing cached market tide data: {e}")
            return None

    async def is_market_tide_stale(self, max_age_minutes: Optional[int] = None) -> bool:
        """
        Check if cached market tide data is stale.

        Args:
            max_age_minutes: Maximum age in minutes. Uses settings default if not specified.

        Returns:
            True if data is stale or doesn't exist.
        """
        if max_age_minutes is None:
            max_age_minutes = get_settings().market_tide_interval

        data = await self.load_market_tide()
        if data is None:
            return True

        age = datetime.now() - data.fetch_timestamp
        return age > timedelta(minutes=max_age_minutes)

    # Ticker Flow Cache Methods

    def _ticker_flow_filename(self, symbol: str) -> str:
        """Get filename for a ticker's flow data"""
        return f"{self.TICKER_FLOW_PREFIX}{symbol.upper()}.json"

    async def save_ticker_flow(self, data: TickerFlowData):
        """Save ticker flow data to cache"""
        filename = self._ticker_flow_filename(data.symbol)
        await self._write_json(filename, data.to_dict())
        logger.info(
            f"Ticker flow cached: {data.symbol}, "
            f"sentiment={data.sentiment_score:.2f}"
        )

    async def load_ticker_flow(self, symbol: str) -> Optional[TickerFlowData]:
        """Load ticker flow data from cache"""
        filename = self._ticker_flow_filename(symbol)
        data = await self._read_json(filename)
        if data is None:
            return None
        try:
            return TickerFlowData.from_dict(data)
        except Exception as e:
            logger.error(f"Error parsing cached ticker flow data for {symbol}: {e}")
            return None

    async def is_ticker_flow_stale(
        self, symbol: str, max_age_minutes: Optional[int] = None
    ) -> bool:
        """
        Check if cached ticker flow data is stale.

        Args:
            symbol: Ticker symbol
            max_age_minutes: Maximum age in minutes. Uses settings default if not specified.

        Returns:
            True if data is stale or doesn't exist.
        """
        if max_age_minutes is None:
            max_age_minutes = get_settings().ticker_flow_interval

        data = await self.load_ticker_flow(symbol)
        if data is None:
            return True

        age = datetime.now() - data.timestamp
        return age > timedelta(minutes=max_age_minutes)

    async def load_all_ticker_flows(self) -> Dict[str, TickerFlowData]:
        """Load all cached ticker flow data"""
        result = {}
        try:
            for file_path in self.cache_dir.glob(f"{self.TICKER_FLOW_PREFIX}*.json"):
                symbol = file_path.stem.replace(self.TICKER_FLOW_PREFIX, "")
                data = await self.load_ticker_flow(symbol)
                if data:
                    result[symbol] = data
        except Exception as e:
            logger.error(f"Error loading all ticker flows: {e}")
        return result

    # Scraper Status Cache Methods

    async def save_status(self, status: ScraperStatus):
        """Save scraper status to cache"""
        await self._write_json(self.STATUS_FILE, status.to_dict())

    async def load_status(self) -> ScraperStatus:
        """Load scraper status from cache"""
        data = await self._read_json(self.STATUS_FILE)
        if data is None:
            return ScraperStatus()
        try:
            return ScraperStatus.from_dict(data)
        except Exception as e:
            logger.error(f"Error parsing cached scraper status: {e}")
            return ScraperStatus()

    # Session Cache Methods

    async def save_session(self, cookies: Dict[str, Any], expiry: Optional[datetime] = None):
        """
        Save session cookies to cache.

        Args:
            cookies: Browser cookies to save
            expiry: When the session expires
        """
        data = {
            "cookies": cookies,
            "saved_at": datetime.now().isoformat(),
            "expiry": expiry.isoformat() if expiry else None,
        }
        await self._write_json(self.SESSION_FILE, data)
        logger.info("Session cookies cached")

    async def load_session(self) -> Optional[Dict[str, Any]]:
        """
        Load session cookies from cache.

        Returns:
            Cookie data if valid session exists, None otherwise.
        """
        data = await self._read_json(self.SESSION_FILE)
        if data is None:
            return None

        # Check expiry
        if data.get("expiry"):
            expiry = datetime.fromisoformat(data["expiry"])
            if datetime.now() > expiry:
                logger.info("Cached session has expired")
                return None

        return data.get("cookies")

    async def clear_session(self):
        """Clear cached session"""
        file_path = self._get_file_path(self.SESSION_FILE)
        try:
            if file_path.exists():
                await aiofiles.os.remove(file_path)
                logger.info("Session cache cleared")
        except Exception as e:
            logger.error(f"Error clearing session cache: {e}")

    # Cleanup Methods

    async def cleanup_old_files(self, max_age_hours: int = 24):
        """
        Remove cache files older than specified age.

        Args:
            max_age_hours: Maximum age in hours for cache files
        """
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        cleaned = 0

        try:
            for file_path in self.cache_dir.glob("*.json"):
                # Don't delete status or session files
                if file_path.name in [self.STATUS_FILE, self.SESSION_FILE]:
                    continue

                stat = file_path.stat()
                file_time = datetime.fromtimestamp(stat.st_mtime)
                if file_time < cutoff:
                    await aiofiles.os.remove(file_path)
                    cleaned += 1
                    logger.debug(f"Removed old cache file: {file_path.name}")

            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} old cache files")

        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")

    async def clear_all(self):
        """Clear all cache files"""
        try:
            for file_path in self.cache_dir.glob("*.json"):
                await aiofiles.os.remove(file_path)
            logger.info("All cache files cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the cache"""
        stats = {
            "cache_dir": str(self.cache_dir),
            "market_tide_cached": False,
            "market_tide_age_minutes": None,
            "ticker_flows_cached": 0,
            "session_valid": False,
            "total_files": 0,
            "total_size_bytes": 0,
        }

        try:
            # Check market tide
            market_tide = await self.load_market_tide()
            if market_tide:
                stats["market_tide_cached"] = True
                age = datetime.now() - market_tide.fetch_timestamp
                stats["market_tide_age_minutes"] = int(age.total_seconds() / 60)

            # Check ticker flows
            flows = await self.load_all_ticker_flows()
            stats["ticker_flows_cached"] = len(flows)

            # Check session
            session = await self.load_session()
            stats["session_valid"] = session is not None

            # Count files and size
            for file_path in self.cache_dir.glob("*.json"):
                stats["total_files"] += 1
                stats["total_size_bytes"] += file_path.stat().st_size

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")

        return stats
