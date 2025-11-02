"""
Insider Trading & Institutional Holdings Sentiment Provider
===========================================================

Integration for tracking insider trading (Form 4) and institutional holdings (13F filings)
to provide sentiment signals based on insider and institutional activity.
"""

import logging
import re
import signal
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import threading

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    import requests
except ImportError:
    requests = None

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

from ...config.settings import settings
from .models import SymbolSentiment, SentimentLevel
from .repository import SentimentRepository
from .sentiment_analyzer import SentimentAnalyzer
from ...utils.cache import get_cache_manager
from ...utils.rate_limiter import get_rate_limiter
from ...utils.monitoring import get_usage_monitor

logger = logging.getLogger(__name__)


class InsiderTradingTimeoutError(Exception):
    """Custom timeout exception for insider trading"""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout"""
    raise InsiderTradingTimeoutError("yfinance API call timed out")


@dataclass
class InsiderTransaction:
    """Insider transaction data"""
    symbol: str
    insider_name: str
    transaction_type: str  # "Buy", "Sell", "Option Exercise", etc.
    transaction_date: datetime
    shares: Optional[int] = None
    price: Optional[float] = None
    value: Optional[float] = None
    position_type: Optional[str] = None  # "Director", "Officer", "10% Owner", etc.


@dataclass
class InstitutionalHolding:
    """Institutional holding data"""
    symbol: str
    institution_name: str
    shares: int
    value: float
    percentage: float  # Percentage of outstanding shares
    filing_date: datetime
    change_shares: Optional[int] = None  # Change from previous filing
    change_percentage: Optional[float] = None


class InsiderTradingClient:
    """
    Client for fetching insider trading and institutional holdings data
    
    Uses yfinance for basic insider trading data (major holders)
    and can be extended with SEC EDGAR for Form 4 and 13F filings.
    """
    
    def __init__(self):
        """Initialize insider trading client"""
        if yf is None:
            raise ImportError(
                "yfinance is required for insider trading integration. "
                "Install with: pip install yfinance"
            )
        
        self.config = settings.insider_trading
        self.rate_limiter = get_rate_limiter("insider_trading_client")
        logger.info("InsiderTradingClient initialized")
    
    def is_available(self) -> bool:
        """Check if client is available"""
        return self.config.enabled
    
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
            InsiderTradingTimeoutError if function exceeds timeout
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
                except InsiderTradingTimeoutError:
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
                raise InsiderTradingTimeoutError(f"yfinance API call exceeded {timeout}s timeout")
            
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
            InsiderTradingTimeoutError,
            TimeoutError,
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
    
    def _check_rate_limit(self):
        """
        Check and enforce rate limit before making API call
        
        Raises:
            Exception if rate limit exceeded and wait failed
        """
        rate_limit = self.config.rate_limit_requests_per_minute
        window_seconds = 60  # 1 minute
        
        is_allowed, rate_status = self.rate_limiter.check_rate_limit(
            limit=rate_limit,
            window_seconds=window_seconds
        )
        
        if not is_allowed:
            logger.debug(f"Rate limit check: {rate_status.remaining} remaining, waiting if needed...")
            rate_status = self.rate_limiter.wait_if_needed(
                limit=rate_limit,
                window_seconds=window_seconds
            )
            if rate_status.is_limited:
                raise Exception(f"Rate limit exceeded: {rate_status.message}")
    
    def get_major_holders(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get major holders (insiders and institutions) from yfinance
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with 'insiders' and 'institutions' data
        """
        # Validate symbol
        if not self._validate_symbol(symbol):
            logger.warning(f"Invalid symbol format: {symbol}")
            return None
        
        # Check rate limit
        try:
            self._check_rate_limit()
        except Exception as e:
            logger.error(f"Rate limit error for {symbol}: {e}")
            return None
        
        def _fetch_major_holders():
            ticker = yf.Ticker(symbol)
            return ticker.major_holders
        
        try:
            # Fetch with timeout and retry logic
            major_holders = self._fetch_with_retry(_fetch_major_holders, symbol)
            
            if major_holders is None or major_holders.empty:
                return None
            
            result = {
                'insiders': [],
                'institutions': [],
                'total_insider_percent': 0.0,
                'total_institutional_percent': 0.0
            }
            
            # Parse major holders dataframe
            # Format: [percent, holder_type]
            for idx, row in major_holders.iterrows():
                if len(row) < 2:
                    continue
                
                percent_str = str(row.iloc[0])
                holder_info = str(row.iloc[1]) if len(row) > 1 else ""
                
                # Extract percentage
                try:
                    percent = float(percent_str.replace('%', '').strip())
                except (ValueError, AttributeError):
                    continue
                
                # Categorize by holder type
                holder_lower = holder_info.lower()
                if 'insider' in holder_lower or 'institutional' in holder_lower:
                    if 'insider' in holder_lower:
                        result['insiders'].append({
                            'percent': percent,
                            'info': holder_info
                        })
                        result['total_insider_percent'] += percent
                    elif 'institutional' in holder_lower:
                        result['institutions'].append({
                            'percent': percent,
                            'info': holder_info
                        })
                        result['total_institutional_percent'] += percent
            
            return result if (result['insiders'] or result['institutions']) else None
            
        except Exception as e:
            logger.error(f"Error fetching major holders for {symbol}: {e}", exc_info=True)
            return None
    
    def _fetch_with_retry(self, func, symbol: str, *args, **kwargs):
        """
        Fetch data with retry logic and timeout handling
        
        Args:
            func: Function to execute
            symbol: Symbol for logging
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
        """
        max_retries = self.config.max_retries
        backoff_factor = self.config.retry_backoff_factor
        
        for attempt in range(max_retries + 1):
            try:
                return self._call_with_timeout(func, *args, **kwargs)
            except (ConnectionError, InsiderTradingTimeoutError, TimeoutError, OSError) as e:
                # Retryable network/timeout errors
                if attempt >= max_retries:
                    logger.warning(f"Failed to fetch data for {symbol} after {attempt + 1} attempts: {e}")
                    raise
                
                # Check if error is truly retryable (double-check)
                if not self._is_retryable_error(e):
                    logger.warning(f"Non-retryable error for {symbol}: {e}")
                    raise
                
                # Calculate backoff delay
                delay = backoff_factor ** attempt
                logger.debug(f"Retry attempt {attempt + 1}/{max_retries} for {symbol} after {delay:.2f}s delay")
                time.sleep(delay)
            except Exception as e:
                # Non-retryable errors (programming errors, validation errors, etc.)
                # Don't retry these - they indicate a bug or invalid input
                logger.error(f"Non-retryable error for {symbol}: {e}", exc_info=True)
                raise
        
        raise Exception(f"Failed to fetch data for {symbol} after {max_retries + 1} attempts")
    
    def get_institutional_holders(self, symbol: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get detailed institutional holders from yfinance
        
        Args:
            symbol: Stock symbol
            
        Returns:
            List of institutional holdings
        """
        # Validate symbol
        if not self._validate_symbol(symbol):
            logger.warning(f"Invalid symbol format: {symbol}")
            return None
        
        # Check rate limit
        try:
            self._check_rate_limit()
        except Exception as e:
            logger.error(f"Rate limit error for {symbol}: {e}")
            return None
        
        def _fetch_institutional_holders():
            ticker = yf.Ticker(symbol)
            return ticker.institutional_holders
        
        try:
            # Fetch with timeout and retry logic
            institutional_holders = self._fetch_with_retry(_fetch_institutional_holders, symbol)
            
            if institutional_holders is None or institutional_holders.empty:
                return None
            
            holdings = []
            for _, row in institutional_holders.iterrows():
                holdings.append({
                    'institution': str(row.get('Holder', 'Unknown')),
                    'shares': int(row.get('Shares', 0)),
                    'date_reported': row.get('Date Reported', datetime.now()),
                    'percent_held': float(row.get('% Out', 0)) if '% Out' in row else 0.0,
                    'value': float(row.get('Value', 0)) if 'Value' in row else None
                })
            
            return holdings
            
        except Exception as e:
            logger.error(f"Error fetching institutional holders for {symbol}: {e}", exc_info=True)
            return None
    
    def get_insider_transactions(self, symbol: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get recent insider transactions from yfinance
        
        Args:
            symbol: Stock symbol
            
        Returns:
            List of insider transactions
        """
        # Validate symbol
        if not self._validate_symbol(symbol):
            logger.warning(f"Invalid symbol format: {symbol}")
            return None
        
        # Check rate limit
        try:
            self._check_rate_limit()
        except Exception as e:
            logger.error(f"Rate limit error for {symbol}: {e}")
            return None
        
        def _fetch_insider_transactions():
            ticker = yf.Ticker(symbol)
            return ticker.insider_transactions
        
        try:
            # Fetch with timeout and retry logic
            insider_transactions = self._fetch_with_retry(_fetch_insider_transactions, symbol)
            
            if insider_transactions is None or insider_transactions.empty:
                return None
            
            transactions = []
            for _, row in insider_transactions.iterrows():
                transactions.append({
                    'insider': str(row.get('Insider', 'Unknown')),
                    'transaction': str(row.get('Transaction', 'Unknown')),
                    'date': row.get('Date', datetime.now()),
                    'shares': int(row.get('Shares', 0)),
                    'price': float(row.get('Price', 0)) if 'Price' in row else None,
                    'value': float(row.get('Value', 0)) if 'Value' in row else None
                })
            
            return transactions
            
        except Exception as e:
            logger.error(f"Error fetching insider transactions for {symbol}: {e}", exc_info=True)
            return None


class InsiderTradingSentimentProvider:
    """
    Insider trading sentiment provider
    
    Converts insider trading and institutional holdings data into sentiment signals.
    - Insider buying = positive sentiment
    - Insider selling = negative sentiment (context-dependent)
    - Institutional accumulation = positive sentiment
    - Large institutional position changes = sentiment signals
    """
    
    def __init__(self, persist_to_db: bool = True):
        """
        Initialize insider trading sentiment provider
        
        Args:
            persist_to_db: Whether to persist data to database (default: True)
        """
        self.client = InsiderTradingClient()
        self.analyzer = SentimentAnalyzer()  # For standardized sentiment level calculation
        # Use Redis-backed cache manager (standardized)
        self.cache = get_cache_manager()
        self.cache_ttl = settings.insider_trading.cache_ttl
        self.rate_limiter = get_rate_limiter("insider_trading")
        self.usage_monitor = get_usage_monitor()
        self.persist_to_db = persist_to_db
        self.repository = SentimentRepository() if persist_to_db else None
        
        logger.info(f"InsiderTradingSentimentProvider initialized (persist_to_db={persist_to_db})")
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        return self.client.is_available()
    
    def _get_cache_key(self, symbol: str, hours: int = 24) -> str:
        """Generate cache key for sentiment"""
        return f"insider_trading:sentiment_{symbol}_{hours}"
    
    def _get_from_cache(self, key: str) -> Optional[SymbolSentiment]:
        """Get data from cache using Redis-backed cache manager"""
        cached = self.cache.get(key)
        if cached is not None:
            logger.debug(f"Cache hit for insider trading: {key}")
            return cached
        return None
    
    def _set_cache(self, key: str, data: SymbolSentiment):
        """Store data in cache using Redis-backed cache manager"""
        self.cache.set(key, data, ttl=self.cache_ttl)
    
    def _calculate_insider_sentiment(
        self,
        transactions: List[Dict[str, Any]],
        major_holders: Optional[Dict[str, Any]]
    ) -> float:
        """
        Calculate sentiment from insider transactions
        
        Logic:
        - Buying = positive sentiment
        - Selling = negative sentiment (but less weight if price is high)
        - Large transactions weighted more
        - Recent transactions weighted more
        
        Returns:
            Sentiment score (-1.0 to 1.0)
        """
        if not transactions:
            # If no transactions, check insider ownership percentage
            if major_holders and major_holders.get('total_insider_percent', 0) > 10:
                # High insider ownership = positive (they have skin in the game)
                return 0.2
            return 0.0
        
        # Analyze recent transactions (last 90 days)
        cutoff_date = datetime.now() - timedelta(days=90)
        recent_transactions = [
            t for t in transactions
            if isinstance(t.get('date'), datetime) and t['date'] >= cutoff_date
        ]
        
        if not recent_transactions:
            return 0.0
        
        total_sentiment = 0.0
        total_weight = 0.0
        
        for trans in recent_transactions:
            trans_type = str(trans.get('transaction', '')).lower()
            shares = abs(trans.get('shares', 0))
            value = trans.get('value', 0) if trans.get('value') else (trans.get('price', 0) * shares if trans.get('price') else 0)
            
            # Calculate transaction sentiment
            if 'buy' in trans_type or 'purchase' in trans_type or 'acquired' in trans_type:
                trans_sentiment = 1.0
            elif 'sell' in trans_type or 'sold' in trans_type or 'disposed' in trans_type:
                trans_sentiment = -0.5  # Selling is less negative (could be tax planning, diversification)
            elif 'option' in trans_type or 'exercise' in trans_type:
                trans_sentiment = 0.3  # Option exercise is slightly positive
            else:
                trans_sentiment = 0.0
            
            # Weight by transaction size (log scale for large transactions)
            if value > 0:
                weight = min(1.0, (value / 1000000.0) ** 0.5)  # Log scale weight
            else:
                weight = min(1.0, shares / 10000.0)  # Use shares if no value
            
            # Time decay (more recent = higher weight)
            if isinstance(trans.get('date'), datetime):
                age_days = (datetime.now() - trans['date']).days
                time_weight = max(0.1, 1.0 - (age_days / 90.0))
            else:
                time_weight = 1.0
            
            total_sentiment += trans_sentiment * weight * time_weight
            total_weight += weight * time_weight
        
        if total_weight == 0:
            return 0.0
        
        return max(-1.0, min(1.0, total_sentiment / total_weight))
    
    def _calculate_institutional_sentiment(
        self,
        institutional_holders: List[Dict[str, Any]],
        major_holders: Optional[Dict[str, Any]]
    ) -> float:
        """
        Calculate sentiment from institutional holdings
        
        Logic:
        - High institutional ownership = positive (smart money)
        - Increasing positions = positive
        - Decreasing positions = negative
        - Large institutional holders = higher confidence
        
        Returns:
            Sentiment score (-1.0 to 1.0)
        """
        if not institutional_holders or institutional_holders is None:
            # If no detailed data, use major holders summary
            if major_holders and major_holders.get('total_institutional_percent', 0) > 50:
                # High institutional ownership = positive
                return 0.3
            return 0.0
        
        # Calculate average ownership and sentiment
        total_percent = sum(h.get('percent_held', 0) for h in institutional_holders)
        avg_percent = total_percent / len(institutional_holders) if institutional_holders else 0
        
        # Base sentiment on ownership level (more institutions = better)
        if avg_percent > 1.0:  # Institutions own >1% each on average
            base_sentiment = 0.4
        elif avg_percent > 0.5:
            base_sentiment = 0.2
        else:
            base_sentiment = 0.0
        
        # Check for position changes (if available)
        # Note: yfinance doesn't always provide change data
        changes = [h.get('change_percentage', 0) for h in institutional_holders if h.get('change_percentage')]
        if changes:
            avg_change = sum(changes) / len(changes)
            change_sentiment = max(-0.3, min(0.3, avg_change / 10.0))  # Normalize to -0.3 to 0.3
            base_sentiment += change_sentiment
        
        return max(-1.0, min(1.0, base_sentiment))
    
    def get_sentiment(
        self,
        symbol: str,
        hours: int = 24
    ) -> Optional[SymbolSentiment]:
        """
        Get sentiment for a symbol based on insider trading and institutional holdings
        
        Args:
            symbol: Stock symbol
            hours: Hours parameter (not used, kept for API compatibility)
            
        Returns:
            SymbolSentiment object or None
        """
        # Track provider availability
        is_available = self.is_available()
        try:
            from ...utils.metrics_providers_helpers import track_provider_availability
            track_provider_availability("insider_trading", is_available)
        except (ImportError, Exception) as e:
            logger.debug(f"Could not record availability metric: {e}")
        
        if not is_available:
            logger.warning("Insider trading provider not available")
            return None
        
        # Track API call timing
        import time
        api_start_time = time.time()
        
        # Check cache
        cache_key = self._get_cache_key(symbol, hours)
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"Returning cached insider trading sentiment for {symbol}")
            # Track data freshness
            try:
                from ...utils.metrics_providers_helpers import track_cache_freshness
                track_cache_freshness("insider_trading", "get_sentiment", cached)
            except (ImportError, Exception) as e:
                logger.debug(f"Could not record data freshness metric: {e}")
            self.usage_monitor.record_request("insider_trading", success=True, cached=True)
            return cached
        
        # Check rate limit at provider level
        rate_limit = self.config.rate_limit_requests_per_minute
        window_seconds = 60
        is_allowed, rate_status = self.rate_limiter.check_rate_limit(
            limit=rate_limit,
            window_seconds=window_seconds
        )
        if not is_allowed:
            logger.warning(f"Insider trading rate limit exceeded for {symbol}, waiting...")
            rate_status = self.rate_limiter.wait_if_needed(
                limit=rate_limit,
                window_seconds=window_seconds
            )
            if rate_status.is_limited:
                logger.error(f"Insider trading rate limit still exceeded after wait")
                # Record rate limit hit metric
                try:
                    from ...utils.metrics_providers_helpers import track_rate_limit_hit
                    track_rate_limit_hit("insider_trading")
                except (ImportError, Exception) as e:
                    logger.debug(f"Could not record rate limit metric: {e}")
                self.usage_monitor.record_request("insider_trading", success=False)
                return None
        
        try:
            # Fetch data (client handles its own rate limiting)
            major_holders = self.client.get_major_holders(symbol)
            insider_transactions = self.client.get_insider_transactions(symbol)
            institutional_holders = self.client.get_institutional_holders(symbol)
            
            # Record API response time
            api_response_time = time.time() - api_start_time
            
            # Calculate component sentiments
            insider_sentiment = self._calculate_insider_sentiment(
                insider_transactions or [],
                major_holders
            )
            
            institutional_sentiment = self._calculate_institutional_sentiment(
                institutional_holders or [],
                major_holders
            )
            
            # Combine sentiments using config weights
            insider_weight = self.config.insider_weight
            institutional_weight = self.config.institutional_weight
            
            # Normalize weights to sum to 1.0
            total_weight = insider_weight + institutional_weight
            if total_weight > 0:
                insider_weight /= total_weight
                institutional_weight /= total_weight
            
            combined_sentiment = (insider_sentiment * insider_weight) + (institutional_sentiment * institutional_weight)
            
            # Calculate confidence based on data availability
            confidence = 0.5  # Base confidence
            if insider_transactions:
                confidence += 0.2  # Insider transactions available
            if institutional_holders:
                confidence += 0.2  # Institutional data available
            if major_holders and major_holders.get('total_insider_percent', 0) > 5:
                confidence += 0.1  # Significant insider ownership
            
            confidence = min(1.0, confidence)
            
            # Determine sentiment level using standardized method
            sentiment_level = self.analyzer._score_to_level(combined_sentiment)
            
            # Calculate mention count (use number of transactions/holdings)
            mention_count = 0
            if insider_transactions:
                mention_count += len(insider_transactions)
            if institutional_holders:
                mention_count += len(institutional_holders)
            
            # Create sentiment object
            sentiment = SymbolSentiment(
                symbol=symbol.upper(),
                timestamp=datetime.now(),
                mention_count=mention_count,
                average_sentiment=combined_sentiment,
                weighted_sentiment=combined_sentiment,  # No additional weighting
                influencer_sentiment=None,  # Not applicable
                engagement_score=confidence,  # Use confidence as engagement
                sentiment_level=sentiment_level,
                confidence=confidence,
                volume_trend="stable",  # Insider data doesn't have volume trends
                tweets=[]  # Not applicable
            )
            
            # Cache result
            self._set_cache(cache_key, sentiment)
            
            # Persist to database if enabled
            if self.persist_to_db and self.repository:
                try:
                    self.repository.save_symbol_sentiment(sentiment)
                except Exception as e:
                    logger.warning(f"Failed to save insider trading sentiment to database: {e}")
            
            # Track successful request
            self.usage_monitor.record_request("insider_trading", success=True, cached=False)
            
            logger.info(
                f"Insider trading sentiment for {symbol}: {combined_sentiment:.3f} "
                f"({sentiment_level.value}) - Insider: {insider_sentiment:.3f}, "
                f"Institutional: {institutional_sentiment:.3f}"
            )
            
            return sentiment
            
        except Exception as e:
            logger.error(f"Error getting insider trading sentiment for {symbol}: {e}", exc_info=True)
            self.usage_monitor.record_request("insider_trading", success=False)
            return None
    
    def get_insider_transactions(self, symbol: str) -> Optional[List[Dict[str, Any]]]:
        """Get raw insider transactions data"""
        if not self.is_available():
            return None
        return self.client.get_insider_transactions(symbol)
    
    def get_institutional_holders(self, symbol: str) -> Optional[List[Dict[str, Any]]]:
        """Get raw institutional holders data"""
        if not self.is_available():
            return None
        return self.client.get_institutional_holders(symbol)
    
    def get_major_holders(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get major holders summary"""
        if not self.is_available():
            return None
        return self.client.get_major_holders(symbol)

