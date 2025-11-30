"""
Unusual Whales Scraper Provider
===============================

Main provider class that integrates the scraper with the sentiment system.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from .config import get_settings, UWScraperSettings
from .cache import UWScraperCache
from .browser import UWBrowserSession
from .scheduler import UWScraperScheduler
from .scrapers import MarketTideScraper, TickerFlowScraper
from .models import (
    MarketTideSnapshot,
    TickerFlowData,
    ScraperStatus,
    ScraperStatusCode,
)

logger = logging.getLogger(__name__)


class UnusualWhalesScraperProvider:
    """
    Main provider for Unusual Whales scraped data.

    Provides a clean API for accessing market tide and ticker flow data,
    with automatic caching and background refresh.

    Usage:
        provider = UnusualWhalesScraperProvider()
        await provider.start()

        # Get market tide
        tide = await provider.get_market_tide()
        print(f"Sentiment: {tide.overall_sentiment}")

        # Get ticker flow
        flow = await provider.get_ticker_flow("SPY")
        print(f"SPY sentiment: {flow.sentiment_score}")

        await provider.stop()
    """

    def __init__(
        self,
        settings: Optional[UWScraperSettings] = None,
        enable_scheduler: bool = True,
    ):
        """
        Initialize the provider.

        Args:
            settings: Scraper settings
            enable_scheduler: Whether to enable background scheduling
        """
        self.settings = settings or get_settings()
        self.cache = UWScraperCache()
        self._scheduler: Optional[UWScraperScheduler] = None
        self._browser: Optional[UWBrowserSession] = None
        self._enable_scheduler = enable_scheduler
        self._started = False

    @property
    def is_enabled(self) -> bool:
        """Check if the scraper is enabled"""
        return self.settings.enabled

    @property
    def is_started(self) -> bool:
        """Check if the provider is started"""
        return self._started

    async def start(self):
        """Start the provider and background scheduler"""
        if not self.settings.enabled:
            logger.info("UW scraper is disabled, not starting")
            return

        if self._started:
            logger.warning("Provider already started")
            return

        logger.info("Starting Unusual Whales scraper provider...")

        try:
            # Initialize cache
            await self.cache.initialize()

            # Start scheduler if enabled
            if self._enable_scheduler:
                self._scheduler = UWScraperScheduler(
                    settings=self.settings,
                    cache=self.cache,
                )
                await self._scheduler.start()

            self._started = True
            logger.info("Provider started successfully")

        except Exception as e:
            logger.error(f"Failed to start provider: {e}")
            await self.stop()
            raise

    async def stop(self):
        """Stop the provider and clean up resources"""
        logger.info("Stopping Unusual Whales scraper provider...")

        if self._scheduler:
            await self._scheduler.stop()
            self._scheduler = None

        if self._browser:
            await self._browser.stop()
            self._browser = None

        self._started = False
        logger.info("Provider stopped")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()

    async def get_market_tide(self, force_refresh: bool = False) -> Optional[MarketTideSnapshot]:
        """
        Get market tide data.

        Args:
            force_refresh: If True, fetches fresh data regardless of cache

        Returns:
            MarketTideSnapshot or None if unavailable
        """
        if not self.settings.enabled:
            return None

        # Check cache first
        if not force_refresh:
            cached = await self.cache.load_market_tide()
            if cached and not await self.cache.is_market_tide_stale():
                return cached

        # Fetch fresh data
        if force_refresh or not await self.cache.load_market_tide():
            await self._ensure_browser()
            scraper = MarketTideScraper(self._browser)
            data = await scraper.scrape()

            if data:
                await self.cache.save_market_tide(data)
                return data

        # Return cached even if stale
        return await self.cache.load_market_tide()

    async def get_ticker_flow(
        self,
        symbol: str,
        force_refresh: bool = False
    ) -> Optional[TickerFlowData]:
        """
        Get ticker flow data for a symbol.

        Args:
            symbol: Ticker symbol
            force_refresh: If True, fetches fresh data regardless of cache

        Returns:
            TickerFlowData or None if unavailable
        """
        if not self.settings.enabled:
            return None

        symbol = symbol.upper()

        # Check cache first
        if not force_refresh:
            cached = await self.cache.load_ticker_flow(symbol)
            if cached and not await self.cache.is_ticker_flow_stale(symbol):
                return cached

        # Fetch fresh data
        if force_refresh or not await self.cache.load_ticker_flow(symbol):
            await self._ensure_browser()
            scraper = TickerFlowScraper(self._browser)
            data = await scraper.scrape(symbol)

            if data:
                await self.cache.save_ticker_flow(data)
                return data

        # Return cached even if stale
        return await self.cache.load_ticker_flow(symbol)

    async def get_market_sentiment_score(self) -> float:
        """
        Get overall market sentiment score.

        Returns:
            Float from -1 (bearish) to 1 (bullish), 0 if unavailable
        """
        tide = await self.get_market_tide()
        if tide:
            return tide.overall_sentiment
        return 0.0

    async def get_ticker_sentiment_score(self, symbol: str) -> float:
        """
        Get sentiment score for a specific ticker.

        Args:
            symbol: Ticker symbol

        Returns:
            Float from -1 (bearish) to 1 (bullish), 0 if unavailable
        """
        flow = await self.get_ticker_flow(symbol)
        if flow:
            return flow.sentiment_score
        return 0.0

    async def get_all_ticker_flows(self) -> Dict[str, TickerFlowData]:
        """
        Get all cached ticker flow data.

        Returns:
            Dictionary mapping symbols to their flow data
        """
        return await self.cache.load_all_ticker_flows()

    async def _ensure_browser(self):
        """Ensure browser is available for on-demand scraping"""
        if self._browser is None:
            self._browser = UWBrowserSession(self.settings, self.cache)
            await self._browser.start()

            if self.settings.has_credentials:
                await self._browser.authenticate()

    async def refresh_all(self):
        """Force refresh all data"""
        if self._scheduler and self._scheduler.is_running:
            await self._scheduler.fetch_now(market_tide=True)
        else:
            # Manual refresh
            await self.get_market_tide(force_refresh=True)
            for symbol in self.settings.ticker_flow_symbols:
                await self.get_ticker_flow(symbol, force_refresh=True)

    def get_status(self) -> Dict[str, Any]:
        """
        Get provider status.

        Returns:
            Status dictionary with health information
        """
        status = {
            "enabled": self.settings.enabled,
            "started": self._started,
            "scheduler_running": self._scheduler.is_running if self._scheduler else False,
            "has_credentials": self.settings.has_credentials,
            "symbols": self.settings.ticker_flow_symbols,
            "market_tide_interval": self.settings.market_tide_interval,
            "ticker_flow_interval": self.settings.ticker_flow_interval,
        }

        if self._scheduler:
            status["scheduler"] = self._scheduler.get_status()

        return status

    async def get_health(self) -> Dict[str, Any]:
        """
        Get provider health status.

        Returns:
            Health status with cache info
        """
        cache_stats = await self.cache.get_cache_stats()
        scraper_status = await self.cache.load_status()

        return {
            "healthy": scraper_status.is_healthy,
            "last_success": scraper_status.last_success_time.isoformat() if scraper_status.last_success_time else None,
            "last_error": scraper_status.last_error_message,
            "success_rate": scraper_status.success_rate,
            "consecutive_failures": scraper_status.consecutive_failures,
            "is_authenticated": scraper_status.is_authenticated,
            "cache": cache_stats,
        }


# Singleton instance
_provider: Optional[UnusualWhalesScraperProvider] = None


def get_provider() -> UnusualWhalesScraperProvider:
    """Get or create the singleton provider instance"""
    global _provider
    if _provider is None:
        _provider = UnusualWhalesScraperProvider()
    return _provider


async def start_provider():
    """Start the singleton provider"""
    provider = get_provider()
    await provider.start()
    return provider


async def stop_provider():
    """Stop the singleton provider"""
    global _provider
    if _provider:
        await _provider.stop()
        _provider = None
