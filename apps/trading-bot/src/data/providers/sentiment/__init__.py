"""
Sentiment Data Providers
========================

Providers for collecting and analyzing sentiment data from various sources.
"""

from .base import BaseSentimentProvider
from .twitter import TwitterSentimentProvider
from .reddit import RedditSentimentProvider

try:
    from .google_trends import GoogleTrendsSentimentProvider
except ImportError:
    GoogleTrendsSentimentProvider = None

# Optional providers
try:
    from .news import NewsSentimentProvider
except ImportError:
    NewsSentimentProvider = None

try:
    from .stocktwits import StockTwitsSentimentProvider
except ImportError:
    StockTwitsSentimentProvider = None

try:
    from .sec_filings import SECFilingsSentimentProvider
except ImportError:
    SECFilingsSentimentProvider = None

try:
    from .google_trends import GoogleTrendsSentimentProvider
except ImportError:
    GoogleTrendsSentimentProvider = None

try:
    from .mention_volume import MentionVolumeProvider
except ImportError:
    MentionVolumeProvider = None

try:
    from .analyst_ratings import AnalystRatingsSentimentProvider
except ImportError:
    AnalystRatingsSentimentProvider = None

try:
    from .insider_trading import InsiderTradingSentimentProvider
except ImportError:
    InsiderTradingSentimentProvider = None

try:
    from .options_flow_sentiment import OptionsFlowSentimentProvider
except ImportError:
    OptionsFlowSentimentProvider = None

from .aggregator import SentimentAggregator, AggregatedSentiment

__all__ = [
    'BaseSentimentProvider',
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
    'SentimentAggregator',
    'AggregatedSentiment',
]

