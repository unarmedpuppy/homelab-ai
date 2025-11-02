"""
Confluence Models
=================

Data models for confluence calculation combining technical indicators,
sentiment, and options flow data.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any
from datetime import datetime
from enum import Enum


class ConfluenceLevel(Enum):
    """Confluence level enumeration"""
    VERY_LOW = "very_low"      # 0.0 - 0.3
    LOW = "low"                # 0.3 - 0.5
    MODERATE = "moderate"      # 0.5 - 0.7
    HIGH = "high"              # 0.7 - 0.85
    VERY_HIGH = "very_high"    # 0.85 - 1.0


@dataclass
class TechnicalScore:
    """Technical analysis score breakdown"""
    overall_score: float  # -1.0 to 1.0 (overall technical bias)
    rsi_score: float  # -1.0 to 1.0
    sma_trend_score: float  # -1.0 to 1.0
    volume_score: float  # -1.0 to 1.0
    bollinger_score: float  # -1.0 to 1.0
    indicators: Dict[str, Any] = field(default_factory=dict)  # Raw indicator values


@dataclass
class SentimentScore:
    """Sentiment score component"""
    score: float  # -1.0 to 1.0 (from AggregatedSentiment)
    confidence: float  # 0.0 to 1.0
    source_count: int
    divergence_detected: bool = False


@dataclass
class OptionsFlowScore:
    """Options flow score component"""
    score: float  # -1.0 to 1.0 (from UnusualWhales or similar)
    call_put_ratio: Optional[float] = None
    unusual_activity: bool = False


@dataclass
class ConfluenceBreakdown:
    """Detailed breakdown of confluence calculation"""
    technical_score: TechnicalScore
    sentiment_score: Optional[SentimentScore]
    options_flow_score: Optional[OptionsFlowScore]
    
    # Weighted contributions
    technical_contribution: float  # 0.0 to 1.0
    sentiment_contribution: float  # 0.0 to 1.0
    options_flow_contribution: float  # 0.0 to 1.0
    
    # Raw component scores (before weighting)
    technical_raw: float  # -1.0 to 1.0
    sentiment_raw: Optional[float] = None  # -1.0 to 1.0
    options_flow_raw: Optional[float] = None  # -1.0 to 1.0


@dataclass
class ConfluenceScore:
    """Complete confluence score for a symbol"""
    symbol: str
    timestamp: datetime
    confluence_score: float  # 0.0 to 1.0 (overall confluence strength)
    directional_bias: float  # -1.0 to 1.0 (bullish/bearish bias)
    confluence_level: ConfluenceLevel
    
    # Breakdown
    breakdown: ConfluenceBreakdown
    
    # Components used
    components_used: List[str] = field(default_factory=list)  # ['technical', 'sentiment', 'options_flow']
    
    # Metadata
    confidence: float = 0.0  # 0.0 to 1.0 (confidence in the confluence score)
    volume_trend: str = "stable"  # up, down, stable
    
    # Thresholds
    meets_minimum_threshold: bool = False
    meets_high_threshold: bool = False
    
    # Additional context
    metadata: Dict[str, Any] = field(default_factory=dict)

