"""
Sentiment Analyst Agent (T7: Analyst Agents)
=============================================

Analyzes social media sentiment, options flow, and other sentiment indicators
to produce trading recommendations.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .base import (
    AnalystAgent,
    AnalystConfidence,
    AnalystRecommendation,
    AnalystReport,
    SignalStrength,
)

logger = logging.getLogger(__name__)


class SentimentAnalyst(AnalystAgent):
    """
    Sentiment analysis agent that evaluates market sentiment from multiple sources.

    Analyzes:
    - Social media sentiment (Twitter, Reddit, StockTwits)
    - Options flow sentiment
    - Analyst ratings
    - Insider trading signals
    - News sentiment
    """

    def __init__(
        self,
        name: str = "Sentiment Analyst",
        min_confidence: float = 0.3,
        divergence_penalty: float = 0.2,
    ):
        """
        Initialize Sentiment Analyst.

        Args:
            name: Analyst name
            min_confidence: Minimum confidence threshold for including data
            divergence_penalty: Penalty applied when sources diverge
        """
        super().__init__(name=name, analyst_type="sentiment")

        self.min_confidence = min_confidence
        self.divergence_penalty = divergence_penalty
        self._aggregator = None

    @property
    def aggregator(self):
        """Lazy load sentiment aggregator"""
        if self._aggregator is None:
            try:
                from ...data.providers.sentiment.aggregator import SentimentAggregator
                self._aggregator = SentimentAggregator()
            except ImportError:
                logger.warning("SentimentAggregator not available")
        return self._aggregator

    async def analyze(
        self,
        symbol: str,
        aggregated_sentiment: Optional[Any] = None,
        **kwargs,
    ) -> AnalystReport:
        """
        Analyze sentiment for a symbol.

        Args:
            symbol: Trading symbol to analyze
            aggregated_sentiment: Optional pre-aggregated sentiment data
            **kwargs: Additional parameters

        Returns:
            AnalystReport with sentiment analysis results
        """
        try:
            # Get aggregated sentiment if not provided
            if aggregated_sentiment is None and self.aggregator is not None:
                aggregated_sentiment = await self.aggregator.get_sentiment(symbol)

            if aggregated_sentiment is None:
                return self._create_empty_report(symbol, "No sentiment data available")

            # Extract sentiment components
            components = self._extract_components(aggregated_sentiment)

            # Analyze each component
            social_analysis = self._analyze_social_sentiment(components)
            options_analysis = self._analyze_options_sentiment(components)
            overall_analysis = self._analyze_overall_sentiment(aggregated_sentiment)

            # Combine analyses
            combined = self._combine_analyses(
                social_analysis,
                options_analysis,
                overall_analysis,
                aggregated_sentiment,
            )

            # Build key factors
            key_factors = []
            warnings = []

            if overall_analysis["signal"] != "neutral":
                key_factors.append(f"Overall sentiment: {overall_analysis['signal']} ({overall_analysis['score']:.2f})")

            if social_analysis.get("twitter_signal"):
                key_factors.append(f"Twitter: {social_analysis['twitter_signal']}")
            if social_analysis.get("reddit_signal"):
                key_factors.append(f"Reddit: {social_analysis['reddit_signal']}")
            if options_analysis.get("signal") and options_analysis["signal"] != "neutral":
                key_factors.append(f"Options flow: {options_analysis['signal']}")

            # Add warnings
            if aggregated_sentiment.divergence_detected:
                warnings.append(f"Sentiment divergence detected (score: {aggregated_sentiment.divergence_score:.2f})")
            if aggregated_sentiment.source_count < 2:
                warnings.append(f"Limited data sources ({aggregated_sentiment.source_count})")
            if aggregated_sentiment.confidence < 0.4:
                warnings.append(f"Low confidence data ({aggregated_sentiment.confidence:.2f})")

            # Determine expiration (sentiment data has shorter validity)
            expires_at = datetime.now() + timedelta(hours=1)

            # Build report
            return AnalystReport(
                analyst_name=self.name,
                analyst_type=self.analyst_type,
                symbol=symbol,
                recommendation=self._score_to_recommendation(combined["score"]),
                confidence=self._score_to_confidence(combined["confidence"]),
                confidence_score=combined["confidence"],
                signal_strength=self._score_to_signal_strength(combined["score"]),
                directional_bias=combined["bias"],
                summary=self._generate_summary(aggregated_sentiment, combined),
                key_factors=key_factors,
                warnings=warnings,
                metrics={
                    "unified_sentiment": aggregated_sentiment.unified_sentiment,
                    "confidence": aggregated_sentiment.confidence,
                    "source_count": aggregated_sentiment.source_count,
                    "total_mentions": aggregated_sentiment.total_mentions,
                    "divergence_score": aggregated_sentiment.divergence_score,
                    "twitter_sentiment": aggregated_sentiment.twitter_sentiment,
                    "reddit_sentiment": aggregated_sentiment.reddit_sentiment,
                    "options_sentiment": aggregated_sentiment.options_sentiment,
                    "volume_trend": aggregated_sentiment.volume_trend,
                },
                raw_data={
                    "social_analysis": social_analysis,
                    "options_analysis": options_analysis,
                    "overall_analysis": overall_analysis,
                    "providers_used": aggregated_sentiment.providers_used,
                    "source_breakdown": aggregated_sentiment.source_breakdown,
                },
                expires_at=expires_at,
                data_freshness_seconds=0.0,
            )

        except Exception as e:
            logger.error(f"Sentiment analysis error for {symbol}: {e}", exc_info=True)
            return self._create_empty_report(symbol, f"Analysis error: {str(e)}")

    def _extract_components(self, aggregated: Any) -> Dict[str, Any]:
        """Extract sentiment components from aggregated data"""
        return {
            "unified": aggregated.unified_sentiment,
            "twitter": aggregated.twitter_sentiment,
            "reddit": aggregated.reddit_sentiment,
            "stocktwits": aggregated.stocktwits_sentiment,
            "options": aggregated.options_sentiment,
            "confidence": aggregated.confidence,
            "divergence": aggregated.divergence_score,
            "mentions": aggregated.total_mentions,
            "sources": aggregated.sources if hasattr(aggregated, "sources") else {},
        }

    def _analyze_social_sentiment(self, components: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze social media sentiment"""
        analysis = {
            "score": 0.0,
            "signal": "neutral",
            "twitter_signal": None,
            "reddit_signal": None,
        }

        scores = []
        weights = []

        # Twitter sentiment
        if components.get("twitter") is not None:
            twitter = components["twitter"]
            analysis["twitter_signal"] = self._sentiment_to_signal(twitter)
            scores.append(twitter)
            weights.append(0.5)  # Higher weight for Twitter

        # Reddit sentiment
        if components.get("reddit") is not None:
            reddit = components["reddit"]
            analysis["reddit_signal"] = self._sentiment_to_signal(reddit)
            scores.append(reddit)
            weights.append(0.3)

        # StockTwits sentiment
        if components.get("stocktwits") is not None:
            stocktwits = components["stocktwits"]
            scores.append(stocktwits)
            weights.append(0.2)

        if scores:
            # Weighted average
            total_weight = sum(weights)
            weighted_sum = sum(s * w for s, w in zip(scores, weights))
            analysis["score"] = weighted_sum / total_weight if total_weight > 0 else 0.0
            analysis["signal"] = self._sentiment_to_signal(analysis["score"])

        return analysis

    def _analyze_options_sentiment(self, components: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze options flow sentiment"""
        analysis = {
            "score": 0.0,
            "signal": "neutral",
        }

        options = components.get("options")
        if options is not None:
            analysis["score"] = options
            analysis["signal"] = self._sentiment_to_signal(options)

            # Options flow is a strong indicator
            if abs(options) > 0.5:
                analysis["strong_signal"] = True

        return analysis

    def _analyze_overall_sentiment(self, aggregated: Any) -> Dict[str, Any]:
        """Analyze overall unified sentiment"""
        unified = aggregated.unified_sentiment

        analysis = {
            "score": unified,
            "signal": self._sentiment_to_signal(unified),
            "confidence": aggregated.confidence,
            "level": aggregated.sentiment_level.value if hasattr(aggregated.sentiment_level, "value") else str(aggregated.sentiment_level),
        }

        return analysis

    def _sentiment_to_signal(self, sentiment: float) -> str:
        """Convert sentiment score to signal string"""
        if sentiment >= 0.5:
            return "very_bullish"
        elif sentiment >= 0.2:
            return "bullish"
        elif sentiment >= 0.05:
            return "slightly_bullish"
        elif sentiment <= -0.5:
            return "very_bearish"
        elif sentiment <= -0.2:
            return "bearish"
        elif sentiment <= -0.05:
            return "slightly_bearish"
        else:
            return "neutral"

    def _combine_analyses(
        self,
        social: Dict[str, Any],
        options: Dict[str, Any],
        overall: Dict[str, Any],
        aggregated: Any,
    ) -> Dict[str, Any]:
        """Combine individual analyses into overall score"""
        # Weight the components
        weights = {
            "social": 0.35,
            "options": 0.30,
            "overall": 0.35,
        }

        total_score = (
            social["score"] * weights["social"]
            + options["score"] * weights["options"]
            + overall["score"] * weights["overall"]
        )

        # Apply divergence penalty
        if aggregated.divergence_detected:
            penalty = aggregated.divergence_score * self.divergence_penalty
            total_score = total_score * (1 - penalty)

        # Clip to valid range
        total_score = max(-1.0, min(1.0, total_score))

        # Calculate confidence
        base_confidence = aggregated.confidence

        # Adjust confidence based on source agreement
        scores = [social["score"], options["score"], overall["score"]]
        non_zero_scores = [s for s in scores if abs(s) > 0.05]

        if non_zero_scores:
            signs = [1 if s > 0 else -1 for s in non_zero_scores]
            agreement = abs(sum(signs)) / len(signs)
            confidence = base_confidence * (0.7 + 0.3 * agreement)
        else:
            confidence = base_confidence * 0.5

        # Penalize for divergence
        if aggregated.divergence_detected:
            confidence = confidence * (1 - aggregated.divergence_score * 0.3)

        return {
            "score": total_score,
            "bias": total_score,
            "confidence": min(1.0, max(0.0, confidence)),
        }

    def _generate_summary(self, aggregated: Any, combined: Dict[str, Any]) -> str:
        """Generate human-readable summary"""
        score = combined["score"]
        confidence = combined["confidence"]

        if score >= 0.4:
            direction = "strongly bullish"
        elif score >= 0.2:
            direction = "bullish"
        elif score >= 0.05:
            direction = "slightly bullish"
        elif score <= -0.4:
            direction = "strongly bearish"
        elif score <= -0.2:
            direction = "bearish"
        elif score <= -0.05:
            direction = "slightly bearish"
        else:
            direction = "neutral"

        mentions = aggregated.total_mentions
        sources = aggregated.source_count

        summary = f"Sentiment is {direction} based on {sources} sources ({mentions} mentions). "

        if aggregated.divergence_detected:
            summary += f"Warning: Source divergence detected. "

        summary += f"Confidence: {confidence * 100:.0f}%"

        return summary
