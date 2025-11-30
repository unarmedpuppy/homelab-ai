"""
Unusual Whales Scraper Scheduler
================================

Background task scheduler for automatic data refresh.
"""

import asyncio
import logging
import random
from datetime import datetime, time
from typing import Optional, Callable, Dict, Any, List
from zoneinfo import ZoneInfo

from .config import get_settings, UWScraperSettings
from .cache import UWScraperCache
from .browser import UWBrowserSession
from .scrapers import MarketTideScraper, TickerFlowScraper
from .models import MarketTideSnapshot, TickerFlowData, ScraperStatus

logger = logging.getLogger(__name__)

# Eastern timezone for market hours
ET = ZoneInfo("America/New_York")


class UWScraperScheduler:
    """
    Background scheduler for Unusual Whales scraping.

    Manages:
    - Periodic market tide fetches
    - Staggered ticker flow fetches
    - Rate limiting between requests
    - Error handling with exponential backoff
    - Market hours filtering (optional)
    """

    def __init__(
        self,
        settings: Optional[UWScraperSettings] = None,
        cache: Optional[UWScraperCache] = None,
        on_market_tide: Optional[Callable[[MarketTideSnapshot], None]] = None,
        on_ticker_flow: Optional[Callable[[TickerFlowData], None]] = None,
    ):
        """
        Initialize the scheduler.

        Args:
            settings: Scraper settings
            cache: Cache instance for data persistence
            on_market_tide: Callback when new market tide data is available
            on_ticker_flow: Callback when new ticker flow data is available
        """
        self.settings = settings or get_settings()
        self.cache = cache or UWScraperCache()

        self._on_market_tide = on_market_tide
        self._on_ticker_flow = on_ticker_flow

        self._browser: Optional[UWBrowserSession] = None
        self._market_tide_task: Optional[asyncio.Task] = None
        self._ticker_flow_tasks: Dict[str, asyncio.Task] = {}
        self._running = False

        self._last_market_tide_fetch: Optional[datetime] = None
        self._last_ticker_flow_fetch: Dict[str, datetime] = {}
        self._backoff_until: Optional[datetime] = None
        self._consecutive_failures = 0

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self._running

    async def start(self):
        """Start the background scheduler"""
        if self._running:
            logger.warning("Scheduler is already running")
            return

        logger.info("Starting UW scraper scheduler...")

        try:
            # Initialize cache
            await self.cache.initialize()

            # Start browser session
            self._browser = UWBrowserSession(self.settings, self.cache)
            await self._browser.start()

            # Authenticate if credentials are available
            if self.settings.has_credentials:
                await self._browser.authenticate()

            self._running = True

            # Start background tasks
            self._market_tide_task = asyncio.create_task(
                self._market_tide_loop(),
                name="uw_market_tide_loop"
            )

            # Start ticker flow tasks with staggered start times
            for i, symbol in enumerate(self.settings.ticker_flow_symbols):
                # Stagger start by 2-5 minutes per symbol
                delay = i * (120 + random.randint(0, 180))
                task = asyncio.create_task(
                    self._ticker_flow_loop(symbol, initial_delay=delay),
                    name=f"uw_ticker_flow_{symbol}"
                )
                self._ticker_flow_tasks[symbol] = task

            logger.info(
                f"Scheduler started: market_tide_interval={self.settings.market_tide_interval}m, "
                f"ticker_flow_interval={self.settings.ticker_flow_interval}m, "
                f"symbols={self.settings.ticker_flow_symbols}"
            )

        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            await self.stop()
            raise

    async def stop(self):
        """Stop the background scheduler"""
        logger.info("Stopping UW scraper scheduler...")
        self._running = False

        # Cancel all tasks
        if self._market_tide_task:
            self._market_tide_task.cancel()
            try:
                await self._market_tide_task
            except asyncio.CancelledError:
                pass
            self._market_tide_task = None

        for symbol, task in self._ticker_flow_tasks.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._ticker_flow_tasks.clear()

        # Stop browser
        if self._browser:
            await self._browser.stop()
            self._browser = None

        logger.info("Scheduler stopped")

    async def _market_tide_loop(self):
        """Background loop for market tide fetching"""
        logger.info("Market tide loop started")

        while self._running:
            try:
                # Check if we should fetch
                if await self._should_fetch_market_tide():
                    await self._fetch_market_tide()

                # Wait for next interval
                wait_time = self.settings.market_tide_interval * 60
                # Add some jitter
                wait_time += random.randint(-60, 60)
                await asyncio.sleep(max(60, wait_time))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in market tide loop: {e}")
                await asyncio.sleep(60)

    async def _ticker_flow_loop(self, symbol: str, initial_delay: int = 0):
        """Background loop for ticker flow fetching"""
        logger.info(f"Ticker flow loop started for {symbol}")

        if initial_delay > 0:
            logger.debug(f"Waiting {initial_delay}s before first {symbol} fetch")
            await asyncio.sleep(initial_delay)

        while self._running:
            try:
                # Check if we should fetch
                if await self._should_fetch_ticker_flow(symbol):
                    await self._fetch_ticker_flow(symbol)

                # Wait for next interval
                wait_time = self.settings.ticker_flow_interval * 60
                # Add some jitter
                wait_time += random.randint(-120, 120)
                await asyncio.sleep(max(120, wait_time))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in ticker flow loop for {symbol}: {e}")
                await asyncio.sleep(60)

    async def _should_fetch_market_tide(self) -> bool:
        """Check if we should fetch market tide data"""
        # Check backoff
        if self._backoff_until and datetime.now() < self._backoff_until:
            return False

        # Check market hours if enabled
        if self.settings.market_hours_only and not self._is_market_hours():
            return False

        # Check cache staleness
        return await self.cache.is_market_tide_stale()

    async def _should_fetch_ticker_flow(self, symbol: str) -> bool:
        """Check if we should fetch ticker flow data"""
        # Check backoff
        if self._backoff_until and datetime.now() < self._backoff_until:
            return False

        # Check market hours if enabled
        if self.settings.market_hours_only and not self._is_market_hours():
            return False

        # Check cache staleness
        return await self.cache.is_ticker_flow_stale(symbol)

    def _is_market_hours(self) -> bool:
        """Check if current time is within market hours (ET)"""
        now_et = datetime.now(ET)
        current_time = now_et.time()

        market_open = time(
            self.settings.market_open_hour,
            self.settings.market_open_minute
        )
        market_close = time(
            self.settings.market_close_hour,
            self.settings.market_close_minute
        )

        # Check if it's a weekday
        if now_et.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False

        return market_open <= current_time <= market_close

    async def _fetch_market_tide(self):
        """Fetch market tide data"""
        logger.info("Fetching market tide...")

        try:
            scraper = MarketTideScraper(self._browser)
            data = await scraper.scrape()

            if data:
                # Save to cache
                await self.cache.save_market_tide(data)
                self._last_market_tide_fetch = datetime.now()
                self._consecutive_failures = 0

                # Trigger callback
                if self._on_market_tide:
                    try:
                        self._on_market_tide(data)
                    except Exception as e:
                        logger.error(f"Error in market tide callback: {e}")

                logger.info(f"Market tide fetched: sentiment={data.overall_sentiment:.2f}")
            else:
                self._handle_fetch_failure()

        except Exception as e:
            logger.error(f"Market tide fetch error: {e}")
            self._handle_fetch_failure()

    async def _fetch_ticker_flow(self, symbol: str):
        """Fetch ticker flow data for a symbol"""
        logger.info(f"Fetching ticker flow for {symbol}...")

        try:
            scraper = TickerFlowScraper(self._browser)
            data = await scraper.scrape(symbol)

            if data:
                # Save to cache
                await self.cache.save_ticker_flow(data)
                self._last_ticker_flow_fetch[symbol] = datetime.now()
                self._consecutive_failures = 0

                # Trigger callback
                if self._on_ticker_flow:
                    try:
                        self._on_ticker_flow(data)
                    except Exception as e:
                        logger.error(f"Error in ticker flow callback: {e}")

                logger.info(
                    f"Ticker flow fetched: {symbol}, "
                    f"sentiment={data.sentiment_score:.2f}"
                )
            else:
                self._handle_fetch_failure()

        except Exception as e:
            logger.error(f"Ticker flow fetch error for {symbol}: {e}")
            self._handle_fetch_failure()

    def _handle_fetch_failure(self):
        """Handle a fetch failure with exponential backoff"""
        self._consecutive_failures += 1

        # Exponential backoff: 1min, 2min, 4min, 8min, max 30min
        backoff_seconds = min(60 * (2 ** (self._consecutive_failures - 1)), 1800)

        self._backoff_until = datetime.now()
        from datetime import timedelta
        self._backoff_until += timedelta(seconds=backoff_seconds)

        logger.warning(
            f"Fetch failed ({self._consecutive_failures} consecutive), "
            f"backing off for {backoff_seconds}s"
        )

    async def fetch_now(self, market_tide: bool = True, symbols: Optional[List[str]] = None):
        """
        Trigger immediate fetch (bypasses normal schedule).

        Args:
            market_tide: Whether to fetch market tide
            symbols: Specific symbols to fetch (all if None)
        """
        if not self._browser:
            logger.error("Cannot fetch - scheduler not started")
            return

        if market_tide:
            await self._fetch_market_tide()

        target_symbols = symbols or self.settings.ticker_flow_symbols
        for symbol in target_symbols:
            await self._fetch_ticker_flow(symbol)
            # Add delay between fetches
            await asyncio.sleep(self.settings.min_request_spacing)

    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        return {
            "running": self._running,
            "authenticated": self._browser.is_authenticated if self._browser else False,
            "last_market_tide_fetch": self._last_market_tide_fetch.isoformat() if self._last_market_tide_fetch else None,
            "last_ticker_flow_fetches": {
                symbol: ts.isoformat()
                for symbol, ts in self._last_ticker_flow_fetch.items()
            },
            "consecutive_failures": self._consecutive_failures,
            "backoff_until": self._backoff_until.isoformat() if self._backoff_until else None,
            "market_hours_only": self.settings.market_hours_only,
            "is_market_hours": self._is_market_hours(),
            "symbols": self.settings.ticker_flow_symbols,
        }
