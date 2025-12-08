"""
Base Sentiment Provider
=======================

Abstract base class for all sentiment providers.
Provides common infrastructure for caching, rate limiting, metrics, and persistence.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict

from ....config.settings import settings
from .models import SymbolSentiment
from .repository import SentimentRepository
from ....utils.cache import get_cache_manager
from ....utils.rate_limiter import get_rate_limiter
from ....utils.monitoring import get_usage_monitor

logger = logging.getLogger(__name__)


class BaseSentimentProvider(ABC):
    """
    Abstract base class for sentiment providers.

    Provides common infrastructure:
    - Caching via Redis-backed cache manager
    - Rate limiting
    - Usage monitoring
    - Database persistence (optional)
    - Metrics recording

    Subclasses must implement:
    - provider_name: str property
    - is_available() -> bool
    - _fetch_sentiment(symbol, hours) -> Optional[SymbolSentiment]
    """

    def __init__(self, persist_to_db: bool = True):
        """
        Initialize base sentiment provider.

        Args:
            persist_to_db: Whether to persist data to database (default: True)
        """
        self.persist_to_db = persist_to_db
        self.cache = get_cache_manager()
        self.rate_limiter = get_rate_limiter(self.provider_name)
        self.usage_monitor = get_usage_monitor()
        self.repository = SentimentRepository() if persist_to_db else None

        # Subclasses should set these in their __init__
        self._cache_ttl: int = 300  # Default 5 minutes
        self._rate_limit: int = 100  # Default requests per window
        self._rate_window_seconds: int = 3600  # Default 1 hour

        logger.info(f"{self.__class__.__name__} initialized (persist_to_db={persist_to_db})")

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Return the provider name (e.g., 'twitter', 'reddit', 'stocktwits').

        Used for cache keys, rate limiting, and metrics.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the provider is available and properly configured.

        Returns:
            True if provider can be used, False otherwise.
        """
        pass

    @abstractmethod
    def _fetch_sentiment(self, symbol: str, hours: int = 24) -> Optional[SymbolSentiment]:
        """
        Fetch sentiment data from the external source.

        This is the core method that subclasses implement.
        It should NOT handle caching or rate limiting - those are handled by get_sentiment().

        Args:
            symbol: Stock symbol to analyze
            hours: Hours of data to fetch

        Returns:
            SymbolSentiment object or None if unavailable
        """
        pass

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache using Redis-backed cache manager."""
        cache_key = f"{self.provider_name}:{key}"
        return self.cache.get(cache_key)

    def _set_cache(self, key: str, data: Any) -> None:
        """Store data in cache using Redis-backed cache manager."""
        cache_key = f"{self.provider_name}:{key}"
        self.cache.set(cache_key, data, ttl=self._cache_ttl)

    def _record_availability_metric(self, is_available: bool) -> None:
        """Record provider availability metric."""
        try:
            from ....utils.metrics import update_provider_availability
            update_provider_availability(self.provider_name, is_available)
        except (ImportError, AttributeError) as e:
            logger.debug(f"Could not record availability metric: {e}")

    def _record_rate_limit_metric(self) -> None:
        """Record rate limit hit metric."""
        try:
            from ....utils.metrics import record_rate_limit_hit
            record_rate_limit_hit(self.provider_name)
        except (ImportError, AttributeError) as e:
            logger.debug(f"Could not record rate limit metric: {e}")

    def _record_data_freshness_metric(self, cached_data: SymbolSentiment) -> None:
        """Record data freshness metric for cached data."""
        try:
            from datetime import datetime
            from ....utils.metrics import update_data_freshness
            cache_age = (datetime.now() - cached_data.timestamp).total_seconds()
            update_data_freshness(self.provider_name, "get_sentiment", cache_age)
        except (ImportError, AttributeError) as e:
            logger.debug(f"Could not record data freshness metric: {e}")

    def _record_api_latency_metric(self, latency_seconds: float) -> None:
        """Record API call latency metric."""
        try:
            from ....utils.metrics import record_api_latency
            record_api_latency(self.provider_name, "get_sentiment", latency_seconds)
        except (ImportError, AttributeError) as e:
            logger.debug(f"Could not record API latency metric: {e}")

    def _check_rate_limit(self) -> bool:
        """
        Check and handle rate limiting.

        Returns:
            True if request is allowed, False if rate limited.
        """
        is_allowed, rate_status = self.rate_limiter.check_rate_limit(
            limit=self._rate_limit,
            window_seconds=self._rate_window_seconds
        )

        if not is_allowed:
            logger.warning(f"{self.provider_name} rate limit exceeded, waiting...")
            rate_status = self.rate_limiter.wait_if_needed(
                limit=self._rate_limit,
                window_seconds=self._rate_window_seconds
            )
            if rate_status.is_limited:
                logger.error(f"{self.provider_name} rate limit still exceeded after wait")
                self._record_rate_limit_metric()
                self.usage_monitor.record_request(self.provider_name, success=False)
                return False

        return True

    def get_sentiment(self, symbol: str, hours: int = 24) -> Optional[SymbolSentiment]:
        """
        Get sentiment for a symbol with caching and rate limiting.

        This method handles:
        - Availability checking
        - Rate limiting
        - Cache lookup
        - Metrics recording
        - Calling _fetch_sentiment() for actual data retrieval

        Args:
            symbol: Stock symbol to analyze
            hours: Hours of data to fetch (default: 24)

        Returns:
            SymbolSentiment object or None if unavailable
        """
        # Track provider availability
        available = self.is_available()
        self._record_availability_metric(available)

        if not available:
            logger.warning(f"{self.provider_name} client not available")
            return None

        # Check rate limit
        if not self._check_rate_limit():
            return None

        # Check cache
        cache_key = f"sentiment_{symbol}_{hours}"
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"Returning cached sentiment for {symbol} from {self.provider_name}")
            self._record_data_freshness_metric(cached)
            self.usage_monitor.record_request(self.provider_name, success=True, cached=True)
            return cached

        # Fetch from external source
        api_start_time = time.time()
        try:
            result = self._fetch_sentiment(symbol, hours)
            api_latency = time.time() - api_start_time
            self._record_api_latency_metric(api_latency)

            if result:
                # Cache the result
                self._set_cache(cache_key, result)

                # Persist to database if enabled
                if self.persist_to_db and self.repository:
                    try:
                        self.repository.save_symbol_sentiment(result, source=self.provider_name)
                    except (OSError, IOError) as e:
                        logger.warning(f"Failed to persist sentiment to database: {e}")

                self.usage_monitor.record_request(self.provider_name, success=True)
            else:
                self.usage_monitor.record_request(self.provider_name, success=False)

            return result

        except (ConnectionError, TimeoutError, OSError) as e:
            logger.error(f"Network error fetching sentiment from {self.provider_name}: {e}")
            self.usage_monitor.record_request(self.provider_name, success=False)
            return None
        except (ValueError, KeyError, AttributeError) as e:
            logger.error(f"Data parsing error from {self.provider_name}: {e}")
            self.usage_monitor.record_request(self.provider_name, success=False)
            return None
