"""
Unusual Whales Scraper Configuration
=====================================

Settings and configuration for the web scraper.
All settings can be overridden via environment variables.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


@dataclass
class UWScraperSettings:
    """
    Configuration settings for the Unusual Whales scraper.

    All settings can be overridden via environment variables with the
    UW_SCRAPER_ prefix.
    """

    # Enable/disable the scraper
    enabled: bool = field(
        default_factory=lambda: os.getenv("UW_SCRAPER_ENABLED", "true").lower() == "true"
    )

    # Rate limiting intervals (in minutes)
    market_tide_interval: int = field(
        default_factory=lambda: int(os.getenv("UW_SCRAPER_MARKET_TIDE_INTERVAL", "30"))
    )
    ticker_flow_interval: int = field(
        default_factory=lambda: int(os.getenv("UW_SCRAPER_TICKER_FLOW_INTERVAL", "60"))
    )

    # Minimum seconds between any requests (to avoid rate limiting)
    min_request_spacing: int = field(
        default_factory=lambda: int(os.getenv("UW_SCRAPER_MIN_REQUEST_SPACING", "60"))
    )

    # Symbols to track for ticker flow
    ticker_flow_symbols: List[str] = field(
        default_factory=lambda: os.getenv(
            "UW_SCRAPER_TICKER_FLOW_SYMBOLS",
            "SPY,QQQ,AAPL,NVDA,TSLA"
        ).split(",")
    )

    # Cache directory
    cache_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("UW_SCRAPER_CACHE_DIR", "/app/data/uw_scraper_cache")
        )
    )

    # Authentication credentials
    username: Optional[str] = field(
        default_factory=lambda: os.getenv("UW_SCRAPER_USERNAME")
    )
    password: Optional[str] = field(
        default_factory=lambda: os.getenv("UW_SCRAPER_PASSWORD")
    )

    # Session cookie (alternative to username/password)
    session_cookie: Optional[str] = field(
        default_factory=lambda: os.getenv("UW_SCRAPER_SESSION_COOKIE")
    )

    # Browser settings
    headless: bool = field(
        default_factory=lambda: os.getenv("UW_SCRAPER_HEADLESS", "true").lower() == "true"
    )
    user_agent: str = field(
        default_factory=lambda: os.getenv(
            "UW_SCRAPER_USER_AGENT",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    )

    # Timeouts (in milliseconds)
    page_load_timeout: int = field(
        default_factory=lambda: int(os.getenv("UW_SCRAPER_PAGE_LOAD_TIMEOUT", "30000"))
    )
    navigation_timeout: int = field(
        default_factory=lambda: int(os.getenv("UW_SCRAPER_NAVIGATION_TIMEOUT", "60000"))
    )

    # Retry settings
    max_retries: int = field(
        default_factory=lambda: int(os.getenv("UW_SCRAPER_MAX_RETRIES", "3"))
    )
    retry_delay: int = field(
        default_factory=lambda: int(os.getenv("UW_SCRAPER_RETRY_DELAY", "5"))
    )

    # Market hours filtering (ET timezone)
    market_hours_only: bool = field(
        default_factory=lambda: os.getenv("UW_SCRAPER_MARKET_HOURS_ONLY", "false").lower() == "true"
    )
    market_open_hour: int = 9   # 9:30 AM ET
    market_open_minute: int = 30
    market_close_hour: int = 16  # 4:00 PM ET
    market_close_minute: int = 0

    # Debug settings
    debug: bool = field(
        default_factory=lambda: os.getenv("UW_SCRAPER_DEBUG", "false").lower() == "true"
    )
    screenshot_on_error: bool = field(
        default_factory=lambda: os.getenv("UW_SCRAPER_SCREENSHOT_ON_ERROR", "true").lower() == "true"
    )
    screenshot_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("UW_SCRAPER_SCREENSHOT_DIR", "/app/data/uw_scraper_screenshots")
        )
    )

    @property
    def has_credentials(self) -> bool:
        """Check if authentication credentials are configured"""
        return bool(self.username and self.password) or bool(self.session_cookie)

    @property
    def login_url(self) -> str:
        """URL for login page"""
        return "https://unusualwhales.com/login"

    @property
    def market_tide_url(self) -> str:
        """URL for market tide/overview page"""
        return "https://unusualwhales.com/flow/overview"

    def ticker_flow_url(self, symbol: str) -> str:
        """URL for ticker-specific flow page"""
        return f"https://unusualwhales.com/option-charts/ticker-flow?ticker_symbol={symbol.upper()}"

    def ensure_directories(self):
        """Create required directories if they don't exist"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        if self.screenshot_on_error:
            self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> dict:
        """Convert to dictionary (for logging, excludes sensitive data)"""
        return {
            "enabled": self.enabled,
            "market_tide_interval": self.market_tide_interval,
            "ticker_flow_interval": self.ticker_flow_interval,
            "min_request_spacing": self.min_request_spacing,
            "ticker_flow_symbols": self.ticker_flow_symbols,
            "cache_dir": str(self.cache_dir),
            "has_credentials": self.has_credentials,
            "headless": self.headless,
            "page_load_timeout": self.page_load_timeout,
            "max_retries": self.max_retries,
            "market_hours_only": self.market_hours_only,
            "debug": self.debug,
        }


# Global settings instance
_settings: Optional[UWScraperSettings] = None


def get_settings() -> UWScraperSettings:
    """Get the global settings instance"""
    global _settings
    if _settings is None:
        _settings = UWScraperSettings()
    return _settings


def reset_settings():
    """Reset settings (for testing)"""
    global _settings
    _settings = None
