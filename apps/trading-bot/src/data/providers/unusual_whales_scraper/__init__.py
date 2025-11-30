"""
Unusual Whales Web Scraper
==========================

Web scraper for extracting market tide and ticker flow data from Unusual Whales
without requiring the paid API subscription ($350/month).

This module is intentionally isolated from the main codebase to avoid polluting
other components with scraping-specific dependencies.

Features:
- Authenticated scraping with session cookie injection
- Hyper-rate-limited requests (30-60 minute intervals)
- File-based caching for persistence across container restarts
- Background scheduling for automatic data refresh
- Market tide data extraction (net call/put premium, volume)
- Per-ticker flow data extraction

Usage:
    from src.data.providers.unusual_whales_scraper import (
        UnusualWhalesScraperProvider,
        MarketTideSnapshot,
        TickerFlowData,
    )

    provider = UnusualWhalesScraperProvider()
    await provider.start()

    # Get market tide data
    tide = await provider.get_market_tide()
    print(f"Market sentiment: {tide.overall_sentiment}")

    # Get ticker flow
    flow = await provider.get_ticker_flow("SPY")
    print(f"SPY sentiment: {flow.sentiment_score}")
"""

from .models import (
    MarketTideDataPoint,
    MarketTideSnapshot,
    TickerFlowData,
    ScraperStatus,
    ScraperStatusCode,
    AuthCredentials,
)

from .config import UWScraperSettings, get_settings
from .cache import UWScraperCache
from .provider import (
    UnusualWhalesScraperProvider,
    get_provider,
    start_provider,
    stop_provider,
)

__all__ = [
    # Data models
    "MarketTideDataPoint",
    "MarketTideSnapshot",
    "TickerFlowData",
    "ScraperStatus",
    "ScraperStatusCode",
    "AuthCredentials",
    # Config
    "UWScraperSettings",
    "get_settings",
    # Cache
    "UWScraperCache",
    # Provider
    "UnusualWhalesScraperProvider",
    "get_provider",
    "start_provider",
    "stop_provider",
]
