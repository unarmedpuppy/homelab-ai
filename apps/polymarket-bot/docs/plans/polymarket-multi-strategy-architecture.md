# Polymarket Multi-Strategy Architecture Plan

**Date:** 2025-12-15
**Status:** PLANNING - Architecture design for strategy isolation

## Summary

Design a clean multi-strategy architecture that allows adding new trading strategies without breaking the existing GabagoolStrategy. Strategies should be isolated but share common infrastructure.

---

## Current State

### What Works Well
- **BaseStrategy abstract class** - Clean interface with `start()`, `stop()`, `on_opportunity()`
- **Shared execution layer** - `PolymarketClient.execute_dual_leg_order_parallel()` handles order placement
- **Event system** - `TradeEventEmitter` for strategy→dashboard communication
- **Config pattern** - Each strategy has its own config class with enable/disable flag

### What Needs Improvement
- **GabagoolStrategy is monolithic** - 3,400+ lines with directional/near-resolution baked in
- **No strategy registry** - Strategies manually wired in main.py
- **No shared position limits** - Each strategy could exceed total exposure
- **Dashboard coupling** - Strategies directly call dashboard functions

---

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              GabagoolBot (main.py)                          │
│                                                                             │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐           │
│  │ StrategyManager │   │ RiskManager     │   │ DashboardServer │           │
│  │                 │   │ (shared limits) │   │ (event consumer)│           │
│  └────────┬────────┘   └────────┬────────┘   └────────┬────────┘           │
│           │                     │                     │                     │
│  ┌────────┴────────────────────┴─────────────────────┘                     │
│  │                                                                          │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  │ Gabagool    │  │ Momentum    │  │ Mean Revert │  │ Copy Trade  │    │
│  │  │ Strategy    │  │ Strategy    │  │ Strategy    │  │ Strategy    │    │
│  │  │ (arbitrage) │  │ (trend)     │  │ (spread)    │  │ (follow)    │    │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
│  │         │                │                │                │            │
│  └─────────┴────────────────┴────────────────┴────────────────┘            │
│                              │                                              │
│                     ┌────────┴────────┐                                     │
│                     │ Shared Services │                                     │
│                     │ - PolymarketClient (execution)                       │
│                     │ - PolymarketWebSocket (data)                         │
│                     │ - MarketFinder (discovery)                           │
│                     │ - Database (persistence)                             │
│                     │ - EventEmitter (events)                              │
│                     └─────────────────┘                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Design Principles

### 1. Strategy Isolation
Each strategy:
- Has its own config class (`XxxStrategyConfig`)
- Has its own enable/disable flag
- Tracks its own positions separately
- Cannot interfere with other strategies' state

### 2. Shared Infrastructure
All strategies share:
- `PolymarketClient` - Order execution
- `PolymarketWebSocket` - Real-time data
- `MarketFinder` - Market discovery
- `Database` - Trade persistence (with strategy_id column)
- `EventEmitter` - Dashboard updates

### 3. Coordinated Risk Management
A shared `RiskManager` enforces:
- Total daily exposure limit (across all strategies)
- Total position limit per market
- Circuit breaker (halt all strategies on loss threshold)

### 4. Strategy Registry Pattern
```python
class StrategyManager:
    """Manages strategy lifecycle and coordination."""

    def __init__(self, config: AppConfig, client: PolymarketClient):
        self._strategies: Dict[str, BaseStrategy] = {}
        self._risk_manager = RiskManager(config)

    def register(self, name: str, strategy: BaseStrategy):
        """Register a strategy with the manager."""
        self._strategies[name] = strategy

    async def start_all(self):
        """Start all enabled strategies."""
        for name, strategy in self._strategies.items():
            if strategy.is_enabled:
                await strategy.start()

    async def stop_all(self):
        """Stop all running strategies."""
        for strategy in self._strategies.values():
            await strategy.stop()

    def reserve_budget(self, strategy_id: str, amount: float) -> bool:
        """Reserve budget for a trade (coordinated across strategies)."""
        return self._risk_manager.reserve(strategy_id, amount)

    def release_budget(self, strategy_id: str, amount: float):
        """Release unused budget back to pool."""
        self._risk_manager.release(strategy_id, amount)
```

---

## Implementation Plan

### Phase 1: Extract Shared Risk Management

**Goal:** Create a shared RiskManager that all strategies use for budget/exposure limits.

**Files to create:**
- `src/risk/manager.py` - RiskManager class with reserve/release pattern

**Changes:**
- GabagoolStrategy uses RiskManager instead of internal limits
- Add `strategy_id` column to trades table for attribution

### Phase 2: Create StrategyManager

**Goal:** Registry pattern for strategy lifecycle management.

**Files to create:**
- `src/strategies/manager.py` - StrategyManager class

**Changes:**
- main.py uses StrategyManager instead of direct strategy instantiation
- Strategies register themselves on init

### Phase 3: Refactor BaseStrategy Interface

**Goal:** Cleaner interface with risk management integration.

```python
class BaseStrategy(ABC):
    """Base class for all trading strategies."""

    strategy_id: str  # Unique identifier for this strategy

    @abstractmethod
    async def start(self) -> None:
        """Start the strategy."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the strategy."""
        pass

    @abstractmethod
    async def on_opportunity(self, opportunity: ArbitrageOpportunity) -> Optional[TradeResult]:
        """Process a trading opportunity."""
        pass

    @property
    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if strategy is enabled."""
        pass

    def request_budget(self, amount: float) -> bool:
        """Request budget from shared RiskManager."""
        return self._strategy_manager.reserve_budget(self.strategy_id, amount)

    def release_budget(self, amount: float):
        """Release budget back to shared pool."""
        self._strategy_manager.release_budget(self.strategy_id, amount)
```

### Phase 4: Add New Strategy Template

**Goal:** Document how to add a new strategy.

**Files to create:**
- `src/strategies/template.py` - Example strategy implementation
- `docs/ADDING_STRATEGIES.md` - Step-by-step guide

---

## Adding a New Strategy (Future Process)

### Step 1: Create Config Class
```python
# In config.py
@dataclass
class MomentumStrategyConfig:
    """Momentum strategy configuration."""
    enabled: bool = False
    lookback_periods: int = 5
    min_trend_strength: float = 0.6
    max_position_usd: float = 10.0

    @classmethod
    def from_env(cls) -> "MomentumStrategyConfig":
        return cls(
            enabled=os.getenv("MOMENTUM_ENABLED", "false").lower() == "true",
            # ... other fields
        )
```

### Step 2: Create Strategy Class
```python
# In strategies/momentum.py
class MomentumStrategy(BaseStrategy):
    """Trend-following strategy for 15-minute markets."""

    strategy_id = "momentum"

    def __init__(self, client: PolymarketClient, config: AppConfig):
        self.client = client
        self.config = config.momentum
        self._running = False

    @property
    def is_enabled(self) -> bool:
        return self.config.enabled

    async def start(self):
        if not self.is_enabled:
            return
        self._running = True
        # Setup monitoring, callbacks, etc.

    async def stop(self):
        self._running = False

    async def on_opportunity(self, opportunity):
        # Strategy-specific logic
        if not self._should_trade(opportunity):
            return None

        # Request budget from shared pool
        if not self.request_budget(self.config.max_position_usd):
            return None  # Insufficient budget

        try:
            result = await self._execute_trade(opportunity)
            return result
        finally:
            # Release any unused budget
            self.release_budget(unused_amount)
```

### Step 3: Register Strategy
```python
# In main.py
async def _init_strategies(self):
    self.strategy_manager = StrategyManager(self.config, self.client)

    # Register all strategies
    self.strategy_manager.register("gabagool", GabagoolStrategy(self.client, self.config))
    self.strategy_manager.register("momentum", MomentumStrategy(self.client, self.config))
    # ... more strategies

    await self.strategy_manager.start_all()
```

### Step 4: Add Environment Variables
```env
# .env.template
# Momentum Strategy
MOMENTUM_ENABLED=false
MOMENTUM_LOOKBACK_PERIODS=5
MOMENTUM_MIN_TREND_STRENGTH=0.6
MOMENTUM_MAX_POSITION_USD=10.0
```

---

## Risk Coordination

### Budget Reservation Pattern

```python
class RiskManager:
    """Coordinates risk across all strategies."""

    def __init__(self, config: AppConfig):
        self._lock = asyncio.Lock()
        self._available_budget = config.gabagool.max_daily_exposure_usd
        self._reserved: Dict[str, float] = {}  # strategy_id -> reserved amount
        self._daily_pnl: Dict[str, float] = {}  # strategy_id -> P&L

    async def reserve(self, strategy_id: str, amount: float) -> bool:
        """Reserve budget for a trade. Returns True if approved."""
        async with self._lock:
            if amount > self._available_budget:
                return False

            self._available_budget -= amount
            self._reserved[strategy_id] = self._reserved.get(strategy_id, 0) + amount
            return True

    async def release(self, strategy_id: str, amount: float):
        """Release unused budget back to pool."""
        async with self._lock:
            self._available_budget += amount
            self._reserved[strategy_id] = max(0, self._reserved.get(strategy_id, 0) - amount)

    async def record_pnl(self, strategy_id: str, pnl: float):
        """Record P&L for a strategy (for circuit breaker)."""
        async with self._lock:
            self._daily_pnl[strategy_id] = self._daily_pnl.get(strategy_id, 0) + pnl

            # Check circuit breaker
            total_pnl = sum(self._daily_pnl.values())
            if total_pnl < -self._max_daily_loss:
                self._circuit_breaker_triggered = True
```

### Position Limit Coordination

```python
class PositionCoordinator:
    """Tracks positions across all strategies."""

    def __init__(self):
        self._positions: Dict[str, Dict[str, float]] = {}  # market_id -> {strategy_id -> shares}

    def get_total_position(self, market_id: str) -> float:
        """Get total position across all strategies."""
        return sum(self._positions.get(market_id, {}).values())

    def can_add_position(self, market_id: str, shares: float, max_total: float) -> bool:
        """Check if adding position would exceed limit."""
        current = self.get_total_position(market_id)
        return (current + shares) <= max_total
```

---

## Migration Path

### Minimal Disruption Approach

1. **Keep GabagoolStrategy unchanged** - Don't refactor existing working code
2. **Add StrategyManager alongside** - New strategies use it, Gabagool can opt-in later
3. **Add RiskManager gradually** - Start with budget tracking, add coordination over time
4. **New strategies use new patterns** - Existing code continues working

### Database Schema Addition

```sql
-- Add strategy_id to trades table
ALTER TABLE trades ADD COLUMN strategy_id TEXT DEFAULT 'gabagool';

-- Index for strategy queries
CREATE INDEX idx_trades_strategy ON trades(strategy_id);
```

---

## Strategy Ideas (Future)

| Strategy | Type | Risk Level | Description |
|----------|------|------------|-------------|
| **Gabagool** | Arbitrage | Low | YES+NO < $1.00 (current) |
| **Momentum** | Directional | Medium | Follow price trends in final minutes |
| **Mean Reversion** | Directional | Medium | Bet on overreactions returning to fair value |
| **Copy Trading** | Following | Low | Mirror successful traders |
| **Market Making** | Liquidity | High | Place orders on both sides, capture spread |
| **Event Driven** | Directional | High | Trade based on external signals (news, etc.) |

---

## Implementation Priority

| Priority | Task | Effort | Impact |
|----------|------|--------|--------|
| **P1** | Add `strategy_id` to trades table | Low | Enables attribution |
| **P2** | Create RiskManager with budget reservation | Medium | Enables coordination |
| **P3** | Create StrategyManager registry | Medium | Clean lifecycle |
| **P4** | Document adding new strategies | Low | Developer experience |
| **P5** | Refactor Gabagool to use RiskManager | Medium | Consistency |

---

## Questions for Review

1. **Budget sharing vs per-strategy limits?**
   - Option A: Single shared pool, strategies compete for budget
   - Option B: Per-strategy limits with optional shared reserve
   - Recommendation: Start with shared pool, add per-strategy limits later

2. **Strategy priority?**
   - Should some strategies have priority for budget/execution?
   - Recommendation: FIFO for now, add priority queue later if needed

3. **Position conflicts?**
   - What if two strategies want opposite positions on same market?
   - Recommendation: Allow it (hedging), but log for monitoring

4. **Dashboard attribution?**
   - Should dashboard show which strategy made each trade?
   - Recommendation: Yes, add strategy_id to trade display

---

## Related Documents

- [polymarket-bot-strategy-improvements.md](./polymarket-bot-strategy-improvements.md) - Phase 1-2 improvements
- [parallel-markets-plan.md](./parallel-markets-plan.md) - Multi-market parallelization
- [STRATEGY_ARCHITECTURE.md](../../apps/polymarket-bot/docs/STRATEGY_ARCHITECTURE.md) - Current architecture
