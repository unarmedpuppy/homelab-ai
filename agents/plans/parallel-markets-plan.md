# Parallel Markets Execution Plan

**Date:** 2025-12-15
**Status:** DEFERRED - Design complete, implementation pending

## Summary

Enable parallel execution of opportunities across multiple markets simultaneously. Currently the bot processes opportunities sequentially from a single queue. This plan outlines the architecture for parallel execution to capture more opportunities when multiple markets have spreads.

---

## Current Architecture

```
Opportunities → Single Queue → Single Processor → Execute sequentially
```

- Opportunities from multiple markets (BTC, ETH, SOL) go into a single queue
- A single processor task pulls from the queue and executes one at a time
- Each trade takes ~5-10 seconds to execute (API calls, order placement, confirmation)
- If BTC and ETH both have spreads, ETH waits for BTC to complete

---

## Proposed Architecture

```
Opportunities → Single Queue → Worker Pool (N workers) → Execute in parallel
                                    ↓
                              Budget Manager
                              (balance, daily limits, active positions)
```

### Key Components

#### 1. BudgetManager Class

Thread-safe budget reservation for parallel execution:

```python
class BudgetManager:
    """Thread-safe budget reservation for parallel execution."""

    def __init__(self, initial_balance: float):
        self._available = initial_balance
        self._reserved = 0.0
        self._lock = asyncio.Lock()

    async def reserve(self, amount: float) -> Optional[float]:
        """Reserve budget for a trade. Returns reserved amount or None if insufficient."""
        async with self._lock:
            if self._available >= amount:
                self._available -= amount
                self._reserved += amount
                return amount
            return None

    async def release(self, amount: float):
        """Release unused budget back to pool."""
        async with self._lock:
            self._reserved -= amount
            self._available += amount

    async def commit(self, amount: float):
        """Commit spent budget (remove from reserved)."""
        async with self._lock:
            self._reserved -= amount

    async def get_available(self) -> float:
        """Get current available balance."""
        async with self._lock:
            return self._available
```

#### 2. Worker Pattern

Each opportunity spawns a worker that:
1. Reserves budget from shared pool (atomic operation)
2. Executes the trade (tranches if gradual entry enabled)
3. Releases unused budget back
4. Updates shared metrics (daily exposure, P&L)

```python
async def _opportunity_worker(self, opportunity: ArbitrageOpportunity):
    """Execute a single opportunity with budget reservation."""

    # Calculate needed budget
    needed = self._calculate_trade_budget(opportunity)

    # Try to reserve budget
    reserved = await self._budget_manager.reserve(needed)
    if not reserved:
        log.info("Insufficient budget for parallel execution",
                 asset=opportunity.market.asset,
                 needed=f"${needed:.2f}")
        return

    try:
        # Execute with reserved budget
        result = await self.on_opportunity(opportunity, budget=reserved)

        if result and result.success:
            # Commit spent amount
            await self._budget_manager.commit(result.total_cost)
            # Release unused
            await self._budget_manager.release(reserved - result.total_cost)
        else:
            # Release all reserved budget
            await self._budget_manager.release(reserved)

    except Exception as e:
        # Always release on error
        await self._budget_manager.release(reserved)
        raise
```

#### 3. Parallel Queue Processor

Replace single processor with semaphore-limited parallel execution:

```python
async def _queue_processor_loop(self):
    """Process opportunities with parallel execution."""

    # Semaphore limits concurrent workers
    semaphore = asyncio.Semaphore(self.gabagool_config.max_concurrent_opportunities)
    active_workers: Set[asyncio.Task] = set()

    while self._running:
        try:
            opportunity = await asyncio.wait_for(
                self._opportunity_queue.get(),
                timeout=0.1
            )
        except asyncio.TimeoutError:
            continue

        if not opportunity.is_valid:
            continue

        # Spawn worker with semaphore
        async def run_with_semaphore(opp):
            async with semaphore:
                await self._opportunity_worker(opp)

        task = asyncio.create_task(run_with_semaphore(opportunity))
        active_workers.add(task)
        task.add_done_callback(active_workers.discard)
```

---

## Configuration

```python
# In GabagoolConfig
parallel_opportunities_enabled: bool = False  # Disabled by default
max_concurrent_opportunities: int = 3  # Max parallel workers
```

```env
# .env.template
GABAGOOL_PARALLEL_OPPORTUNITIES_ENABLED=false
GABAGOOL_MAX_CONCURRENT_OPPORTUNITIES=3
```

---

## Design Decisions

### 1. Should workers share the same market?

**Decision:** NO - Dedupe per market (condition_id)

If two BTC opportunities come in 100ms apart, only execute the first one. The second is likely stale or the spread has changed.

```python
# Track active executions per market
self._executing_markets: Set[str] = set()

async def _opportunity_worker(self, opportunity):
    market_id = opportunity.market.condition_id

    # Skip if already executing this market
    if market_id in self._executing_markets:
        log.debug("Skipping duplicate market execution", asset=opportunity.market.asset)
        return

    self._executing_markets.add(market_id)
    try:
        # ... execute ...
    finally:
        self._executing_markets.discard(market_id)
```

### 2. Priority ordering?

**Decision:** First-come-first-served (FIFO)

Simplest approach. Larger spreads naturally get picked up faster because they're detected first. Priority queue adds complexity without clear benefit.

### 3. Concurrency limit?

**Decision:** Start with `max_concurrent_opportunities=3`, configurable

- 3 is conservative for 3 markets (BTC, ETH, SOL)
- Can scale up as more markets are added
- Natural limit is also `available_capital / min_trade_size`

---

## Shared State Requirements

State that needs protection with locks:

| State | Protection | Notes |
|-------|------------|-------|
| `available_balance` | BudgetManager lock | Atomic reserve/release |
| `daily_exposure` | Atomic increment | Track in BudgetManager |
| `daily_pnl` | Atomic update | Track in BudgetManager |
| `_executing_markets` | Set operations | Prevent duplicate executions |
| `_active_markets` | Read-only during execution | No lock needed |

---

## Implementation Order

1. **Create BudgetManager class** - `src/risk/budget_manager.py`
2. **Add config parameters** - `parallel_opportunities_enabled`, `max_concurrent_opportunities`
3. **Refactor queue processor** - Add semaphore-based parallel execution
4. **Add market deduplication** - Prevent duplicate market executions
5. **Update on_opportunity** - Accept budget parameter for worker pattern
6. **Create regression tests** - `tests/test_phase3_parallel_markets.py`
7. **Update .env.template** - Document new config options
8. **Update STRATEGY_ARCHITECTURE.md** - Document Phase 20

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Over-committing capital | BudgetManager with atomic reservation |
| API rate limiting | Semaphore limits concurrent requests |
| Race conditions on shared state | Locks on budget, atomic operations |
| Partial fills across workers | Each worker handles its own position tracking |
| Duplicate market execution | Dedupe set with condition_id |

---

## Testing Strategy

1. **Unit tests for BudgetManager** - reserve/release/commit atomicity
2. **Integration tests** - Multiple workers with shared budget
3. **Race condition tests** - Concurrent reservation attempts
4. **E2E tests** - Full parallel execution flow

---

## Dashboard Updates

- Add "Active Workers" indicator (0/3, 1/3, etc.)
- Show per-worker execution status
- Display reserved vs available budget

---

## Questions for Future

1. Should we add priority based on spread size?
2. Should we allow multiple executions per market (for gradual entry)?
3. Should we add per-market budget limits?

---

## Related Documents

- [polymarket-bot-strategy-improvements.md](./polymarket-bot-strategy-improvements.md) - Parent plan
- [STRATEGY_ARCHITECTURE.md](../apps/polymarket-bot/docs/STRATEGY_ARCHITECTURE.md) - Architecture docs
