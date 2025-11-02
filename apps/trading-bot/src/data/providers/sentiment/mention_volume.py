"""
Mention Volume Provider
=======================

Aggregates mention volume data from multiple social media sources (Twitter, Reddit, StockTwits)
to track overall attention and detect mention spikes and trends.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field

from ...config.settings import settings
from .repository import SentimentRepository

logger = logging.getLogger(__name__)


@dataclass
class MentionVolume:
    """Mention volume data for a symbol"""
    symbol: str
    timestamp: datetime
    total_mentions: int
    twitter_mentions: int = 0
    reddit_mentions: int = 0
    stocktwits_mentions: int = 0
    news_mentions: int = 0
    volume_trend: str = "stable"  # up, down, stable
    momentum_score: float = 0.0  # -1.0 to 1.0 (positive = accelerating, negative = decelerating)
    spike_detected: bool = False
    spike_magnitude: float = 0.0  # Multiplier above baseline (e.g., 2.0 = 2x normal)


class MentionVolumeProvider:
    """
    Aggregates mention volume from multiple social media sources
    
    Tracks overall attention levels, detects spikes, and calculates momentum.
    """
    
    def __init__(self, persist_to_db: bool = True):
        """
        Initialize mention volume provider
        
        Args:
            persist_to_db: Whether to use database for data retrieval
        """
        self.config = settings.mention_volume
        self.persist_to_db = persist_to_db
        self.repository = SentimentRepository() if persist_to_db else None
        
        logger.info(f"MentionVolumeProvider initialized (persist_to_db={persist_to_db})")
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        return self.persist_to_db and self.repository is not None
    
    def get_mention_volume(
        self,
        symbol: str,
        hours: int = 24,
        lookback_hours: int = 168  # 7 days for baseline comparison
    ) -> Optional[MentionVolume]:
        # Input validation
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        symbol = symbol.strip().upper()
        if not symbol:
            raise ValueError("Symbol cannot be empty after stripping")
        if not isinstance(hours, int) or hours <= 0:
            raise ValueError("hours must be a positive integer")
        if not isinstance(lookback_hours, int) or lookback_hours <= 0:
            raise ValueError("lookback_hours must be a positive integer")
        if lookback_hours < hours:
            raise ValueError("lookback_hours must be >= hours")
        
        if not self.is_available():
            logger.warning("MentionVolumeProvider not available (requires database)")
            return None
        
        try:
            # Get recent mentions from database
            cutoff_time = datetime.now() - timedelta(hours=hours)
            baseline_cutoff = datetime.now() - timedelta(hours=lookback_hours)
            
            # Aggregate mentions by source
            twitter_mentions = 0
            reddit_mentions = 0
            stocktwits_mentions = 0
            news_mentions = 0
            
            # Get tweets (includes Twitter and StockTwits messages with prefixes)
            tweets = self.repository.get_tweets_for_symbol(
                symbol, 
                hours=hours, 
                limit=self.config.max_query_limit
            )
            
            for tweet in tweets:
                if tweet.tweet_id.startswith("stocktwits_"):
                    stocktwits_mentions += 1
                elif tweet.tweet_id.startswith("news_"):
                    news_mentions += 1
                else:
                    # Assume Twitter if no prefix
                    twitter_mentions += 1
            
            # Get Reddit posts
            reddit_posts = self.repository.get_reddit_posts_for_symbol(
                symbol,
                hours=hours,
                limit=self.config.max_query_limit
            )
            reddit_mentions = len(reddit_posts)
            
            total_mentions = twitter_mentions + reddit_mentions + stocktwits_mentions + news_mentions
            
            if total_mentions == 0:
                logger.debug(f"No mentions found for {symbol} in the last {hours} hours")
                return None
            
            # Get baseline mentions for comparison
            baseline_mentions = self._get_baseline_mentions(
                symbol, 
                baseline_cutoff,
                hours
            )
            
            # Calculate trend and momentum
            volume_trend = self._calculate_volume_trend(
                total_mentions,
                baseline_mentions,
                hours
            )
            
            momentum_score = self._calculate_momentum(
                symbol,
                hours
            )
            
            # Detect spikes
            spike_detected, spike_magnitude = self._detect_spike(
                total_mentions,
                baseline_mentions
            )
            
            return MentionVolume(
                symbol=symbol,
                timestamp=datetime.now(),
                total_mentions=total_mentions,
                twitter_mentions=twitter_mentions,
                reddit_mentions=reddit_mentions,
                stocktwits_mentions=stocktwits_mentions,
                news_mentions=news_mentions,
                volume_trend=volume_trend,
                momentum_score=momentum_score,
                spike_detected=spike_detected,
                spike_magnitude=spike_magnitude
            )
            
        except ValueError as e:
            logger.error(f"Invalid input for mention volume query: {symbol}, error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting mention volume for {symbol}: {e}", exc_info=True)
            return None
    
    def _get_baseline_mentions(
        self,
        symbol: str,
        baseline_cutoff: datetime,
        window_hours: int
    ) -> float:
        """
        Get baseline average mentions for comparison
        
        Args:
            symbol: Stock symbol
            baseline_cutoff: Start of baseline period
            window_hours: Hours per baseline window
            
        Returns:
            Average mentions per window
        """
        try:
            # Get mentions in baseline period (excluding recent window)
            recent_cutoff = datetime.now() - timedelta(hours=window_hours)
            
            baseline_tweets = self.repository.get_tweets_for_symbol(
                symbol,
                hours=(datetime.now() - baseline_cutoff).total_seconds() / 3600,
                limit=self.config.volume_trend_max_limit
            )
            
            # Filter to baseline period (exclude recent window)
            baseline_tweets = [
                t for t in baseline_tweets 
                if t.created_at < recent_cutoff and t.created_at >= baseline_cutoff
            ]
            
            baseline_reddit = self.repository.get_reddit_posts_for_symbol(
                symbol,
                hours=(datetime.now() - baseline_cutoff).total_seconds() / 3600,
                limit=self.config.volume_trend_max_limit
            )
            baseline_reddit = [
                p for p in baseline_reddit
                if p.created_at < recent_cutoff and p.created_at >= baseline_cutoff
            ]
            
            baseline_total = len(baseline_tweets) + len(baseline_reddit)
            
            # Calculate average per window
            baseline_windows = (datetime.now() - baseline_cutoff).total_seconds() / 3600 / window_hours
            baseline_windows = max(1, baseline_windows)  # Avoid division by zero
            
            return baseline_total / baseline_windows
            
        except Exception as e:
            logger.warning(f"Error calculating baseline mentions: {e}")
            return 0.0
    
    def _calculate_volume_trend(
        self,
        current_mentions: int,
        baseline_avg: float,
        hours: int
    ) -> str:
        """
        Calculate volume trend direction
        
        Args:
            current_mentions: Current period mentions
            baseline_avg: Baseline average mentions
            hours: Hours in current period
            
        Returns:
            Trend direction: "up", "down", or "stable"
        """
        if baseline_avg == 0:
            return "stable" if current_mentions == 0 else "up"
        
        # Calculate mentions per hour
        current_rate = current_mentions / hours if hours > 0 else 0.0
        baseline_rate = baseline_avg / hours if hours > 0 else 0.0
        
        # Threshold: configurable percentage change (default 20%)
        threshold = self.config.volume_trend_change_threshold
        change_pct = (current_rate - baseline_rate) / baseline_rate if baseline_rate > 0 else 0.0
        
        if change_pct > threshold:
            return "up"
        elif change_pct < -threshold:
            return "down"
        else:
            return "stable"
    
    def _calculate_momentum(
        self,
        symbol: str,
        hours: int
    ) -> float:
        """
        Calculate mention momentum (acceleration/deceleration)
        
        Args:
            symbol: Stock symbol
            hours: Hours of recent data
            
        Returns:
            Momentum score (-1.0 to 1.0)
        """
        try:
            # Split recent period into two halves
            half_hours = hours / 2
            recent_cutoff = datetime.now() - timedelta(hours=half_hours)
            
            # Fetch all data once, then split in memory (fix redundant fetching)
            all_tweets = self.repository.get_tweets_for_symbol(
                symbol,
                hours=hours,
                limit=self.config.max_query_limit
            )
            all_reddit_posts = self.repository.get_reddit_posts_for_symbol(
                symbol,
                hours=hours,
                limit=self.config.max_query_limit
            )
            
            # Split into first and second half in memory
            first_half_tweets = [t for t in all_tweets if t.created_at < recent_cutoff]
            first_half_reddit = [p for p in all_reddit_posts if p.created_at < recent_cutoff]
            first_half_total = len(first_half_tweets) + len(first_half_reddit)
            
            second_half_tweets = [t for t in all_tweets if t.created_at >= recent_cutoff]
            second_half_reddit = [p for p in all_reddit_posts if p.created_at >= recent_cutoff]
            second_half_total = len(second_half_tweets) + len(second_half_reddit)
            
            # Calculate momentum
            if first_half_total == 0:
                return 1.0 if second_half_total > 0 else 0.0
            
            growth_rate = (second_half_total - first_half_total) / first_half_total
            momentum = min(1.0, max(-1.0, growth_rate))
            
            return momentum
            
        except Exception as e:
            logger.warning(f"Error calculating momentum: {e}")
            return 0.0
    
    def _detect_spike(
        self,
        current_mentions: int,
        baseline_avg: float
    ) -> Tuple[bool, float]:
        """
        Detect if there's a mention spike
        
        Args:
            current_mentions: Current period mentions
            baseline_avg: Baseline average mentions
            
        Returns:
            Tuple of (spike_detected: bool, spike_magnitude: float)
        """
        if baseline_avg == 0:
            return (current_mentions > 0, float('inf') if current_mentions > 0 else 0.0)
        
        magnitude = current_mentions / baseline_avg if baseline_avg > 0 else 0.0
        
        # Spike threshold: configurable (default 2x baseline)
        spike_detected = magnitude >= self.config.spike_threshold
        
        return (spike_detected, magnitude)
    
    def get_volume_trend(
        self,
        symbol: str,
        hours: int = 24,
        interval_hours: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get mention volume trend over time
        
        Args:
            symbol: Stock symbol
            hours: Total hours of historical data
            interval_hours: Interval between data points
            
        Returns:
            List of volume data points
        """
        if not self.is_available():
            return []
        
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            interval_seconds = interval_hours * 3600
            
            # Use configured limit instead of hardcoded value
            max_limit = self.config.volume_trend_max_limit
            
            # Get mentions in the period (database already filters by cutoff via hours parameter)
            tweets = self.repository.get_tweets_for_symbol(
                symbol,
                hours=hours,
                limit=max_limit
            )
            
            reddit_posts = self.repository.get_reddit_posts_for_symbol(
                symbol,
                hours=hours,
                limit=max_limit
            )
            
            # Group by time intervals
            grouped = defaultdict(int)
            
            for tweet in tweets:
                if tweet.created_at < cutoff:
                    continue
                interval_key = int((tweet.created_at - cutoff).total_seconds() / interval_seconds)
                grouped[interval_key] += 1
            
            for post in reddit_posts:
                if post.created_at < cutoff:
                    continue
                interval_key = int((post.created_at - cutoff).total_seconds() / interval_seconds)
                grouped[interval_key] += 1
            
            # Build trend data points
            trend_points = []
            for interval_key in sorted(grouped.keys()):
                timestamp = cutoff + timedelta(seconds=interval_key * interval_seconds)
                trend_points.append({
                    "timestamp": timestamp.isoformat(),
                    "mentions": grouped[interval_key],
                    "interval_hours": interval_hours
                })
            
            return trend_points
            
        except Exception as e:
            logger.error(f"Error getting volume trend for {symbol}: {e}", exc_info=True)
            return []
    
    def get_trending_by_volume(
        self,
        hours: int = 24,
        min_mentions: int = 10,
        min_momentum: float = 0.3,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get symbols trending by mention volume
        
        Args:
            hours: Hours of data to analyze
            min_mentions: Minimum mentions required
            min_momentum: Minimum momentum score
            limit: Maximum results to return
            
        Returns:
            List of trending symbols with volume metrics
        """
        if not self.is_available():
            return []
        
        try:
            # Get trending symbols from repository (aggregated from all sources)
            trending = self.repository.get_trending_symbols(
                hours=hours,
                min_mentions=min_mentions,
                limit=limit * 2  # Get more, then filter by momentum
            )
            
            # Enhance with volume metrics
            # Batch process symbols to reduce individual queries (mitigate N+1)
            result = []
            symbols_to_process = [symbol_data['symbol'] for symbol_data in trending]
            
            # Process in batches to balance memory and query efficiency
            batch_size = self.config.batch_size
            for i in range(0, len(symbols_to_process), batch_size):
                batch_symbols = symbols_to_process[i:i + batch_size]
                batch_data = {sd['symbol']: sd for sd in trending if sd['symbol'] in batch_symbols}
                
                for symbol in batch_symbols:
                    try:
                        volume_data = self.get_mention_volume(symbol, hours=hours)
                        
                        if volume_data and volume_data.momentum_score >= min_momentum:
                            symbol_data = batch_data[symbol]
                            result.append({
                                "symbol": symbol,
                                "total_mentions": volume_data.total_mentions,
                                "twitter_mentions": volume_data.twitter_mentions,
                                "reddit_mentions": volume_data.reddit_mentions,
                                "stocktwits_mentions": volume_data.stocktwits_mentions,
                                "news_mentions": volume_data.news_mentions,
                                "volume_trend": volume_data.volume_trend,
                                "momentum_score": volume_data.momentum_score,
                                "spike_detected": volume_data.spike_detected,
                                "spike_magnitude": volume_data.spike_magnitude,
                                "average_sentiment": symbol_data.get('average_sentiment', 0.0),
                                "last_mentioned": symbol_data.get('last_mentioned')
                            })
                    except Exception as e:
                        logger.warning(f"Error processing volume for {symbol}: {e}")
                        continue
            
            # Sort by momentum, then by mentions
            result.sort(
                key=lambda x: (x['momentum_score'], x['total_mentions']),
                reverse=True
            )
            
            return result[:limit]
            
        except Exception as e:
            logger.error(f"Error getting trending by volume: {e}", exc_info=True)
            return []

