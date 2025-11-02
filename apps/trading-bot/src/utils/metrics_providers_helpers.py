"""
Provider Metrics Helper Utilities
==================================

Helper functions for consistently adding metrics to provider code.
"""

import logging
import time
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import metrics functions (gracefully handle if not available)
try:
    from .metrics_providers import (
        record_rate_limit_hit,
        update_data_freshness,
        update_provider_availability,
        update_provider_uptime
    )
    _METRICS_AVAILABLE = True
except ImportError:
    _METRICS_AVAILABLE = False
    logger.debug("Provider metrics functions not available")


def track_rate_limit_hit(provider: str):
    """
    Track rate limit hit for a provider
    
    Args:
        provider: Provider name
    """
    if not _METRICS_AVAILABLE:
        return
    
    try:
        record_rate_limit_hit(provider)
    except Exception as e:
        logger.debug(f"Error recording rate limit hit for {provider}: {e}")


def track_cache_freshness(provider: str, endpoint: str, cached_data: any):
    """
    Track data freshness when cache hit occurs
    
    Args:
        provider: Provider name
        endpoint: API endpoint name
        cached_data: Cached data object (must have .timestamp attribute)
    """
    if not _METRICS_AVAILABLE:
        return
    
    try:
        if hasattr(cached_data, 'timestamp') and cached_data.timestamp:
            cache_age = (datetime.now() - cached_data.timestamp).total_seconds()
            update_data_freshness(provider, endpoint, cache_age)
    except Exception as e:
        logger.debug(f"Error recording cache freshness for {provider}: {e}")


def track_provider_availability(provider: str, is_available: bool):
    """
    Track provider availability status
    
    Args:
        provider: Provider name
        is_available: Whether provider is available
    """
    if not _METRICS_AVAILABLE:
        return
    
    try:
        update_provider_availability(provider, is_available)
    except Exception as e:
        logger.debug(f"Error recording provider availability for {provider}: {e}")


def track_provider_uptime(provider: str, seconds_since_last_success: float):
    """
    Track provider uptime (time since last successful call)
    
    Args:
        provider: Provider name
        seconds_since_last_success: Seconds since last successful API call
    """
    if not _METRICS_AVAILABLE:
        return
    
    try:
        update_provider_uptime(provider, seconds_since_last_success)
    except Exception as e:
        logger.debug(f"Error recording provider uptime for {provider}: {e}")


class ProviderMetricsTracker:
    """
    Context manager for tracking provider API calls with timing and metrics
    
    Usage:
        with ProviderMetricsTracker("twitter", "get_sentiment") as tracker:
            result = api_call()
            tracker.record_success(response_time=0.5)
    """
    
    def __init__(self, provider: str, endpoint: str = "default"):
        self.provider = provider
        self.endpoint = endpoint
        self.start_time = None
        self.response_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            self.response_time = time.time() - self.start_time
        return False  # Don't suppress exceptions
    
    def record_response_time(self, response_time: Optional[float] = None):
        """
        Record response time (will use elapsed time if not provided)
        
        Args:
            response_time: Optional response time in seconds
        """
        if response_time is not None:
            self.response_time = response_time
        elif self.start_time:
            self.response_time = time.time() - self.start_time
        
        return self.response_time

