"""
Base Analyst Agent (T7: Analyst Agents)
=======================================

Abstract base class for all analyst agents.
Each agent analyzes a specific aspect and produces a structured AnalystReport.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AnalystRecommendation(Enum):
    """Analyst recommendation"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"
    NO_OPINION = "no_opinion"


class AnalystConfidence(Enum):
    """Confidence level in the analysis"""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    VERY_LOW = "very_low"


class SignalStrength(Enum):
    """Signal strength indicator"""
    VERY_STRONG = "very_strong"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    VERY_WEAK = "very_weak"
    NEUTRAL = "neutral"


@dataclass
class AnalystReport:
    """
    Structured report from an analyst agent.

    This is the standard output format for all analyst agents,
    enabling aggregation and comparison across different analysis types.
    """
    # Identification
    analyst_name: str
    analyst_type: str
    symbol: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Core recommendation
    recommendation: AnalystRecommendation = AnalystRecommendation.NO_OPINION
    confidence: AnalystConfidence = AnalystConfidence.LOW
    confidence_score: float = 0.5  # 0.0 to 1.0

    # Signal details
    signal_strength: SignalStrength = SignalStrength.NEUTRAL
    directional_bias: float = 0.0  # -1.0 (bearish) to 1.0 (bullish)

    # Reasoning
    summary: str = ""
    key_factors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Supporting data
    metrics: Dict[str, Any] = field(default_factory=dict)
    raw_data: Dict[str, Any] = field(default_factory=dict)

    # Execution suggestions
    suggested_entry: Optional[float] = None
    suggested_stop_loss: Optional[float] = None
    suggested_take_profit: Optional[float] = None

    # Validity
    expires_at: Optional[datetime] = None
    data_freshness_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary"""
        return {
            "analyst_name": self.analyst_name,
            "analyst_type": self.analyst_type,
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "recommendation": self.recommendation.value,
            "confidence": self.confidence.value,
            "confidence_score": self.confidence_score,
            "signal_strength": self.signal_strength.value,
            "directional_bias": self.directional_bias,
            "summary": self.summary,
            "key_factors": self.key_factors,
            "warnings": self.warnings,
            "metrics": self.metrics,
            "suggested_entry": self.suggested_entry,
            "suggested_stop_loss": self.suggested_stop_loss,
            "suggested_take_profit": self.suggested_take_profit,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "data_freshness_seconds": self.data_freshness_seconds,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalystReport":
        """Create report from dictionary"""
        return cls(
            analyst_name=data.get("analyst_name", "unknown"),
            analyst_type=data.get("analyst_type", "unknown"),
            symbol=data.get("symbol", ""),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now(),
            recommendation=AnalystRecommendation(data.get("recommendation", "no_opinion")),
            confidence=AnalystConfidence(data.get("confidence", "low")),
            confidence_score=data.get("confidence_score", 0.5),
            signal_strength=SignalStrength(data.get("signal_strength", "neutral")),
            directional_bias=data.get("directional_bias", 0.0),
            summary=data.get("summary", ""),
            key_factors=data.get("key_factors", []),
            warnings=data.get("warnings", []),
            metrics=data.get("metrics", {}),
            raw_data=data.get("raw_data", {}),
            suggested_entry=data.get("suggested_entry"),
            suggested_stop_loss=data.get("suggested_stop_loss"),
            suggested_take_profit=data.get("suggested_take_profit"),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            data_freshness_seconds=data.get("data_freshness_seconds", 0.0),
        )

    def is_bullish(self) -> bool:
        """Check if recommendation is bullish"""
        return self.recommendation in (AnalystRecommendation.BUY, AnalystRecommendation.STRONG_BUY)

    def is_bearish(self) -> bool:
        """Check if recommendation is bearish"""
        return self.recommendation in (AnalystRecommendation.SELL, AnalystRecommendation.STRONG_SELL)

    def is_expired(self) -> bool:
        """Check if report has expired"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


class AnalystAgent(ABC):
    """
    Abstract base class for analyst agents.

    Each analyst agent specializes in a particular type of analysis
    (technical, sentiment, fundamentals, news) and produces a standardized
    AnalystReport that can be used for decision-making.
    """

    def __init__(self, name: str, analyst_type: str):
        """
        Initialize analyst agent.

        Args:
            name: Human-readable name for this analyst
            analyst_type: Type identifier (technical, sentiment, news, fundamentals)
        """
        self.name = name
        self.analyst_type = analyst_type
        self._enabled = True
        self._weight = 1.0
        logger.info(f"Initialized {analyst_type} analyst: {name}")

    @property
    def enabled(self) -> bool:
        """Check if analyst is enabled"""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        """Enable/disable analyst"""
        self._enabled = value

    @property
    def weight(self) -> float:
        """Get analyst weight for aggregation"""
        return self._weight

    @weight.setter
    def weight(self, value: float):
        """Set analyst weight (0.0 to 2.0)"""
        self._weight = max(0.0, min(2.0, value))

    @abstractmethod
    async def analyze(self, symbol: str, **kwargs) -> AnalystReport:
        """
        Analyze a symbol and produce a report.

        Args:
            symbol: Trading symbol to analyze
            **kwargs: Additional analysis parameters

        Returns:
            AnalystReport with analysis results
        """
        pass

    def _create_empty_report(self, symbol: str, reason: str = "Analysis unavailable") -> AnalystReport:
        """Create an empty report when analysis fails"""
        return AnalystReport(
            analyst_name=self.name,
            analyst_type=self.analyst_type,
            symbol=symbol,
            recommendation=AnalystRecommendation.NO_OPINION,
            confidence=AnalystConfidence.VERY_LOW,
            confidence_score=0.0,
            summary=reason,
            warnings=[reason],
        )

    def _score_to_recommendation(self, score: float) -> AnalystRecommendation:
        """Convert a -1.0 to 1.0 score to recommendation"""
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

    def _score_to_confidence(self, score: float) -> AnalystConfidence:
        """Convert a 0.0 to 1.0 confidence score to confidence level"""
        if score >= 0.8:
            return AnalystConfidence.VERY_HIGH
        elif score >= 0.6:
            return AnalystConfidence.HIGH
        elif score >= 0.4:
            return AnalystConfidence.MODERATE
        elif score >= 0.2:
            return AnalystConfidence.LOW
        else:
            return AnalystConfidence.VERY_LOW

    def _score_to_signal_strength(self, score: float) -> SignalStrength:
        """Convert absolute score to signal strength"""
        abs_score = abs(score)
        if abs_score >= 0.8:
            return SignalStrength.VERY_STRONG
        elif abs_score >= 0.6:
            return SignalStrength.STRONG
        elif abs_score >= 0.4:
            return SignalStrength.MODERATE
        elif abs_score >= 0.2:
            return SignalStrength.WEAK
        elif abs_score > 0.05:
            return SignalStrength.VERY_WEAK
        else:
            return SignalStrength.NEUTRAL
