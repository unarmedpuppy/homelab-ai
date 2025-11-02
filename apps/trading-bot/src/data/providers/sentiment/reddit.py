"""
Reddit Sentiment Provider
=========================

Integration with Reddit API for sentiment analysis of stock mentions.
"""

import logging
import re
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import time

try:
    import praw
    from praw.exceptions import RedditAPIException, ClientException
except ImportError:
    praw = None
    RedditAPIException = None
    ClientException = None

from ...config.settings import settings
from .models import SymbolSentiment, SentimentLevel, Tweet, TweetSentiment
from .sentiment_analyzer import SentimentAnalyzer
from .repository import SentimentRepository
from .volume_trend import calculate_volume_trend_from_repository

logger = logging.getLogger(__name__)


class RedditPost:
    """Reddit post/comment data model (similar to Tweet)"""
    def __init__(
        self,
        post_id: str,
        text: str,
        author: str,
        created_at: datetime,
        score: int = 0,
        upvote_ratio: float = 1.0,
        num_comments: int = 0,
        subreddit: str = "",
        is_post: bool = True,
        parent_id: Optional[str] = None,
        symbols_mentioned: Optional[List[str]] = None
    ):
        self.post_id = post_id
        self.text = text
        self.author = author if author != "[deleted]" else "unknown"
        self.created_at = created_at
        self.score = score
        self.upvote_ratio = upvote_ratio
        self.num_comments = num_comments
        self.subreddit = subreddit
        self.is_post = is_post
        self.parent_id = parent_id
        self.symbols_mentioned = symbols_mentioned or []
        
        # For compatibility with Tweet-like interface
        self.tweet_id = post_id  # Alias for compatibility
        self.author_id = author
        self.author_username = author
        self.like_count = score
        self.retweet_count = num_comments  # Use comments as engagement metric
        self.reply_count = 0  # Not directly available
        self.quote_count = 0
        self.is_retweet = False
        self.is_quote = False
        self.is_reply = not is_post
        self.language = "en"
        self.raw_data = None


class RedditClient:
    """
    Reddit API client using PRAW with rate limiting and error handling
    
    Handles authentication, rate limiting, and API requests.
    """
    
    def __init__(self):
        """Initialize Reddit client"""
        if praw is None:
            raise ImportError(
                "praw is required for Reddit integration. "
                "Install with: pip install praw"
            )
        
        self.config = settings.reddit
        
        # Validate credentials
        if not self.config.client_id or not self.config.client_secret:
            logger.warning("Reddit Client ID/Secret not configured. Reddit sentiment will be disabled.")
            self.reddit = None
            return
        
        # Initialize PRAW client
        try:
            self.reddit = praw.Reddit(
                client_id=self.config.client_id,
                client_secret=self.config.client_secret,
                user_agent=self.config.user_agent,
                username=self.config.username,
                password=self.config.password
            )
            
            # Test connection
            if self.reddit.read_only:
                logger.info("Reddit client initialized successfully (read-only mode)")
            else:
                logger.info("Reddit client initialized successfully (authenticated mode)")
        except Exception as e:
            logger.error(f"Failed to initialize Reddit client: {e}")
            self.reddit = None
    
    def is_available(self) -> bool:
        """Check if Reddit client is available and authenticated"""
        if self.reddit is None:
            return False
        
        try:
            # Test with a simple read operation
            _ = self.reddit.user.me() if not self.reddit.read_only else None
            return True
        except Exception:
            # Read-only mode is fine
            return True
    
    def get_subreddits(self) -> List[str]:
        """Get list of subreddits to monitor"""
        return [s.strip() for s in self.config.subreddits.split(",") if s.strip()]
    
    def search_posts(self, query: str, subreddit: Optional[str] = None,
                     limit: Optional[int] = None,
                     time_filter: str = "day") -> List[RedditPost]:
        """
        Search for posts matching query
        
        Args:
            query: Search query string
            subreddit: Specific subreddit (None for all configured subreddits)
            limit: Maximum number of results (default: from config)
            time_filter: Time filter (hour, day, week, month, year, all)
            
        Returns:
            List of RedditPost objects
        """
        if not self.is_available():
            logger.warning("Reddit client not available")
            return []
        
        if limit is None:
            limit = min(self.config.max_results, 100)  # Reasonable default
        
        posts = []
        subreddits_to_search = [subreddit] if subreddit else self.get_subreddits()
        
        try:
            for subreddit_name in subreddits_to_search:
                try:
                    subreddit_obj = self.reddit.subreddit(subreddit_name)
                    
                    # Search posts
                    search_results = subreddit_obj.search(
                        query,
                        limit=limit,
                        time_filter=time_filter,
                        sort="relevance"
                    )
                    
                    for submission in search_results:
                        # Skip if score too low
                        if submission.score < self.config.min_score:
                            continue
                        
                        # Skip if text too short
                        if len(submission.selftext or "") < self.config.min_length:
                            continue
                        
                        post = RedditPost(
                            post_id=submission.id,
                            text=submission.title + " " + (submission.selftext or ""),
                            author=str(submission.author) if submission.author else "unknown",
                            created_at=datetime.fromtimestamp(submission.created_utc),
                            score=submission.score,
                            upvote_ratio=submission.upvote_ratio,
                            num_comments=submission.num_comments,
                            subreddit=subreddit_name,
                            is_post=True
                        )
                        posts.append(post)
                        
                except Exception as e:
                    logger.warning(f"Error searching subreddit {subreddit_name}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(posts)} posts for query: {query[:50]}...")
            return posts
            
        except RedditAPIException as e:
            logger.warning(f"Reddit API error: {e}")
            return []
        except ClientException as e:
            logger.error(f"Reddit client error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error searching Reddit posts: {e}", exc_info=True)
            return []
    
    def get_recent_posts(self, subreddit: Optional[str] = None,
                        limit: Optional[int] = None,
                        time_filter: str = "day") -> List[RedditPost]:
        """
        Get recent posts from subreddit(s)
        
        Args:
            subreddit: Specific subreddit (None for all configured subreddits)
            limit: Maximum number of results
            time_filter: Time filter (hour, day, week, month, year, all)
            
        Returns:
            List of RedditPost objects
        """
        if not self.is_available():
            logger.warning("Reddit client not available")
            return []
        
        if limit is None:
            limit = min(self.config.max_results, 100)
        
        posts = []
        subreddits_to_search = [subreddit] if subreddit else self.get_subreddits()
        
        try:
            for subreddit_name in subreddits_to_search:
                try:
                    subreddit_obj = self.reddit.subreddit(subreddit_name)
                    
                    # Get hot/top posts
                    for submission in subreddit_obj.hot(limit=limit):
                        # Skip if score too low
                        if submission.score < self.config.min_score:
                            continue
                        
                        # Skip if text too short
                        text = submission.title + " " + (submission.selftext or "")
                        if len(text) < self.config.min_length:
                            continue
                        
                        post = RedditPost(
                            post_id=submission.id,
                            text=text,
                            author=str(submission.author) if submission.author else "unknown",
                            created_at=datetime.fromtimestamp(submission.created_utc),
                            score=submission.score,
                            upvote_ratio=submission.upvote_ratio,
                            num_comments=submission.num_comments,
                            subreddit=subreddit_name,
                            is_post=True
                        )
                        posts.append(post)
                        
                        # Also get top comments from the post
                        submission.comments.replace_more(limit=0)
                        for comment in submission.comments.list()[:10]:  # Top 10 comments
                            if comment.score >= self.config.min_score and len(comment.body or "") >= self.config.min_length:
                                comment_post = RedditPost(
                                    post_id=comment.id,
                                    text=comment.body or "",
                                    author=str(comment.author) if comment.author else "unknown",
                                    created_at=datetime.fromtimestamp(comment.created_utc),
                                    score=comment.score,
                                    upvote_ratio=1.0,
                                    num_comments=0,
                                    subreddit=subreddit_name,
                                    is_post=False,
                                    parent_id=submission.id
                                )
                                posts.append(comment_post)
                        
                except Exception as e:
                    logger.warning(f"Error getting posts from {subreddit_name}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(posts)} posts/comments from Reddit")
            return posts
            
        except Exception as e:
            logger.error(f"Error getting recent Reddit posts: {e}", exc_info=True)
            return []
    
    def extract_symbols(self, text: str) -> List[str]:
        """
        Extract stock symbols from text
        
        Args:
            text: Text to analyze
            
        Returns:
            List of stock symbols found
        """
        # Pattern for $SYMBOL or SYMBOL mentions
        pattern = r'\$([A-Z]{1,5})\b|(?<![A-Z])([A-Z]{1,5})(?=\s+(?:stock|shares|option|call|put|calls|puts|to the moon|🚀|📈))'
        
        symbols = []
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        for match in matches:
            symbol = match[0] or match[1]
            if symbol and symbol not in symbols:
                # Filter out common false positives
                if symbol not in ["I", "A", "IT", "AM", "PM", "DD", "TL", "DR"]:
                    symbols.append(symbol.upper())
        
        return symbols
    
    def build_symbol_query(self, symbol: str) -> str:
        """
        Build Reddit search query for a stock symbol
        
        Args:
            symbol: Stock symbol (e.g., "SPY")
            
        Returns:
            Search query string
        """
        # Search for $SYMBOL or SYMBOL stock
        return f'${symbol} OR "{symbol} stock" OR "{symbol} shares"'


class RedditSentimentProvider:
    """
    Reddit sentiment provider for stock symbols
    
    Handles post/comment collection, sentiment analysis, and aggregation.
    """
    
    def __init__(self, persist_to_db: bool = True):
        """
        Initialize Reddit sentiment provider
        
        Args:
            persist_to_db: Whether to persist data to database (default: True)
        """
        self.client = RedditClient()
        self.analyzer = SentimentAnalyzer()
        self.cache = get_cache_manager()
        self.cache_ttl = settings.reddit.cache_ttl
        self.rate_limiter = get_rate_limiter("reddit")
        self.usage_monitor = get_usage_monitor()
        self.persist_to_db = persist_to_db
        self.repository = SentimentRepository() if persist_to_db else None
        
        logger.info(f"RedditSentimentProvider initialized (persist_to_db={persist_to_db})")
    
    def is_available(self) -> bool:
        """Check if Reddit provider is available"""
        return self.client.is_available()
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache using Redis-backed cache manager"""
        cache_key = f"reddit:{key}"
        return self.cache.get(cache_key)
    
    def _set_cache(self, key: str, data: Any):
        """Store data in cache using Redis-backed cache manager"""
        cache_key = f"reddit:{key}"
        self.cache.set(cache_key, data, ttl=self.cache_ttl)
    
    def get_sentiment(self, symbol: str, hours: int = 24) -> Optional[SymbolSentiment]:
        """
        Get sentiment for a symbol from Reddit
        
        Args:
            symbol: Stock symbol
            hours: Hours of data to analyze (default: 24)
            
        Returns:
            SymbolSentiment object or None
        """
        if not self.is_available():
            logger.warning("Reddit client not available")
            return None
        
        # Check rate limit (60 requests per minute)
        is_allowed, rate_status = self.rate_limiter.check_rate_limit(limit=60, window_seconds=60)
        if not is_allowed:
            logger.warning(f"Reddit rate limit exceeded for {symbol}, waiting...")
            rate_status = self.rate_limiter.wait_if_needed(limit=60, window_seconds=60)
            if rate_status.is_limited:
                logger.error(f"Reddit rate limit still exceeded after wait")
                self.usage_monitor.record_request("reddit", success=False)
                return None
        
        # Check cache
        cache_key = f"sentiment_{symbol}_{hours}"
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"Returning cached sentiment for {symbol}")
            self.usage_monitor.record_request("reddit", success=True, cached=True)
            return cached
        
        # Calculate time window
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Determine time filter
        if hours <= 1:
            time_filter = "hour"
        elif hours <= 24:
            time_filter = "day"
        elif hours <= 168:  # 7 days
            time_filter = "week"
        else:
            time_filter = "month"
        
        # Search for posts mentioning symbol
        query = self.client.build_symbol_query(symbol)
        posts = self.client.search_posts(query, limit=settings.reddit.max_results, time_filter=time_filter)
        
        # Also get recent posts and filter by symbol
        recent_posts = self.client.get_recent_posts(limit=settings.reddit.max_results, time_filter=time_filter)
        
        # Filter posts by symbol mention and time window
        relevant_posts = []
        for post in posts + recent_posts:
            # Check if symbol is mentioned
            symbols_found = self.client.extract_symbols(post.text)
            if symbol.upper() in [s.upper() for s in symbols_found]:
                # Check time window
                if start_time <= post.created_at <= end_time:
                    post.symbols_mentioned = symbols_found
                    relevant_posts.append(post)
        
        if not relevant_posts:
            logger.info(f"No Reddit posts found for {symbol}")
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
        
        # Analyze sentiment for each post
        post_sentiments = []
        
        for post in relevant_posts:
            # Calculate engagement weight based on upvotes and comments
            # Reddit posts use upvote ratio and score
            engagement_score = self._calculate_engagement_score(post)
            engagement_weight = self.analyzer.calculate_engagement_weight(engagement_score)
            
            # Convert RedditPost to Tweet-like object for analyzer
            tweet_like = Tweet(
                tweet_id=f"reddit_{post.post_id}",  # Prefix to avoid conflicts with Twitter IDs
                text=post.text,
                author_id=post.author,
                author_username=post.author,
                created_at=post.created_at,
                like_count=post.score,
                retweet_count=post.num_comments,
                reply_count=0,
                quote_count=0,
                is_retweet=False,
                is_quote=False,
                is_reply=not post.is_post,
                language="en",
                symbols_mentioned=post.symbols_mentioned
            )
            
            # Save Reddit post to database if persistence enabled
            post_model = None
            if self.persist_to_db and self.repository:
                try:
                    post_model = self.repository.save_reddit_post(post)
                except Exception as e:
                    logger.warning(f"Failed to save Reddit post to database: {e}")
            
            sentiment_result = self.analyzer.analyze_tweet(
                tweet=tweet_like,
                symbol=symbol,
                engagement_weight=engagement_weight,
                influencer_weight=1.0  # No influencer tracking for Reddit yet
            )
            
            # Save Reddit sentiment to database if persistence enabled
            if self.persist_to_db and self.repository and post_model:
                try:
                    self.repository.save_reddit_sentiment(sentiment_result, post_model)
                except Exception as e:
                    logger.warning(f"Failed to save Reddit post sentiment to database: {e}")
            
            post_sentiments.append(sentiment_result)
        
        # Aggregate sentiment
        if not post_sentiments:
            return None
        
        mention_count = len(post_sentiments)
        
        # Calculate average sentiment
        average_sentiment = sum(ps.sentiment_score for ps in post_sentiments) / mention_count
        
        # Calculate weighted average (using upvote ratio and score)
        total_weighted = sum(ps.weighted_score for ps in post_sentiments)
        total_weight = sum(
            ps.engagement_score
            for ps in post_sentiments
        )
        
        if total_weight > 0:
            weighted_sentiment = total_weighted / total_weight
        else:
            weighted_sentiment = average_sentiment
        
        # Determine sentiment level
        sentiment_level = self.analyzer._score_to_level(weighted_sentiment)
        
        # Calculate confidence (based on sample size and polarity)
        avg_confidence = sum(ps.confidence for ps in post_sentiments) / mention_count
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
            influencer_sentiment=None,
            engagement_score=sum(ps.engagement_score for ps in post_sentiments) / mention_count,
            sentiment_level=sentiment_level,
            confidence=confidence,
            volume_trend=volume_trend,
            tweets=post_sentiments[:10]  # Store top 10 for reference
        )
        
        # Save symbol sentiment to database if persistence enabled (reuse Twitter table)
        if self.persist_to_db and self.repository:
            try:
                self.repository.save_symbol_sentiment(sentiment)
            except Exception as e:
                logger.warning(f"Failed to save Reddit symbol sentiment to database: {e}")
        
        # Cache result
        self._set_cache(cache_key, sentiment)
        
        # Record successful request
        self.usage_monitor.record_request("reddit", success=True, cached=False)
        
        logger.info(
            f"Reddit sentiment for {symbol}: {weighted_sentiment:.3f} "
            f"({sentiment_level.value}) - {mention_count} mentions"
        )
        
        return sentiment
    
    def _calculate_engagement_score(self, post: RedditPost) -> float:
        """
        Calculate engagement score for a Reddit post/comment
        
        Args:
            post: RedditPost object
            
        Returns:
            Engagement score (0.0 to 1.0+)
        """
        # Reddit-specific engagement calculation
        # Weight score by upvote ratio and total score
        base_score = post.score * post.upvote_ratio
        comment_bonus = post.num_comments * 0.5  # Comments add value
        
        total_engagement = base_score + comment_bonus
        
        # Normalize using logarithmic scaling (similar to Twitter)
        if total_engagement == 0:
            return 0.0
        
        import math
        normalized = math.log10(total_engagement + 1) / math.log10(10000)
        
        return min(normalized, 2.0)  # Cap at 2.0x
    
    def get_trending_symbols(self, min_mentions: int = 10) -> List[Dict[str, Any]]:
        """
        Get trending stock symbols on Reddit
        
        Args:
            min_mentions: Minimum mentions to be considered trending
            
        Returns:
            List of trending symbols with mention counts
        """
        if not self.is_available():
            return []
        
        # Get recent posts
        posts = self.client.get_recent_posts(limit=500, time_filter="day")
        
        # Count symbol mentions
        symbol_counts: Dict[str, int] = {}
        
        for post in posts:
            symbols = self.client.extract_symbols(post.text)
            for symbol in symbols:
                symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        
        # Filter by minimum mentions and sort
        trending = [
            {"symbol": symbol, "mentions": count}
            for symbol, count in symbol_counts.items()
            if count >= min_mentions
        ]
        
        trending.sort(key=lambda x: x["mentions"], reverse=True)
        
        logger.info(f"Found {len(trending)} trending symbols on Reddit")
        return trending[:20]  # Top 20

