# Trading Bot Implementation Roadmap

*Last Updated: 2024-11-27*

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

### T2: Remove Backward Compatibility Duplication
**Goal**: Clean up `src/core/strategy.py` wrapper

**Current**: File re-exports from `strategy/base.py` AND duplicates `SignalType`, `ExitReason` enums

**Action**:
- [ ] Remove duplicate enum definitions (lines 35-50)
- [ ] Keep re-exports for backward compatibility OR migrate all imports to `strategy.base`
- [ ] Update any files still importing from `src/core/strategy.py`

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

### T6: WebSocket Data Producer Integration
**Goal**: Connect data sources to WebSocket streams

**Current State**:
- WebSocket manager exists (`src/api/websocket/manager.py`)
- 6 stream types defined but not connected to data producers

**Tasks**:
- [ ] Create background tasks that poll/stream data
- [ ] Connect IBKR market data to `price_updates` stream
- [ ] Connect sentiment aggregator to `sentiment_updates` stream
- [ ] Connect options flow to `options_flow` stream
- [ ] Add health checks to WebSocket connections

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

### T9: IBKR Integration Testing
**Goal**: Verify live execution pipeline end-to-end

**Tasks**:
- [ ] Create paper trading test script
- [ ] Test order submission, modification, cancellation
- [ ] Test position sync accuracy
- [ ] Test error handling for network failures
- [ ] Document required IBKR permissions

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

## Phase 5: Advanced Analytics (Priority: Low)

### T14: Market Regime Detection
**Goal**: Identify bull/bear/sideways markets

**Tasks**:
- [ ] Implement regime classifier (volatility + trend)
- [ ] Adjust strategy parameters per regime
- [ ] Backtest regime-aware strategies

### T15: Pattern Recognition
**Goal**: Detect chart patterns

**Tasks**:
- [ ] Implement head & shoulders detection
- [ ] Implement double top/bottom
- [ ] Implement triangle patterns
- [ ] Integrate patterns into signal generation

### T16: ML Signal Enhancement
**Goal**: Machine learning for signal prediction

**Tasks**:
- [ ] Feature engineering from existing indicators
- [ ] Train classifier for signal quality
- [ ] A/B test ML-enhanced vs base strategy

---

## Immediate Next Steps

1. **T1: Consolidate Metrics** - Biggest code quality win
2. **T6: WebSocket Producers** - Enable real-time features
3. **T9: IBKR Testing** - Validate live trading readiness

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
