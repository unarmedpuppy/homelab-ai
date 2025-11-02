"""
Google Trends Provider
======================

Integration with Google Trends API (via pytrends) to track search interest
and trending topics for stock symbols.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time

try:
    from pytrends.request import TrendReq
except ImportError:
    TrendReq = None

from ...config.settings import settings
from ...utils.cache import get_cache_manager
from ..sentiment.models import SymbolSentiment, SentimentLevel

logger = logging.getLogger(__name__)


class GoogleTrendsProvider:
    """
    Google Trends provider for tracking search interest
    
    Uses pytrends library to query Google Trends API.
    Note: Google Trends has rate limits and may require delays between requests.
    """
    
    def __init__(self):
        """Initialize Google Trends provider"""
        if TrendReq is None:
            raise ImportError(
                "pytrends is required for Google Trends integration. "
                "Install with: pip install pytrends"
            )
        
        self.config = settings.google_trends
        self.cache = get_cache_manager()
        self.pytrends = TrendReq(
            hl='en-US',
            tz=360,  # UTC offset
            retries=2,
            backoff_factor=0.1
        )
        
        self.last_request_time = 0.0
        self.request_delay = self.config.request_delay
        
        logger.info("GoogleTrendsProvider initialized")
    
    def _rate_limit(self):
        """Enforce rate limiting by adding delay between requests"""
        if not self.config.rate_limit_enabled:
            return
        
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
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
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return func()
            except (Exception, AttributeError) as e:
                # Google Trends API errors are often transient
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(
                        f"Google Trends request failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {wait_time:.2f}s: {e}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Google Trends request failed after {max_retries} attempts: {e}")
                    raise
        
        if last_exception:
            raise last_exception
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        return TrendReq is not None and self.config.enabled
    
    def get_search_interest(
        self,
        symbol: str,
        timeframe: str = 'today 1-m',
        geo: str = 'US'
    ) -> Optional[Dict[str, Any]]:
        """
        Get search interest data for a symbol
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'SPY')
            timeframe: Timeframe for trends (e.g., 'today 1-m', 'today 3-m', 'today 12-m')
            geo: Geographic location (default: 'US')
            
        Returns:
            Dictionary with interest data or None
        """
        # Input validation
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        symbol = symbol.strip().upper()
        if not symbol:
            raise ValueError("Symbol cannot be empty after stripping")
        
        if not self.is_available():
            return None
        
        try:
            # Rate limit check
            self._rate_limit()
            
            # Google Trends requires a keyword
            # Use stock symbol + "stock" for better results
            keyword = f"{symbol} stock"
            
            def build_and_get_data():
                # Build payload
                self.pytrends.build_payload(
                    [keyword],
                    cat=0,  # All categories
                    timeframe=timeframe,
                    geo=geo,
                    gprop=''  # Web search (default)
                )
                
                # Get interest over time
                return self.pytrends.interest_over_time()
            
            # Retry on transient failures
            interest_df = self._retry_request(build_and_get_data, max_retries=2, backoff_factor=2.0)
            
            if interest_df.empty:
                logger.debug(f"No Google Trends data for {symbol}")
                return None
            
            # Get related queries
            related_queries = self.pytrends.related_queries()
            
            # Calculate metrics
            recent_interest = interest_df[keyword].tail(7).mean() if len(interest_df) >= 7 else interest_df[keyword].mean()
            max_interest = interest_df[keyword].max()
            current_interest = interest_df[keyword].iloc[-1] if len(interest_df) > 0 else 0
            
            # Calculate trend (comparing last 7 days to previous 7 days)
            if len(interest_df) >= 14:
                recent_avg = interest_df[keyword].tail(7).mean()
                previous_avg = interest_df[keyword].tail(14).head(7).mean()
                trend_change = ((recent_avg - previous_avg) / previous_avg * 100) if previous_avg > 0 else 0.0
            else:
                trend_change = 0.0
            
            # Normalize to 0-100 scale (Google Trends already provides this)
            interest_score = float(current_interest)  # Already 0-100
            trend_score = min(100, max(-100, trend_change))
            
            # Get related queries
            top_rising = []
            top_queries = []
            
            if related_queries and keyword in related_queries:
                rising = related_queries[keyword].get('rising')
                top = related_queries[keyword].get('top')
                
                if rising is not None:
                    top_rising = rising.head(10).to_dict('records') if not rising.empty else []
                if top is not None:
                    top_queries = top.head(10).to_dict('records') if not top.empty else []
            
            return {
                'symbol': symbol.upper(),
                'keyword': keyword,
                'interest_score': interest_score,  # 0-100
                'max_interest': float(max_interest),
                'recent_avg_interest': float(recent_interest),
                'trend_change': trend_change,  # Percentage change
                'trend_score': trend_score,  # -100 to 100
                'timeframe': timeframe,
                'geo': geo,
                'top_rising_queries': top_rising,
                'top_queries': top_queries,
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache result
            self.cache.set(cache_key, result, ttl=self.config.cache_ttl)
            
            return result
            
        except ValueError as e:
            logger.error(f"Invalid input for Google Trends query: {symbol}, error: {e}")
            raise
        except (KeyError, AttributeError, IndexError) as e:
            logger.warning(f"Data structure error getting Google Trends for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting Google Trends data for {symbol}: {e}", exc_info=True)
            return None
    
    def get_interest_sentiment(self, symbol: str, hours: int = 24) -> Optional[SymbolSentiment]:
        """
        Convert Google Trends interest data to sentiment-like score
        
        Args:
            symbol: Stock symbol
            hours: Hours of historical data (converted to appropriate timeframe)
            
        Returns:
            SymbolSentiment object with interest-based scoring
        """
        # Convert hours to Google Trends timeframe
        if hours <= 24:
            timeframe = 'now 1-H'  # Last hour
        elif hours <= 168:  # 7 days
            timeframe = 'today 1-w'
        elif hours <= 720:  # 30 days
            timeframe = 'today 1-m'
        else:
            timeframe = 'today 3-m'
        
        interest_data = self.get_search_interest(symbol, timeframe=timeframe)
        
        if not interest_data:
            return None
        
        # Convert interest to sentiment-like score (-1 to 1)
        # High interest + rising trend = positive sentiment
        # Low interest + falling trend = negative sentiment
        
        interest_normalized = interest_data['interest_score'] / 100.0  # 0-1
        trend_normalized = interest_data['trend_score'] / 100.0  # -1 to 1
        
        # Combine interest level and trend
        # Base sentiment from interest level (scaled to -0.5 to 0.5)
        base_sentiment = (interest_normalized - 0.5) * 1.0
        
        # Trend adds momentum (up to ±0.5)
        trend_contribution = trend_normalized * 0.5
        
        # Combined sentiment (-1 to 1)
        sentiment_score = base_sentiment + trend_contribution
        sentiment_score = max(-1.0, min(1.0, sentiment_score))
        
        # Calculate confidence based on data quality
        confidence = min(1.0, interest_normalized * 0.8 + 0.2)  # Higher interest = higher confidence
        
        # Determine sentiment level
        if sentiment_score >= 0.6:
            sentiment_level = SentimentLevel.VERY_BULLISH
        elif sentiment_score >= 0.2:
            sentiment_level = SentimentLevel.BULLISH
        elif sentiment_score >= -0.2:
            sentiment_level = SentimentLevel.NEUTRAL
        elif sentiment_score >= -0.6:
            sentiment_level = SentimentLevel.BEARISH
        else:
            sentiment_level = SentimentLevel.VERY_BEARISH
        
        return SymbolSentiment(
            symbol=symbol.upper(),
            timestamp=datetime.now(),
            mention_count=int(interest_data['interest_score']),  # Use interest as "mention count"
            average_sentiment=sentiment_score,
            weighted_sentiment=sentiment_score,
            influencer_sentiment=sentiment_score,
            engagement_score=interest_normalized,
            sentiment_level=sentiment_level,
            confidence=confidence,
            volume_trend="up" if trend_normalized > 0.1 else "down" if trend_normalized < -0.1 else "stable"
        )
    
    def get_trending_symbols(self, min_interest: int = 50) -> List[Dict]:
        """
        Get symbols with high search interest (trending)
        
        Note: Google Trends doesn't have a direct "trending stocks" API,
        so this would need to query multiple symbols or use related queries.
        
        Args:
            min_interest: Minimum interest score (0-100) to be considered trending
            
        Returns:
            List of trending symbols with interest data
        """
        # This is a placeholder - would need to maintain a list of symbols to check
        # or use related queries from a popular symbol query
        logger.warning("get_trending_symbols not fully implemented - requires symbol list")
        return []

