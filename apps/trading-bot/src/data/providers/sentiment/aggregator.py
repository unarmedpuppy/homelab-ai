"""
Sentiment Aggregator
====================

Unified system to aggregate sentiment from multiple data sources (Twitter, Reddit, etc.)
into a single, weighted sentiment score.
"""

import logging
from typing import Dict, List, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .models import SymbolSentiment
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from ....config.settings import settings
from .models import SymbolSentiment, SentimentLevel
from ....utils.cache import get_cache_manager
from ....utils.metrics import (
    get_or_create_histogram,
    get_or_create_counter,
    get_or_create_gauge,
    track_duration_context
)

# Import providers (may not all be available)
try:
    from .twitter import TwitterSentimentProvider
except ImportError:
    TwitterSentimentProvider = None

try:
    from .reddit import RedditSentimentProvider
except ImportError:
    RedditSentimentProvider = None

# Future providers (optional)
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
    from .analyst_ratings import AnalystRatingsSentimentProvider
except ImportError:
    AnalystRatingsSentimentProvider = None

try:
    from .insider_trading import InsiderTradingSentimentProvider
except ImportError:
    InsiderTradingSentimentProvider = None

try:
    from .dark_pool import DarkPoolSentimentProvider
except ImportError:
    DarkPoolSentimentProvider = None

try:
    from .options_flow import OptionsFlowSentimentProvider
except ImportError:
    OptionsFlowSentimentProvider = None

logger = logging.getLogger(__name__)


@dataclass
class SourceSentiment:
    """Sentiment data from a single source"""
    source: str  # 'twitter', 'reddit', etc.
    symbol: str
    sentiment_score: float  # -1.0 to 1.0
    weighted_sentiment: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    mention_count: int
    timestamp: datetime
    sentiment_level: SentimentLevel
    source_weight: float = 1.0  # Weight for this source in aggregation


@dataclass
class AggregatedSentiment:
    """Aggregated sentiment across all sources"""
    symbol: str
    timestamp: datetime
    unified_sentiment: float  # -1.0 to 1.0 (weighted average)
    confidence: float  # 0.0 to 1.0 (aggregated confidence)
    sentiment_level: SentimentLevel
    source_count: int  # Number of sources used in aggregation
    total_mentions: int  # Total mentions across all sources
    providers_used: List[str] = field(default_factory=list)  # List of provider names
    divergence_detected: bool = False  # Whether divergence was detected
    divergence_score: float = 0.0  # 0.0 to 1.0 (higher = more divergence)
    volume_trend: str = "stable"  # up, down, stable
    twitter_sentiment: Optional[float] = None  # Twitter-specific sentiment
    reddit_sentiment: Optional[float] = None  # Reddit-specific sentiment
    stocktwits_sentiment: Optional[float] = None  # StockTwits-specific sentiment
    options_sentiment: Optional[float] = None  # Options flow-specific sentiment
    sources: Dict[str, SourceSentiment] = field(default_factory=dict)
    source_breakdown: Dict[str, float] = field(default_factory=dict)  # source -> contribution %
    
    
class SentimentAggregator:
    """
    Aggregates sentiment from multiple sources into a unified score
    
    Features:
    - Weighted averaging across sources
    - Time-decay weighting (recent data weighted more)
    - Divergence detection (when sources disagree)
    - Confidence aggregation
    - Configurable source weights
    """
    
    def __init__(
        self,
        source_weights: Optional[Dict[str, float]] = None,
        time_decay_hours: Optional[int] = None,
        min_confidence: Optional[float] = None,
        persist_to_db: bool = True
    ):
        """
        Initialize sentiment aggregator
        
        Args:
            source_weights: Weight multipliers for each source (default: from settings)
            time_decay_hours: Hours after which sentiment is half-weighted (default: from settings)
            min_confidence: Minimum confidence threshold for including source (default: from settings)
            persist_to_db: Whether to persist aggregated sentiment to database
        """
        # Get config (handle case where it might not exist)
        try:
            self.config = settings.sentiment_aggregator
            default_time_decay = self.config.time_decay_half_life_hours
            default_min_confidence = self.config.min_provider_confidence
            default_divergence_threshold = self.config.divergence_threshold
            default_weights = {
                'twitter': self.config.weight_twitter,
                'reddit': self.config.weight_reddit,
                'stocktwits': self.config.weight_stocktwits,
                'news': self.config.weight_news,
                'options': self.config.weight_options,
                'google_trends': self.config.weight_google_trends,
                'analyst_ratings': self.config.weight_analyst_ratings,
                'insider_trading': getattr(self.config, 'weight_insider_trading', 0.25),
                'dark_pool': getattr(self.config, 'weight_dark_pool', 1.5)  # High weight for institutional data
            }
        except AttributeError:
            # Fallback if settings not configured
            logger.warning("SentimentAggregatorSettings not found, using defaults")
            default_time_decay = 24
            default_min_confidence = 0.3
            default_divergence_threshold = 0.5
            default_weights = {
                'twitter': 1.0,
                'reddit': 1.0,
                'stocktwits': 0.8,
                'news': 1.2,
                'sec_filings': 1.5,  # Higher weight for official filings
                'options': 1.0,
                'analyst_ratings': 1.5,
                'google_trends': 0.8,
                'insider_trading': 1.3,
                'dark_pool': 1.5  # High weight for institutional/smart money data
            }
        
        # Use settings defaults if not provided
        self.source_weights = source_weights or default_weights
        self.time_decay_hours = time_decay_hours or default_time_decay
        self.min_confidence = min_confidence or default_min_confidence
        self.divergence_threshold = default_divergence_threshold
        self.persist_to_db = persist_to_db
        
        # Initialize Redis-backed cache for aggregated results
        self.cache = get_cache_manager()
        try:
            self.cache_ttl = settings.sentiment_aggregator.cache_ttl
        except AttributeError:
            self.cache_ttl = 300  # Default 5 minutes
        
        # Initialize providers
        self.providers: Dict[str, Any] = {}
        self._initialize_providers()
        
        logger.info(
            f"SentimentAggregator initialized with sources: {list(self.providers.keys())}"
        )
        
        # Initialize metrics
        self._init_metrics()
    
    def _init_metrics(self):
        """Initialize Prometheus metrics for sentiment tracking"""
        # Sentiment calculation duration
        self.metric_sentiment_duration = get_or_create_histogram(
            'sentiment_calculation_duration_seconds',
            'Time spent calculating aggregated sentiment',
            labelnames=['symbol'],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
        )
        
        # Sentiment calculation count
        self.metric_sentiment_count = get_or_create_counter(
            'sentiment_calculations_total',
            'Total number of sentiment calculations',
            labelnames=['symbol', 'result']  # result: success, failed, cached
        )
        
        # Provider usage tracking
        self.metric_provider_usage = get_or_create_counter(
            'sentiment_provider_usage_total',
            'Number of times each sentiment provider was used',
            labelnames=['provider', 'symbol', 'status']  # status: success, error, skipped
        )
        
        # Aggregated sentiment distribution
        self.metric_sentiment_distribution = get_or_create_histogram(
            'sentiment_score_distribution',
            'Distribution of aggregated sentiment scores',
            labelnames=['symbol', 'sentiment_level'],  # sentiment_level: very_bearish, bearish, neutral, bullish, very_bullish
            buckets=[-1.0, -0.6, -0.3, -0.1, 0.1, 0.3, 0.6, 1.0]
        )
        
        # Sentiment divergence detection
        self.metric_divergence_detected = get_or_create_counter(
            'sentiment_divergence_detected_total',
            'Number of times sentiment divergence was detected',
            labelnames=['symbol', 'severity']  # severity: low, medium, high
        )
        
        # Provider contribution (gauge - current weight)
        self.metric_provider_contribution = get_or_create_gauge(
            'sentiment_provider_weight',
            'Current weight/contribution of each sentiment provider',
            labelnames=['provider']
        )
        
        # Number of sources used
        self.metric_sources_count = get_or_create_histogram(
            'sentiment_sources_count',
            'Number of sources used in sentiment aggregation',
            labelnames=['symbol'],
            buckets=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        )
        
        # Set initial provider weights as gauges
        for provider_name in self.providers.keys():
            weight = self.source_weights.get(provider_name, 1.0)
            self.metric_provider_contribution.labels(provider=provider_name).set(weight)
    
    def _initialize_providers(self):
        """Initialize available sentiment providers"""
        # Twitter (only if available)
        if TwitterSentimentProvider is not None:
            try:
                twitter_provider = TwitterSentimentProvider(persist_to_db=self.persist_to_db)
                if twitter_provider.is_available():
                    self.providers['twitter'] = twitter_provider
                    logger.debug("Twitter provider available")
            except Exception as e:
                logger.warning(f"Twitter provider not available: {e}")
        
        # Reddit (only if available)
        if RedditSentimentProvider is not None:
            try:
                reddit_provider = RedditSentimentProvider(persist_to_db=self.persist_to_db)
                if reddit_provider.is_available():
                    self.providers['reddit'] = reddit_provider
                    logger.debug("Reddit provider available")
            except Exception as e:
                logger.warning(f"Reddit provider not available: {e}")
        
        # StockTwits provider
        if StockTwitsSentimentProvider is not None:
            try:
                stocktwits_provider = StockTwitsSentimentProvider(persist_to_db=self.persist_to_db)
                if stocktwits_provider.is_available():
                    self.providers['stocktwits'] = stocktwits_provider
                    logger.debug("StockTwits provider available")
            except Exception as e:
                logger.warning(f"StockTwits provider not available: {e}")
        
        # SEC Filings provider (only if available)
        if SECFilingsSentimentProvider is not None:
            try:
                sec_provider = SECFilingsSentimentProvider(persist_to_db=self.persist_to_db)
                if sec_provider.is_available():
                    self.providers['sec_filings'] = sec_provider
                    logger.debug("SEC filings provider available")
            except Exception as e:
                logger.warning(f"SEC filings provider not available: {e}")
        
        # News provider (only if available)
        if NewsSentimentProvider is not None:
            try:
                news_provider = NewsSentimentProvider(persist_to_db=self.persist_to_db)
                if news_provider.is_available():
                    self.providers['news'] = news_provider
                    logger.debug("News provider available")
            except Exception as e:
                logger.warning(f"News provider not available: {e}")
        
        # Google Trends provider (only if available)
        if GoogleTrendsSentimentProvider is not None:
            try:
                google_trends_provider = GoogleTrendsSentimentProvider(persist_to_db=self.persist_to_db)
                if google_trends_provider.is_available():
                    self.providers['google_trends'] = google_trends_provider
                    logger.debug("Google Trends provider available")
            except Exception as e:
                logger.warning(f"Google Trends provider not available: {e}")
        
        # Analyst Ratings provider (only if available)
        if AnalystRatingsSentimentProvider is not None:
            try:
                analyst_ratings_provider = AnalystRatingsSentimentProvider(persist_to_db=self.persist_to_db)
                if analyst_ratings_provider.is_available():
                    self.providers['analyst_ratings'] = analyst_ratings_provider
                    logger.debug("Analyst Ratings provider available")
            except Exception as e:
                logger.warning(f"Analyst Ratings provider not available: {e}")
        
        # Insider Trading provider (only if available)
        if InsiderTradingSentimentProvider is not None:
            try:
                insider_provider = InsiderTradingSentimentProvider(persist_to_db=self.persist_to_db)
                if insider_provider.is_available():
                    self.providers['insider_trading'] = insider_provider
                    logger.debug("Insider Trading provider available")
            except Exception as e:
                logger.warning(f"Insider Trading provider not available: {e}")
        
        # Dark Pool provider (only if available)
        try:
            from ..data.dark_pool import DarkPoolSentimentProvider
            if DarkPoolSentimentProvider is not None:
                try:
                    dark_pool_provider = DarkPoolSentimentProvider(persist_to_db=self.persist_to_db)
                    if dark_pool_provider.is_available():
                        self.providers['dark_pool'] = dark_pool_provider
                        logger.debug("Dark Pool provider available")
                except Exception as e:
                    logger.warning(f"Dark Pool provider not available: {e}")
        except ImportError:
            pass
        
        # Options Flow provider (only if available)
        try:
            from .options_flow_sentiment import OptionsFlowSentimentProvider
            if OptionsFlowSentimentProvider is not None:
                try:
                    options_provider = OptionsFlowSentimentProvider(persist_to_db=self.persist_to_db)
                    if options_provider.is_available():
                        self.providers['options'] = options_provider
                        logger.debug("Options flow provider available")
                except Exception as e:
                    logger.debug(f"Options flow provider not available: {e}")
        except ImportError:
            pass  # Options flow provider not implemented yet
    
    def get_aggregated_sentiment(
        self,
        symbol: str,
        hours: int = 24,
        sources: Optional[List[str]] = None
    ) -> Optional[AggregatedSentiment]:
        """
        Get aggregated sentiment for a symbol across all sources
        
        Args:
            symbol: Stock symbol
            hours: Hours of historical data to analyze
            sources: Optional list of sources to use (None = all available)
            
        Returns:
            AggregatedSentiment object or None if no data available
        """
        symbol = symbol.upper()
        sources = sources or list(self.providers.keys())
        
        # Track calculation duration using internal metrics
        import time
        calc_start_time = time.time()
        try:
            # Check cache
            cache_key = f"aggregated_{symbol}_{hours}_{','.join(sorted(sources))}"
            cached = self._get_from_cache(cache_key)
            if cached:
                logger.debug(f"Returning cached aggregated sentiment for {symbol}")
                self.metric_sentiment_count.labels(symbol=symbol, result='cached').inc()
                return cached
            
            if not sources:
                logger.warning(f"No sentiment sources available for {symbol}")
                self.metric_sentiment_count.labels(symbol=symbol, result='failed').inc()
                return None
            
            # Collect sentiment from each source
            source_sentiments: Dict[str, SourceSentiment] = {}
            
            for source_name in sources:
                if source_name not in self.providers:
                    logger.debug(f"Source {source_name} not available, skipping")
                    self.metric_provider_usage.labels(
                        provider=source_name,
                        symbol=symbol,
                        status='skipped'
                    ).inc()
                    continue
                
                provider = self.providers[source_name]
                
                try:
                    sentiment = provider.get_sentiment(symbol, hours=hours)
                    
                    if sentiment and sentiment.confidence >= self.min_confidence:
                        source_weight = self.source_weights.get(source_name, 1.0)
                        
                        # Apply time decay
                        time_weight = self._calculate_time_decay(
                            sentiment.timestamp,
                            hours=self.time_decay_hours
                        )
                        
                        source_sentiments[source_name] = SourceSentiment(
                            source=source_name,
                            symbol=symbol,
                            sentiment_score=sentiment.average_sentiment,
                            weighted_sentiment=sentiment.weighted_sentiment,
                            confidence=sentiment.confidence,
                            mention_count=sentiment.mention_count,
                            timestamp=sentiment.timestamp,
                            sentiment_level=sentiment.sentiment_level,
                            source_weight=source_weight * time_weight
                        )
                        
                        # Track successful provider usage
                        self.metric_provider_usage.labels(
                            provider=source_name,
                            symbol=symbol,
                            status='success'
                        ).inc()
                    else:
                        # Provider returned no data or low confidence
                        self.metric_provider_usage.labels(
                            provider=source_name,
                            symbol=symbol,
                            status='skipped'
                        ).inc()
                    
                except Exception as e:
                    logger.warning(f"Error getting sentiment from {source_name} for {symbol}: {e}")
                    self.metric_provider_usage.labels(
                        provider=source_name,
                        symbol=symbol,
                        status='error'
                    ).inc()
                    continue
            
            if not source_sentiments:
                logger.debug(f"No sentiment data available for {symbol} from any source")
                self.metric_sentiment_count.labels(symbol=symbol, result='failed').inc()
                return None
            
            # Track number of sources used
            self.metric_sources_count.labels(symbol=symbol).observe(len(source_sentiments))
            
            # Aggregate sentiment
            aggregated = self._aggregate_source_sentiments(symbol, source_sentiments)
            
            # Track aggregated sentiment distribution
            if aggregated:
                sentiment_level_str = aggregated.sentiment_level.value if hasattr(aggregated.sentiment_level, 'value') else str(aggregated.sentiment_level)
                self.metric_sentiment_distribution.labels(
                    symbol=symbol,
                    sentiment_level=sentiment_level_str
                ).observe(aggregated.unified_sentiment)
                
                # Track divergence detection
                if aggregated.divergence_detected:
                    # Determine severity based on divergence score
                    if aggregated.divergence_score >= 0.7:
                        severity = 'high'
                    elif aggregated.divergence_score >= 0.4:
                        severity = 'medium'
                    else:
                        severity = 'low'
                    
                    self.metric_divergence_detected.labels(
                        symbol=symbol,
                        severity=severity
                    ).inc()
                
                # Cache result
                self._set_cache(cache_key, aggregated)
                
                # Track successful calculation
                self.metric_sentiment_count.labels(symbol=symbol, result='success').inc()
            
            # Track calculation duration
            calc_duration = time.time() - calc_start_time
            self.metric_sentiment_duration.labels(symbol=symbol).observe(calc_duration)
            
            return aggregated
        except Exception as e:
            # Track failed calculation duration
            calc_duration = time.time() - calc_start_time
            self.metric_sentiment_duration.labels(symbol=symbol).observe(calc_duration)
            raise
    
    def _calculate_time_decay(self, timestamp: datetime, hours: int = 24) -> float:
        """
        Calculate time decay weight
        
        Args:
            timestamp: When the sentiment was calculated
            hours: Half-life in hours (sentiment is half-weighted after this time)
            
        Returns:
            Weight factor (1.0 = recent, 0.0 = very old)
        """
        age_hours = (datetime.now() - timestamp).total_seconds() / 3600
        
        if age_hours <= 0:
            return 1.0
        
        # Exponential decay: weight = 2^(-age / half_life)
        decay_factor = 2 ** (-age_hours / hours)
        
        # Ensure minimum weight of 0.1 for data up to ~3x half-life
        return max(decay_factor, 0.1 if age_hours < hours * 3 else 0.0)
    
    def _aggregate_source_sentiments(
        self,
        symbol: str,
        source_sentiments: Dict[str, SourceSentiment]
    ) -> AggregatedSentiment:
        """
        Aggregate sentiment from multiple sources
        
        Args:
            symbol: Stock symbol
            source_sentiments: Dictionary of source -> SourceSentiment
            
        Returns:
            AggregatedSentiment object
        """
        # Calculate weighted average
        total_weight = 0.0
        weighted_sum = 0.0
        total_mentions = 0
        confidence_sum = 0.0
        
        source_breakdown = {}
        
        for source_name, source_sent in source_sentiments.items():
            # Effective weight = source_weight * confidence
            effective_weight = source_sent.source_weight * source_sent.confidence
            
            weighted_sum += source_sent.weighted_sentiment * effective_weight
            total_weight += effective_weight
            total_mentions += source_sent.mention_count
            confidence_sum += source_sent.confidence
            
            # Track contribution percentage
            source_breakdown[source_name] = effective_weight
        
        # Normalize breakdown to percentages
        if total_weight > 0:
            source_breakdown = {
                k: (v / total_weight * 100) 
                for k, v in source_breakdown.items()
            }
        
        # Calculate unified sentiment
        unified_sentiment = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        # Calculate aggregated confidence (average, weighted by mentions)
        aggregated_confidence = confidence_sum / len(source_sentiments) if source_sentiments else 0.0
        
        # Detect divergence (variance in sentiment scores)
        divergence_score = self._calculate_divergence(source_sentiments)
        divergence_detected = divergence_score > self.divergence_threshold
        
        # Determine sentiment level
        sentiment_level = self._score_to_level(unified_sentiment)
        
        # Extract provider-specific sentiments
        twitter_sentiment = source_sentiments.get('twitter')
        reddit_sentiment = source_sentiments.get('reddit')
        options_sentiment = source_sentiments.get('options')
        
        # Get providers used
        providers_used = list(source_sentiments.keys())
        
        # Calculate volume trend based on aggregated source trends
        # Use weighted vote from sources (weighted by mention count)
        volume_trend = "stable"
        if total_mentions > 0:
            # Get trends from all source sentiments
            trends = [s.volume_trend for s in source_sentiments.values()]
            if trends:
                # Count up/down trends (weighted by mention count)
                up_weight = sum(s.mention_count for s in source_sentiments.values() if s.volume_trend == "up")
                down_weight = sum(s.mention_count for s in source_sentiments.values() if s.volume_trend == "down")
                
                if up_weight > down_weight and up_weight > 0:
                    volume_trend = "up"
                elif down_weight > up_weight and down_weight > 0:
                    volume_trend = "down"
                else:
                    volume_trend = "stable"
        
        return AggregatedSentiment(
            symbol=symbol,
            timestamp=datetime.now(),
            unified_sentiment=unified_sentiment,
            confidence=aggregated_confidence,
            sentiment_level=sentiment_level,
            source_count=len(source_sentiments),
            total_mentions=total_mentions,
            providers_used=providers_used,
            divergence_detected=divergence_detected,
            divergence_score=divergence_score,
            volume_trend=volume_trend,
            twitter_sentiment=twitter_sentiment.weighted_sentiment if twitter_sentiment else None,
            reddit_sentiment=reddit_sentiment.weighted_sentiment if reddit_sentiment else None,
            stocktwits_sentiment=stocktwits_sentiment.weighted_sentiment if stocktwits_sentiment else None,
            options_sentiment=options_sentiment.weighted_sentiment if options_sentiment else None,
            sources=source_sentiments,
            source_breakdown=source_breakdown
        )
    
    def _calculate_divergence(
        self,
        source_sentiments: Dict[str, SourceSentiment]
    ) -> float:
        """
        Calculate divergence score (0.0 = all agree, 1.0 = completely disagree)
        
        Args:
            source_sentiments: Dictionary of source -> SourceSentiment
            
        Returns:
            Divergence score (0.0 to 1.0)
        """
        if len(source_sentiments) < 2:
            return 0.0  # No divergence with single source
        
        sentiments = [s.weighted_sentiment for s in source_sentiments.values()]
        
        # Calculate variance
        mean_sentiment = sum(sentiments) / len(sentiments)
        variance = sum((s - mean_sentiment) ** 2 for s in sentiments) / len(sentiments)
        
        # Normalize to 0-1 (max variance would be if half at -1 and half at +1)
        max_variance = 1.0  # Maximum possible variance
        divergence = min(variance / max_variance, 1.0)
        
        return divergence
    
    def _score_to_level(self, score: float) -> SentimentLevel:
        """Convert sentiment score to level"""
        if score >= 0.6:
            return SentimentLevel.VERY_BULLISH
        elif score >= 0.2:
            return SentimentLevel.BULLISH
        elif score <= -0.6:
            return SentimentLevel.VERY_BEARISH
        elif score <= -0.2:
            return SentimentLevel.BEARISH
        else:
            return SentimentLevel.NEUTRAL
    
    def update_source_weight(self, source: str, weight: float):
        """Update weight for a specific source"""
        self.source_weights[source] = weight
        logger.info(f"Updated {source} weight to {weight}")
    
    def get_available_sources(self) -> List[str]:
        """Get list of available sentiment sources"""
        return list(self.providers.keys())
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers (alias for get_available_sources)"""
        return self.get_available_sources()
    
    def get_provider_status(self) -> Dict[str, bool]:
        """Get status of all providers"""
        return {
            name: provider.is_available() 
            for name, provider in self.providers.items()
        }
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache using Redis-backed cache manager"""
        cache_key = f"aggregated:{key}"
        return self.cache.get(cache_key)
    
    def _set_cache(self, key: str, data: Any):
        """
        Store data in cache using Redis-backed cache manager
        
        Note: AggregatedSentiment contains datetime objects which are serialized
        via CacheManager's json.dumps(value, default=str) fallback.
        """
        cache_key = f"aggregated:{key}"
        try:
            self.cache.set(cache_key, data, ttl=self.cache_ttl)
        except (TypeError, ValueError) as e:
            # Log cache serialization errors but don't fail
            logger.warning(
                f"Failed to cache aggregated sentiment: {e}. "
                f"Data may not be fully serializable. Key: {cache_key}",
                extra={
                    'cache_key': cache_key,
                    'error_type': type(e).__name__,
                    'operation': 'cache_set'
                }
            )
