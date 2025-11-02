"""
StockTwits Sentiment Provider
=============================

Integration with StockTwits API for sentiment analysis.
StockTwits provides built-in bullish/bearish sentiment indicators.
"""

import logging
import time
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque

try:
    import requests
except ImportError:
    requests = None

from ...config.settings import settings
from .models import Tweet, TweetSentiment, SymbolSentiment, SentimentLevel
from .sentiment_analyzer import SentimentAnalyzer
from .repository import SentimentRepository
from .volume_trend import calculate_volume_trend_from_repository
from ...utils.cache import get_cache_manager
from ...utils.rate_limiter import get_rate_limiter
from ...utils.monitoring import get_usage_monitor

logger = logging.getLogger(__name__)


@dataclass
class StockTwitsMessage:
    """StockTwits message data model"""
    message_id: int
    body: str
    created_at: datetime
    user_id: int
    username: str
    symbol: Optional[str] = None
    sentiment: Optional[str] = None  # "Bullish", "Bearish", or None
    likes_count: int = 0
    raw_data: Optional[Dict[str, Any]] = None


class StockTwitsClient:
    """
    StockTwits API client
    
    Handles:
    - API authentication (optional token)
    - Rate limiting
    - Message fetching
    - Error handling
    """
    
    def __init__(self):
        """Initialize StockTwits client"""
        if requests is None:
            raise ImportError(
                "requests is required for StockTwits integration. "
                "Install with: pip install requests"
            )
        
        self.config = settings.stocktwits
        self.base_url = self.config.base_url
        self.api_token = getattr(self.config, 'api_token', None) or getattr(self.config, 'access_token', None)
        self.request_times = deque()
        self.rate_limit_requests_per_hour = 200 if not self.api_token else 1000
        self.min_request_interval = 3600.0 / self.rate_limit_requests_per_hour
        
        logger.info("StockTwitsClient initialized")
    
    def is_available(self) -> bool:
        """Check if StockTwits client is available"""
        return requests is not None
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with optional authentication"""
        headers = {
            "Accept": "application/json",
            "User-Agent": "TradingBot/1.0"
        }
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers
    
    def _rate_limit_check(self):
        """Check and enforce rate limiting"""
        if not self.config.rate_limit_enabled:
            return
        
        now = time.time()
        
        # Remove old request times (older than 1 hour)
        while self.request_times and now - self.request_times[0] > 3600:
            self.request_times.popleft()
        
        # Check if we're at the limit
        if len(self.request_times) >= self.rate_limit_requests_per_hour:
            sleep_time = 3600 - (now - self.request_times[0])
            if sleep_time > 0:
                logger.debug(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
        
        # Ensure minimum interval between requests
        if self.request_times:
            time_since_last = now - self.request_times[-1]
            if time_since_last < self.min_request_interval:
                sleep_time = self.min_request_interval - time_since_last
                time.sleep(sleep_time)
        
        self.request_times.append(time.time())
    
    def _retry_request(self, func, max_retries: int = 3, backoff_factor: float = 1.0):
        """
        Retry wrapper for API requests with exponential backoff
        
        Args:
            func: Function to retry
            max_retries: Maximum number of retry attempts
            backoff_factor: Exponential backoff multiplier
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries fail
        """
        import time
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return func()
            except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {wait_time:.2f}s: {e}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {max_retries} attempts: {e}")
                    raise
            except Exception as e:
                # Don't retry on non-network errors
                logger.error(f"Non-retryable error: {e}")
                raise
        
        if last_exception:
            raise last_exception
    
    def get_messages_for_symbol(self, symbol: str, limit: int = 30) -> List[StockTwitsMessage]:
        """
        Get messages for a symbol
        
        Args:
            symbol: Stock symbol (e.g., AAPL)
            limit: Maximum number of messages (1-30, default: 30)
            
        Returns:
            List of StockTwitsMessage objects
        """
        if not self.is_available():
            return []
        
        self._rate_limit_check()
        
        limit = min(limit, self.config.max_results)
        url = f"{self.base_url}/streams/symbol/{symbol.upper()}.json"
        params = {"limit": limit}
        
        try:
            def make_request():
                return requests.get(url, headers=self._get_headers(), params=params, timeout=10)
            
            response = self._retry_request(make_request, max_retries=3, backoff_factor=1.0)
            response.raise_for_status()
            
            data = response.json()
            messages = []
            
            for msg_data in data.get("messages", []):
                try:
                    # Parse sentiment
                    sentiment = None
                    if "sentiment" in msg_data and msg_data["sentiment"]:
                        sentiment_basic = msg_data["sentiment"].get("basic")
                        if sentiment_basic:
                            sentiment = sentiment_basic  # "Bullish" or "Bearish"
                    
                    # Parse user
                    user = msg_data.get("user", {})
                    user_id = user.get("id", 0)
                    username = user.get("username", "unknown")
                    
                    # Parse symbol (primary symbol mentioned)
                    symbols = msg_data.get("symbols", [])
                    symbol_name = symbols[0].get("symbol") if symbols else None
                    
                    # Parse created_at
                    created_at_str = msg_data.get("created_at")
                    created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00")) if created_at_str else datetime.now()
                    
                    message = StockTwitsMessage(
                        message_id=msg_data.get("id", 0),
                        body=msg_data.get("body", ""),
                        created_at=created_at,
                        user_id=user_id,
                        username=username,
                        symbol=symbol_name,
                        sentiment=sentiment,
                        likes_count=msg_data.get("reshares", {}).get("likes", 0) or 0,
                        raw_data=msg_data
                    )
                    messages.append(message)
                except Exception as e:
                    logger.warning(f"Error parsing StockTwits message: {e}")
                    continue
            
            logger.debug(f"Fetched {len(messages)} messages for {symbol}")
            return messages
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching StockTwits messages for {symbol}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching StockTwits messages: {e}", exc_info=True)
            return []
    
    def get_trending_symbols(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get trending symbols from StockTwits
        
        Args:
            limit: Maximum number of symbols to return
            
        Returns:
            List of trending symbols with metrics
        """
        if not self.is_available():
            return []
        
        self._rate_limit_check()
        
        url = f"{self.base_url}/streams/trending.json"
        params = {"limit": limit}
        
        try:
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            trending = []
            
            for symbol_data in data.get("symbols", [])[:limit]:
                try:
                    trending.append({
                        "symbol": symbol_data.get("symbol"),
                        "title": symbol_data.get("title"),
                        "watchlist_count": symbol_data.get("watchlist_count", 0)
                    })
                except Exception as e:
                    logger.warning(f"Error parsing trending symbol: {e}")
                    continue
            
            logger.debug(f"Fetched {len(trending)} trending symbols")
            return trending
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching trending symbols: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching trending symbols: {e}", exc_info=True)
            return []


class StockTwitsSentimentProvider:
    """
    StockTwits sentiment provider for stock symbols
    
    Handles message collection, sentiment analysis, and aggregation.
    Uses built-in StockTwits sentiment indicators.
    """
    
    def __init__(self, persist_to_db: bool = True):
        """
        Initialize StockTwits sentiment provider
        
        Args:
            persist_to_db: Whether to persist data to database (default: True)
        """
        self.client = StockTwitsClient()
        self.analyzer = SentimentAnalyzer() if settings.stocktwits.enable_vader else None
        self.cache = get_cache_manager()
        self.cache_ttl = settings.stocktwits.cache_ttl
        self.rate_limiter = get_rate_limiter("stocktwits")
        self.usage_monitor = get_usage_monitor()
        self.persist_to_db = persist_to_db
        self.repository = SentimentRepository() if persist_to_db else None
        
        logger.info(f"StockTwitsSentimentProvider initialized (persist_to_db={persist_to_db})")
    
    def is_available(self) -> bool:
        """Check if StockTwits provider is available"""
        return self.client.is_available()
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache using Redis-backed cache manager"""
        cache_key = f"stocktwits:{key}"
        return self.cache.get(cache_key)
    
    def _set_cache(self, key: str, data: Any):
        """Store data in cache using Redis-backed cache manager"""
        cache_key = f"stocktwits:{key}"
        self.cache.set(cache_key, data, ttl=self.cache_ttl)
    
    def _sentiment_to_score(self, sentiment: Optional[str]) -> float:
        """Convert StockTwits sentiment string to numeric score"""
        if sentiment == "Bullish":
            return 0.7  # Positive but not as strong as explicit positive
        elif sentiment == "Bearish":
            return -0.7  # Negative but not as strong as explicit negative
        else:
            return 0.0  # Neutral or null
    
    def get_sentiment(self, symbol: str, hours: int = 24) -> Optional[SymbolSentiment]:
        """
        Get sentiment for a symbol from StockTwits messages
        
        Args:
            symbol: Stock symbol
            hours: Hours of data to analyze (default: 24)
            
        Returns:
            SymbolSentiment object or None
        """
        # Track provider availability
        is_available = self.is_available()
        try:
            from ...utils.metrics_providers_helpers import track_provider_availability
            track_provider_availability("stocktwits", is_available)
        except (ImportError, Exception) as e:
            logger.debug(f"Could not record availability metric: {e}")
        
        if not is_available:
            logger.warning("StockTwits client not available")
            return None
        
        # Check rate limit (200 requests per hour without token, 1000 with token)
        rate_limit = 1000 if self.client.api_token else 200
        window_seconds = 3600  # 1 hour
        is_allowed, rate_status = self.rate_limiter.check_rate_limit(limit=rate_limit, window_seconds=window_seconds)
        if not is_allowed:
            logger.warning(f"StockTwits rate limit exceeded for {symbol}, waiting...")
            rate_status = self.rate_limiter.wait_if_needed(limit=rate_limit, window_seconds=window_seconds)
            if rate_status.is_limited:
                logger.error(f"StockTwits rate limit still exceeded after wait")
                # Record rate limit hit metric
                try:
                    from ...utils.metrics_providers_helpers import track_rate_limit_hit
                    track_rate_limit_hit("stocktwits")
                except (ImportError, Exception) as e:
                    logger.debug(f"Could not record rate limit metric: {e}")
                self.usage_monitor.record_request("stocktwits", success=False)
                return None
        
        # Track API call timing
        import time
        api_start_time = time.time()
        
        # Check cache
        cache_key = f"sentiment_{symbol}_{hours}"
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"Returning cached sentiment for {symbol}")
            # Track data freshness
            try:
                from ...utils.metrics_providers_helpers import track_cache_freshness
                track_cache_freshness("stocktwits", "get_sentiment", cached)
            except (ImportError, Exception) as e:
                logger.debug(f"Could not record data freshness metric: {e}")
            self.usage_monitor.record_request("stocktwits", success=True, cached=True)
            return cached
        
        # Fetch messages
        messages = self.client.get_messages_for_symbol(symbol.upper(), limit=settings.stocktwits.max_results)
        
        # Record API response time
        api_response_time = time.time() - api_start_time
        
        if not messages:
            logger.info(f"No StockTwits messages found for {symbol}")
            # Return neutral sentiment
            sentiment = SymbolSentiment(
                symbol=symbol,
                timestamp=datetime.now(),
                mention_count=0,
                average_sentiment=0.0,
                weighted_sentiment=0.0,
                sentiment_level=SentimentLevel.NEUTRAL,
                confidence=0.0
            )
            self._set_cache(cache_key, sentiment)
            return sentiment
        
        # Filter by time window
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_messages = [msg for msg in messages if msg.created_at >= cutoff_time]
        
        if not recent_messages:
            logger.info(f"No StockTwits messages found for {symbol} in last {hours} hours")
            sentiment = SymbolSentiment(
                symbol=symbol,
                timestamp=datetime.now(),
                mention_count=0,
                average_sentiment=0.0,
                weighted_sentiment=0.0,
                sentiment_level=SentimentLevel.NEUTRAL,
                confidence=0.0
            )
            self._set_cache(cache_key, sentiment)
            return sentiment
        
        # Analyze sentiment for each message
        message_sentiments = []
        
        for msg in recent_messages:
            # Convert StockTwits message to Tweet-like object
            tweet_like = Tweet(
                tweet_id=f"stocktwits_{msg.message_id}",
                text=msg.body,
                author_id=str(msg.user_id),
                author_username=msg.username,
                created_at=msg.created_at,
                like_count=msg.likes_count,
                retweet_count=0,  # StockTwits doesn't have retweets
                reply_count=0,
                quote_count=0,
                is_retweet=False,
                is_quote=False,
                is_reply=False,
                language="en",
                symbols_mentioned=[symbol.upper()] if msg.symbol else []
            )
            
            # Save message to database if persistence enabled
            tweet_model = None
            if self.persist_to_db and self.repository:
                try:
                    tweet_model = self.repository.save_tweet(tweet_like)
                except Exception as e:
                    logger.warning(f"Failed to save StockTwits message to database: {e}")
            
            # Calculate sentiment score
            # Primary: Use built-in StockTwits sentiment
            builtin_score = self._sentiment_to_score(msg.sentiment)
            
            # Optional: Enhance with VADER if enabled
            vader_score = 0.0
            if self.analyzer:
                vader_result = self.analyzer.analyze(msg.body)
                vader_score = vader_result['compound']
            
            # Combine scores (70% built-in, 30% VADER if enabled)
            if self.analyzer:
                combined_score = (builtin_score * 0.7) + (vader_score * 0.3)
            else:
                combined_score = builtin_score
            
            # Calculate engagement weight (likes + base weight)
            engagement_weight = 1.0 + (msg.likes_count / 100.0)  # Cap at ~2.0x for 100+ likes
            
            # Calculate confidence based on sentiment strength and engagement
            confidence = 0.5  # Base confidence
            if msg.sentiment:
                confidence += 0.2  # Built-in sentiment increases confidence
            if msg.likes_count > 0:
                confidence += min(msg.likes_count / 50.0, 0.3)  # Engagement increases confidence
            
            # Weighted sentiment score
            weighted_score = combined_score * engagement_weight
            
            sentiment_result = TweetSentiment(
                tweet_id=tweet_like.tweet_id,
                symbol=symbol,
                sentiment_score=combined_score,
                confidence=min(confidence, 1.0),
                sentiment_level=self.analyzer._score_to_level(weighted_score) if self.analyzer else self._score_to_level_simple(combined_score),
                vader_scores={
                    'compound': combined_score,
                    'pos': 0.0 if combined_score <= 0 else combined_score,
                    'neu': 1.0 - abs(combined_score),
                    'neg': 0.0 if combined_score >= 0 else abs(combined_score)
                },
                engagement_score=engagement_weight,
                influencer_weight=1.0,  # StockTwits users are equally weighted
                weighted_score=weighted_score,
                timestamp=msg.created_at
            )
            
            # Save message sentiment to database if persistence enabled
            if self.persist_to_db and self.repository and tweet_model:
                try:
                    self.repository.save_tweet_sentiment(sentiment_result, tweet_model)
                except Exception as e:
                    logger.warning(f"Failed to save StockTwits sentiment to database: {e}")
            
            message_sentiments.append(sentiment_result)
        
        # Aggregate sentiment
        if not message_sentiments:
            return None
        
        mention_count = len(message_sentiments)
        
        # Calculate average sentiment
        average_sentiment = sum(ts.sentiment_score for ts in message_sentiments) / mention_count
        
        # Calculate weighted average
        total_weighted = sum(ts.weighted_score for ts in message_sentiments)
        total_weight = sum(ts.engagement_score for ts in message_sentiments)
        
        if total_weight > 0:
            weighted_sentiment = total_weighted / total_weight
        else:
            weighted_sentiment = average_sentiment
        
        # Determine sentiment level
        sentiment_level = self._score_to_level_simple(weighted_sentiment)
        if self.analyzer:
            sentiment_level = self.analyzer._score_to_level(weighted_sentiment)
        
        # Calculate confidence (average of message confidences)
        avg_confidence = sum(ts.confidence for ts in message_sentiments) / mention_count
        volume_confidence = min(mention_count / 20, 1.0)  # Max confidence at 20+ messages
        confidence = (avg_confidence + volume_confidence) / 2
        
        # Calculate volume trend by comparing with historical data
        volume_trend = "stable"
        if self.repository:
            try:
                volume_trend = calculate_volume_trend_from_repository(
                    repository=self.repository,
                    symbol=symbol,
                    current_mention_count=mention_count,
                    hours=hours,
                    threshold_percent=0.2  # 20% change threshold
                )
            except Exception as e:
                logger.debug(f"Error calculating volume trend for {symbol}: {e}")
                volume_trend = "stable"
        
        sentiment = SymbolSentiment(
            symbol=symbol,
            timestamp=datetime.now(),
            mention_count=mention_count,
            average_sentiment=average_sentiment,
            weighted_sentiment=weighted_sentiment,
            influencer_sentiment=None,  # Not applicable for StockTwits
            engagement_score=sum(msg.likes_count for msg in recent_messages),
            sentiment_level=sentiment_level,
            confidence=confidence,
            volume_trend=volume_trend,
            tweets=message_sentiments[:10]  # Store top 10 for reference
        )
        
        # Save symbol sentiment to database if persistence enabled
        if self.persist_to_db and self.repository:
            try:
                self.repository.save_symbol_sentiment(sentiment)
            except Exception as e:
                logger.warning(f"Failed to save symbol sentiment to database: {e}")
        
        # Cache result
        self._set_cache(cache_key, sentiment)
        
        # Record API response time (already calculated above)
        try:
            from ...utils.metrics_providers import record_provider_response_time
            record_provider_response_time("stocktwits", api_response_time)
        except (ImportError, Exception) as e:
            logger.debug(f"Could not record response time metric: {e}")
        
        # Record successful request with response time
        self.usage_monitor.record_request("stocktwits", success=True, cached=False, response_time=api_response_time)
        
        logger.info(
            f"StockTwits sentiment for {symbol}: {weighted_sentiment:.3f} "
            f"({sentiment_level.value}) - {mention_count} messages"
        )
        
        return sentiment
    
    def _score_to_level_simple(self, score: float) -> SentimentLevel:
        """Simple score to level conversion (without VADER analyzer)"""
        if score >= 0.5:
            return SentimentLevel.VERY_BULLISH
        elif score >= 0.1:
            return SentimentLevel.BULLISH
        elif score <= -0.5:
            return SentimentLevel.VERY_BEARISH
        elif score <= -0.1:
            return SentimentLevel.BEARISH
        else:
            return SentimentLevel.NEUTRAL
    
    def get_trending_symbols(self) -> List[Dict[str, Any]]:
        """
        Get trending stock symbols on StockTwits
        
        Returns:
            List of trending symbols with watchlist counts
        """
        if not self.is_available():
            return []
        
        trending = self.client.get_trending_symbols(limit=20)
        
        logger.info(f"Found {len(trending)} trending symbols on StockTwits")
        return trending
