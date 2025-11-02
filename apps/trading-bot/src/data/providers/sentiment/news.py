"""
Financial News Sentiment Provider
==================================

Integration with financial news sources for sentiment analysis of stock mentions.
Supports RSS feeds, NewsAPI, and web scraping.
"""

import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time

try:
    import feedparser
    from newspaper import Article
except ImportError:
    feedparser = None
    Article = None

try:
    from newsapi import NewsApiClient
except ImportError:
    NewsApiClient = None

from ...config.settings import settings
from .models import SymbolSentiment, SentimentLevel, Tweet, TweetSentiment
from .sentiment_analyzer import SentimentAnalyzer
from .repository import SentimentRepository
from .volume_trend import calculate_volume_trend_from_repository

logger = logging.getLogger(__name__)


class NewsArticle:
    """News article data model (similar to Tweet)"""
    def __init__(
        self,
        article_id: str,
        title: str,
        text: str,
        source: str,
        url: str,
        published_at: datetime,
        author: Optional[str] = None,
        symbols_mentioned: Optional[List[str]] = None
    ):
        self.article_id = article_id
        self.title = title
        self.text = text
        self.source = source
        self.url = url
        self.published_at = published_at
        self.author = author or "unknown"
        self.symbols_mentioned = symbols_mentioned or []
        
        # For compatibility with Tweet-like interface
        self.tweet_id = f"news_{article_id}"
        self.author_id = self.author
        self.author_username = self.author
        self.created_at = published_at
        self.like_count = 0  # Not applicable for news
        self.retweet_count = 0
        self.reply_count = 0
        self.quote_count = 0
        self.is_retweet = False
        self.is_quote = False
        self.is_reply = False
        self.language = "en"
        self.raw_data = None


class NewsClient:
    """
    Financial news client supporting RSS feeds, NewsAPI, and web scraping
    
    Handles multiple news sources and article fetching.
    """
    
    def __init__(self):
        """Initialize news client"""
        self.config = settings.news
        
        # Validate configuration
        if not self.config.enabled:
            logger.warning("News provider is disabled in configuration")
            self.available = False
            return
        
        self.available = True
        
        # Initialize NewsAPI client if API key provided
        self.newsapi_client = None
        if self.config.newsapi_key and NewsApiClient:
            try:
                self.newsapi_client = NewsApiClient(api_key=self.config.newsapi_key)
                logger.info("NewsAPI client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize NewsAPI client: {e}")
        
        # RSS feed sources
        self.rss_feeds = [
            feed.strip() 
            for feed in self.config.rss_feeds.split(",") 
            if feed.strip()
        ] if self.config.rss_feeds else []
        
        logger.info(f"NewsClient initialized with {len(self.rss_feeds)} RSS feeds")
    
    def is_available(self) -> bool:
        """Check if news client is available"""
        return self.available and (
            len(self.rss_feeds) > 0 or 
            self.newsapi_client is not None
        )
    
    def extract_symbols(self, text: str) -> List[str]:
        """
        Extract stock symbols from text
        
        Args:
            text: Text to analyze
            
        Returns:
            List of stock symbols found
        """
        # Pattern for $SYMBOL or SYMBOL mentions with context
        pattern = r'\$([A-Z]{1,5})\b|(?<![A-Z])([A-Z]{1,5})(?=\s+(?:stock|shares|equity|shares|IPO|earnings|revenue))'
        
        symbols = []
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        for match in matches:
            symbol = match[0] or match[1]
            if symbol and symbol not in symbols:
                # Filter out common false positives
                if symbol not in ["I", "A", "IT", "AM", "PM", "DD", "TL", "DR", "CEO", "CFO"]:
                    symbols.append(symbol.upper())
        
        return symbols
    
    def fetch_from_rss(self, symbol: Optional[str] = None, hours: int = 24) -> List[NewsArticle]:
        """
        Fetch articles from RSS feeds
        
        Args:
            symbol: Stock symbol to filter (None for all articles)
            hours: Hours of articles to retrieve
            
        Returns:
            List of NewsArticle objects
        """
        if not self.rss_feeds:
            return []
        
        articles = []
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        for feed_url in self.rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    try:
                        # Parse published date
                        published_time = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now()
                        
                        # Skip old articles
                        if published_time < cutoff_time:
                            continue
                        
                        # Get article content
                        title = entry.get('title', '')
                        summary = entry.get('summary', '')
                        link = entry.get('link', '')
                        
                        # Try to fetch full article text
                        article_text = summary
                        if self.config.fetch_full_text and Article:
                            try:
                                article = Article(link)
                                article.download()
                                article.parse()
                                article_text = article.text or summary
                            except Exception as e:
                                logger.debug(f"Failed to fetch full text for {link}: {e}")
                        
                        # Combine title and text
                        full_text = f"{title} {article_text}"
                        
                        # Extract symbols
                        symbols_found = self.extract_symbols(full_text)
                        
                        # Filter by symbol if specified
                        if symbol and symbol.upper() not in [s.upper() for s in symbols_found]:
                            continue
                        
                        article = NewsArticle(
                            article_id=entry.get('id', link),
                            title=title,
                            text=full_text,
                            source=entry.get('source', {}).get('title', 'RSS') if hasattr(entry, 'source') else 'RSS',
                            url=link,
                            published_at=published_time,
                            author=entry.get('author', 'unknown'),
                            symbols_mentioned=symbols_found
                        )
                        
                        articles.append(article)
                        
                    except Exception as e:
                        logger.warning(f"Error parsing RSS entry: {e}")
                        continue
                
            except Exception as e:
                logger.warning(f"Error fetching RSS feed {feed_url}: {e}")
                continue
        
        logger.info(f"Fetched {len(articles)} articles from RSS feeds")
        return articles
    
    def fetch_from_newsapi(self, symbol: str, hours: int = 24) -> List[NewsArticle]:
        """
        Fetch articles from NewsAPI
        
        Args:
            symbol: Stock symbol to search for
            hours: Hours of articles to retrieve
            
        Returns:
            List of NewsArticle objects
        """
        if not self.newsapi_client:
            return []
        
        articles = []
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        try:
            # Search for articles mentioning the symbol
            query = f"{symbol} OR ${symbol} OR {symbol} stock"
            
            # Get articles
            response = self.newsapi_client.get_everything(
                q=query,
                language='en',
                sort_by='publishedAt',
                page_size=min(self.config.max_results, 100)  # NewsAPI limit
            )
            
            if response.get('status') == 'ok':
                for article_data in response.get('articles', []):
                    try:
                        # Parse published date
                        published_str = article_data.get('publishedAt', '')
                        if published_str:
                            published_time = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                            if published_time.tzinfo:
                                published_time = published_time.replace(tzinfo=None)
                        else:
                            published_time = datetime.now()
                        
                        # Skip old articles
                        if published_time < cutoff_time:
                            continue
                        
                        title = article_data.get('title', '')
                        description = article_data.get('description', '')
                        content = article_data.get('content', '')
                        url = article_data.get('url', '')
                        source = article_data.get('source', {}).get('name', 'NewsAPI')
                        
                        # Combine text
                        full_text = f"{title} {description} {content}"
                        
                        # Extract symbols
                        symbols_found = self.extract_symbols(full_text)
                        
                        article = NewsArticle(
                            article_id=url or article_data.get('urlToImage', ''),
                            title=title,
                            text=full_text,
                            source=source,
                            url=url,
                            published_at=published_time,
                            author=article_data.get('author'),
                            symbols_mentioned=symbols_found
                        )
                        
                        articles.append(article)
                        
                    except Exception as e:
                        logger.warning(f"Error parsing NewsAPI article: {e}")
                        continue
            
        except Exception as e:
            logger.error(f"Error fetching from NewsAPI: {e}")
        
        logger.info(f"Fetched {len(articles)} articles from NewsAPI")
        return articles


class NewsSentimentProvider:
    """
    Financial news sentiment provider for stock symbols
    
    Handles article collection, sentiment analysis, and aggregation.
    """
    
    def __init__(self, persist_to_db: bool = True):
        """
        Initialize news sentiment provider
        
        Args:
            persist_to_db: Whether to persist data to database (default: True)
        """
        self.client = NewsClient()
        self.analyzer = SentimentAnalyzer()
        self.cache = get_cache_manager()
        self.cache_ttl = settings.news.cache_ttl
        self.rate_limiter = get_rate_limiter("news")
        self.usage_monitor = get_usage_monitor()
        self.persist_to_db = persist_to_db
        self.repository = SentimentRepository() if persist_to_db else None
        
        logger.info(f"NewsSentimentProvider initialized (persist_to_db={persist_to_db})")
    
    def is_available(self) -> bool:
        """Check if news provider is available"""
        return self.client.is_available()
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache using Redis-backed cache manager"""
        cache_key = f"news:{key}"
        return self.cache.get(cache_key)
    
    def _set_cache(self, key: str, data: Any):
        """Store data in cache using Redis-backed cache manager"""
        cache_key = f"news:{key}"
        self.cache.set(cache_key, data, ttl=self.cache_ttl)
    
    def get_sentiment(self, symbol: str, hours: int = 24) -> Optional[SymbolSentiment]:
        """
        Get sentiment for a symbol from financial news
        
        Args:
            symbol: Stock symbol
            hours: Hours of data to analyze (default: 24)
            
        Returns:
            SymbolSentiment object or None
        """
        if not self.is_available():
            logger.warning("News client not available")
            return None
        
        # Check rate limit (100 requests per minute)
        is_allowed, rate_status = self.rate_limiter.check_rate_limit(limit=100, window_seconds=60)
        if not is_allowed:
            logger.warning(f"News rate limit exceeded for {symbol}, waiting...")
            rate_status = self.rate_limiter.wait_if_needed(limit=100, window_seconds=60)
            if rate_status.is_limited:
                logger.error(f"News rate limit still exceeded after wait")
                self.usage_monitor.record_request("news", success=False)
                return None
        
        # Check cache
        cache_key = f"sentiment_{symbol}_{hours}"
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"Returning cached sentiment for {symbol}")
            self.usage_monitor.record_request("news", success=True, cached=True)
            return cached
        
        # Fetch articles from all sources
        articles = []
        
        # Fetch from RSS feeds
        rss_articles = self.client.fetch_from_rss(symbol=symbol, hours=hours)
        articles.extend(rss_articles)
        
        # Fetch from NewsAPI
        if self.client.newsapi_client:
            newsapi_articles = self.client.fetch_from_newsapi(symbol=symbol, hours=hours)
            articles.extend(newsapi_articles)
        
        # Remove duplicates (by URL)
        seen_urls = set()
        unique_articles = []
        for article in articles:
            if article.url and article.url not in seen_urls:
                seen_urls.add(article.url)
                unique_articles.append(article)
        
        if not unique_articles:
            logger.info(f"No news articles found for {symbol}")
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
        
        # Analyze sentiment for each article
        article_sentiments = []
        
        for article in unique_articles:
            # Convert NewsArticle to Tweet-like object for analyzer
            tweet_like = Tweet(
                tweet_id=article.tweet_id,
                text=f"{article.title} {article.text}",
                author_id=article.author,
                author_username=article.author,
                created_at=article.published_at,
                like_count=0,
                retweet_count=0,
                reply_count=0,
                quote_count=0,
                is_retweet=False,
                is_quote=False,
                is_reply=False,
                language="en",
                symbols_mentioned=article.symbols_mentioned
            )
            
            # Save article to database if persistence enabled
            tweet_model = None
            if self.persist_to_db and self.repository:
                try:
                    tweet_model = self.repository.save_tweet(tweet_like)
                except Exception as e:
                    logger.warning(f"Failed to save news article to database: {e}")
            
            # News articles get base engagement weight (1.0)
            # Financial news is generally more credible than social media
            engagement_weight = 1.2  # Slightly higher weight for news
            
            sentiment_result = self.analyzer.analyze_tweet(
                tweet=tweet_like,
                symbol=symbol,
                engagement_weight=engagement_weight,
                influencer_weight=1.0
            )
            
            # Save sentiment to database if persistence enabled
            if self.persist_to_db and self.repository and tweet_model:
                try:
                    self.repository.save_tweet_sentiment(sentiment_result, tweet_model)
                except Exception as e:
                    logger.warning(f"Failed to save news sentiment to database: {e}")
            
            article_sentiments.append(sentiment_result)
        
        # Aggregate sentiment
        if not article_sentiments:
            return None
        
        mention_count = len(article_sentiments)
        
        # Calculate average sentiment
        average_sentiment = sum(as_.sentiment_score for as_ in article_sentiments) / mention_count
        
        # Calculate weighted average
        total_weighted = sum(as_.weighted_score for as_ in article_sentiments)
        total_weight = sum(as_.engagement_score for as_ in article_sentiments)
        
        if total_weight > 0:
            weighted_sentiment = total_weighted / total_weight
        else:
            weighted_sentiment = average_sentiment
        
        # Determine sentiment level
        sentiment_level = self.analyzer._score_to_level(weighted_sentiment)
        
        # Calculate confidence (based on sample size and polarity)
        avg_confidence = sum(as_.confidence for as_ in article_sentiments) / mention_count
        volume_confidence = min(mention_count / 20, 1.0)  # Max confidence at 20+ articles
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
            engagement_score=sum(as_.engagement_score for as_ in article_sentiments) / mention_count,
            sentiment_level=sentiment_level,
            confidence=confidence,
            volume_trend=volume_trend,
            tweets=article_sentiments[:10]  # Store top 10 for reference
        )
        
        # Save symbol sentiment to database if persistence enabled
        if self.persist_to_db and self.repository:
            try:
                self.repository.save_symbol_sentiment(sentiment)
            except Exception as e:
                logger.warning(f"Failed to save symbol sentiment to database: {e}")
        
        # Cache result
        self._set_cache(cache_key, sentiment)
        
        # Record successful request
        self.usage_monitor.record_request("news", success=True, cached=False)
        
        logger.info(
            f"News sentiment for {symbol}: {weighted_sentiment:.3f} "
            f"({sentiment_level.value}) - {mention_count} articles"
        )
        
        return sentiment
