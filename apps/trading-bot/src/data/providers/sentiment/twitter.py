"""
Twitter/X Sentiment Provider
============================

Integration with Twitter API v2 for sentiment analysis of stock mentions.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time
from collections import deque

try:
    import tweepy
    from tweepy import Client, RateLimitError, TooManyRequests
except ImportError:
    tweepy = None
    Client = None
    RateLimitError = None
    TooManyRequests = None

from ....config.settings import settings
from .models import Tweet, TweetSentiment, SymbolSentiment, SentimentLevel, Influencer
from .sentiment_analyzer import SentimentAnalyzer
from .repository import SentimentRepository
from .volume_trend import calculate_volume_trend_from_repository

logger = logging.getLogger(__name__)


class TwitterClient:
    """
    Twitter API v2 client with rate limiting and error handling
    
    Handles authentication, rate limiting, and API requests.
    """
    
    def __init__(self):
        """Initialize Twitter client"""
        if tweepy is None:
            raise ImportError(
                "tweepy is required for Twitter integration. "
                "Install with: pip install tweepy"
            )
        
        self.config = settings.twitter
        
        # Validate credentials
        if not self.config.bearer_token:
            logger.warning("Twitter Bearer Token not configured. Twitter sentiment will be disabled.")
            self.client = None
            return
        
        # Initialize Tweepy client
        try:
            self.client = Client(
                bearer_token=self.config.bearer_token,
                consumer_key=self.config.api_key,
                consumer_secret=self.config.api_secret,
                access_token=self.config.access_token,
                access_token_secret=self.config.access_token_secret,
                wait_on_rate_limit=self.config.rate_limit_enabled
            )
            logger.info("Twitter client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Twitter client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Twitter client is available and authenticated"""
        return self.client is not None
    
    def _rate_limit_check(self):
        """Check and handle rate limits"""
        if not self.config.rate_limit_enabled:
            return
        
        # Tweepy handles rate limiting automatically when wait_on_rate_limit=True
        # This is a placeholder for manual rate limiting if needed
        pass
    
    def search_tweets(self, query: str, max_results: Optional[int] = None,
                     start_time: Optional[datetime] = None,
                     end_time: Optional[datetime] = None) -> List[Tweet]:
        """
        Search for tweets matching query
        
        Args:
            query: Search query string
            max_results: Maximum number of results (default: from config)
            start_time: Start time for search
            end_time: End time for search
            
        Returns:
            List of Tweet objects
        """
        if not self.is_available():
            logger.warning("Twitter client not available")
            return []
        
        if max_results is None:
            max_results = min(self.config.max_results, 100)  # API limit is 100
        
        try:
            # Build search parameters
            params = {
                'query': query,
                'max_results': max_results,
                'tweet_fields': [
                    'created_at', 'public_metrics', 'author_id', 'lang',
                    'in_reply_to_user_id', 'referenced_tweets'
                ],
                'user_fields': ['username', 'verified', 'public_metrics'],
                'expansions': ['author_id']
            }
            
            if start_time:
                params['start_time'] = start_time.isoformat()
            if end_time:
                params['end_time'] = end_time.isoformat()
            
            # Execute search
            response = self.client.search_recent_tweets(**params)
            
            if not response.data:
                return []
            
            # Map users by ID for author lookup
            users = {}
            if response.includes and 'users' in response.includes:
                users = {user.id: user for user in response.includes['users']}
            
            # Convert to Tweet objects
            tweets = []
            for tweet_data in response.data:
                author_id = tweet_data.author_id
                author = users.get(author_id)
                
                metrics = tweet_data.public_metrics
                
                # Check if retweet or reply
                is_retweet = False
                is_reply = tweet_data.in_reply_to_user_id is not None
                is_quote = False
                
                if tweet_data.referenced_tweets:
                    for ref in tweet_data.referenced_tweets:
                        if ref.type == 'retweeted':
                            is_retweet = True
                        elif ref.type == 'quoted':
                            is_quote = True
                
                # Skip retweets if configured
                if is_retweet:
                    continue
                
                tweet = Tweet(
                    tweet_id=tweet_data.id,
                    text=tweet_data.text,
                    author_id=author_id,
                    author_username=author.username if author else "unknown",
                    created_at=tweet_data.created_at,
                    like_count=metrics.get('like_count', 0),
                    retweet_count=metrics.get('retweet_count', 0),
                    reply_count=metrics.get('reply_count', 0),
                    quote_count=metrics.get('quote_count', 0),
                    is_retweet=is_retweet,
                    is_quote=is_quote,
                    is_reply=is_reply,
                    language=tweet_data.lang,
                    raw_data=tweet_data.data if hasattr(tweet_data, 'data') else None
                )
                
                tweets.append(tweet)
            
            logger.info(f"Retrieved {len(tweets)} tweets for query: {query[:50]}...")
            return tweets
            
        except (RateLimitError, TooManyRequests) as e:
            logger.warning(
                f"Twitter rate limit error searching tweets: {e}",
                extra={
                    'query': query[:50],
                    'error_type': type(e).__name__,
                    'operation': 'search_tweets'
                }
            )
            return []
        except Exception as e:
            logger.error(
                f"Unexpected error searching tweets: {e}",
                exc_info=True,
                extra={
                    'query': query[:50],
                    'error_type': type(e).__name__,
                    'operation': 'search_tweets'
                }
            )
            return []
    
    def build_symbol_query(self, symbol: str, exclude_retweets: bool = True,
                          language: Optional[str] = None) -> str:
        """
        Build Twitter search query for a stock symbol
        
        Args:
            symbol: Stock symbol (e.g., "SPY")
            exclude_retweets: Whether to exclude retweets
            language: Language code (default: from config)
            
        Returns:
            Search query string
        """
        # Build query: $SYMBOL OR #SYMBOL OR "SYMBOL stock"
        query_parts = [
            f'${symbol}',
            f'#{symbol}',
            f'"{symbol} stock"'
        ]
        
        query = ' OR '.join(query_parts)
        
        # Exclude retweets
        if exclude_retweets:
            query += ' -is:retweet'
        
        # Language filter
        if language is None:
            language = self.config.search_language
        if language:
            query += f' lang:{language}'
        
        return query
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user information
        
        Args:
            user_id: Twitter user ID
            
        Returns:
            User information dictionary or None
        """
        if not self.is_available():
            return None
        
        try:
            user = self.client.get_user(
                id=user_id,
                user_fields=['username', 'verified', 'public_metrics', 'description']
            )
            
            if user.data:
                return {
                    'id': user.data.id,
                    'username': user.data.username,
                    'verified': user.data.verified,
                    'follower_count': user.data.public_metrics.get('followers_count', 0),
                    'following_count': user.data.public_metrics.get('following_count', 0),
                    'tweet_count': user.data.public_metrics.get('tweet_count', 0)
                }
        except Exception as e:
            logger.error(f"Error getting user info for {user_id}: {e}")
        
        return None


class TwitterSentimentProvider:
    """
    Twitter sentiment provider for stock symbols
    
    Handles tweet collection, sentiment analysis, and aggregation.
    """
    
    def __init__(self, persist_to_db: bool = True):
        """
        Initialize Twitter sentiment provider
        
        Args:
            persist_to_db: Whether to persist data to database (default: True)
        """
        self.client = TwitterClient()
        self.analyzer = SentimentAnalyzer()
        self.cache = get_cache_manager()
        self.cache_ttl = settings.twitter.cache_ttl
        self.rate_limiter = get_rate_limiter("twitter")
        self.usage_monitor = get_usage_monitor()
        self.influencers: Dict[str, Influencer] = {}
        self.persist_to_db = persist_to_db
        self.repository = SentimentRepository() if persist_to_db else None
        
        # Load influencers from database if available
        if self.persist_to_db and self.repository:
            self._load_influencers_from_db()
        
        logger.info(f"TwitterSentimentProvider initialized (persist_to_db={persist_to_db})")
    
    def is_available(self) -> bool:
        """Check if Twitter provider is available"""
        return self.client.is_available()
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache using Redis-backed cache manager"""
        cache_key = f"twitter:{key}"
        return self.cache.get(cache_key)
    
    def _set_cache(self, key: str, data: Any):
        """Store data in cache using Redis-backed cache manager"""
        cache_key = f"twitter:{key}"
        self.cache.set(cache_key, data, ttl=self.cache_ttl)
    
    def _load_influencers_from_db(self):
        """Load influencers from database"""
        if not self.repository:
            return
        
        try:
            db_influencers = self.repository.get_influencers(active_only=True)
            for db_inf in db_influencers:
                influencer = Influencer(
                    user_id=db_inf.user_id,
                    username=db_inf.username,
                    display_name=db_inf.display_name or db_inf.username,
                    follower_count=db_inf.follower_count,
                    following_count=db_inf.following_count,
                    tweet_count=db_inf.tweet_count,
                    is_verified=db_inf.is_verified,
                    is_protected=db_inf.is_protected,
                    category=db_inf.category,
                    weight_multiplier=db_inf.weight_multiplier,
                    is_active=db_inf.is_active,
                    added_at=db_inf.added_at
                )
                self.influencers[db_inf.user_id] = influencer
            
            logger.info(f"Loaded {len(self.influencers)} influencers from database")
        except Exception as e:
            logger.warning(f"Failed to load influencers from database: {e}")
    
    def get_sentiment(self, symbol: str, hours: int = 24) -> Optional[SymbolSentiment]:
        """
        Get sentiment for a symbol
        
        Args:
            symbol: Stock symbol
            hours: Hours of data to analyze (default: 24)
            
        Returns:
            SymbolSentiment object or None
        """
        # Track provider availability
        is_available = self.is_available()
        try:
            from ....utils.metrics_providers import update_provider_availability
            update_provider_availability("twitter", is_available)
        except (ImportError, Exception) as e:
            logger.debug(f"Could not record availability metric: {e}")
        
        if not is_available:
            logger.warning("Twitter client not available")
            return None
        
        # Check rate limit (300 requests per 15 minutes = 900 seconds)
        is_allowed, rate_status = self.rate_limiter.check_rate_limit(limit=300, window_seconds=900)
        if not is_allowed:
            logger.warning(f"Twitter rate limit exceeded for {symbol}, waiting...")
            rate_status = self.rate_limiter.wait_if_needed(limit=300, window_seconds=900)
            if rate_status.is_limited:
                logger.error(f"Twitter rate limit still exceeded after wait")
                # Record rate limit hit metric
                try:
                    from ....utils.metrics_providers import record_rate_limit_hit
                    record_rate_limit_hit("twitter")
                except (ImportError, Exception) as e:
                    logger.debug(f"Could not record rate limit metric: {e}")
                self.usage_monitor.record_request("twitter", success=False)
                return None
        
        # Check cache
        cache_key = f"sentiment_{symbol}_{hours}"
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"Returning cached sentiment for {symbol}")
            # Track data freshness
            try:
                from ....utils.metrics_providers import update_data_freshness
                cache_age = (datetime.now() - cached.timestamp).total_seconds()
                update_data_freshness("twitter", "get_sentiment", cache_age)
            except (ImportError, Exception) as e:
                logger.debug(f"Could not record data freshness metric: {e}")
            self.usage_monitor.record_request("twitter", success=True, cached=True)
            return cached
        
        # Track API call timing
        import time
        api_start_time = time.time()
        
        # Calculate time window
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Build query
        query = self.client.build_symbol_query(symbol)
        
        # Search tweets
        tweets = self.client.search_tweets(
            query=query,
            start_time=start_time,
            end_time=end_time
        )
        
        # Record API response time
        api_response_time = time.time() - api_start_time
        try:
            from ....utils.metrics_providers import record_provider_response_time
            record_provider_response_time("twitter", api_response_time)
        except (ImportError, Exception) as e:
            logger.debug(f"Could not record response time metric: {e}")
        
        if not tweets:
            logger.info(f"No tweets found for {symbol}")
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
        
        # Analyze sentiment for each tweet
        tweet_sentiments = []
        
        for tweet in tweets:
            # Extract symbol mentions
            if symbol.upper() not in [s.upper() for s in tweet.symbols_mentioned]:
                tweet.symbols_mentioned.append(symbol.upper())
            
            # Save tweet to database if persistence enabled
            tweet_model = None
            if self.persist_to_db and self.repository:
                try:
                    tweet_model = self.repository.save_tweet(tweet)
                except Exception as e:
                    logger.warning(f"Failed to save tweet to database: {e}")
            
            # Calculate engagement weight
            engagement_score = self.analyzer._calculate_engagement_score(tweet)
            engagement_weight = self.analyzer.calculate_engagement_weight(engagement_score)
            
            # Check if influencer
            influencer_weight = 1.0
            if tweet.author_id in self.influencers:
                influencer = self.influencers[tweet.author_id]
                influencer_weight = influencer.weight_multiplier
            
            # Analyze sentiment
            sentiment_result = self.analyzer.analyze_tweet(
                tweet=tweet,
                symbol=symbol,
                engagement_weight=engagement_weight,
                influencer_weight=influencer_weight
            )
            
            # Save tweet sentiment to database if persistence enabled
            if self.persist_to_db and self.repository and tweet_model:
                try:
                    self.repository.save_tweet_sentiment(sentiment_result, tweet_model)
                except Exception as e:
                    logger.warning(f"Failed to save tweet sentiment to database: {e}")
            
            tweet_sentiments.append(sentiment_result)
        
        # Aggregate sentiment
        if not tweet_sentiments:
            return None
        
        mention_count = len(tweet_sentiments)
        
        # Calculate average sentiment
        average_sentiment = sum(ts.sentiment_score for ts in tweet_sentiments) / mention_count
        
        # Calculate weighted average
        total_weighted = sum(ts.weighted_score for ts in tweet_sentiments)
        total_weight = sum(
            ts.engagement_score * ts.influencer_weight 
            for ts in tweet_sentiments
        )
        
        if total_weight > 0:
            weighted_sentiment = total_weighted / total_weight
        else:
            weighted_sentiment = average_sentiment
        
        # Calculate influencer-only sentiment
        influencer_sentiments = [
            ts for ts in tweet_sentiments 
            if ts.influencer_weight > 1.0
        ]
        
        influencer_sentiment = None
        if influencer_sentiments:
            influencer_sentiment = sum(
                ts.weighted_score for ts in influencer_sentiments
            ) / len(influencer_sentiments)
        
        # Calculate engagement score
        total_engagement = sum(ts.engagement_score for ts in tweet_sentiments)
        avg_engagement = total_engagement / mention_count if mention_count > 0 else 0.0
        
        # Determine sentiment level
        sentiment_level = self.analyzer._score_to_level(weighted_sentiment)
        
        # Calculate confidence (based on sample size and polarity)
        avg_confidence = sum(ts.confidence for ts in tweet_sentiments) / mention_count
        volume_confidence = min(mention_count / 50, 1.0)  # Max confidence at 50+ mentions
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
            influencer_sentiment=influencer_sentiment,
            engagement_score=avg_engagement,
            sentiment_level=sentiment_level,
            confidence=confidence,
            volume_trend=volume_trend,
            tweets=tweet_sentiments[:10]  # Store top 10 for reference
        )
        
        # Save symbol sentiment to database if persistence enabled
        if self.persist_to_db and self.repository:
            try:
                self.repository.save_symbol_sentiment(sentiment)
            except Exception as e:
                logger.warning(f"Failed to save symbol sentiment to database: {e}")
        
        # Cache result
        self._set_cache(cache_key, sentiment)
        
        # Record successful request with response time
        self.usage_monitor.record_request(
            "twitter", 
            success=True, 
            cached=False,
            response_time=api_response_time
        )
        
        logger.info(
            f"Sentiment for {symbol}: {weighted_sentiment:.3f} "
            f"({sentiment_level.value}) - {mention_count} mentions"
        )
        
        return sentiment
    
    def add_influencer(self, user_id: str, username: str, 
                      category: str = "trader", weight_multiplier: float = 1.5):
        """
        Add an influencer to track
        
        Args:
            user_id: Twitter user ID
            username: Twitter username
            category: Category (trader, analyst, news, etc.)
            weight_multiplier: Weight multiplier for their tweets
        """
        # Get user info
        user_info = self.client.get_user_info(user_id)
        
        influencer = Influencer(
            user_id=user_id,
            username=username,
            display_name=username,
            follower_count=user_info.get('follower_count', 0) if user_info else 0,
            following_count=user_info.get('following_count', 0) if user_info else 0,
            tweet_count=user_info.get('tweet_count', 0) if user_info else 0,
            is_verified=user_info.get('verified', False) if user_info else False,
            category=category,
            weight_multiplier=weight_multiplier
        )
        
        # Save to database if persistence enabled
        if self.persist_to_db and self.repository:
            try:
                self.repository.save_influencer(influencer)
            except Exception as e:
                logger.warning(f"Failed to save influencer to database: {e}")
        
        self.influencers[user_id] = influencer
        logger.info(f"Added influencer: {username} ({category})")
    
    def get_trending_symbols(self, min_mentions: int = 50) -> List[Dict[str, Any]]:
        """
        Get trending stock symbols on Twitter
        
        Args:
            min_mentions: Minimum mentions to be considered trending
            
        Returns:
            List of trending symbols with mention counts
        """
        # This would require tracking mentions across multiple symbols
        # For now, return empty list - can be enhanced later
        logger.warning("Trending symbols detection not yet implemented")
        return []

