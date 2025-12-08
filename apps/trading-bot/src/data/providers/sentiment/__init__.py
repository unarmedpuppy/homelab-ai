"""
Sentiment Data Providers
========================

Providers for collecting and analyzing sentiment data from various sources.

All providers inherit from BaseSentimentProvider which provides common infrastructure
for caching, rate limiting, metrics, and persistence.
"""

from typing import Optional, Type

# Base class (always available)
from .base import BaseSentimentProvider

# Core models and aggregation (always available)
from .models import SymbolSentiment, SentimentLevel, Tweet, TweetSentiment
from .aggregator import SentimentAggregator, AggregatedSentiment


def _safe_import(module: str, class_name: str) -> Optional[Type]:
    """Safely import a provider class, returning None if dependencies are missing."""
    try:
        mod = __import__(f".{module}", globals(), locals(), [class_name], 1)
        return getattr(mod, class_name)
    except (ImportError, AttributeError):
        return None


# Provider imports - each may fail if external dependencies are missing
TwitterSentimentProvider = _safe_import("twitter", "TwitterSentimentProvider")
RedditSentimentProvider = _safe_import("reddit", "RedditSentimentProvider")
NewsSentimentProvider = _safe_import("news", "NewsSentimentProvider")
StockTwitsSentimentProvider = _safe_import("stocktwits", "StockTwitsSentimentProvider")
SECFilingsSentimentProvider = _safe_import("sec_filings", "SECFilingsSentimentProvider")
GoogleTrendsSentimentProvider = _safe_import("google_trends", "GoogleTrendsSentimentProvider")
MentionVolumeProvider = _safe_import("mention_volume", "MentionVolumeProvider")
AnalystRatingsSentimentProvider = _safe_import("analyst_ratings", "AnalystRatingsSentimentProvider")
InsiderTradingSentimentProvider = _safe_import("insider_trading", "InsiderTradingSentimentProvider")
OptionsFlowSentimentProvider = _safe_import("options_flow_sentiment", "OptionsFlowSentimentProvider")

__all__ = [
    # Base class
    'BaseSentimentProvider',
    # Models
    'SymbolSentiment',
    'SentimentLevel',
    'Tweet',
    'TweetSentiment',
    # Aggregation
    'SentimentAggregator',
    'AggregatedSentiment',
    # Providers (may be None if dependencies missing)
    'TwitterSentimentProvider',
    'RedditSentimentProvider',
    'NewsSentimentProvider',
    'StockTwitsSentimentProvider',
    'SECFilingsSentimentProvider',
    'GoogleTrendsSentimentProvider',
    'MentionVolumeProvider',
    'AnalystRatingsSentimentProvider',
    'InsiderTradingSentimentProvider',
    'OptionsFlowSentimentProvider',
]

