"""
Data Provider Metrics Utilities
================================

Metrics helpers for tracking data provider operations, cache performance, and API usage.
"""

import logging
import time
from typing import Optional

from ..config.settings import settings
from .metrics import (
    get_or_create_counter,
    get_or_create_histogram,
    get_or_create_gauge,
    get_metrics_registry
)

logger = logging.getLogger(__name__)


def get_provider_metrics():
    """
    Get or create data provider metrics
    
    Returns:
        Tuple of (requests_total, response_time, errors_total, rate_limit_hits, cache_hit_rate, api_calls, api_duration, api_errors, cache_hits, cache_misses)
    """
    if not settings.metrics.enabled:
        return None, None, None, None, None, None, None, None, None, None
    
    registry = get_metrics_registry()
    
    # Provider requests counter: provider, status (Prometheus-compatible)
    requests_total = get_or_create_counter(
        name="provider_requests_total",
        documentation="Total number of provider API requests",
        labelnames=["provider", "status"],  # status: success, failure, cached
        registry=registry
    )
    
    # Provider response time histogram (Prometheus-compatible)
    response_time = get_or_create_histogram(
        name="provider_response_time_seconds",
        documentation="Provider API response time in seconds",
        labelnames=["provider"],
        buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
        registry=registry
    )
    
    # Provider errors counter: provider, error_type (Prometheus-compatible)
    errors_total = get_or_create_counter(
        name="provider_errors_total",
        documentation="Total number of provider errors",
        labelnames=["provider", "error_type"],
        registry=registry
    )
    
    # Rate limit hits counter: provider
    rate_limit_hits = get_or_create_counter(
        name="provider_rate_limit_hits_total",
        documentation="Total number of rate limit hits",
        labelnames=["provider"],
        registry=registry
    )
    
    # Cache hit rate gauge: provider (Prometheus-compatible)
    cache_hit_rate = get_or_create_gauge(
        name="provider_cache_hit_rate",
        documentation="Cache hit rate per provider (0.0 to 1.0)",
        labelnames=["provider"],
        registry=registry
    )
    
    # API call counter: provider, endpoint (legacy compatibility)
    api_calls = get_or_create_counter(
        name="provider_api_calls_total",
        documentation="Total number of API calls by provider",
        labelnames=["provider", "endpoint"],
        registry=registry
    )
    
    # API response duration histogram: provider, endpoint
    api_duration = get_or_create_histogram(
        name="provider_api_duration_seconds",
        documentation="API response time by provider and endpoint",
        labelnames=["provider", "endpoint"],
        buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
        registry=registry
    )
    
    # API error counter: provider, endpoint, error_type
    api_errors = get_or_create_counter(
        name="provider_api_errors_total",
        documentation="Total number of API errors by provider",
        labelnames=["provider", "endpoint", "error_type"],
        registry=registry
    )
    
    # Rate limit hits counter: provider
    rate_limit_hits = get_or_create_counter(
        name="provider_rate_limit_hits_total",
        documentation="Total number of rate limit hits by provider",
        labelnames=["provider"],
        registry=registry
    )
    
    # Cache hits counter: provider
    cache_hits = get_or_create_counter(
        name="provider_cache_hits_total",
        documentation="Total number of cache hits by provider",
        labelnames=["provider"],
        registry=registry
    )
    
    # Cache misses counter: provider
    cache_misses = get_or_create_counter(
        name="provider_cache_misses_total",
        documentation="Total number of cache misses by provider",
        labelnames=["provider"],
        registry=registry
    )
    
    return requests_total, response_time, errors_total, rate_limit_hits, cache_hit_rate, api_calls, api_duration, api_errors, cache_hits, cache_misses


def get_cache_metrics():
    """
    Get or create cache-specific metrics
    
    Returns:
        Tuple of (cache_size, cache_ttl_seconds, data_freshness)
    """
    if not settings.metrics.enabled:
        return None, None, None
    
    registry = get_metrics_registry()
    
    # Cache size gauge: provider, cache_key_pattern
    cache_size = get_or_create_gauge(
        name="provider_cache_size",
        documentation="Number of items in cache by provider",
        labelnames=["provider"],
        registry=registry
    )
    
    # Cache TTL gauge: provider
    cache_ttl_seconds = get_or_create_gauge(
        name="provider_cache_ttl_seconds",
        documentation="Cache TTL in seconds by provider",
        labelnames=["provider"],
        registry=registry
    )
    
    # Data freshness gauge: provider (age of cached data in seconds)
    data_freshness = get_or_create_gauge(
        name="provider_data_freshness_seconds",
        documentation="Age of cached data in seconds (0 = fresh, higher = stale)",
        labelnames=["provider", "endpoint"],
        registry=registry
    )
    
    return cache_size, cache_ttl_seconds, data_freshness


def get_provider_availability_metrics():
    """
    Get or create provider availability metrics
    
    Returns:
        Tuple of (provider_available, provider_uptime_seconds)
    """
    if not settings.metrics.enabled:
        return None, None
    
    registry = get_metrics_registry()
    
    # Provider availability gauge: provider (1=available, 0=unavailable)
    provider_available = get_or_create_gauge(
        name="provider_available",
        documentation="Provider availability status (1=available, 0=unavailable)",
        labelnames=["provider"],
        registry=registry
    )
    
    # Provider uptime gauge: provider (seconds since last successful call)
    provider_uptime_seconds = get_or_create_gauge(
        name="provider_uptime_seconds",
        documentation="Time since last successful API call (seconds)",
        labelnames=["provider"],
        registry=registry
    )
    
    return provider_available, provider_uptime_seconds


def record_provider_request(provider: str, success: bool = True, cached: bool = False):
    """
    Record a provider API request
    
    Args:
        provider: Provider name
        success: Whether request was successful
        cached: Whether result came from cache
    """
    requests_total, _, _, _, _, api_calls, _, _, _, _ = get_provider_metrics()
    
    if requests_total:
        try:
            if cached:
                status = "cached"
            elif success:
                status = "success"
            else:
                status = "failure"
            
            requests_total.labels(
                provider=provider,
                status=status
            ).inc()
        except Exception as e:
            logger.debug(f"Error recording provider request metric: {e}")
    
    # Also record in legacy format for compatibility
    if api_calls:
        try:
            api_calls.labels(provider=provider, endpoint="default").inc()
        except Exception:
            pass


def record_api_call(provider: str, endpoint: str = "default"):
    """
    Record an API call (legacy compatibility)
    
    Args:
        provider: Provider name (e.g., "twitter", "reddit", "stocktwits")
        endpoint: API endpoint or method name
    """
    _, _, _, _, _, api_calls, _, _, _, _ = get_provider_metrics()
    if api_calls:
        try:
            api_calls.labels(provider=provider, endpoint=endpoint).inc()
        except Exception as e:
            logger.warning(f"Error recording API call metric: {e}")


def record_provider_response_time(provider: str, response_time: float):
    """
    Record provider response time
    
    Args:
        provider: Provider name
        response_time: Response time in seconds
    """
    _, response_time_metric, _, _, _, _, api_duration, _, _, _ = get_provider_metrics()
    
    if response_time_metric:
        try:
            response_time_metric.labels(provider=provider).observe(response_time)
        except Exception as e:
            logger.debug(f"Error recording provider response time metric: {e}")
    
    # Also record in legacy format for compatibility
    if api_duration:
        try:
            record_api_duration(provider, "default", response_time)
        except Exception:
            pass


def record_api_duration(provider: str, endpoint: str, duration: float):
    """
    Record API call duration (legacy compatibility)
    
    Args:
        provider: Provider name
        endpoint: API endpoint or method name
        duration: Duration in seconds
    """
    _, _, _, _, _, _, api_duration, _, _, _ = get_provider_metrics()
    if api_duration:
        try:
            api_duration.labels(provider=provider, endpoint=endpoint).observe(duration)
        except Exception as e:
            logger.warning(f"Error recording API duration metric: {e}")


def record_provider_error(provider: str, error_type: str):
    """
    Record a provider error
    
    Args:
        provider: Provider name
        error_type: Error type (e.g., "timeout", "connection_error", "api_error")
    """
    _, _, errors_total, _, _, _, _, api_errors, _, _ = get_provider_metrics()
    
    if errors_total:
        try:
            errors_total.labels(
                provider=provider,
                error_type=error_type
            ).inc()
        except Exception as e:
            logger.debug(f"Error recording provider error metric: {e}")
    
    # Also record in legacy format for compatibility
    if api_errors:
        try:
            record_api_error(provider, "default", error_type)
        except Exception:
            pass


def record_api_error(provider: str, endpoint: str, error_type: str):
    """
    Record an API error (legacy compatibility)
    
    Args:
        provider: Provider name
        endpoint: API endpoint or method name
        error_type: Error type (e.g., "timeout", "rate_limit", "connection_error", "api_error")
    """
    _, _, _, _, _, _, _, api_errors, _, _ = get_provider_metrics()
    if api_errors:
        try:
            api_errors.labels(
                provider=provider,
                endpoint=endpoint,
                error_type=error_type
            ).inc()
        except Exception as e:
            logger.warning(f"Error recording API error metric: {e}")


def record_rate_limit_hit(provider: str):
    """
    Record a rate limit hit
    
    Args:
        provider: Provider name
    """
    _, _, _, rate_limit_hits, _, _, _, _, _, _ = get_provider_metrics()
    if rate_limit_hits:
        try:
            rate_limit_hits.labels(provider=provider).inc()
        except Exception as e:
            logger.warning(f"Error recording rate limit hit metric: {e}")


def record_cache_hit(provider: str):
    """
    Record a cache hit (legacy compatibility)
    
    Args:
        provider: Provider name
    """
    _, _, _, _, _, _, _, _, cache_hits, _ = get_provider_metrics()
    if cache_hits:
        try:
            cache_hits.labels(provider=provider).inc()
        except Exception as e:
            logger.warning(f"Error recording cache hit metric: {e}")


def record_cache_miss(provider: str):
    """
    Record a cache miss (legacy compatibility)
    
    Args:
        provider: Provider name
    """
    _, _, _, _, _, _, _, _, _, cache_misses = get_provider_metrics()
    if cache_misses:
        try:
            cache_misses.labels(provider=provider).inc()
        except Exception as e:
            logger.warning(f"Error recording cache miss metric: {e}")


def update_data_freshness(provider: str, endpoint: str, age_seconds: float):
    """
    Update data freshness metric
    
    Args:
        provider: Provider name
        endpoint: API endpoint or method name
        age_seconds: Age of cached data in seconds
    """
    _, _, data_freshness = get_cache_metrics()
    if data_freshness:
        try:
            data_freshness.labels(provider=provider, endpoint=endpoint).set(age_seconds)
        except Exception as e:
            logger.warning(f"Error updating data freshness metric: {e}")


def update_provider_availability(provider: str, available: bool):
    """
    Update provider availability status
    
    Args:
        provider: Provider name
        available: Whether provider is available
    """
    provider_available, _ = get_provider_availability_metrics()
    if provider_available:
        try:
            provider_available.labels(provider=provider).set(1 if available else 0)
        except Exception as e:
            logger.warning(f"Error updating provider availability metric: {e}")


def update_provider_uptime(provider: str, seconds_since_last_success: float):
    """
    Update provider uptime metric (time since last successful call)
    
    Args:
        provider: Provider name
        seconds_since_last_success: Seconds since last successful API call
    """
    _, provider_uptime_seconds = get_provider_availability_metrics()
    if provider_uptime_seconds:
        try:
            provider_uptime_seconds.labels(provider=provider).set(seconds_since_last_success)
        except Exception as e:
            logger.warning(f"Error updating provider uptime metric: {e}")


# Context manager for tracking provider API calls
class track_provider_call:
    """
    Context manager for tracking provider API calls with automatic timing and error tracking
    
    Usage:
        with track_provider_call("twitter", "search_tweets") as tracker:
            result = twitter_api.search(...)
            tracker.set_cache_hit(True)
    """
    
    def __init__(self, provider: str, endpoint: str = "default"):
        self.provider = provider
        self.endpoint = endpoint
        self.start_time = None
        self.cache_hit = False
    
    def __enter__(self):
        self.start_time = time.time()
        record_api_call(self.provider, self.endpoint)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        # Record duration
        record_api_duration(self.provider, self.endpoint, duration)
        
        # Record cache hit/miss
        if self.cache_hit:
            record_cache_hit(self.provider)
        else:
            record_cache_miss(self.provider)
        
        # Record errors
        if exc_type is not None:
            error_type = "unknown_error"
            if exc_type.__name__ == "TimeoutError" or "timeout" in str(exc_val).lower():
                error_type = "timeout"
            elif "rate limit" in str(exc_val).lower() or "429" in str(exc_val):
                error_type = "rate_limit"
                record_rate_limit_hit(self.provider)
            elif "connection" in str(exc_val).lower():
                error_type = "connection_error"
            elif exc_type.__name__ == "HTTPError" or "http" in str(exc_val).lower():
                error_type = "api_error"
            
            record_api_error(self.provider, self.endpoint, error_type)
            update_provider_availability(self.provider, False)
        else:
            update_provider_availability(self.provider, True)
            update_provider_uptime(self.provider, 0.0)  # Reset uptime on success
        
        # Don't suppress exceptions
        return False
    
    def set_cache_hit(self, hit: bool):
        """Mark whether this call resulted in a cache hit"""
        self.cache_hit = hit


def update_cache_hit_rate(provider: str, hit_rate: float):
    """
    Update cache hit rate for a provider
    
    Args:
        provider: Provider name
        hit_rate: Cache hit rate (0.0 to 1.0)
    """
    _, _, _, _, cache_hit_rate, _, _, _, _, _ = get_provider_metrics()
    
    if cache_hit_rate:
        try:
            cache_hit_rate.labels(provider=provider).set(hit_rate)
        except Exception as e:
            logger.debug(f"Error updating cache hit rate metric: {e}")
