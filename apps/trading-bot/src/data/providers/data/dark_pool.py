"""
Dark Pool & Institutional Flow Data Provider
============================================

Integration for tracking dark pool trading activity and institutional flow data.
Dark pools are private exchanges where large institutional trades are executed
without showing up on public order books.

Note: Most dark pool data providers require paid API access (FlowAlgo, Cheddar Flow, etc.)
This implementation provides the foundation structure that can be extended with actual APIs.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

try:
    import requests
except ImportError:
    requests = None

from ...config.settings import settings
from ...utils.cache import get_cache_manager
from ...utils.rate_limiter import get_rate_limiter
from ...utils.monitoring import get_usage_monitor

logger = logging.getLogger(__name__)


class TradeType(Enum):
    """Dark pool trade type"""
    BUY = "buy"
    SELL = "sell"
    UNKNOWN = "unknown"


@dataclass
class DarkPoolTrade:
    """Dark pool trade data"""
    symbol: str
    timestamp: datetime
    volume: int  # Number of shares
    price: float
    trade_type: TradeType
    dark_pool_name: Optional[str] = None  # e.g., "ATS-1", "ATS-2", etc.
    market_impact: Optional[float] = None  # Estimated market impact
    block_size: bool = False  # True if this is a large block trade


@dataclass
class InstitutionalFlow:
    """Institutional flow data"""
    symbol: str
    timestamp: datetime
    net_flow: float  # Net buying pressure (positive = buying, negative = selling)
    buy_volume: int = 0
    sell_volume: int = 0
    dark_pool_volume: int = 0  # Volume traded in dark pools
    block_trades: int = 0  # Number of large block trades
    institutional_percentage: float = 0.0  # % of volume from institutions


@dataclass
class DarkPoolSnapshot:
    """Snapshot of dark pool activity for a symbol"""
    symbol: str
    timestamp: datetime
    total_dark_pool_volume: int
    dark_pool_percentage: float  # % of total volume in dark pools
    net_dark_pool_flow: float  # Net buying/selling in dark pools
    block_trades: List[DarkPoolTrade] = field(default_factory=list)
    institutional_flow: Optional[InstitutionalFlow] = None


class DarkPoolClient:
    """
    Client for fetching dark pool and institutional flow data
    
    Note: This is a foundation implementation. Most dark pool data requires paid APIs.
    Examples of providers:
    - FlowAlgo (https://flowalgo.com) - Paid subscription
    - Cheddar Flow (https://cheddarflow.com) - Paid subscription
    - Polygon.io (has some dark pool data in premium tiers)
    - NYSE/NSX dark pool data (requires subscription)
    
    This implementation provides placeholder methods that can be extended with actual API calls.
    """
    
    def __init__(self):
        """Initialize dark pool client"""
        # Check if any dark pool API credentials are configured
        self.config = getattr(settings, 'dark_pool', None)
        
        # API credentials (set via environment variables)
        self.api_key = None
        self.base_url = None
        self.enabled = False
        
        # Initialize from config if available
        if self.config:
            self.api_key = getattr(self.config, 'api_key', None)
            self.base_url = getattr(self.config, 'base_url', None)
            self.enabled = getattr(self.config, 'enabled', False) if self.config else False
        
        logger.info(f"DarkPoolClient initialized (enabled={self.enabled})")
    
    def is_available(self) -> bool:
        """Check if dark pool client is available"""
        # Return True if API key is configured, False otherwise
        # This allows the structure to exist but won't fetch data without API key
        return self.enabled and self.api_key is not None
    
    def get_dark_pool_snapshot(
        self,
        symbol: str,
        days: int = 1
    ) -> Optional[DarkPoolSnapshot]:
        """
        Get dark pool activity snapshot for a symbol
        
        Args:
            symbol: Stock symbol
            days: Number of days to look back (default: 1)
            
        Returns:
            DarkPoolSnapshot or None if no data/API unavailable
        """
        if not self.is_available():
            logger.debug(f"Dark pool client not available for {symbol} (no API key configured)")
            return None
        
        # TODO: Implement actual API call when API provider is selected
        # Example structure:
        # response = requests.get(
        #     f"{self.base_url}/dark-pool/{symbol}",
        #     headers={"Authorization": f"Bearer {self.api_key}"},
        #     params={"days": days}
        # )
        # data = response.json()
        # ... parse data into DarkPoolSnapshot ...
        
        logger.warning(
            f"Dark pool API not implemented yet. "
            f"Configure DARK_POOL_API_KEY and DARK_POOL_BASE_URL to enable."
        )
        return None
    
    def get_institutional_flow(
        self,
        symbol: str,
        days: int = 1
    ) -> Optional[InstitutionalFlow]:
        """
        Get institutional flow data for a symbol
        
        Args:
            symbol: Stock symbol
            days: Number of days to look back
            
        Returns:
            InstitutionalFlow or None if no data/API unavailable
        """
        if not self.is_available():
            return None
        
        # TODO: Implement actual API call
        # This would typically come from the same or different endpoint
        
        return None
    
    def get_block_trades(
        self,
        symbol: str,
        hours: int = 24
    ) -> List[DarkPoolTrade]:
        """
        Get large block trades for a symbol
        
        Args:
            symbol: Stock symbol
            hours: Hours of data to retrieve
            
        Returns:
            List of DarkPoolTrade objects
        """
        if not self.is_available():
            return []
        
        # TODO: Implement actual API call
        
        return []


class DarkPoolSentimentProvider:
    """
    Dark pool sentiment provider
    
    Converts dark pool and institutional flow data into sentiment signals.
    - High dark pool buying = positive sentiment (institutions accumulating)
    - High dark pool selling = negative sentiment (institutions distributing)
    - Large block trades = significant institutional activity
    - Net institutional flow = buying/selling pressure indicator
    """
    
    def __init__(self, persist_to_db: bool = True):
        """
        Initialize dark pool sentiment provider
        
        Args:
            persist_to_db: Whether to persist data to database (default: True)
        """
        self.client = DarkPoolClient()
        self.cache = get_cache_manager()
        self.cache_ttl = 1800  # 30 minutes default cache (dark pool data changes less frequently)
        
        # Get cache TTL from config if available
        if hasattr(settings, 'dark_pool') and hasattr(settings.dark_pool, 'cache_ttl'):
            self.cache_ttl = settings.dark_pool.cache_ttl
        
        self.rate_limiter = get_rate_limiter("dark_pool")
        self.usage_monitor = get_usage_monitor()
        self.persist_to_db = persist_to_db
        
        # Import repository only if needed
        if persist_to_db:
            try:
                from ..sentiment.repository import SentimentRepository
                self.repository = SentimentRepository()
            except ImportError:
                logger.warning("SentimentRepository not available, database persistence disabled")
                self.repository = None
        else:
            self.repository = None
        
        logger.info(f"DarkPoolSentimentProvider initialized (persist_to_db={persist_to_db}, available={self.is_available()})")
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        return self.client.is_available()
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache"""
        cache_key = f"dark_pool:{key}"
        return self.cache.get(cache_key)
    
    def _set_cache(self, key: str, data: Any):
        """Store data in cache"""
        cache_key = f"dark_pool:{key}"
        self.cache.set(cache_key, data, ttl=self.cache_ttl)
    
    def _calculate_sentiment_from_snapshot(
        self,
        snapshot: DarkPoolSnapshot
    ) -> float:
        """
        Calculate sentiment score from dark pool snapshot
        
        Logic:
        - High dark pool volume with net buying = positive sentiment
        - High dark pool volume with net selling = negative sentiment
        - Block trades indicate strong institutional interest
        - Dark pool percentage indicates institutional participation
        
        Returns:
            Sentiment score (-1.0 to 1.0)
        """
        if snapshot is None:
            return 0.0
        
        # Base sentiment from net flow
        # Normalize net flow to -1.0 to 1.0 range
        # Assuming net flow is in shares, normalize by typical daily volume
        net_flow_normalized = snapshot.net_dark_pool_flow / max(1, snapshot.total_dark_pool_volume)
        base_sentiment = max(-1.0, min(1.0, net_flow_normalized * 2.0))
        
        # Adjust based on dark pool percentage
        # Higher dark pool % = more institutional interest = higher confidence
        dark_pool_multiplier = min(1.5, 1.0 + (snapshot.dark_pool_percentage / 100.0))
        
        # Block trades indicate strong conviction
        block_trade_bonus = min(0.3, len(snapshot.block_trades) * 0.1)
        
        # Combine factors
        sentiment = base_sentiment * dark_pool_multiplier + block_trade_bonus
        
        # Normalize back to -1.0 to 1.0
        return max(-1.0, min(1.0, sentiment))
    
    def _calculate_sentiment_from_flow(
        self,
        flow: InstitutionalFlow
    ) -> float:
        """
        Calculate sentiment score from institutional flow
        
        Returns:
            Sentiment score (-1.0 to 1.0)
        """
        if flow is None:
            return 0.0
        
        # Normalize net flow
        total_volume = flow.buy_volume + flow.sell_volume
        if total_volume == 0:
            return 0.0
        
        # Calculate net buying percentage
        net_buying_pct = (flow.buy_volume - flow.sell_volume) / total_volume
        
        # Convert to sentiment (-1.0 to 1.0)
        sentiment = net_buying_pct * 2.0  # Scale to -2.0 to 2.0, then clamp
        
        # Weight by institutional percentage
        institutional_weight = min(1.5, 1.0 + (flow.institutional_percentage / 100.0))
        
        sentiment = sentiment * institutional_weight
        
        return max(-1.0, min(1.0, sentiment))
    
    def get_sentiment(
        self,
        symbol: str,
        hours: int = 24
    ) -> Optional[Any]:
        """
        Get sentiment for a symbol based on dark pool and institutional flow
        
        Args:
            symbol: Stock symbol
            hours: Hours of data to analyze (default: 24)
            
        Returns:
            SymbolSentiment object or None if no data/API unavailable
        """
        if not self.is_available():
            logger.debug(f"Dark pool provider not available for {symbol}")
            return None
        
        # Check cache
        cache_key = f"sentiment_{symbol}_{hours}"
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"Returning cached dark pool sentiment for {symbol}")
            if self.usage_monitor:
                self.usage_monitor.record_request("dark_pool", success=True, cached=True)
            return cached
        
        try:
            # Check rate limit
            if self.rate_limiter:
                is_allowed, rate_status = self.rate_limiter.check_rate_limit(limit=60, window_seconds=60)
                if not is_allowed:
                    logger.warning(f"Rate limit exceeded for dark pool {symbol}, waiting...")
                    rate_status = self.rate_limiter.wait_if_needed(limit=60, window_seconds=60)
                    if rate_status.is_limited:
                        logger.error(f"Rate limit still exceeded after wait")
                        if self.usage_monitor:
                            self.usage_monitor.record_request("dark_pool", success=False)
                        return None
            
            # Fetch dark pool snapshot
            days = max(1, int(hours / 24))
            snapshot = self.client.get_dark_pool_snapshot(symbol, days=days)
            flow = self.client.get_institutional_flow(symbol, days=days)
            
            # Record request
            if self.usage_monitor:
                self.usage_monitor.record_request("dark_pool", success=True, cached=False)
            
            # If no data available, return None
            if snapshot is None and flow is None:
                logger.debug(f"No dark pool data available for {symbol}")
                return None
            
            # Calculate sentiment from available data
            sentiment_snapshot = 0.0
            sentiment_flow = 0.0
            
            if snapshot:
                sentiment_snapshot = self._calculate_sentiment_from_snapshot(snapshot)
            
            if flow:
                sentiment_flow = self._calculate_sentiment_from_flow(flow)
            
            # Combine sentiments (weight snapshot more if both available)
            if snapshot and flow:
                combined_sentiment = (sentiment_snapshot * 0.6) + (sentiment_flow * 0.4)
            elif snapshot:
                combined_sentiment = sentiment_snapshot
            else:
                combined_sentiment = sentiment_flow
            
            # Calculate confidence
            confidence = 0.5  # Base confidence
            if snapshot:
                confidence += 0.2  # Dark pool data available
                if snapshot.block_trades:
                    confidence += 0.1  # Block trades available
            if flow:
                confidence += 0.2  # Institutional flow available
            
            confidence = min(1.0, confidence)
            
            # Import SymbolSentiment from sentiment models
            from ..sentiment.models import SymbolSentiment, SentimentLevel
            
            # Determine sentiment level
            if combined_sentiment >= 0.6:
                sentiment_level = SentimentLevel.VERY_BULLISH
            elif combined_sentiment >= 0.2:
                sentiment_level = SentimentLevel.BULLISH
            elif combined_sentiment <= -0.6:
                sentiment_level = SentimentLevel.VERY_BEARISH
            elif combined_sentiment <= -0.2:
                sentiment_level = SentimentLevel.BEARISH
            else:
                sentiment_level = SentimentLevel.NEUTRAL
            
            # Calculate mention count (use number of block trades)
            mention_count = len(snapshot.block_trades) if snapshot else 0
            
            # Create sentiment object
            sentiment = SymbolSentiment(
                symbol=symbol.upper(),
                timestamp=datetime.now(),
                mention_count=mention_count,
                average_sentiment=combined_sentiment,
                weighted_sentiment=combined_sentiment,
                influencer_sentiment=None,
                engagement_score=confidence,
                sentiment_level=sentiment_level,
                confidence=confidence,
                volume_trend="stable",  # Dark pool data doesn't have trends in this format
                tweets=[]  # Not applicable
            )
            
            # Cache result
            self._set_cache(cache_key, sentiment)
            
            # Persist to database if enabled
            if self.persist_to_db and self.repository:
                try:
                    self.repository.save_symbol_sentiment(sentiment)
                except Exception as e:
                    logger.warning(f"Failed to save dark pool sentiment to database: {e}")
            
            logger.info(
                f"Dark pool sentiment for {symbol}: {combined_sentiment:.3f} "
                f"({sentiment_level.value}) - Confidence: {confidence:.3f}"
            )
            
            return sentiment
            
        except Exception as e:
            logger.error(f"Error getting dark pool sentiment for {symbol}: {e}", exc_info=True)
            if self.usage_monitor:
                self.usage_monitor.record_request("dark_pool", success=False)
            return None

