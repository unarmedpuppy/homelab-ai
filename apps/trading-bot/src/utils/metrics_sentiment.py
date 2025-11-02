"""
Sentiment Metrics Utilities
============================

Metrics helpers for tracking sentiment analysis operations and performance.
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


def get_sentiment_metrics():
    """
    Get or create sentiment analysis metrics
    
    Returns:
        Tuple of (calculation_duration, aggregations_total, provider_usage, sentiment_distribution, divergence_detections)
    """
    if not settings.metrics.enabled:
        return None, None, None, None, None
    
    registry = get_metrics_registry()
    
    # Sentiment calculation duration histogram: provider
    calculation_duration = get_or_create_histogram(
        name="sentiment_calculation_duration_seconds",
        documentation="Time to calculate sentiment by provider",
        labelnames=["provider"],
        buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
        registry=registry
    )
    
    # Aggregations counter: symbol
    aggregations_total = get_or_create_counter(
        name="sentiment_aggregations_total",
        documentation="Total number of sentiment aggregations performed",
        labelnames=["symbol"],
        registry=registry
    )
    
    # Provider usage counter: provider, symbol
    provider_usage = get_or_create_counter(
        name="sentiment_provider_usage_total",
        documentation="Total number of times each sentiment provider was used",
        labelnames=["provider", "symbol"],
        registry=registry
    )
    
    # Aggregated sentiment distribution histogram: symbol
    sentiment_distribution = get_or_create_histogram(
        name="sentiment_score_distribution",
        documentation="Distribution of aggregated sentiment scores",
        labelnames=["symbol"],
        buckets=(-1.0, -0.8, -0.6, -0.4, -0.2, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
        registry=registry
    )
    
    # Divergence detections counter: symbol, divergence_type
    divergence_detections = get_or_create_counter(
        name="sentiment_divergence_detections_total",
        documentation="Total number of sentiment divergences detected",
        labelnames=["symbol", "divergence_type"],  # bullish_divergence, bearish_divergence
        registry=registry
    )
    
    return calculation_duration, aggregations_total, provider_usage, sentiment_distribution, divergence_detections


def record_sentiment_calculation(provider: str, duration: float):
    """
    Record sentiment calculation duration
    
    Args:
        provider: Provider name (e.g., "twitter", "reddit", "aggregated")
        duration: Calculation duration in seconds
    """
    calculation_duration, _, _, _, _ = get_sentiment_metrics()
    
    if calculation_duration:
        try:
            calculation_duration.labels(provider=provider).observe(duration)
        except Exception as e:
            logger.warning(f"Error recording sentiment calculation duration: {e}")


def record_sentiment_aggregation(symbol: str):
    """
    Record a sentiment aggregation operation
    
    Args:
        symbol: Stock symbol
    """
    _, aggregations_total, _, _, _ = get_sentiment_metrics()
    
    if aggregations_total:
        try:
            aggregations_total.labels(symbol=symbol).inc()
        except Exception as e:
            logger.warning(f"Error recording sentiment aggregation: {e}")


def record_provider_usage(provider: str, symbol: str):
    """
    Record sentiment provider usage
    
    Args:
        provider: Provider name (e.g., "twitter", "reddit", "stocktwits")
        symbol: Stock symbol
    """
    _, _, provider_usage, _, _ = get_sentiment_metrics()
    
    if provider_usage:
        try:
            provider_usage.labels(provider=provider, symbol=symbol).inc()
        except Exception as e:
            logger.warning(f"Error recording provider usage: {e}")


def record_sentiment_score(symbol: str, score: float):
    """
    Record aggregated sentiment score distribution
    
    Args:
        symbol: Stock symbol
        score: Sentiment score (-1.0 to 1.0)
    """
    _, _, _, sentiment_distribution, _ = get_sentiment_metrics()
    
    if sentiment_distribution:
        try:
            sentiment_distribution.labels(symbol=symbol).observe(score)
        except Exception as e:
            logger.warning(f"Error recording sentiment score: {e}")


def record_divergence_detection(symbol: str, divergence_type: str):
    """
    Record a sentiment divergence detection
    
    Args:
        symbol: Stock symbol
        divergence_type: Type of divergence ("bullish_divergence", "bearish_divergence", etc.)
    """
    _, _, _, _, divergence_detections = get_sentiment_metrics()
    
    if divergence_detections:
        try:
            divergence_detections.labels(
                symbol=symbol,
                divergence_type=divergence_type
            ).inc()
        except Exception as e:
            logger.warning(f"Error recording divergence detection: {e}")


# Context manager for tracking sentiment calculations
class track_sentiment_calculation:
    """
    Context manager for tracking sentiment calculation with automatic timing
    
    Usage:
        with track_sentiment_calculation("twitter", "AAPL") as tracker:
            sentiment = calculate_sentiment(...)
            tracker.record_score(sentiment.score)
    """
    
    def __init__(self, provider: str, symbol: str):
        self.provider = provider
        self.symbol = symbol
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        record_provider_usage(self.provider, self.symbol)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        record_sentiment_calculation(self.provider, duration)
        return False  # Don't suppress exceptions
    
    def record_score(self, score: float):
        """Record sentiment score (for aggregated sentiment)"""
        if self.provider == "aggregated":
            record_sentiment_score(self.symbol, score)

