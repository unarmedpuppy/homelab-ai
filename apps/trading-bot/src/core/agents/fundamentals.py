"""
Fundamentals Analyst Agent (T7: Analyst Agents)
================================================

Analyzes fundamental data including analyst ratings, price targets,
and financial metrics to produce trading recommendations.
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


class FundamentalsAnalyst(AnalystAgent):
    """
    Fundamentals analysis agent that evaluates analyst ratings and price targets.

    Analyzes:
    - Analyst ratings (buy/sell/hold distribution)
    - Price targets (upside/downside potential)
    - Insider trading activity
    - Institutional ownership changes
    """

    def __init__(
        self,
        name: str = "Fundamentals Analyst",
        min_analysts: int = 3,
        upside_threshold: float = 0.15,
    ):
        """
        Initialize Fundamentals Analyst.

        Args:
            name: Analyst name
            min_analysts: Minimum analysts needed for analysis
            upside_threshold: Minimum upside % to consider bullish
        """
        super().__init__(name=name, analyst_type="fundamentals")

        self.min_analysts = min_analysts
        self.upside_threshold = upside_threshold
        self._ratings_provider = None
        self._insider_provider = None

    @property
    def ratings_provider(self):
        """Lazy load analyst ratings provider"""
        if self._ratings_provider is None:
            try:
                from ...data.providers.sentiment.analyst_ratings import AnalystRatingsSentimentProvider
                self._ratings_provider = AnalystRatingsSentimentProvider()
            except ImportError:
                logger.warning("AnalystRatingsSentimentProvider not available")
        return self._ratings_provider

    @property
    def insider_provider(self):
        """Lazy load insider trading provider"""
        if self._insider_provider is None:
            try:
                from ...data.providers.sentiment.insider_trading import InsiderTradingSentimentProvider
                self._insider_provider = InsiderTradingSentimentProvider()
            except ImportError:
                logger.warning("InsiderTradingSentimentProvider not available")
        return self._insider_provider

    async def analyze(
        self,
        symbol: str,
        current_price: Optional[float] = None,
        analyst_data: Optional[Dict[str, Any]] = None,
        insider_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> AnalystReport:
        """
        Analyze fundamentals for a symbol.

        Args:
            symbol: Trading symbol to analyze
            current_price: Current stock price
            analyst_data: Optional analyst ratings data
            insider_data: Optional insider trading data
            **kwargs: Additional parameters

        Returns:
            AnalystReport with fundamentals analysis results
        """
        try:
            # Fetch data if not provided
            if analyst_data is None:
                analyst_data = await self._fetch_analyst_data(symbol)

            if insider_data is None:
                insider_data = await self._fetch_insider_data(symbol)

            # Check if we have enough data
            if not analyst_data and not insider_data:
                return self._create_empty_report(symbol, "No fundamental data available")

            # Analyze each component
            ratings_analysis = self._analyze_ratings(analyst_data) if analyst_data else {"score": 0, "signal": "neutral"}
            target_analysis = self._analyze_price_targets(analyst_data, current_price) if analyst_data else {"score": 0, "signal": "neutral"}
            insider_analysis = self._analyze_insider_activity(insider_data) if insider_data else {"score": 0, "signal": "neutral"}

            # Combine analyses
            combined = self._combine_analyses(
                ratings_analysis,
                target_analysis,
                insider_analysis,
            )

            # Build key factors
            key_factors = []
            warnings = []

            if ratings_analysis.get("analyst_count", 0) > 0:
                key_factors.append(
                    f"Analyst consensus: {ratings_analysis.get('consensus', 'N/A')} "
                    f"({ratings_analysis['analyst_count']} analysts)"
                )

            if target_analysis.get("upside_pct") is not None:
                upside = target_analysis["upside_pct"]
                direction = "upside" if upside > 0 else "downside"
                key_factors.append(f"Price target {direction}: {abs(upside):.1f}%")

            if insider_analysis.get("signal") != "neutral":
                key_factors.append(f"Insider activity: {insider_analysis['signal']}")

            # Add warnings
            if ratings_analysis.get("analyst_count", 0) < self.min_analysts:
                warnings.append(f"Limited analyst coverage ({ratings_analysis.get('analyst_count', 0)} analysts)")

            if target_analysis.get("wide_range"):
                warnings.append("Wide range in price targets - uncertainty")

            if insider_analysis.get("significant_selling"):
                warnings.append("Significant insider selling detected")

            # Fundamentals have longer validity
            expires_at = datetime.now() + timedelta(days=1)

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
                summary=self._generate_summary(ratings_analysis, target_analysis, combined),
                key_factors=key_factors,
                warnings=warnings,
                metrics={
                    "analyst_count": ratings_analysis.get("analyst_count", 0),
                    "buy_count": ratings_analysis.get("buy_count", 0),
                    "hold_count": ratings_analysis.get("hold_count", 0),
                    "sell_count": ratings_analysis.get("sell_count", 0),
                    "consensus": ratings_analysis.get("consensus", "N/A"),
                    "target_price": target_analysis.get("target_price"),
                    "target_high": target_analysis.get("target_high"),
                    "target_low": target_analysis.get("target_low"),
                    "upside_pct": target_analysis.get("upside_pct"),
                    "insider_net_activity": insider_analysis.get("net_activity", 0),
                },
                raw_data={
                    "ratings_analysis": ratings_analysis,
                    "target_analysis": target_analysis,
                    "insider_analysis": insider_analysis,
                },
                suggested_entry=current_price,
                suggested_take_profit=target_analysis.get("target_price"),
                expires_at=expires_at,
                data_freshness_seconds=0.0,
            )

        except Exception as e:
            logger.error(f"Fundamentals analysis error for {symbol}: {e}", exc_info=True)
            return self._create_empty_report(symbol, f"Analysis error: {str(e)}")

    async def _fetch_analyst_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch analyst ratings data"""
        if self.ratings_provider is None:
            return None

        try:
            sentiment = await self.ratings_provider.get_sentiment(symbol)
            if sentiment and hasattr(sentiment, "raw_data"):
                return sentiment.raw_data
            return None
        except Exception as e:
            logger.warning(f"Error fetching analyst data for {symbol}: {e}")
            return None

    async def _fetch_insider_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch insider trading data"""
        if self.insider_provider is None:
            return None

        try:
            sentiment = await self.insider_provider.get_sentiment(symbol)
            if sentiment and hasattr(sentiment, "raw_data"):
                return sentiment.raw_data
            return None
        except Exception as e:
            logger.warning(f"Error fetching insider data for {symbol}: {e}")
            return None

    def _analyze_ratings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze analyst ratings distribution"""
        analysis = {
            "score": 0.0,
            "signal": "neutral",
            "analyst_count": 0,
            "buy_count": 0,
            "hold_count": 0,
            "sell_count": 0,
            "consensus": "N/A",
        }

        # Extract rating counts
        buy = data.get("buy", 0) + data.get("strong_buy", 0) + data.get("outperform", 0)
        hold = data.get("hold", 0) + data.get("neutral", 0)
        sell = data.get("sell", 0) + data.get("strong_sell", 0) + data.get("underperform", 0)

        total = buy + hold + sell
        if total == 0:
            return analysis

        analysis["analyst_count"] = total
        analysis["buy_count"] = buy
        analysis["hold_count"] = hold
        analysis["sell_count"] = sell

        # Calculate score (-1 to 1)
        # Buy = +1, Hold = 0, Sell = -1
        weighted_sum = (buy * 1.0) + (hold * 0.0) + (sell * -1.0)
        analysis["score"] = weighted_sum / total

        # Determine consensus
        if buy > hold and buy > sell:
            if buy / total > 0.6:
                analysis["consensus"] = "Strong Buy"
            else:
                analysis["consensus"] = "Buy"
        elif sell > hold and sell > buy:
            if sell / total > 0.6:
                analysis["consensus"] = "Strong Sell"
            else:
                analysis["consensus"] = "Sell"
        else:
            analysis["consensus"] = "Hold"

        # Determine signal
        if analysis["score"] >= 0.5:
            analysis["signal"] = "strongly_bullish"
        elif analysis["score"] >= 0.2:
            analysis["signal"] = "bullish"
        elif analysis["score"] <= -0.5:
            analysis["signal"] = "strongly_bearish"
        elif analysis["score"] <= -0.2:
            analysis["signal"] = "bearish"

        return analysis

    def _analyze_price_targets(
        self, data: Dict[str, Any], current_price: Optional[float]
    ) -> Dict[str, Any]:
        """Analyze price target data"""
        analysis = {
            "score": 0.0,
            "signal": "neutral",
            "target_price": None,
            "target_high": None,
            "target_low": None,
            "upside_pct": None,
            "wide_range": False,
        }

        # Extract price targets
        target = data.get("target_price") or data.get("price_target") or data.get("mean_target")
        target_high = data.get("target_high") or data.get("high_target")
        target_low = data.get("target_low") or data.get("low_target")

        if target is not None:
            analysis["target_price"] = float(target)
        if target_high is not None:
            analysis["target_high"] = float(target_high)
        if target_low is not None:
            analysis["target_low"] = float(target_low)

        # Calculate upside/downside if we have current price
        if current_price and analysis["target_price"]:
            upside = (analysis["target_price"] - current_price) / current_price
            analysis["upside_pct"] = upside * 100

            # Score based on upside potential
            if upside >= self.upside_threshold:
                analysis["score"] = min(1.0, upside * 2)  # Cap at 1.0
                analysis["signal"] = "bullish"
            elif upside <= -self.upside_threshold:
                analysis["score"] = max(-1.0, upside * 2)
                analysis["signal"] = "bearish"
            else:
                analysis["score"] = upside * 2
                analysis["signal"] = "neutral"

        # Check for wide target range (indicates uncertainty)
        if analysis["target_high"] and analysis["target_low"] and current_price:
            range_pct = (analysis["target_high"] - analysis["target_low"]) / current_price
            if range_pct > 0.5:  # More than 50% range
                analysis["wide_range"] = True

        return analysis

    def _analyze_insider_activity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze insider trading activity"""
        analysis = {
            "score": 0.0,
            "signal": "neutral",
            "net_activity": 0,
            "buy_transactions": 0,
            "sell_transactions": 0,
            "significant_selling": False,
        }

        if not data:
            return analysis

        # Extract transaction counts
        buys = data.get("buys", 0) or data.get("buy_count", 0)
        sells = data.get("sells", 0) or data.get("sell_count", 0)

        analysis["buy_transactions"] = buys
        analysis["sell_transactions"] = sells
        analysis["net_activity"] = buys - sells

        total = buys + sells
        if total == 0:
            return analysis

        # Calculate score based on net activity ratio
        net_ratio = (buys - sells) / total
        analysis["score"] = net_ratio * 0.5  # Scale down as insider data is one factor

        if net_ratio > 0.3:
            analysis["signal"] = "insider_buying"
        elif net_ratio < -0.3:
            analysis["signal"] = "insider_selling"
            if net_ratio < -0.5:
                analysis["significant_selling"] = True

        return analysis

    def _combine_analyses(
        self,
        ratings: Dict[str, Any],
        targets: Dict[str, Any],
        insider: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Combine analyses into overall score"""
        # Weighted combination
        weights = {
            "ratings": 0.45,
            "targets": 0.35,
            "insider": 0.20,
        }

        total_score = (
            ratings["score"] * weights["ratings"]
            + targets["score"] * weights["targets"]
            + insider["score"] * weights["insider"]
        )

        total_score = max(-1.0, min(1.0, total_score))

        # Calculate confidence
        # More analysts = higher confidence
        analyst_count = ratings.get("analyst_count", 0)
        analyst_confidence = min(1.0, analyst_count / 20)  # Max at 20 analysts

        # Reduce for wide target range
        if targets.get("wide_range"):
            analyst_confidence *= 0.7

        confidence = 0.3 + (analyst_confidence * 0.5)

        # Check for agreement between ratings and targets
        if (ratings["score"] > 0 and targets["score"] > 0) or (
            ratings["score"] < 0 and targets["score"] < 0
        ):
            confidence = min(1.0, confidence + 0.1)

        return {
            "score": total_score,
            "bias": total_score,
            "confidence": confidence,
        }

    def _generate_summary(
        self,
        ratings: Dict[str, Any],
        targets: Dict[str, Any],
        combined: Dict[str, Any],
    ) -> str:
        """Generate human-readable summary"""
        score = combined["score"]

        if score >= 0.4:
            direction = "strongly bullish"
        elif score >= 0.15:
            direction = "bullish"
        elif score <= -0.4:
            direction = "strongly bearish"
        elif score <= -0.15:
            direction = "bearish"
        else:
            direction = "neutral"

        summary = f"Fundamental analysis is {direction}. "

        if ratings.get("consensus") != "N/A":
            summary += f"Analyst consensus: {ratings['consensus']} ({ratings['analyst_count']} analysts). "

        if targets.get("upside_pct") is not None:
            upside = targets["upside_pct"]
            if upside > 0:
                summary += f"Price target implies {upside:.1f}% upside. "
            else:
                summary += f"Price target implies {abs(upside):.1f}% downside. "

        summary += f"Confidence: {combined['confidence'] * 100:.0f}%"

        return summary
