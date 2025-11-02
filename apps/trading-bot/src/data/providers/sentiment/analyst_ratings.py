"""
Analyst Ratings Sentiment Provider
===================================

Integration with yfinance for analyst ratings and price targets.
Tracks analyst recommendations, upgrades/downgrades, and price target changes.
"""

import logging
import re
import signal
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from functools import wraps
import threading

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type,
        RetryError
    )
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False
    retry = lambda **kwargs: lambda f: f  # No-op decorator
    stop_after_attempt = None
    wait_exponential = None
    retry_if_exception_type = None
    RetryError = Exception

from ....config.settings import settings
from ....utils.cache import get_cache_manager
from ....utils.rate_limiter import get_rate_limiter
from ....utils.monitoring import get_usage_monitor
from .models import SymbolSentiment, SentimentLevel
from .repository import SentimentRepository

logger = logging.getLogger(__name__)


@dataclass
class AnalystRating:
    """
    Analyst rating data for a stock symbol
    
    Attributes:
        symbol: Stock symbol (e.g., "AAPL", "MSFT")
        rating: Textual rating ("Strong Buy", "Buy", "Hold", "Sell", "Strong Sell")
        rating_numeric: Numeric rating on scale of 1.0 to 5.0
            - 1.0 = Strong Buy
            - 2.0 = Buy
            - 3.0 = Hold
            - 4.0 = Sell
            - 5.0 = Strong Sell
        price_target: Mean/consensus price target (dollars)
        price_target_high: Highest price target among analysts (dollars)
        price_target_low: Lowest price target among analysts (dollars)
        price_target_mean: Average/mean price target (dollars, typically same as price_target)
        number_of_analysts: Number of analysts providing ratings
        current_price: Current stock price (dollars)
        price_target_upside: Percentage upside/downside to price target
            - Positive value = upside (target > current)
            - Negative value = downside (target < current)
        timestamp: Timestamp when data was fetched
    """
    symbol: str
    rating: str
    rating_numeric: float
    price_target: Optional[float] = None
    price_target_high: Optional[float] = None
    price_target_low: Optional[float] = None
    price_target_mean: Optional[float] = None
    number_of_analysts: int = 0
    current_price: Optional[float] = None
    price_target_upside: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)


class AnalystRatingsTimeoutError(Exception):
    """Custom timeout exception for analyst ratings"""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout"""
    raise AnalystRatingsTimeoutError("yfinance API call timed out")


class AnalystRatingsClient:
    """
    Client for fetching analyst ratings from yfinance
    
    yfinance provides analyst recommendations and price targets via ticker.info
    """
    
    def __init__(self):
        """Initialize analyst ratings client"""
        if yf is None:
            raise ImportError(
                "yfinance is required for analyst ratings integration. "
                "Install with: pip install yfinance"
            )
        
        self.config = settings.analyst_ratings
        logger.info("AnalystRatingsClient initialized")
    
    def is_available(self) -> bool:
        """Check if client is available"""
        if not self.config.enabled:
            return False
        return True
    
    def _validate_symbol(self, symbol: str) -> bool:
        """
        Validate symbol format
        
        Args:
            symbol: Stock symbol to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not symbol or not isinstance(symbol, str):
            return False
        
        # Convert to uppercase and strip whitespace
        symbol_upper = symbol.strip().upper()
        
        # Check length (typical symbols are 1-5 chars, but some ETFs can be longer)
        if len(symbol_upper) < 1 or len(symbol_upper) > 10:
            return False
        
        # Check format: alphanumeric only (no special characters)
        if not re.match(r'^[A-Z0-9]+$', symbol_upper):
            return False
        
        return True
    
    def _call_with_timeout(self, func, *args, **kwargs):
        """
        Execute function with timeout using signal-based approach (Unix only)
        Falls back to thread-based timeout on Windows
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            TimeoutError if function exceeds timeout
        """
        timeout = self.config.timeout_seconds
        
        # For Unix systems, use signal-based timeout
        if hasattr(signal, 'SIGALRM'):
            def timeout_wrapper():
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(timeout)
                try:
                    result = func(*args, **kwargs)
                    signal.alarm(0)  # Cancel alarm
                    return result
                except AnalystRatingsTimeoutError:
                    raise
                finally:
                    signal.signal(signal.SIGALRM, old_handler)
                    signal.alarm(0)
            
            return timeout_wrapper()
        else:
            # Windows fallback: use threading (less precise but works)
            result_container = []
            exception_container = []
            
            def target():
                try:
                    result_container.append(func(*args, **kwargs))
                except Exception as e:
                    exception_container.append(e)
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout=timeout)
            
            if thread.is_alive():
                # Thread is still running, timeout occurred
                raise AnalystRatingsTimeoutError(f"yfinance API call exceeded {timeout}s timeout")
            
            if exception_container:
                raise exception_container[0]
            
            if result_container:
                return result_container[0]
            
            raise RuntimeError("Function completed but returned no result")
    
    @staticmethod
    def _is_retryable_error(exception: Exception) -> bool:
        """
        Determine if an exception is retryable
        
        Args:
            exception: Exception to check
            
        Returns:
            True if exception should trigger retry
        """
        # Network-related errors (retryable)
        retryable_types = (
            ConnectionError,
            AnalystRatingsTimeoutError,
            TimeoutError,  # Built-in timeout error
            OSError,  # Network errors often raise OSError
        )
        
        # Check exception type
        if isinstance(exception, retryable_types):
            return True
        
        # Check exception message for common retryable errors
        error_msg = str(exception).lower()
        retryable_patterns = [
            'timeout',
            'connection',
            'network',
            'temporary',
            'unavailable',
            '503',
            '502',
            '504',
            '500'
        ]
        
        return any(pattern in error_msg for pattern in retryable_patterns)
    
    def _rating_to_numeric(self, rating: str) -> float:
        """
        Convert rating string to numeric value
        
        Args:
            rating: Rating string (e.g., "Strong Buy", "Buy", etc.)
            
        Returns:
            Numeric rating (1.0 = Strong Buy, 5.0 = Strong Sell)
        """
        rating_lower = rating.lower() if rating else ""
        
        if "strong buy" in rating_lower:
            return 1.0
        elif "buy" in rating_lower:
            return 2.0
        elif "hold" in rating_lower:
            return 3.0
        elif "sell" in rating_lower:
            return 4.0
        elif "strong sell" in rating_lower:
            return 5.0
        else:
            return 3.0  # Default to Hold if unknown
    
    def _recommendation_mean_to_rating(self, mean: Optional[float]) -> str:
        """
        Convert recommendation mean (1-5) to rating string
        
        Args:
            mean: Recommendation mean (1.0-5.0)
            
        Returns:
            Rating string
        """
        if mean is None:
            return "Hold"
        
        if mean <= 1.5:
            return "Strong Buy"
        elif mean <= 2.5:
            return "Buy"
        elif mean <= 3.5:
            return "Hold"
        elif mean <= 4.5:
            return "Sell"
        else:
            return "Strong Sell"
    
    def _check_data_freshness(self, rating: AnalystRating, info: Dict[str, Any]) -> None:
        """
        Check if analyst data appears stale and log warnings
        
        Args:
            rating: AnalystRating object to check
            info: Raw yfinance info dict for additional context
        """
        warning_threshold_days = self.config.data_freshness_warning_days
        
        # Heuristic: If no analysts, data might be stale
        if rating.number_of_analysts == 0:
            logger.debug(f"No analyst data for {rating.symbol} - data may be stale or unavailable")
            return
        
        # Heuristic: If price target is extremely far from current price (>50% difference),
        # it might indicate stale data or major market movement
        if rating.current_price and rating.price_target and rating.price_target > 0:
            price_diff_pct = abs(rating.price_target_upside) if rating.price_target_upside else 0
            if price_diff_pct > 50:
                logger.warning(
                    f"Large price target discrepancy for {rating.symbol}: "
                    f"{price_diff_pct:.1f}% difference (current=${rating.current_price:.2f}, "
                    f"target=${rating.price_target:.2f}). Data may be stale or market moved significantly."
                )
        
        # Note: yfinance doesn't provide explicit "last updated" timestamps for analyst data,
        # so we rely on heuristics and cache TTL to ensure freshness
    
    def _fetch_yfinance_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch data from yfinance with retry logic and timeout
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Info dictionary from yfinance or None
        """
        if not self.is_available():
            logger.warning("Analyst ratings client not available")
            return None
        
        # Validate symbol first
        if not self._validate_symbol(symbol):
            logger.warning(f"Invalid symbol format: {symbol}")
            raise ValueError(f"Invalid symbol format: {symbol}. Symbols must be 1-10 alphanumeric characters.")
        
        symbol_upper = symbol.strip().upper()
        
        # Define the actual fetch function
        def _fetch():
            ticker = yf.Ticker(symbol_upper)
            # Wrap info access with timeout
            return self._call_with_timeout(lambda: ticker.info)
        
        # Apply retry logic if tenacity is available
        if TENACITY_AVAILABLE and self.config.max_retries > 1:
            @retry(
                stop=stop_after_attempt(self.config.max_retries),
                wait=wait_exponential(multiplier=self.config.retry_backoff_factor, min=1, max=10),
                retry=retry_if_exception_type((ConnectionError, AnalystRatingsTimeoutError, TimeoutError, OSError)),
                reraise=True
            )
            def _fetch_with_retry():
                return _fetch()
            
            try:
                return _fetch_with_retry()
            except RetryError as e:
                logger.error(f"Failed to fetch yfinance data for {symbol_upper} after {self.config.max_retries} retries: {e}")
                return None
            except (AnalystRatingsTimeoutError, TimeoutError, ConnectionError, OSError) as e:
                if self._is_retryable_error(e):
                    logger.warning(f"Retryable error fetching {symbol_upper} (but retries exhausted): {e}")
                else:
                    logger.error(f"Non-retryable error fetching {symbol_upper}: {e}")
                return None
        else:
            # No retry logic, just execute with timeout
            try:
                return _fetch()
            except (AnalystRatingsTimeoutError, TimeoutError) as e:
                logger.error(f"Timeout fetching yfinance data for {symbol_upper}: {e}")
                return None
            except (ConnectionError, OSError) as e:
                if self._is_retryable_error(e):
                    logger.warning(f"Network error fetching {symbol_upper} (consider enabling retry logic): {e}")
                else:
                    logger.error(f"Error fetching {symbol_upper}: {e}")
                return None
    
    def get_analyst_rating(self, symbol: str) -> Optional[AnalystRating]:
        """
        Get analyst rating for a symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            AnalystRating object or None
        """
        if not self.is_available():
            logger.warning("Analyst ratings client not available")
            return None
        
        # Validate symbol first (early return for invalid symbols)
        if not self._validate_symbol(symbol):
            logger.warning(f"Invalid symbol format: {symbol}")
            return None
        
        symbol_upper = symbol.strip().upper()
        
        try:
            # Fetch data with retry and timeout
            info = self._fetch_yfinance_data(symbol_upper)
            
            if info is None:
                logger.debug(f"No data returned from yfinance for {symbol_upper}")
                return None
            
            # Get recommendation data
            recommendation_mean = info.get('recommendationMean')
            recommendation_key = info.get('recommendationKey', 'hold')
            
            # Get price targets
            target_high = info.get('targetHighPrice')
            target_low = info.get('targetLowPrice')
            target_mean = info.get('targetMeanPrice')
            target_price = target_mean  # Use mean as primary target
            
            # Get number of analysts
            num_analysts = info.get('numberOfAnalystOpinions', 0)
            
            # Get current price
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            
            # Convert recommendation to numeric
            if recommendation_mean is not None:
                rating_numeric = float(recommendation_mean)
            else:
                rating_numeric = self._rating_to_numeric(recommendation_key)
            
            rating = self._recommendation_mean_to_rating(rating_numeric)
            
            # Calculate upside/downside (validate prices are positive)
            price_target_upside = None
            if current_price and current_price > 0 and target_price and target_price > 0:
                price_target_upside = ((target_price - current_price) / current_price) * 100
            
            rating_obj = AnalystRating(
                symbol=symbol_upper,
                rating=rating,
                rating_numeric=rating_numeric,
                price_target=target_price,
                price_target_high=target_high,
                price_target_low=target_low,
                price_target_mean=target_mean,
                number_of_analysts=num_analysts,
                current_price=current_price,
                price_target_upside=price_target_upside,
                timestamp=datetime.now()
            )
            
            # Check data freshness (warn if data seems stale)
            self._check_data_freshness(rating_obj, info)
            
            return rating_obj
            
        except ValueError as e:
            # Invalid symbol format (validation error)
            logger.warning(f"Validation error for symbol {symbol_upper}: {e}")
            return None
        except (TypeError, KeyError) as e:
            # Data parsing error (invalid response structure)
            logger.warning(f"Invalid data structure from yfinance for {symbol_upper}: {e}")
            return None
        except (AnalystRatingsTimeoutError, TimeoutError) as e:
            # Timeout error (network/slow API)
            logger.error(f"Timeout fetching analyst rating for {symbol_upper}: {e}")
            return None
        except (ConnectionError, OSError) as e:
            # Network error (retryable)
            logger.error(f"Network error fetching analyst rating for {symbol_upper}: {e}")
            return None
        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected error fetching analyst rating for {symbol_upper}: {e}", exc_info=True)
            return None


class AnalystRatingsSentimentProvider:
    """
    Analyst ratings sentiment provider
    
    Converts analyst ratings and price targets into sentiment signals.
    """
    
    def __init__(self, persist_to_db: bool = True):
        """
        Initialize analyst ratings sentiment provider
        
        Args:
            persist_to_db: Whether to persist data to database (default: True)
        """
        self.client = AnalystRatingsClient()
        self.cache = get_cache_manager()
        self.cache_ttl = settings.analyst_ratings.cache_ttl
        self.rate_limiter = get_rate_limiter("analyst_ratings")
        self.usage_monitor = get_usage_monitor()
        self.persist_to_db = persist_to_db
        self.repository = SentimentRepository() if persist_to_db else None
        
        logger.info(f"AnalystRatingsSentimentProvider initialized (persist_to_db={persist_to_db})")
    
    def is_available(self) -> bool:
        """Check if analyst ratings provider is available"""
        return self.client.is_available()
    
    def _get_cache_key(self, symbol: str, hours: int = 24) -> str:
        """Generate cache key for sentiment"""
        return f"analyst_ratings_sentiment_{symbol}_{hours}"
    
    def _get_from_cache(self, key: str) -> Optional[SymbolSentiment]:
        """Get data from cache if not expired"""
        cached = self.cache.get(key)
        if cached is not None:
            logger.debug(f"Cache hit for analyst ratings: {key}")
            return cached
        return None
    
    def _set_cache(self, key: str, data: Any):
        """Store data in cache"""
        self.cache.set(key, data, ttl=self.cache_ttl)
    
    def _rating_to_sentiment(self, rating: AnalystRating) -> float:
        """
        Convert analyst rating to sentiment score
        
        Args:
            rating: AnalystRating object
            
        Returns:
            Sentiment score (-1.0 to 1.0)
        """
        if not rating:
            return 0.0
        
        # Convert rating (1-5 scale) to sentiment (-1 to 1)
        # 1.0 (Strong Buy) = 1.0, 3.0 (Hold) = 0.0, 5.0 (Strong Sell) = -1.0
        base_sentiment = 1.0 - ((rating.rating_numeric - 1.0) / 4.0) * 2.0  # Maps 1->1.0, 3->0.0, 5->-1.0
        
        # Adjust based on price target upside/downside
        if rating.price_target_upside is not None:
            # Boost sentiment if significant upside (>20%), reduce if significant downside (<-20%)
            upside_boost = max(-0.3, min(0.3, rating.price_target_upside / 100.0))
            base_sentiment = max(-1.0, min(1.0, base_sentiment + upside_boost))
        
        # Adjust based on number of analysts (more analysts = higher confidence)
        # But don't change sentiment, just use for confidence calculation
        
        return base_sentiment
    
    def get_sentiment(self, symbol: str, hours: int = 24) -> Optional[SymbolSentiment]:
        """
        Get sentiment for a symbol based on analyst ratings
        
        Args:
            symbol: Stock symbol
            hours: Hours of data (not used for analyst ratings, kept for API compatibility)
            
        Returns:
            SymbolSentiment object or None
        """
        if not self.is_available():
            logger.warning("Analyst ratings client not available")
            return None
        
        # Check rate limit (yfinance: conservative limit of 200 requests per hour)
        rate_limit = 200
        window_seconds = 3600  # 1 hour
        is_allowed, rate_status = self.rate_limiter.check_rate_limit(limit=rate_limit, window_seconds=window_seconds)
        if not is_allowed:
            logger.warning(f"Analyst ratings rate limit exceeded for {symbol}, waiting...")
            rate_status = self.rate_limiter.wait_if_needed(limit=rate_limit, window_seconds=window_seconds)
            if rate_status.is_limited:
                logger.error(f"Analyst ratings rate limit still exceeded after wait")
                self.usage_monitor.record_request("analyst_ratings", success=False)
                return None
        
        # Check cache
        cache_key = self._get_cache_key(symbol, hours)
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"Returning cached analyst ratings sentiment for {symbol}")
            self.usage_monitor.record_request("analyst_ratings", success=True, cached=True)
            return cached
        
        # Fetch analyst rating
        rating = self.client.get_analyst_rating(symbol)
        
        if not rating:
            logger.info(f"No analyst rating data found for {symbol}")
            self.usage_monitor.record_request("analyst_ratings", success=True, cached=False)
            # Return neutral sentiment
            sentiment = SymbolSentiment(
                symbol=symbol,
                timestamp=datetime.now(),
                mention_count=0,
                average_sentiment=0.0,
                weighted_sentiment=0.0,
                sentiment_level=SentimentLevel.NEUTRAL,
                confidence=0.3  # Low confidence for missing data
            )
            self._set_cache(cache_key, sentiment)
            return sentiment
        
        # Convert rating to sentiment score
        sentiment_score = self._rating_to_sentiment(rating)
        
        # Calculate confidence based on number of analysts
        # More analysts = higher confidence
        if rating.number_of_analysts > 0:
            confidence = min(0.3 + (rating.number_of_analysts / 20.0), 1.0)  # Max confidence at 20+ analysts
        else:
            confidence = 0.3  # Low confidence if no analyst count available (match missing data confidence)
        
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
        
        # Create sentiment object
        sentiment = SymbolSentiment(
            symbol=symbol,
            timestamp=datetime.now(),
            mention_count=rating.number_of_analysts,  # Use analyst count as "mention" proxy
            average_sentiment=sentiment_score,
            weighted_sentiment=sentiment_score,  # Analyst ratings don't have engagement weighting
            influencer_sentiment=None,  # Not applicable for analyst ratings
            engagement_score=confidence,  # Use confidence as engagement proxy
            sentiment_level=sentiment_level,
            confidence=confidence,
            volume_trend="stable",  # Analyst ratings don't have volume trends
            tweets=[]  # Not applicable for analyst ratings
        )
        
        # Save symbol sentiment to database if persistence enabled
        if self.persist_to_db and self.repository:
            try:
                self.repository.save_symbol_sentiment(sentiment)
            except Exception as e:
                logger.warning(f"Failed to save analyst ratings sentiment to database: {e}")
        
        # Cache result
        self._set_cache(cache_key, sentiment)
        
        # Track successful request
        self.usage_monitor.record_request("analyst_ratings", success=True, cached=False)
        
        logger.info(
            f"Analyst ratings sentiment for {symbol}: {sentiment_score:.3f} "
            f"({sentiment_level.value}) - {rating.rating} ({rating.number_of_analysts} analysts)"
        )
        
        return sentiment
    
    def get_analyst_rating(self, symbol: str) -> Optional[AnalystRating]:
        """
        Get raw analyst rating data
        
        Args:
            symbol: Stock symbol
            
        Returns:
            AnalystRating object or None
        """
        if not self.is_available():
            return None
        
        return self.client.get_analyst_rating(symbol)
    
    def get_analyst_ratings_batch(self, symbols: List[str]) -> Dict[str, Optional[AnalystRating]]:
        """
        Get analyst ratings for multiple symbols (batch fetch)
        
        Uses yfinance Tickers for efficient batch fetching when available.
        Falls back to individual fetches if batch fails.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary mapping symbol to AnalystRating (or None if unavailable)
        """
        if not self.is_available():
            return {symbol: None for symbol in symbols}
        
        # Validate and normalize symbols
        valid_symbols = []
        results = {}
        
        for symbol in symbols:
            if self.client._validate_symbol(symbol):
                symbol_upper = symbol.strip().upper()
                valid_symbols.append(symbol_upper)
                results[symbol_upper] = None
            else:
                logger.warning(f"Invalid symbol in batch request: {symbol}")
                results[symbol] = None
        
        if not valid_symbols:
            return results
        
        # Try batch fetch using yfinance Tickers (plural)
        try:
            tickers = yf.Tickers(" ".join(valid_symbols))
            
            # Fetch data for each symbol from batch
            for symbol_upper in valid_symbols:
                try:
                    # Get ticker from batch - Tickers stores as dict with symbol as key
                    # Access directly: tickers[symbol] or via .tickers dict
                    if hasattr(tickers, 'tickers') and isinstance(tickers.tickers, dict):
                        ticker = tickers.tickers.get(symbol_upper)
                    elif hasattr(tickers, symbol_upper):
                        ticker = getattr(tickers, symbol_upper)
                    else:
                        # Try direct dictionary access
                        ticker = tickers.get(symbol_upper) if hasattr(tickers, 'get') else None
                    
                    if ticker is None:
                        # Fallback to individual fetch
                        results[symbol_upper] = self.client.get_analyst_rating(symbol_upper)
                        continue
                    
                    # Fetch info with timeout
                    info = self.client._call_with_timeout(lambda: ticker.info)
                    
                    if info is None or not info:
                        results[symbol_upper] = None
                        continue
                    
                    # Parse rating from batch data (reuse existing logic)
                    # Get recommendation data
                    recommendation_mean = info.get('recommendationMean')
                    recommendation_key = info.get('recommendationKey', 'hold')
                    
                    # Get price targets
                    target_high = info.get('targetHighPrice')
                    target_low = info.get('targetLowPrice')
                    target_mean = info.get('targetMeanPrice')
                    target_price = target_mean
                    
                    # Get number of analysts
                    num_analysts = info.get('numberOfAnalystOpinions', 0)
                    
                    # Get current price
                    current_price = info.get('currentPrice') or info.get('regularMarketPrice')
                    
                    # Convert recommendation to numeric
                    if recommendation_mean is not None:
                        rating_numeric = float(recommendation_mean)
                    else:
                        rating_numeric = self.client._rating_to_numeric(recommendation_key)
                    
                    rating = self.client._recommendation_mean_to_rating(rating_numeric)
                    
                    # Calculate upside/downside
                    price_target_upside = None
                    if current_price and current_price > 0 and target_price and target_price > 0:
                        price_target_upside = ((target_price - current_price) / current_price) * 100
                    
                    rating_obj = AnalystRating(
                        symbol=symbol_upper,
                        rating=rating,
                        rating_numeric=rating_numeric,
                        price_target=target_price,
                        price_target_high=target_high,
                        price_target_low=target_low,
                        price_target_mean=target_mean,
                        number_of_analysts=num_analysts,
                        current_price=current_price,
                        price_target_upside=price_target_upside,
                        timestamp=datetime.now()
                    )
                    
                    # Check data freshness
                    self.client._check_data_freshness(rating_obj, info)
                    
                    results[symbol_upper] = rating_obj
                    
                except Exception as e:
                    logger.debug(f"Error processing {symbol_upper} in batch: {e}, falling back to individual fetch")
                    # Fallback to individual fetch
                    results[symbol_upper] = self.client.get_analyst_rating(symbol_upper)
            
            logger.info(f"Batch fetched analyst ratings for {len(valid_symbols)} symbols")
            return results
            
        except Exception as e:
            logger.warning(f"Batch fetch failed, falling back to individual fetches: {e}")
            # Fallback to individual fetches
            for symbol_upper in valid_symbols:
                if results[symbol_upper] is None:
                    results[symbol_upper] = self.client.get_analyst_rating(symbol_upper)
            
            return results

