# Trading Bot Implementation Roadmap

*Last Updated: 2024-11-30*

## Current State Assessment

### What's Working Well
- **Core Strategy System**: BaseStrategy with 3 concrete implementations (Momentum, RangeBound, LevelBased)
- **Risk Management**: Complete suite (position sizing, stop loss, profit taking, compliance, account monitoring)
- **Sentiment Analysis**: 13+ providers with aggregation
- **Backtesting Engine**: Event-driven with metrics calculator
- **API Layer**: 17 route modules, comprehensive REST API
- **Test Coverage**: 59 test files covering strategies, risk, providers, and API

### Issues Identified

#### 1. Code Redundancy
| Issue | Location | Impact |
|-------|----------|--------|
| Metrics fragmentation | `src/utils/metrics*.py` (8 files, 57KB) | Hard to maintain, no single source of truth |
| Backward compat layer | `src/core/strategy.py` | Duplicates enums from `strategy/base.py` |
| Sentiment provider pattern | `src/data/providers/sentiment/` (13 files) | Similar boilerplate in each provider |

#### 2. Style Inconsistencies
| Issue | Examples |
|-------|----------|
| Import patterns | Mixed relative depths (`...config` vs `..strategy`) |
| Type hints | Some functions missing hints (e.g., `sentiment=None` without type) |
| Error handling | Mix of broad `except Exception` and specific catches |
| Naming | `pdh/pdl` abbreviations vs `current_price` full names |

#### 3. Missing/Incomplete
- WebSocket data producers not connected to streams
- Live execution needs integration testing
- No WebSocket tests
- UI not connected to real-time data

---

## Phase 1: Code Quality & Cleanup (Priority: High)

### T1: Consolidate Metrics System ✓ COMPLETED
**Goal**: Reduce 8 metrics files to 3 well-organized modules

**Result**:
```
src/utils/metrics/
├── __init__.py   (172 lines) - Public API exports
├── registry.py   (348 lines) - Core registry, get_or_create, decorators
└── collectors.py (1014 lines) - All metric collection (trading, system, providers, business)
```

**Summary**:
- Consolidated 8 files (~2100 lines) → 3 files (~1534 lines)
- Updated 25+ import sites across codebase
- Removed legacy duplicate metrics
- Clean single-source-of-truth for all metrics

### T2: Remove Backward Compatibility Duplication ✓ COMPLETED
**Goal**: Clean up `src/core/strategy.py` wrapper

**Result**:
- Removed 270+ lines of duplicate class/enum definitions
- Now a clean re-export module (~57 lines)
- Removed legacy `SMAStrategy` (unused, replaced by MomentumStrategy)
- Removed `StrategyFactory` (functionality in registry)
- All imports still work via backward-compatible re-exports

### T3: Standardize Import Patterns
**Goal**: Consistent relative imports across codebase

**Convention**:
```python
# Within same package
from .module import Class

# Parent package
from ..package.module import Class

# Always use absolute for external packages
from fastapi import APIRouter
```

**Files to update**: Focus on `src/data/providers/sentiment/` which has deepest nesting

### T4: Add Missing Type Hints
**Goal**: 100% type hint coverage on public functions

**Priority files**:
- `src/core/strategy/range_bound.py` - `sentiment` parameter
- `src/data/providers/sentiment/*.py` - Return types
- `src/utils/*.py` - Helper functions

### T5: Standardize Error Handling
**Goal**: Replace broad `except Exception` with specific exceptions

**Pattern to follow**:
```python
# Bad
except Exception as e:
    logger.error(f"Error: {e}")

# Good
except (ConnectionError, TimeoutError) as e:
    logger.error(f"Network error: {e}")
    raise DataProviderError(f"Failed to fetch data: {e}") from e
except ValueError as e:
    logger.warning(f"Invalid data: {e}")
    return default_value
```

---

## Phase 2: Real-time Infrastructure (Priority: High)

### T6: WebSocket Data Producer Integration ✅
**Goal**: Connect data sources to WebSocket streams

**Completed**:
- Background polling tasks in all stream classes (PriceUpdateStream, SentimentUpdateStream, OptionsFlowStream, etc.)
- IBKR/market data connected via `DataProviderManager` in `price_updates.py`
- Sentiment aggregator connected via `SentimentUpdateStream` in `sentiment_updates.py`
- Options flow connected via `UnusualWhalesClient` in `options_flow.py`
- Health monitoring via `StreamHealthMonitor` in `health.py`

**Tasks**:
- [x] Create background tasks that poll/stream data
- [x] Connect IBKR market data to `price_updates` stream
- [x] Connect sentiment aggregator to `sentiment_updates` stream
- [x] Connect options flow to `options_flow` stream
- [x] Add health checks to WebSocket connections

### T7: UI WebSocket Integration
**Goal**: Dashboard receives and displays real-time data

**Tasks**:
- [ ] Update `dashboard.html` JavaScript to handle WebSocket messages
- [ ] Implement reconnection logic with exponential backoff
- [ ] Add visual indicators for connection status
- [ ] Display real-time price updates in UI

### T8: WebSocket Testing
**Goal**: Add test coverage for real-time streaming

**Tasks**:
- [ ] Create `tests/integration/test_websocket.py`
- [ ] Test connection lifecycle (connect, disconnect, reconnect)
- [ ] Test message broadcasting
- [ ] Test error handling and recovery

---

## Phase 3: Live Trading Pipeline (Priority: High)

### T9: IBKR Integration Testing ✅
**Goal**: Verify live execution pipeline end-to-end

**Completed**:
- Comprehensive paper trading test script (`scripts/test_ibkr_paper_trading.py`)
- Tests connection, reconnection, account, market data, historical data
- Tests order placement (limit orders), cancellation
- Tests position sync via PositionSyncService
- Tests error handling (invalid symbols, disconnected operations)
- Tests callback registration
- IBKR setup documentation (`docs/IBKR_SETUP.md`)

**Tasks**:
- [x] Create paper trading test script
- [x] Test order submission, modification, cancellation
- [x] Test position sync accuracy
- [x] Test error handling for network failures
- [x] Document required IBKR permissions

### T10: Strategy-to-Execution Pipeline
**Goal**: Connect strategy signals to order execution

**Tasks**:
- [ ] Create `src/core/executor.py` - Signal to order translator
- [ ] Implement safety checks before execution:
  - Max daily loss limit
  - Max position size
  - Trading hours validation
  - Cash availability check
- [ ] Add execution logging and audit trail
- [ ] Test with paper account

---

## Phase 4: Enhanced Features (Priority: Medium)

### T11: Sentiment Provider Base Class
**Goal**: Reduce boilerplate in sentiment providers

**Current**: Each provider has similar init, error handling, caching

**Target**:
```python
class BaseSentimentProvider(ABC):
    def __init__(self, config: dict):
        self.cache = get_cache_manager()
        self.rate_limiter = RateLimiter(config.get('rate_limit', 60))

    @abstractmethod
    async def fetch_raw_data(self, symbol: str) -> dict: ...

    async def get_sentiment(self, symbol: str) -> SentimentResult:
        # Common caching, rate limiting, error handling
        ...
```

**Tasks**:
- [ ] Create `BaseSentimentProvider` abstract class
- [ ] Migrate Twitter provider as template
- [ ] Migrate remaining providers
- [ ] Update aggregator to use new interface

### T12: Parameter Optimization
**Goal**: Automated strategy parameter tuning

**Tasks**:
- [ ] Implement grid search optimizer
- [ ] Add genetic algorithm option
- [ ] Create parameter space configuration
- [ ] Add walk-forward validation
- [ ] UI for viewing optimization results

### T13: Backtest Visualization
**Goal**: Interactive charts for backtest results

**Tasks**:
- [ ] Add equity curve chart
- [ ] Add trade markers on price chart
- [ ] Add drawdown visualization
- [ ] Export to HTML report

---

## Phase 5: Multi-Agent Trading Architecture (Priority: High)

*Inspired by [TradingAgents](https://github.com/TauricResearch/TradingAgents) multi-agent framework*

### T17: Risk Manager Agent ✅ COMPLETED
**Goal**: Add a risk management layer as final approval gate before trade execution

**Location**: `src/core/risk/portfolio_risk.py`, `src/core/risk/manager.py`

**Result**:
```
src/core/risk/
├── portfolio_risk.py  (~767 lines) - Portfolio-level risk checks
├── manager.py         (~441 lines) - Unified risk manager with T17 integration
└── __init__.py        - Exports all portfolio risk types
```

**Implemented**:
- `PortfolioRiskChecker` class with configurable settings via `PortfolioRiskSettings`
- Position concentration check (max 5% per position)
- Symbol exposure check (max 10% per symbol across positions)
- Sector exposure check (max 25% per sector)
- Correlation check with existing positions (sector-based proxy)
- Daily loss circuit breaker (2% max, with cooldown)
- Market regime detector (bull/bear/sideways/high_vol)
- Integrated into `RiskManager.validate_trade()` as final approval gate
- Prometheus metrics: `portfolio_risk_checks_total`, `portfolio_risk_score`, `portfolio_risk_circuit_breaker_*`, `portfolio_risk_trade_decisions_total`
- API endpoints: `/api/risk/status`, `/api/risk/portfolio-risk`, `/api/risk/portfolio-risk/evaluate`, `/api/risk/portfolio-risk/reset-circuit-breaker`
- Config in `settings.py`: `portfolio_risk_enabled`, `portfolio_risk_strict_mode`

---

### T18: Bull/Bear Debate Mechanism
**Goal**: Reduce confirmation bias by having opposing viewpoints argue before trade decisions

**Location**: `src/core/agents/researchers.py`

**Implementation**:
```python
@dataclass
class ResearchReport:
    stance: Literal["bullish", "bearish"]
    confidence: float  # 0.0 to 1.0
    arguments: List[str]
    supporting_data: Dict[str, Any]
    risk_factors: List[str]

class BullResearcher:
    """Finds and presents bullish case for a symbol."""

    async def research(self, symbol: str, data: MarketData) -> ResearchReport:
        arguments = []
        confidence = 0.0

        # Check technical bullish signals
        if data.rsi < 30:
            arguments.append(f"RSI oversold at {data.rsi:.1f}")
            confidence += 0.15

        # Check sentiment
        if data.sentiment.score > 0.6:
            arguments.append(f"Positive sentiment: {data.sentiment.score:.2f}")
            confidence += 0.20

        # Check options flow
        if data.options_flow.call_put_ratio > 1.5:
            arguments.append(f"Bullish options flow: {data.options_flow.call_put_ratio:.2f} C/P ratio")
            confidence += 0.25

        return ResearchReport(
            stance="bullish",
            confidence=min(confidence, 1.0),
            arguments=arguments,
            ...
        )

class BearResearcher:
    """Finds and presents bearish case for a symbol."""
    # Mirror implementation looking for bearish signals

class DebateArbiter:
    """Synthesizes bull/bear reports into final decision."""

    async def arbitrate(
        self,
        bull_report: ResearchReport,
        bear_report: ResearchReport
    ) -> TradeDecision:
        # Weight by confidence and argument count
        bull_score = bull_report.confidence * len(bull_report.arguments)
        bear_score = bear_report.confidence * len(bear_report.arguments)

        net_score = bull_score - bear_score

        if abs(net_score) < self.min_conviction_threshold:
            return TradeDecision(action="hold", reason="Insufficient conviction")

        return TradeDecision(
            action="buy" if net_score > 0 else "sell",
            confidence=abs(net_score) / (bull_score + bear_score),
            bull_arguments=bull_report.arguments,
            bear_arguments=bear_report.arguments,
        )
```

**Tasks**:
- [ ] Create `BullResearcher` class that aggregates bullish signals from all data sources
- [ ] Create `BearResearcher` class that aggregates bearish signals from all data sources
- [ ] Implement `DebateArbiter` to synthesize opposing views into weighted decision
- [ ] Add configurable conviction threshold (minimum net score to act)
- [ ] Create debate history logging for backtesting analysis
- [ ] Add `/api/debate/{symbol}` endpoint to view current bull/bear arguments
- [ ] Create Prometheus metrics (`debate_outcomes`, `conviction_scores`)

---

### T19: Analyst Agent Abstraction
**Goal**: Refactor data providers into specialized analyst agents with common interface

**Location**: `src/core/agents/analysts/`

**Implementation**:
```python
# src/core/agents/analysts/base.py
class BaseAnalyst(ABC):
    """Abstract base class for all analyst agents."""

    name: str
    weight: float = 1.0  # Relative importance in aggregation

    @abstractmethod
    async def analyze(self, symbol: str) -> AnalystSignal:
        """Produce a signal for the given symbol."""
        ...

    @abstractmethod
    def get_signal_components(self) -> List[str]:
        """List of data points this analyst considers."""
        ...

@dataclass
class AnalystSignal:
    analyst_name: str
    symbol: str
    signal: Literal["strong_buy", "buy", "hold", "sell", "strong_sell"]
    confidence: float
    components: Dict[str, Any]  # Supporting data
    timestamp: datetime

# src/core/agents/analysts/sentiment.py
class SentimentAnalyst(BaseAnalyst):
    """Aggregates sentiment from Twitter, Reddit, StockTwits, news."""

    name = "sentiment"
    weight = 0.15

    def __init__(self):
        self.providers = [
            TwitterProvider(),
            RedditProvider(),
            StockTwitsProvider(),
            NewsProvider(),
        ]

    async def analyze(self, symbol: str) -> AnalystSignal:
        sentiments = await asyncio.gather(*[
            p.get_sentiment(symbol) for p in self.providers
        ])
        aggregated = self._aggregate(sentiments)
        return AnalystSignal(
            analyst_name=self.name,
            symbol=symbol,
            signal=self._score_to_signal(aggregated.score),
            confidence=aggregated.confidence,
            components={"twitter": ..., "reddit": ..., ...}
        )

# src/core/agents/analysts/flow.py
class FlowAnalyst(BaseAnalyst):
    """Analyzes options flow from Unusual Whales data."""

    name = "options_flow"
    weight = 0.25

    async def analyze(self, symbol: str) -> AnalystSignal:
        flow_data = await self.uw_client.get_ticker_flow(symbol)
        # Analyze call/put ratio, premium, sweep activity
        ...

# src/core/agents/analysts/fundamental.py
class FundamentalAnalyst(BaseAnalyst):
    """Analyzes insider trading, institutional holdings, analyst ratings."""

    name = "fundamental"
    weight = 0.20

    async def analyze(self, symbol: str) -> AnalystSignal:
        insider = await self.insider_provider.get_activity(symbol)
        institutional = await self.institutional_provider.get_holdings(symbol)
        ratings = await self.ratings_provider.get_ratings(symbol)
        ...

# src/core/agents/analysts/technical.py
class TechnicalAnalyst(BaseAnalyst):
    """Analyzes price action, indicators, and patterns."""

    name = "technical"
    weight = 0.40

    async def analyze(self, symbol: str) -> AnalystSignal:
        data = await self.market_data.get_ohlcv(symbol)
        rsi = calculate_rsi(data)
        macd = calculate_macd(data)
        ...
```

**Aggregation Layer**:
```python
# src/core/agents/analysts/aggregator.py
class AnalystAggregator:
    """Combines signals from all analysts into unified recommendation."""

    def __init__(self, analysts: List[BaseAnalyst]):
        self.analysts = analysts

    async def get_consensus(self, symbol: str) -> ConsensusSignal:
        signals = await asyncio.gather(*[
            a.analyze(symbol) for a in self.analysts
        ])

        # Weighted average of signals
        weighted_score = sum(
            s.confidence * self._signal_to_score(s.signal) * a.weight
            for s, a in zip(signals, self.analysts)
        ) / sum(a.weight for a in self.analysts)

        return ConsensusSignal(
            symbol=symbol,
            recommendation=self._score_to_signal(weighted_score),
            confidence=...,
            breakdown={s.analyst_name: s for s in signals}
        )
```

**Tasks**:
- [ ] Create `BaseAnalyst` abstract class with common interface in `src/core/agents/analysts/base.py`
- [ ] Implement `SentimentAnalyst` wrapping Twitter, Reddit, StockTwits, news providers
- [ ] Implement `FlowAnalyst` wrapping Unusual Whales scraper data
- [ ] Implement `FundamentalAnalyst` wrapping insider, institutional, ratings providers
- [ ] Implement `TechnicalAnalyst` wrapping existing indicator calculations
- [ ] Create `AnalystAggregator` for weighted signal combination
- [ ] Add analyst weights to config (allow per-analyst weight tuning)
- [ ] Create `/api/analysts/{symbol}` endpoint showing breakdown by analyst
- [ ] Add Prometheus metrics per analyst (`analyst_signals`, `analyst_confidence`)

---

### T20: LLM Synthesis Layer (Optional)
**Goal**: Use LLM for natural language trade explanations and anomaly detection

**Location**: `src/core/agents/llm/`

**Implementation**:
```python
# src/core/agents/llm/synthesizer.py
class TradeRationaleSynthesizer:
    """Uses LLM to generate human-readable trade explanations."""

    def __init__(self, client: OpenAI | Anthropic):
        self.client = client
        self.model = settings.llm.model  # "gpt-4o-mini" or "claude-3-haiku"

    async def explain_trade(
        self,
        signal: TradingSignal,
        analyst_breakdown: Dict[str, AnalystSignal],
        debate_result: Optional[DebateResult] = None
    ) -> str:
        prompt = f"""
        Explain this trading decision in 2-3 sentences:

        Action: {signal.action} {signal.symbol}

        Analyst signals:
        {self._format_analysts(analyst_breakdown)}

        Bull/Bear debate:
        {self._format_debate(debate_result)}

        Provide a concise explanation focusing on the key factors.
        """

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        return response.choices[0].message.content

class SignalContradictionDetector:
    """Detects when analyst signals strongly contradict each other."""

    async def detect_contradictions(
        self,
        signals: Dict[str, AnalystSignal]
    ) -> List[Contradiction]:
        # Find pairs where one is bullish and other is bearish with high confidence
        contradictions = []
        for a1, s1 in signals.items():
            for a2, s2 in signals.items():
                if a1 >= a2:
                    continue
                if self._is_opposite(s1.signal, s2.signal):
                    if s1.confidence > 0.7 and s2.confidence > 0.7:
                        contradictions.append(Contradiction(
                            analyst1=a1, signal1=s1,
                            analyst2=a2, signal2=s2,
                        ))
        return contradictions

class UnusualConditionAlert:
    """Uses LLM to detect and explain unusual market conditions."""

    async def check_conditions(self, market_data: MarketData) -> Optional[Alert]:
        # Check for unusual patterns
        if self._is_unusual(market_data):
            explanation = await self._explain_with_llm(market_data)
            return Alert(
                severity="warning",
                message=explanation,
                data=market_data
            )
        return None
```

**Tasks**:
- [ ] Add OpenAI/Anthropic API configuration to settings
- [ ] Create `TradeRationaleSynthesizer` for natural language trade explanations
- [ ] Create `SignalContradictionDetector` to flag conflicting high-confidence signals
- [ ] Create `UnusualConditionAlert` for LLM-powered anomaly detection
- [ ] Add `/api/explain/{trade_id}` endpoint for trade explanations
- [ ] Make LLM layer optional (gracefully disabled if no API key)
- [ ] Add cost tracking for LLM API calls

**Config**:
```python
class LLMSettings(BaseSettings):
    enabled: bool = False
    provider: Literal["openai", "anthropic"] = "openai"
    model: str = "gpt-4o-mini"
    api_key: Optional[str] = None
    max_tokens_per_explanation: int = 150
    monthly_budget_usd: float = 10.0
```

---

## Phase 6: Advanced Analytics (Priority: Low)

### T21: Market Regime Detection
**Goal**: Identify bull/bear/sideways markets

*Note: This overlaps with T17 (Risk Manager) which includes regime detection for risk adjustment.*

**Tasks**:
- [ ] Implement regime classifier (volatility + trend)
- [ ] Adjust strategy parameters per regime
- [ ] Backtest regime-aware strategies

### T22: Pattern Recognition
**Goal**: Detect chart patterns

**Tasks**:
- [ ] Implement head & shoulders detection
- [ ] Implement double top/bottom
- [ ] Implement triangle patterns
- [ ] Integrate patterns into signal generation

### T23: ML Signal Enhancement
**Goal**: Machine learning for signal prediction

**Tasks**:
- [ ] Feature engineering from existing indicators
- [ ] Train classifier for signal quality
- [ ] A/B test ML-enhanced vs base strategy

---

## Immediate Next Steps

### Completed
- ✅ **T1: Consolidate Metrics** - Reduced 8 files to 3
- ✅ **T2: Remove Backward Compatibility** - Clean re-exports
- ✅ **T6: WebSocket Producers** - Real-time data connected
- ✅ **T9: IBKR Testing** - Paper trading validated
- ✅ **T17: Risk Manager Agent** - Portfolio risk checks, circuit breaker, market regime
- ✅ **T7/T8: Analyst Agents & Debate Room** - Bull/Bear debate UI with multi-analyst integration

### Priority 1: Trading Safety (Before Live Trading)
1. **T10: Strategy-to-Execution Pipeline** - Connect signals to orders

### Priority 2: Enhanced Features
2. **T20: LLM Synthesis** - Optional trade explanations
3. **UI WebSocket Integration** - Real-time price/sentiment updates in dashboard

---

## Style Guide Reference

### Imports
```python
# Standard library
import os
from typing import Optional, List

# Third party
import pandas as pd
from fastapi import APIRouter

# Local - absolute for cross-package
from src.config.settings import settings

# Local - relative for same package
from .base import BaseStrategy
from ..utils.cache import CacheManager
```

### Type Hints
```python
def calculate_signal(
    self,
    data: pd.DataFrame,
    position: Optional[Position] = None,
    sentiment: Optional[AggregatedSentiment] = None,
) -> TradingSignal:
```

### Error Handling
```python
try:
    result = await self.fetch_data(symbol)
except aiohttp.ClientError as e:
    logger.error(f"Network error fetching {symbol}: {e}")
    raise DataProviderError(f"Failed to fetch {symbol}") from e
except ValidationError as e:
    logger.warning(f"Invalid data for {symbol}: {e}")
    return None
```

### Logging
```python
import logging
logger = logging.getLogger(__name__)

logger.debug("Detailed info for debugging")
logger.info("Normal operation events")
logger.warning("Unexpected but handled")
logger.error("Failed operation", exc_info=True)
```
