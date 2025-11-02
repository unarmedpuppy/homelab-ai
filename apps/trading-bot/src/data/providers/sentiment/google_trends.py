"""
Google Trends Sentiment Provider
=================================

Integration with Google Trends API (via pytrends) for tracking search volume
and interest trends for stock symbols. Search volume can be a leading indicator
of market sentiment and retail interest.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time

try:
    from pytrends.request import TrendReq
    pytrends_available = True
except ImportError:
    TrendReq = None
    pytrends_available = False

from ....config.settings import settings
from .models import SymbolSentiment, SentimentLevel
from .repository import SentimentRepository
from ....utils.cache import get_cache_manager

logger = logging.getLogger(__name__)


class GoogleTrendsClient:
    """
    Google Trends API client using pytrends
    
    Note: pytrends uses unofficial API and may have rate limits.
    Be respectful of rate limits.
    """
    
    def __init__(self):
        """Initialize Google Trends client"""
        if not pytrends_available:
            logger.warning(
                "pytrends is not installed. Google Trends integration disabled. "
                "Install with: pip install pytrends"
            )
            self.pytrends = None
            return
        
        self.config = settings.google_trends
        
        try:
            # Initialize pytrends (no auth required, but may need rate limiting)
            self.pytrends = TrendReq(
                hl='en-US',
                tz=360,  # UTC offset
                timeout=(10, 14),  # Connection and read timeouts
                retries=2,
                backoff_factor=0.1,
                requests_args={}
            )
            logger.info("Google Trends client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Google Trends client: {e}")
            self.pytrends = None
    
    def is_available(self) -> bool:
        """Check if Google Trends client is available"""
        return self.pytrends is not None
    
    def get_interest_over_time(
        self,
        keyword: str,
        timeframe: str = 'today 12-m',
        geo: str = 'US'
    ) -> Optional[Dict[str, Any]]:
        """
        Get interest over time for a keyword
        
        Args:
            keyword: Search term (e.g., "AAPL stock" or "AAPL")
            timeframe: Time range (e.g., 'today 12-m', 'today 3-m', 'today 1-m')
            geo: Geographic location (default: 'US' for United States)
        
        Returns:
            Dictionary with timestamps and interest values, or None on error
        """
        if not self.is_available():
            return None
        
        try:
            # Build payload
            self.pytrends.build_payload(
                [keyword],
                cat=0,  # All categories
                timeframe=timeframe,
                geo=geo,
                gprop=''  # Web search (vs news, images, youtube, etc.)
            )
            
            # Get interest over time
            interest_data = self.pytrends.interest_over_time()
            
            if interest_data.empty or keyword not in interest_data.columns:
                logger.debug(f"No interest data available for '{keyword}'")
                return None
            
            # Convert to dictionary format
            result = {
                'keyword': keyword,
                'timeframe': timeframe,
                'geo': geo,
                'data': []
            }
            
            for timestamp, row in interest_data.iterrows():
                value = int(row[keyword])
                result['data'].append({
                    'timestamp': timestamp.to_pydatetime() if hasattr(timestamp, 'to_pydatetime') else timestamp,
                    'interest': value  # 0-100 scale
                })
            
            logger.debug(f"Retrieved {len(result['data'])} data points for '{keyword}'")
            return result
        
        except Exception as e:
            logger.warning(f"Error getting interest over time for '{keyword}': {e}")
            return None
    
    def get_related_queries(
        self,
        keyword: str,
        geo: str = 'US'
    ) -> Optional[Dict[str, List[Dict[str, Any]]]]:
        """
        Get related queries (rising and top)
        
        Args:
            keyword: Search term
            geo: Geographic location
        
        Returns:
            Dictionary with 'rising' and 'top' related queries
        """
        if not self.is_available():
            return None
        
        try:
            self.pytrends.build_payload([keyword], geo=geo)
            related = self.pytrends.related_queries()
            
            if not related or keyword not in related:
                return None
            
            keyword_related = related[keyword]
            
            result = {
                'rising': [],
                'top': []
            }
            
            if keyword_related.get('rising') is not None:
                for _, row in keyword_related['rising'].iterrows():
                    result['rising'].append({
                        'query': row['query'],
                        'value': int(row['value']) if 'value' in row else 0
                    })
            
            if keyword_related.get('top') is not None:
                for _, row in keyword_related['top'].iterrows():
                    result['top'].append({
                        'query': row['query'],
                        'value': int(row['value']) if 'value' in row else 0
                    })
            
            return result
        
        except Exception as e:
            logger.debug(f"Error getting related queries for '{keyword}': {e}")
            return None
    
    def get_interest_by_region(
        self,
        keyword: str,
        geo: str = 'US',
        resolution: str = 'COUNTRY'
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get interest by region
        
        Args:
            keyword: Search term
            geo: Geographic location to search within
            resolution: 'COUNTRY', 'REGION', 'CITY', or 'DMA' (Designated Market Area)
        
        Returns:
            List of regions with interest values
        """
        if not self.is_available():
            return None
        
        try:
            self.pytrends.build_payload([keyword], geo=geo)
            regional = self.pytrends.interest_by_region(
                resolution=resolution,
                inc_low_vol=True,
                inc_geo_code=False
            )
            
            if regional.empty or keyword not in regional.columns:
                return None
            
            result = []
            for region, row in regional.iterrows():
                result.append({
                    'region': str(region),
                    'interest': int(row[keyword])
                })
            
            return result
        
        except Exception as e:
            logger.debug(f"Error getting interest by region for '{keyword}': {e}")
            return None
    
    def extract_symbol(self, keyword: str) -> Optional[str]:
        """
        Extract stock symbol from search keyword
        Common patterns: "AAPL stock", "$AAPL", "AAPL", "Apple stock"
        """
        import re
        
        # Pattern for $SYMBOL or SYMBOL
        symbol_pattern = r'\$?([A-Z]{1,5})\b'
        matches = re.findall(symbol_pattern, keyword.upper())
        
        if matches:
            # Return first match that looks like a stock symbol (1-5 letters)
            for match in matches:
                if 1 <= len(match) <= 5:
                    return match
        
        return None


class GoogleTrendsSentimentProvider:
    """
    Sentiment provider for Google Trends data
    
    Converts search volume trends into sentiment scores.
    Rising search volume can indicate increasing interest (positive for retail sentiment),
    while declining volume may indicate waning interest.
    """
    
    def __init__(self, persist_to_db: bool = True):
        """
        Initialize Google Trends sentiment provider
        
        Args:
            persist_to_db: Whether to persist data to database
        """
        self.client = GoogleTrendsClient()
        self.config = settings.google_trends
        self.persist_to_db = persist_to_db
        self.repository = SentimentRepository() if persist_to_db else None
        
        # Use Redis-backed cache manager (standardized)
        self.cache = get_cache_manager()
        self.cache_ttl = self.config.cache_ttl
        
        # Rate limiting
        self.last_request_time = 0.0
        self.min_request_interval = 1.0  # Minimum seconds between requests (pytrends is rate-limited)
        
        logger.info("GoogleTrendsSentimentProvider initialized")
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        return self.client.is_available()
    
    def _get_cache_key(self, symbol: str, hours: int) -> str:
        """Generate cache key"""
        return f"google_trends:{symbol}_{hours}"
    
    def _get_from_cache(self, key: str) -> Optional[SymbolSentiment]:
        """Get data from cache using Redis-backed cache manager"""
        return self.cache.get(key)
    
    def _set_cache(self, key: str, data: SymbolSentiment):
        """Store data in cache using Redis-backed cache manager"""
        self.cache.set(key, data, ttl=self.cache_ttl)
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _calculate_sentiment_from_trends(
        self,
        interest_data: List[Dict[str, Any]],
        current_timestamp: datetime
    ) -> float:
        """
        Calculate sentiment score from interest trends
        
        Logic:
        - Rising interest (trending up) = positive sentiment
        - Declining interest (trending down) = negative sentiment
        - High absolute interest = higher confidence
        
        Returns:
            Sentiment score (-1.0 to 1.0)
        """
        if not interest_data or len(interest_data) < 2:
            return 0.0
        
        # Get recent data points (last 30 days worth, or available data)
        recent_cutoff = current_timestamp - timedelta(days=30)
        recent_data = [
            d for d in interest_data
            if isinstance(d['timestamp'], datetime) and d['timestamp'] >= recent_cutoff
        ]
        
        if len(recent_data) < 2:
            recent_data = interest_data[-7:] if len(interest_data) >= 7 else interest_data
        
        if len(recent_data) < 2:
            return 0.0
        
        # Calculate trend (linear regression slope)
        interests = [d['interest'] for d in recent_data]
        
        # Normalize interest values (0-100 scale -> 0-1 scale)
        normalized = [i / 100.0 for i in interests]
        
        # Calculate simple trend (difference between first and last)
        first_half_avg = sum(normalized[:len(normalized)//2]) / (len(normalized)//2)
        second_half_avg = sum(normalized[len(normalized)//2:]) / (len(normalized) - len(normalized)//2)
        
        trend = second_half_avg - first_half_avg
        
        # Current interest level (higher = more attention)
        current_interest = normalized[-1] if normalized else 0.5
        
        # Combine trend and absolute level
        # Trend contributes -1 to +1, current level contributes 0 to 0.5
        sentiment = trend * 0.7 + (current_interest - 0.5) * 0.3
        
        # Clamp to [-1, 1]
        return max(-1.0, min(1.0, sentiment))
    
    def get_sentiment(
        self,
        symbol: str,
        hours: int = 24
    ) -> Optional[SymbolSentiment]:
        """
        Get sentiment for a symbol based on Google Trends data
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            hours: Hours of historical data to analyze (for cache key, not used for Trends API)
        
        Returns:
            SymbolSentiment object or None if unavailable
        """
        symbol = symbol.upper()
        
        # Track provider availability
        is_available = self.is_available()
        try:
            from ....utils.metrics_providers_helpers import track_provider_availability
            track_provider_availability("google_trends", is_available)
        except (ImportError, Exception) as e:
            logger.debug(f"Could not record availability metric: {e}")
        
        # Track API call timing
        api_start_time = time.time()
        
        # Check cache
        cache_key = self._get_cache_key(symbol, hours)
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"Returning cached Google Trends sentiment for {symbol}")
            # Track data freshness
            try:
                from ....utils.metrics_providers_helpers import track_cache_freshness
                track_cache_freshness("google_trends", "get_sentiment", cached)
            except (ImportError, Exception) as e:
                logger.debug(f"Could not record data freshness metric: {e}")
            return cached
        
        if not is_available:
            logger.warning("Google Trends provider not available")
            return None
        
        try:
            # Rate limit
            self._rate_limit()
            
            # Build search keywords (try multiple variations)
            keywords = [
                f"{symbol} stock",
                f"${symbol}",
                symbol
            ]
            
            interest_data = None
            keyword_used = None
            
            # Try keywords in order of preference
            for keyword in keywords:
                interest_result = self.client.get_interest_over_time(
                    keyword=keyword,
                    timeframe='today 3-m',  # 3 months of data
                    geo=self.config.geo
                )
                
                if interest_result and interest_result.get('data'):
                    interest_data = interest_result['data']
                    keyword_used = keyword
                    break
            
            if not interest_data:
                logger.debug(f"No interest data available for {symbol}")
                return None
            
            # Calculate sentiment from trends
            sentiment_score = self._calculate_sentiment_from_trends(
                interest_data,
                datetime.now()
            )
            
            # Calculate confidence based on data quality and volume
            avg_interest = sum(d['interest'] for d in interest_data) / len(interest_data) if interest_data else 0
            confidence = min(0.7, avg_interest / 100.0)  # Max 0.7 confidence (search volume is indirect)
            
            # Determine sentiment level
            if sentiment_score >= 0.6:
                level = SentimentLevel.VERY_BULLISH
            elif sentiment_score >= 0.2:
                level = SentimentLevel.BULLISH
            elif sentiment_score <= -0.6:
                level = SentimentLevel.VERY_BEARISH
            elif sentiment_score <= -0.2:
                level = SentimentLevel.BEARISH
            else:
                level = SentimentLevel.NEUTRAL
            
            # Create sentiment object
            sentiment = SymbolSentiment(
                symbol=symbol,
                timestamp=datetime.now(),
                mention_count=len(interest_data),  # Use data point count as "mentions"
                average_sentiment=sentiment_score,
                weighted_sentiment=sentiment_score,  # No weighting for trends
                influencer_sentiment=None,  # Not applicable
                engagement_score=avg_interest / 100.0,  # Interest level as engagement
                sentiment_level=level,
                confidence=confidence,
                volume_trend="up" if sentiment_score > 0.1 else "down" if sentiment_score < -0.1 else "stable"
            )
            
            # Record API response time
            api_response_time = time.time() - api_start_time
            
            # Cache result
            self._set_cache(cache_key, sentiment)
            
            # Track request via usage monitor (if available)
            try:
                from ....utils.monitoring import get_usage_monitor
                usage_monitor = get_usage_monitor()
                usage_monitor.record_request(
                    "google_trends",
                    success=True,
                    cached=False,
                    response_time=api_response_time
                )
            except (ImportError, Exception) as e:
                logger.debug(f"Could not record usage metrics: {e}")
            
            # Persist to database if enabled
            if self.persist_to_db and self.repository:
                try:
                    self.repository.save_symbol_sentiment(sentiment)
                except Exception as e:
                    logger.warning(f"Failed to save Google Trends sentiment to database: {e}")
                
                logger.info(
                    f"Google Trends sentiment for {symbol}: {sentiment_score:.3f} "
                    f"(level: {level.value}, confidence: {confidence:.3f})"
                )
            
            return sentiment
            
        except Exception as e:
            logger.error(f"Error getting Google Trends sentiment for {symbol}: {e}", exc_info=True)
            return None
    
    def get_related_searches(
        self,
        symbol: str
    ) -> Optional[Dict[str, List[Dict[str, Any]]]]:
        """
        Get related searches for a symbol
        
        Returns:
            Dictionary with 'rising' and 'top' related queries
        """
        if not self.is_available():
            return None
        
        try:
            self._rate_limit()
            keyword = f"{symbol} stock"
            return self.client.get_related_queries(keyword, geo=self.config.geo)
        except Exception as e:
            logger.error(f"Error getting related searches for {symbol}: {e}")
            return None
