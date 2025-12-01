"""
Analyst Registry (T7: Analyst Agents)
======================================

Manages registration, lookup, and coordination of analyst agents.
Provides aggregation of multiple analyst reports for decision-making.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from .base import (
    AnalystAgent,
    AnalystConfidence,
    AnalystRecommendation,
    AnalystReport,
    SignalStrength,
)

logger = logging.getLogger(__name__)


@dataclass
class AggregatedAnalysis:
    """
    Aggregated analysis from multiple analysts.

    Combines reports from all enabled analysts into a unified view
    with weighted consensus and confidence metrics.
    """

    symbol: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Individual reports
    reports: List[AnalystReport] = field(default_factory=list)
    analyst_count: int = 0

    # Aggregated recommendation
    consensus_recommendation: AnalystRecommendation = AnalystRecommendation.NO_OPINION
    consensus_score: float = 0.0  # -1.0 to 1.0
    consensus_confidence: float = 0.0  # 0.0 to 1.0

    # Agreement metrics
    agreement_score: float = 0.0  # How much analysts agree (0-1)
    bullish_count: int = 0
    bearish_count: int = 0
    neutral_count: int = 0

    # Combined factors
    key_factors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Summary
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "analyst_count": self.analyst_count,
            "consensus": {
                "recommendation": self.consensus_recommendation.value,
                "score": self.consensus_score,
                "confidence": self.consensus_confidence,
            },
            "agreement": {
                "score": self.agreement_score,
                "bullish": self.bullish_count,
                "bearish": self.bearish_count,
                "neutral": self.neutral_count,
            },
            "key_factors": self.key_factors,
            "warnings": self.warnings,
            "summary": self.summary,
            "reports": [r.to_dict() for r in self.reports],
        }


class AnalystRegistry:
    """
    Registry for managing analyst agents.

    Features:
    - Register/unregister analysts
    - Enable/disable analysts
    - Set analyst weights
    - Run analyses across all analysts
    - Aggregate results with weighted consensus
    """

    def __init__(self):
        """Initialize analyst registry"""
        self._analysts: Dict[str, AnalystAgent] = {}
        self._default_analysts_initialized = False
        logger.info("AnalystRegistry initialized (T7: Analyst Agents)")

    def register(self, analyst: AnalystAgent, name: Optional[str] = None) -> str:
        """
        Register an analyst agent.

        Args:
            analyst: AnalystAgent instance
            name: Optional override name (uses analyst.name if not provided)

        Returns:
            Registration key
        """
        key = name or analyst.name
        self._analysts[key] = analyst
        logger.info(f"Registered analyst: {key} (type: {analyst.analyst_type})")
        return key

    def unregister(self, name: str) -> bool:
        """
        Unregister an analyst agent.

        Args:
            name: Analyst name/key

        Returns:
            True if removed, False if not found
        """
        if name in self._analysts:
            del self._analysts[name]
            logger.info(f"Unregistered analyst: {name}")
            return True
        return False

    def get(self, name: str) -> Optional[AnalystAgent]:
        """Get analyst by name"""
        return self._analysts.get(name)

    def get_all(self) -> Dict[str, AnalystAgent]:
        """Get all registered analysts"""
        return dict(self._analysts)

    def get_enabled(self) -> Dict[str, AnalystAgent]:
        """Get all enabled analysts"""
        return {k: v for k, v in self._analysts.items() if v.enabled}

    def set_enabled(self, name: str, enabled: bool) -> bool:
        """Enable/disable an analyst"""
        analyst = self._analysts.get(name)
        if analyst:
            analyst.enabled = enabled
            logger.info(f"Analyst {name} {'enabled' if enabled else 'disabled'}")
            return True
        return False

    def set_weight(self, name: str, weight: float) -> bool:
        """Set analyst weight for aggregation"""
        analyst = self._analysts.get(name)
        if analyst:
            analyst.weight = weight
            logger.info(f"Analyst {name} weight set to {weight}")
            return True
        return False

    def initialize_default_analysts(self):
        """Initialize default set of analysts"""
        if self._default_analysts_initialized:
            return

        try:
            from .technical import TechnicalAnalyst
            from .sentiment import SentimentAnalyst
            from .news import NewsAnalyst
            from .fundamentals import FundamentalsAnalyst

            # Register default analysts
            self.register(TechnicalAnalyst())
            self.register(SentimentAnalyst())
            self.register(NewsAnalyst())
            self.register(FundamentalsAnalyst())

            self._default_analysts_initialized = True
            logger.info("Default analysts initialized")

        except Exception as e:
            logger.error(f"Error initializing default analysts: {e}")

    async def analyze(
        self,
        symbol: str,
        data: Optional[Any] = None,
        **kwargs,
    ) -> AggregatedAnalysis:
        """
        Run analysis across all enabled analysts.

        Args:
            symbol: Trading symbol to analyze
            data: Optional market data (DataFrame for technical analysis)
            **kwargs: Additional parameters passed to analysts

        Returns:
            AggregatedAnalysis with combined results
        """
        enabled_analysts = self.get_enabled()

        if not enabled_analysts:
            return AggregatedAnalysis(
                symbol=symbol,
                summary="No analysts enabled",
            )

        # Run all analyses concurrently
        tasks = []
        for name, analyst in enabled_analysts.items():
            task = self._run_analyst(name, analyst, symbol, data, **kwargs)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect successful reports
        reports = []
        for result in results:
            if isinstance(result, AnalystReport):
                reports.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"Analyst error: {result}")

        # Aggregate reports
        return self._aggregate_reports(symbol, reports)

    async def _run_analyst(
        self,
        name: str,
        analyst: AnalystAgent,
        symbol: str,
        data: Optional[Any],
        **kwargs,
    ) -> AnalystReport:
        """Run a single analyst with error handling"""
        try:
            # Pass data based on analyst type
            if analyst.analyst_type == "technical":
                return await analyst.analyze(symbol, data=data, **kwargs)
            else:
                return await analyst.analyze(symbol, **kwargs)
        except Exception as e:
            logger.error(f"Error running analyst {name}: {e}")
            return analyst._create_empty_report(symbol, f"Error: {str(e)}")

    def _aggregate_reports(
        self, symbol: str, reports: List[AnalystReport]
    ) -> AggregatedAnalysis:
        """Aggregate multiple analyst reports"""
        if not reports:
            return AggregatedAnalysis(
                symbol=symbol,
                summary="No analyst reports available",
            )

        # Calculate weighted scores
        total_weight = 0.0
        weighted_score = 0.0
        weighted_confidence = 0.0

        bullish = 0
        bearish = 0
        neutral = 0

        all_factors = []
        all_warnings = []

        for report in reports:
            # Get analyst weight
            analyst = self._analysts.get(report.analyst_name)
            weight = analyst.weight if analyst else 1.0

            # Accumulate weighted scores
            total_weight += weight
            weighted_score += report.directional_bias * weight
            weighted_confidence += report.confidence_score * weight

            # Count directions
            if report.is_bullish():
                bullish += 1
            elif report.is_bearish():
                bearish += 1
            else:
                neutral += 1

            # Collect factors and warnings
            for factor in report.key_factors[:2]:  # Top 2 from each
                all_factors.append(f"[{report.analyst_name}] {factor}")
            all_warnings.extend(report.warnings)

        # Normalize
        if total_weight > 0:
            consensus_score = weighted_score / total_weight
            consensus_confidence = weighted_confidence / total_weight
        else:
            consensus_score = 0.0
            consensus_confidence = 0.0

        # Calculate agreement
        total_analysts = bullish + bearish + neutral
        if total_analysts > 0:
            max_agreement = max(bullish, bearish, neutral)
            agreement_score = max_agreement / total_analysts
        else:
            agreement_score = 0.0

        # Determine consensus recommendation
        consensus_rec = self._score_to_recommendation(consensus_score)

        # Adjust confidence based on agreement
        adjusted_confidence = consensus_confidence * (0.5 + 0.5 * agreement_score)

        # Generate summary
        summary = self._generate_summary(
            consensus_score,
            adjusted_confidence,
            agreement_score,
            bullish,
            bearish,
            neutral,
        )

        return AggregatedAnalysis(
            symbol=symbol,
            reports=reports,
            analyst_count=len(reports),
            consensus_recommendation=consensus_rec,
            consensus_score=consensus_score,
            consensus_confidence=adjusted_confidence,
            agreement_score=agreement_score,
            bullish_count=bullish,
            bearish_count=bearish,
            neutral_count=neutral,
            key_factors=all_factors[:10],  # Top 10
            warnings=list(set(all_warnings))[:5],  # Unique, top 5
            summary=summary,
        )

    def _score_to_recommendation(self, score: float) -> AnalystRecommendation:
        """Convert score to recommendation"""
        if score >= 0.6:
            return AnalystRecommendation.STRONG_BUY
        elif score >= 0.2:
            return AnalystRecommendation.BUY
        elif score >= -0.2:
            return AnalystRecommendation.HOLD
        elif score >= -0.6:
            return AnalystRecommendation.SELL
        else:
            return AnalystRecommendation.STRONG_SELL

    def _generate_summary(
        self,
        score: float,
        confidence: float,
        agreement: float,
        bullish: int,
        bearish: int,
        neutral: int,
    ) -> str:
        """Generate aggregated summary"""
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

        total = bullish + bearish + neutral
        summary = f"Analyst consensus is {direction}. "
        summary += f"{bullish} bullish, {bearish} bearish, {neutral} neutral out of {total} analysts. "

        if agreement >= 0.8:
            summary += "Strong agreement among analysts. "
        elif agreement <= 0.4:
            summary += "Significant disagreement among analysts. "

        summary += f"Confidence: {confidence * 100:.0f}%"

        return summary

    def get_status(self) -> Dict[str, Any]:
        """Get registry status"""
        analysts_status = {}
        for name, analyst in self._analysts.items():
            analysts_status[name] = {
                "type": analyst.analyst_type,
                "enabled": analyst.enabled,
                "weight": analyst.weight,
            }

        return {
            "total_analysts": len(self._analysts),
            "enabled_count": len(self.get_enabled()),
            "analysts": analysts_status,
        }


# Global registry instance
_registry: Optional[AnalystRegistry] = None


def get_analyst_registry() -> AnalystRegistry:
    """Get or create global AnalystRegistry instance"""
    global _registry
    if _registry is None:
        _registry = AnalystRegistry()
        _registry.initialize_default_analysts()
    return _registry


def register_analyst(analyst: AnalystAgent, name: Optional[str] = None) -> str:
    """Register an analyst with the global registry"""
    return get_analyst_registry().register(analyst, name)


def get_analyst(name: str) -> Optional[AnalystAgent]:
    """Get an analyst from the global registry"""
    return get_analyst_registry().get(name)


async def run_all_analysts(
    symbol: str,
    data: Optional[Any] = None,
    **kwargs,
) -> AggregatedAnalysis:
    """Run all analysts and return aggregated analysis"""
    return await get_analyst_registry().analyze(symbol, data, **kwargs)
