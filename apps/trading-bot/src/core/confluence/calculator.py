"""
Confluence Calculator
====================

Calculates unified confluence scores by combining technical indicators,
sentiment analysis, and options flow data.
"""

import logging
from typing import Dict, Optional, List, Any, Tuple
from datetime import datetime
import pandas as pd
import numpy as np

from ...config.settings import settings
from .models import (
    ConfluenceScore,
    ConfluenceBreakdown,
    ConfluenceLevel,
    TechnicalScore,
    SentimentScore,
    OptionsFlowScore
)
from ..strategy.base import TechnicalIndicators

logger = logging.getLogger(__name__)


class ConfluenceCalculator:
    """
    Calculates confluence scores combining multiple data sources
    
    Combines:
    - Technical indicators (RSI, SMA, Volume, Bollinger Bands)
    - Sentiment analysis (aggregated from multiple sources)
    - Options flow data (Unusual Whales or similar)
    
    Features:
    - Weighted multi-factor scoring
    - Configurable component weights
    - Confluence thresholds for trade filtering
    - Detailed breakdown for analysis
    """
    
    def __init__(
        self,
        use_sentiment: Optional[bool] = None,
        use_options_flow: Optional[bool] = None
    ):
        """
        Initialize confluence calculator
        
        Args:
            use_sentiment: Whether to include sentiment (default: from settings)
            use_options_flow: Whether to include options flow (default: from settings)
        """
        self.config = settings.confluence
        self.indicators = TechnicalIndicators()
        
        # Override settings if provided
        self.use_sentiment = use_sentiment if use_sentiment is not None else self.config.use_sentiment
        self.use_options_flow = use_options_flow if use_options_flow is not None else self.config.use_options_flow
        
        # Lazy-loaded dependencies
        self._sentiment_aggregator = None
        self._options_flow_provider = None
        
        # Cache
        self.cache: Dict[str, tuple] = {}  # key -> (data, timestamp)
        
        logger.info(
            f"ConfluenceCalculator initialized "
            f"(sentiment={'enabled' if self.use_sentiment else 'disabled'}, "
            f"options_flow={'enabled' if self.use_options_flow else 'disabled'})"
        )
    
    def _get_sentiment_aggregator(self):
        """Lazy-load sentiment aggregator"""
        if self._sentiment_aggregator is None:
            try:
                from ...data.providers.sentiment import SentimentAggregator
                self._sentiment_aggregator = SentimentAggregator(persist_to_db=True)
                logger.debug("Sentiment aggregator initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize sentiment aggregator: {e}")
                return None
        return self._sentiment_aggregator
    
    def _get_unusual_whales_manager(self):
        """Lazy-load Unusual Whales manager"""
        if self._unusual_whales_manager is None:
            try:
                from ...data.providers.unusual_whales import UnusualWhalesManager
                self._unusual_whales_manager = UnusualWhalesManager()
                logger.debug("Unusual Whales manager initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Unusual Whales manager: {e}")
                return None
        return self._unusual_whales_manager
    
    def calculate_confluence(
        self,
        symbol: str,
        market_data: pd.DataFrame,
        sentiment_hours: int = 24
    ) -> Optional[ConfluenceScore]:
        """
        Calculate confluence score for a symbol
        
        Args:
            symbol: Stock symbol
            market_data: DataFrame with OHLCV data (columns: open, high, low, close, volume)
            sentiment_hours: Hours of sentiment data to analyze
            
        Returns:
            ConfluenceScore object or None if insufficient data
        """
        symbol = symbol.upper()
        
        # Check cache
        cache_key = f"confluence_{symbol}"
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < self.config.cache_ttl:
                logger.debug(f"Returning cached confluence for {symbol}")
                return data
            else:
                del self.cache[cache_key]
        
        # Validate market data
        if market_data is None or len(market_data) < 20:
            logger.warning(f"Insufficient market data for {symbol}")
            return None
        
        required_columns = ['close']
        missing = [col for col in required_columns if col not in market_data.columns]
        if missing:
            logger.warning(f"Missing required columns for {symbol}: {missing}")
            return None
        
        # Calculate technical score
        technical_score = self._calculate_technical_score(symbol, market_data)
        
        # Get sentiment score
        sentiment_score = None
        if self.use_sentiment:
            sentiment_score = self._get_sentiment_score(symbol, sentiment_hours)
        
        # Get options flow score
        options_flow_score = None
        if self.use_options_flow:
            options_flow_score = self._get_options_flow_score(symbol)
        
        # Calculate weighted confluence
        confluence_score, breakdown = self._combine_scores(
            technical_score,
            sentiment_score,
            options_flow_score
        )
        
        # Determine directional bias (weighted average of component directions)
        directional_bias = self._calculate_directional_bias(
            technical_score,
            sentiment_score,
            options_flow_score,
            breakdown
        )
        
        # Determine confluence level
        confluence_level = self._score_to_level(confluence_score)
        
        # Build components used list
        components_used = ['technical']
        if sentiment_score:
            components_used.append('sentiment')
        if options_flow_score:
            components_used.append('options_flow')
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(breakdown)
        
        # Check thresholds
        meets_minimum = confluence_score >= self.config.min_confluence
        meets_high = confluence_score >= self.config.high_confluence
        
        # Create confluence score
        result = ConfluenceScore(
            symbol=symbol,
            timestamp=datetime.now(),
            confluence_score=confluence_score,
            directional_bias=directional_bias,
            confluence_level=confluence_level,
            breakdown=breakdown,
            components_used=components_used,
            confidence=confidence,
            volume_trend="stable",  # TODO: Calculate from historical data
            meets_minimum_threshold=meets_minimum,
            meets_high_threshold=meets_high,
            metadata={}
        )
        
        # Cache result
        self.cache[cache_key] = (result, datetime.now())
        
        logger.info(
            f"Confluence for {symbol}: {confluence_score:.3f} "
            f"({confluence_level.value}) - "
            f"directional bias: {directional_bias:+.3f}"
        )
        
        return result
    
    def _calculate_technical_score(
        self,
        symbol: str,
        data: pd.DataFrame
    ) -> TechnicalScore:
        """
        Calculate technical analysis score
        
        Args:
            symbol: Stock symbol
            data: OHLCV DataFrame
            
        Returns:
            TechnicalScore object
        """
        close = data['close']
        
        # RSI score (-1.0 to 1.0: oversold = -1, overbought = +1, neutral = 0)
        rsi = self.indicators.rsi(close)
        current_rsi = float(rsi.iloc[-1]) if len(rsi) > 0 else 50.0
        # Normalize: 0-30 = -1 to 0, 30-70 = -1 to +1 (centered), 70-100 = 0 to +1
        if current_rsi <= 30:
            rsi_score = (current_rsi / 30) - 1.0  # -1.0 to 0.0
        elif current_rsi <= 70:
            rsi_score = ((current_rsi - 50) / 20)  # -1.0 to +1.0
        else:
            rsi_score = ((current_rsi - 70) / 30)  # 0.0 to +1.0
        
        # SMA trend score
        sma_short = self.indicators.sma(close, 20)
        sma_long = self.indicators.sma(close, 200) if len(close) >= 200 else self.indicators.sma(close, 50)
        
        current_price = float(close.iloc[-1])
        current_sma_short = float(sma_short.iloc[-1]) if len(sma_short) > 0 else current_price
        current_sma_long = float(sma_long.iloc[-1]) if len(sma_long) > 0 else current_price
        
        # Positive if price > both SMAs (bullish), negative if below (bearish)
        price_vs_sma_short = (current_price - current_sma_short) / current_sma_short
        price_vs_sma_long = (current_price - current_sma_long) / current_sma_long
        
        # Combined SMA trend: weight short-term more
        sma_trend_score = (price_vs_sma_short * 0.6 + price_vs_sma_long * 0.4) * 10  # Scale to -1 to +1
        
        # Volume score
        volume_score = 0.0
        if 'volume' in data.columns:
            volume = data['volume']
            obv = self.indicators.obv(close, volume)
            obv_slope = self.indicators.obv_slope(obv)
            
            if len(obv_slope) > 0:
                current_slope = float(obv_slope.iloc[-1])
                # Normalize: positive slope = bullish, negative = bearish
                # Use logarithmic scaling for volume changes
                volume_score = np.sign(current_slope) * min(abs(current_slope) / 1000000, 1.0)
        
        # Bollinger Bands score
        bollinger_score = 0.0
        try:
            bb = self.indicators.bollinger_bands(close)
            upper = float(bb['upper'].iloc[-1]) if len(bb['upper']) > 0 else current_price
            lower = float(bb['lower'].iloc[-1]) if len(bb['lower']) > 0 else current_price
            middle = float(bb['middle'].iloc[-1]) if len(bb['middle']) > 0 else current_price
            
            # Score: -1 if at lower band, 0 at middle, +1 at upper band
            band_range = upper - lower
            if band_range > 0:
                bollinger_score = ((current_price - middle) / (band_range / 2))
                bollinger_score = max(-1.0, min(1.0, bollinger_score))
        except Exception as e:
            logger.debug(f"Error calculating Bollinger Bands for {symbol}: {e}")
        
        # Calculate weighted overall technical score
        overall_score = (
            rsi_score * self.config.weight_rsi +
            sma_trend_score * self.config.weight_sma_trend +
            volume_score * self.config.weight_volume +
            bollinger_score * self.config.weight_bollinger
        )
        overall_score = max(-1.0, min(1.0, overall_score))
        
        return TechnicalScore(
            overall_score=overall_score,
            rsi_score=rsi_score,
            sma_trend_score=sma_trend_score,
            volume_score=volume_score,
            bollinger_score=bollinger_score,
            indicators={
                'rsi': current_rsi,
                'sma_short': current_sma_short,
                'sma_long': current_sma_long,
                'price': current_price
            }
        )
    
    def _get_sentiment_score(
        self,
        symbol: str,
        hours: int
    ) -> Optional[SentimentScore]:
        """Get sentiment score from aggregator"""
        aggregator = self._get_sentiment_aggregator()
        if aggregator is None:
            return None
        
        try:
            aggregated = aggregator.get_aggregated_sentiment(symbol, hours=hours)
            if aggregated:
                return SentimentScore(
                    score=aggregated.unified_sentiment,
                    confidence=aggregated.confidence,
                    source_count=aggregated.source_count,  # Fixed: use source_count instead of provider_count
                    divergence_detected=aggregated.divergence_detected
                )
        except Exception as e:
            logger.warning(f"Error getting sentiment for {symbol}: {e}")
        
        return None
    
    def _get_options_flow_score(
        self,
        symbol: str
    ) -> Optional[OptionsFlowScore]:
        """Get options flow score from options flow sentiment provider"""
        provider = self._get_options_flow_provider()
        if provider is None or not provider.is_available():
            return None
        
        try:
            # Get sentiment from options flow provider
            sentiment = provider.get_sentiment(symbol, hours=24)
            if sentiment:
                return OptionsFlowScore(
                    score=sentiment.weighted_sentiment,
                    confidence=sentiment.confidence,
                    flow_ratio=None,  # Can be enhanced later
                    unusual_activity=None  # Can be enhanced later
                )
        except Exception as e:
            logger.debug(f"Error getting options flow score for {symbol}: {e}")
        
        return None
    
    def _combine_scores(
        self,
        technical: TechnicalScore,
        sentiment: Optional[SentimentScore],
        options_flow: Optional[OptionsFlowScore]
    ) -> Tuple[float, ConfluenceBreakdown]:
        """
        Combine component scores into unified confluence score
        
        Returns:
            Tuple of (confluence_score, breakdown)
        """
        # Normalize weights based on what's available
        weight_technical = self.config.weight_technical
        weight_sentiment = self.config.weight_sentiment if sentiment else 0.0
        weight_options_flow = self.config.weight_options_flow if options_flow else 0.0
        
        # Renormalize weights to sum to 1.0
        total_weight = weight_technical + weight_sentiment + weight_options_flow
        if total_weight == 0:
            logger.warning("All component weights are zero")
            return 0.0, self._create_empty_breakdown(technical, sentiment, options_flow)
        
        weight_technical /= total_weight
        weight_sentiment /= total_weight
        weight_options_flow /= total_weight
        
        # Calculate directional contributions (absolute values for confluence strength)
        technical_contribution = abs(technical.overall_score) * weight_technical
        sentiment_contribution = abs(sentiment.score) * weight_sentiment if sentiment else 0.0
        options_flow_contribution = abs(options_flow.score) * weight_options_flow if options_flow else 0.0
        
        # Confluence score: weighted average of absolute component strengths
        # This measures how strongly the signals agree (confluence strength)
        confluence_score = (
            technical_contribution +
            sentiment_contribution +
            options_flow_contribution
        )
        
        # Clamp to 0-1 range
        confluence_score = max(0.0, min(1.0, confluence_score))
        
        # Create breakdown
        breakdown = ConfluenceBreakdown(
            technical_score=technical,
            sentiment_score=sentiment,
            options_flow_score=options_flow,
            technical_contribution=technical_contribution,
            sentiment_contribution=sentiment_contribution,
            options_flow_contribution=options_flow_contribution,
            technical_raw=technical.overall_score,
            sentiment_raw=sentiment.score if sentiment else None,
            options_flow_raw=options_flow.score if options_flow else None
        )
        
        return confluence_score, breakdown
    
    def _calculate_directional_bias(
        self,
        technical: TechnicalScore,
        sentiment: Optional[SentimentScore],
        options_flow: Optional[OptionsFlowScore],
        breakdown: ConfluenceBreakdown
    ) -> float:
        """
        Calculate overall directional bias (-1.0 bearish to +1.0 bullish)
        
        This is the weighted average of component directions, not their strength
        """
        weight_technical = breakdown.technical_contribution
        weight_sentiment = breakdown.sentiment_contribution
        weight_options_flow = breakdown.options_flow_contribution
        
        total_weight = weight_technical + weight_sentiment + weight_options_flow
        if total_weight == 0:
            return 0.0
        
        # Weighted average of directions
        directional_sum = (
            technical.overall_score * weight_technical +
            (sentiment.score if sentiment else 0.0) * weight_sentiment +
            (options_flow.score if options_flow else 0.0) * weight_options_flow
        )
        
        return directional_sum / total_weight
    
    def _calculate_confidence(self, breakdown: ConfluenceBreakdown) -> float:
        """Calculate overall confidence in the confluence score"""
        # Average of component confidences, weighted by contribution
        confidences = []
        weights = []
        
        # Technical always has some confidence (1.0)
        confidences.append(1.0)
        weights.append(breakdown.technical_contribution)
        
        if breakdown.sentiment_score:
            confidences.append(breakdown.sentiment_score.confidence)
            weights.append(breakdown.sentiment_contribution)
        
        if breakdown.options_flow_score:
            # Options flow confidence assumed to be moderate-high
            confidences.append(0.7)
            weights.append(breakdown.options_flow_contribution)
        
        if not weights:
            return 0.0
        
        # Weighted average
        total_weight = sum(weights)
        if total_weight == 0:
            return 0.0
        
        weighted_confidence = sum(c * w for c, w in zip(confidences, weights))
        return weighted_confidence / total_weight
    
    def _create_empty_breakdown(
        self,
        technical: TechnicalScore,
        sentiment: Optional[SentimentScore],
        options_flow: Optional[OptionsFlowScore]
    ) -> ConfluenceBreakdown:
        """Create empty breakdown for error cases"""
        return ConfluenceBreakdown(
            technical_score=technical,
            sentiment_score=sentiment,
            options_flow_score=options_flow,
            technical_contribution=0.0,
            sentiment_contribution=0.0,
            options_flow_contribution=0.0,
            technical_raw=technical.overall_score,
            sentiment_raw=sentiment.score if sentiment else None,
            options_flow_raw=options_flow.score if options_flow else None
        )
    
    def _score_to_level(self, score: float) -> ConfluenceLevel:
        """Convert confluence score to level"""
        if score >= 0.85:
            return ConfluenceLevel.VERY_HIGH
        elif score >= 0.7:
            return ConfluenceLevel.HIGH
        elif score >= 0.5:
            return ConfluenceLevel.MODERATE
        elif score >= 0.3:
            return ConfluenceLevel.LOW
        else:
            return ConfluenceLevel.VERY_LOW

