"""
Analyst Agents Package (T7: TradingAgents-inspired Analyst System)
==================================================================

Modular analyst agents that analyze different aspects of a trading opportunity
and produce structured reports for decision-making.

Agents:
- TechnicalAnalyst: RSI, MACD, Bollinger Bands, moving averages, volume
- SentimentAnalyst: Multi-source sentiment aggregation and analysis
- NewsAnalyst: News-based sentiment and event detection
- FundamentalsAnalyst: Analyst ratings, price targets, valuation metrics

Each agent produces an AnalystReport that can be aggregated for final decisions.
"""

from .base import (
    AnalystAgent,
    AnalystReport,
    AnalystRecommendation,
    AnalystConfidence,
    SignalStrength,
)
from .technical import TechnicalAnalyst
from .sentiment import SentimentAnalyst
from .news import NewsAnalyst
from .fundamentals import FundamentalsAnalyst
from .registry import (
    AnalystRegistry,
    AggregatedAnalysis,
    get_analyst_registry,
    register_analyst,
    get_analyst,
    run_all_analysts,
)
from .debate import (
    DebateRoom,
    DebateRecord,
    DebateVerdict,
    DebateRound,
    DebateArgument,
    DebatePosition,
    VerdictType,
    get_debate_room,
    conduct_debate,
)

__all__ = [
    # Base classes
    "AnalystAgent",
    "AnalystReport",
    "AnalystRecommendation",
    "AnalystConfidence",
    "SignalStrength",
    # Analyst implementations
    "TechnicalAnalyst",
    "SentimentAnalyst",
    "NewsAnalyst",
    "FundamentalsAnalyst",
    # Registry
    "AnalystRegistry",
    "AggregatedAnalysis",
    "get_analyst_registry",
    "register_analyst",
    "get_analyst",
    "run_all_analysts",
    # Debate Room
    "DebateRoom",
    "DebateRecord",
    "DebateVerdict",
    "DebateRound",
    "DebateArgument",
    "DebatePosition",
    "VerdictType",
    "get_debate_room",
    "conduct_debate",
]
