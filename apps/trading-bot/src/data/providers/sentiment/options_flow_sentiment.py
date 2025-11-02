"""
Options Flow Sentiment Provider
================================

Provides sentiment scoring based on options flow data.
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta

from ....config.settings import settings
from ..unusual_whales import UnusualWhalesClient, OptionsFlow, FlowDirection
from ...options.pattern_detector import PatternDetector
from ...options.metrics_calculator import OptionsMetricsCalculator
from .models import SymbolSentiment, SentimentLevel
from ....utils.cache import get_cache_manager
from ....utils.rate_limiter import get_rate_limiter
from ....utils.monitoring import get_usage_monitor

logger = logging.getLogger(__name__)


class OptionsFlowSentimentProvider:
    """
    Sentiment provider based on options flow data
    
    Analyzes options flow patterns, put/call ratios, and unusual activity
    to generate sentiment scores.
    """
    
    def __init__(self, persist_to_db: bool = True):
        """
        Initialize options flow sentiment provider
        
        Args:
            persist_to_db: Whether to persist data to database (default: True)
        """
        self.config = settings.unusual_whales
        self.client = None
        self.pattern_detector = PatternDetector()
        self.metrics_calculator = OptionsMetricsCalculator()
        self.cache = get_cache_manager()
        self.cache_ttl = 300  # 5 minutes
        self.rate_limiter = get_rate_limiter("options")
        self.usage_monitor = get_usage_monitor()
        self.persist_to_db = persist_to_db
        
        # Initialize client if API key available
        if self.config.api_key:
            try:
                self.client = UnusualWhalesClient(self.config.api_key, self.config.base_url)
                logger.info("OptionsFlowSentimentProvider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Unusual Whales client: {e}")
        else:
            logger.warning("Unusual Whales API key not configured")
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        return self.client is not None and self.config.api_key is not None
    
    def get_sentiment(self, symbol: str, hours: int = 24) -> Optional[SymbolSentiment]:
        """
        Get sentiment for a symbol based on options flow
        
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
            track_provider_availability("options", is_available)
        except (ImportError, Exception) as e:
            logger.debug(f"Could not record availability metric: {e}")
        
        if not is_available:
            logger.warning("Options flow provider not available")
            return None
        
        # Check rate limit (100 requests per minute)
        is_allowed, rate_status = self.rate_limiter.check_rate_limit(limit=100, window_seconds=60)
        if not is_allowed:
            logger.warning(f"Options rate limit exceeded for {symbol}, waiting...")
            rate_status = self.rate_limiter.wait_if_needed(limit=100, window_seconds=60)
            if rate_status.is_limited:
                logger.error(f"Options rate limit still exceeded after wait")
                # Record rate limit hit metric
                try:
                    from ...utils.metrics_providers_helpers import track_rate_limit_hit
                    track_rate_limit_hit("options")
                except (ImportError, Exception) as e:
                    logger.debug(f"Could not record rate limit metric: {e}")
                self.usage_monitor.record_request("options", success=False)
                return None
        
        # Track API call timing
        import time
        api_start_time = time.time()
        
        # Check cache
        cache_key = f"options_sentiment_{symbol}_{hours}"
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"Returning cached options sentiment for {symbol}")
            # Track data freshness
            try:
                from ...utils.metrics_providers_helpers import track_cache_freshness
                track_cache_freshness("options", "get_sentiment", cached)
            except (ImportError, Exception) as e:
                logger.debug(f"Could not record data freshness metric: {e}")
            self.usage_monitor.record_request("options", success=True, cached=True)
            return cached
        
        try:
            # Get options flow data (using asyncio for async client)
            import asyncio
            
            async def fetch_flows():
                async with self.client as client:
                    return await client.get_options_flow(symbol, hours=hours)
            
            # Run async function in sync context
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            flows = loop.run_until_complete(fetch_flows())
            
            # Record API response time
            api_response_time = time.time() - api_start_time
            
            if not flows:
                logger.info(f"No options flow data for {symbol}")
                return None
            
            # Detect patterns
            flows = self.pattern_detector.detect_patterns(flows)
            
            # Calculate metrics
            metrics = self.metrics_calculator.calculate_flow_metrics(flows)
            pc_ratios = self.metrics_calculator.calculate_put_call_ratio(flows)
            
            # Calculate sentiment score
            sentiment_score = self._calculate_sentiment_score(flows, metrics, pc_ratios)
            
            # Calculate confidence
            confidence = self._calculate_confidence(flows, metrics)
            
            # Determine sentiment level
            sentiment_level = self._score_to_level(sentiment_score)
            
            # Create sentiment object
            sentiment = SymbolSentiment(
                symbol=symbol.upper(),
                timestamp=datetime.now(),
                mention_count=len(flows),
                average_sentiment=sentiment_score,
                weighted_sentiment=sentiment_score,
                influencer_sentiment=None,
                engagement_score=metrics.total_premium / 1000000.0,  # Normalize premium
                sentiment_level=sentiment_level,
                confidence=confidence,
                volume_trend="stable",
                tweets=[]  # Not applicable for options flow
            )
            
            # Cache result
            self._set_cache(cache_key, sentiment)
            
            # Record API response time (already calculated above)
            try:
                from ...utils.metrics_providers import record_provider_response_time
                record_provider_response_time("options", api_response_time)
            except (ImportError, Exception) as e:
                logger.debug(f"Could not record response time metric: {e}")
            
            # Record successful request with response time
            self.usage_monitor.record_request("options", success=True, cached=False, response_time=api_response_time)
            
            logger.info(
                f"Options flow sentiment for {symbol}: {sentiment_score:.3f} "
                f"({sentiment_level.value}) - {len(flows)} flows"
            )
            
            return sentiment
            
        except Exception as e:
            logger.error(f"Error getting options flow sentiment for {symbol}: {e}", exc_info=True)
            return None
    
    def _calculate_sentiment_score(
        self,
        flows: List[OptionsFlow],
        metrics,
        pc_ratios
    ) -> float:
        """
        Calculate sentiment score from options flow data
        
        Args:
            flows: List of options flows
            metrics: FlowMetrics object
            pc_ratios: PutCallRatios object
            
        Returns:
            Sentiment score between -1.0 and 1.0
        """
        # Base score from flow direction
        flow_score = (metrics.bullish_flow - metrics.bearish_flow)
        
        # Put/call ratio adjustment
        # Low P/C ratio (< 0.7) = bullish, High P/C ratio (> 1.3) = bearish
        pc_ratio = pc_ratios.volume_ratio
        if pc_ratio < 0.7:
            pc_score = 0.3  # Bullish
        elif pc_ratio > 1.3:
            pc_score = -0.3  # Bearish
        else:
            pc_score = 0.0
        
        # Sweep/block adjustment
        sweep_adjustment = 0.0
        if metrics.sweep_count > 0:
            # Average sweep strength
            sweeps = [f for f in flows if f.is_sweep]
            if sweeps:
                avg_strength = sum(f.sweep_strength for f in sweeps) / len(sweeps)
                # Bullish sweeps (calls) vs bearish sweeps (puts)
                call_sweeps = sum(1 for f in sweeps if f.option_type == "call")
                put_sweeps = sum(1 for f in sweeps if f.option_type == "put")
                if call_sweeps > put_sweeps:
                    sweep_adjustment = 0.2 * avg_strength
                elif put_sweeps > call_sweeps:
                    sweep_adjustment = -0.2 * avg_strength
        
        block_adjustment = 0.0
        if metrics.block_count > 0:
            blocks = [f for f in flows if f.is_block]
            call_blocks = sum(1 for f in blocks if f.option_type == "call")
            put_blocks = sum(1 for f in blocks if f.option_type == "put")
            if call_blocks > put_blocks:
                block_adjustment = 0.15
            elif put_blocks > call_blocks:
                block_adjustment = -0.15
        
        # Combine scores
        final_score = (
            flow_score * 0.5 +
            pc_score * 0.3 +
            sweep_adjustment * 0.1 +
            block_adjustment * 0.1
        )
        
        return max(-1.0, min(1.0, final_score))
    
    def _calculate_confidence(self, flows: List[OptionsFlow], metrics) -> float:
        """
        Calculate confidence in sentiment score
        
        Args:
            flows: List of options flows
            metrics: FlowMetrics object
            
        Returns:
            Confidence between 0.0 and 1.0
        """
        # Base confidence from volume
        volume_confidence = min(metrics.total_volume / 10000, 1.0)
        
        # Premium confidence
        premium_confidence = min(metrics.total_premium / 5000000, 1.0)  # Max at $5M
        
        # Pattern confidence (sweeps/blocks indicate conviction)
        pattern_confidence = min(
            (metrics.sweep_count * 0.1 + metrics.block_count * 0.15),
            1.0
        )
        
        # Average confidence
        confidence = (volume_confidence * 0.4 + premium_confidence * 0.4 + pattern_confidence * 0.2)
        
        return max(0.0, min(1.0, confidence))
    
    def _get_from_cache(self, key: str) -> Optional[SymbolSentiment]:
        """Get data from cache using Redis-backed cache manager"""
        cache_key = f"options:{key}"
        return self.cache.get(cache_key)
    
    def _set_cache(self, key: str, data: SymbolSentiment):
        """Store data in cache using Redis-backed cache manager"""
        cache_key = f"options:{key}"
        self.cache.set(cache_key, data, ttl=self.cache_ttl)
    
    def _score_to_level(self, score: float) -> SentimentLevel:
        """Convert sentiment score to sentiment level"""
        if score >= 0.6:
            return SentimentLevel.VERY_BULLISH
        elif score >= 0.2:
            return SentimentLevel.BULLISH
        elif score >= -0.2:
            return SentimentLevel.NEUTRAL
        elif score >= -0.6:
            return SentimentLevel.BEARISH
        else:
            return SentimentLevel.VERY_BEARISH

