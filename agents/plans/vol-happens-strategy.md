# Vol Happens Strategy Plan

**Date:** 2025-12-15
**Status:** IMPLEMENTED - Phase 1 (Foundation) complete, ready for paper trading

## Summary

"Vol Happens" is a volatility/mean reversion strategy that builds a hedged position over time by buying each side when it hits a target price. It bets that prices will oscillate enough within the 15-minute window for both sides to become cheap at some point.

---

## Strategy Rules

### Entry Conditions

**First Leg (Initiating Position):**
- Price of YES or NO is **at or below $0.48**
- The OTHER side is **at or below $0.52** (prevents entering during strong trends)
- No existing Vol Happens position on this market
- Market has sufficient time remaining (configurable, default >5 minutes)

**Second Leg (Completing Hedge):**
- First leg already filled
- Other side price drops to **at or below $0.48**
- Buy **equal shares** to first leg (not equal dollars)

### Position Sizing

| Parameter | Value | Notes |
|-----------|-------|-------|
| Max position | $5.00 total | Combined both legs |
| First leg max | $2.00 | Single order |
| Second leg max | $3.00 | Must match shares from first leg |
| Min spread target | $0.02 | YES + NO ≤ $0.96 when complete |

### Exit Rules

**Success Exit (Hedged):**
- Both legs filled → Hold to resolution
- Guaranteed payout: 1 share pair = $1.00
- Profit: $1.00 - (YES cost + NO cost)

**Failure Exit (Unhedged):**
- Time remaining ≤ 3:30 (configurable)
- Second leg never filled
- **Hard exit** - sell first leg at market price
- Accept the loss

---

## Example Scenarios

### Scenario 1: Success (Mean Reversion)
```
10:00:00 - Market opens, YES=$0.52, NO=$0.48
10:00:05 - Vol Happens: NO ≤ $0.48 AND YES ≤ $0.52 ✓
         → Buy 4.17 shares NO @ $0.48 = $2.00
         → State: WAITING_FOR_HEDGE

10:03:00 - Price swings, YES=$0.47, NO=$0.53
         → YES ≤ $0.48 ✓
         → Buy 4.17 shares YES @ $0.47 = $1.96
         → State: HEDGED

10:15:00 - Resolution
         → Payout: 4.17 shares × $1.00 = $4.17
         → Cost: $2.00 + $1.96 = $3.96
         → Profit: $0.21 (5.3%)
```

### Scenario 2: Failure (Strong Trend)
```
10:00:00 - Market opens, YES=$0.55, NO=$0.45
         → NO ≤ $0.48 ✓ BUT YES > $0.52 ✗
         → No entry (trend filter)

10:01:00 - YES=$0.52, NO=$0.48
         → NO ≤ $0.48 ✓ AND YES ≤ $0.52 ✓
         → Buy 4.17 shares NO @ $0.48 = $2.00
         → State: WAITING_FOR_HEDGE

10:05:00 - Price trends, YES=$0.65, NO=$0.35
         → YES still > $0.48, waiting...

10:11:30 - Time remaining = 3:30, still unhedged
         → HARD EXIT: Sell NO at market ($0.30)
         → Loss: $2.00 - $1.25 = -$0.75
```

### Scenario 3: Better Spread Capture
```
10:00:00 - YES=$0.50, NO=$0.50
         → Neither at $0.48 yet, waiting...

10:02:00 - YES=$0.48, NO=$0.52
         → YES ≤ $0.48 ✓ AND NO ≤ $0.52 ✓
         → Buy 4.17 shares YES @ $0.48 = $2.00

10:04:00 - YES=$0.54, NO=$0.46
         → NO ≤ $0.48 ✓
         → Buy 4.17 shares NO @ $0.46 = $1.92
         → HEDGED with $0.06 spread!

10:15:00 - Payout: $4.17, Cost: $3.92, Profit: $0.25 (6.4%)
```

---

## State Machine

```
                    ┌─────────────────┐
                    │     IDLE        │
                    │  (no position)  │
                    └────────┬────────┘
                             │
                             │ Entry conditions met:
                             │ - Side A ≤ $0.48
                             │ - Side B ≤ $0.52
                             │ - Time > exit_threshold
                             ▼
                    ┌─────────────────┐
                    │ WAITING_FOR_    │
            ┌───────│     HEDGE       │───────┐
            │       │ (first leg only)│       │
            │       └─────────────────┘       │
            │                                 │
            │ Other side ≤ $0.48              │ Time ≤ exit_threshold
            │                                 │
            ▼                                 ▼
   ┌─────────────────┐               ┌─────────────────┐
   │     HEDGED      │               │   FORCE_EXIT    │
   │ (both legs)     │               │ (sell first leg)│
   └────────┬────────┘               └────────┬────────┘
            │                                 │
            │ Resolution                      │ Order filled
            ▼                                 ▼
   ┌─────────────────┐               ┌─────────────────┐
   │    RESOLVED     │               │     CLOSED      │
   │ (profit locked) │               │   (loss taken)  │
   └─────────────────┘               └─────────────────┘
```

---

## Configuration

```python
@dataclass
class VolHappensConfig:
    """Vol Happens strategy configuration."""

    # Enable/disable
    enabled: bool = False

    # Markets to trade
    markets: List[str] = field(default_factory=lambda: ["BTC", "ETH", "SOL"])

    # Entry thresholds
    entry_price_threshold: float = 0.48  # Buy when side ≤ this price
    trend_filter_threshold: float = 0.52  # Other side must be ≤ this

    # Position sizing
    first_leg_max_usd: float = 2.00  # Max for initiating position
    total_max_usd: float = 5.00  # Max total position (both legs)

    # Exit rules
    exit_time_remaining_seconds: float = 210.0  # 3:30 = 210 seconds
    min_time_to_enter_seconds: float = 300.0  # Don't enter with < 5 min left

    # Execution
    dry_run: bool = True  # Paper trade first
```

```env
# .env.template additions
# Vol Happens Strategy
VOL_HAPPENS_ENABLED=false
VOL_HAPPENS_MARKETS=BTC,ETH,SOL
VOL_HAPPENS_ENTRY_PRICE=0.48
VOL_HAPPENS_TREND_FILTER=0.52
VOL_HAPPENS_FIRST_LEG_MAX=2.00
VOL_HAPPENS_TOTAL_MAX=5.00
VOL_HAPPENS_EXIT_TIME_SECONDS=210
VOL_HAPPENS_MIN_ENTRY_TIME_SECONDS=300
VOL_HAPPENS_DRY_RUN=true
```

---

## Data Structures

```python
@dataclass
class VolHappensPosition:
    """Tracks a Vol Happens position."""

    # Identification
    id: str  # UUID
    market: Market15Min
    strategy_id: str = "vol_happens"

    # First leg
    first_leg_side: str  # "YES" or "NO"
    first_leg_shares: float
    first_leg_price: float
    first_leg_cost: float
    first_leg_filled_at: datetime

    # Second leg (optional until hedged)
    second_leg_shares: Optional[float] = None
    second_leg_price: Optional[float] = None
    second_leg_cost: Optional[float] = None
    second_leg_filled_at: Optional[datetime] = None

    # State
    state: str = "WAITING_FOR_HEDGE"  # WAITING_FOR_HEDGE, HEDGED, FORCE_EXIT, RESOLVED, CLOSED

    # Computed
    @property
    def is_hedged(self) -> bool:
        return self.second_leg_shares is not None

    @property
    def total_cost(self) -> float:
        cost = self.first_leg_cost
        if self.second_leg_cost:
            cost += self.second_leg_cost
        return cost

    @property
    def spread_captured(self) -> float:
        """Spread in dollars (only valid when hedged)."""
        if not self.is_hedged:
            return 0.0
        return 1.0 - (self.first_leg_price + self.second_leg_price)
```

---

## Integration with Existing Architecture

### Shared Components (from Gabagool)
- `PolymarketClient` - Order execution
- `PolymarketWebSocket` - Real-time prices
- `MarketFinder` - 15-minute market discovery
- `Database` - Trade persistence (add `strategy_id` column)
- `EventEmitter` - Dashboard updates

### New Components
- `VolHappensStrategy` - Strategy class
- `VolHappensConfig` - Configuration
- `VolHappensPosition` - Position tracking

### Strategy Isolation
- Vol Happens and Gabagool operate **independently**
- Each tracks its own positions
- Both can have positions on the same market simultaneously
- No shared budget pool (yet) - each has its own limits

---

## Implementation Plan

### Phase 1: Foundation
1. Create `VolHappensConfig` in `config.py`
2. Create `VolHappensStrategy` class in `strategies/vol_happens.py`
3. Add `strategy_id` column to trades table
4. Wire up in `main.py`

### Phase 2: Core Logic
1. Implement entry detection (price + trend filter)
2. Implement first leg execution
3. Implement second leg monitoring and execution
4. Implement force exit at time threshold

### Phase 3: Dashboard Integration
1. Add Vol Happens positions to dashboard
2. Show state (WAITING/HEDGED/etc)
3. Show P&L for completed trades

### Phase 4: Testing
1. Unit tests for entry/exit logic
2. Integration tests with mock market data
3. Paper trading on live markets

---

## Risk Analysis

### Expected Outcomes

| Scenario | Probability | Outcome |
|----------|-------------|---------|
| Both legs fill | ~60-70% | +$0.10 to +$0.25 profit |
| Force exit at loss | ~25-35% | -$0.50 to -$1.00 loss |
| Entry conditions never met | ~5-10% | $0 (no trade) |

### Risk Mitigations

1. **Trend Filter** - Only enter when other side ≤ $0.52
   - Prevents entering during strong directional moves

2. **Small Position Size** - Max $2 first leg
   - Limits downside on unhedged exits

3. **Time-Based Exit** - Hard cut at 3:30 remaining
   - Prevents holding into resolution unhedged

4. **Market Selection** - Only 15-min BTC/ETH/SOL
   - High liquidity, known behavior

### Worst Case

- Enter first leg at $0.48
- Market trends hard, other side never drops
- Exit at 3:30 remaining, price is $0.20
- Loss: $2.00 - $0.83 = **-$1.17**

This is acceptable given the small position size and expected win rate.

---

## Questions Resolved

| Question | Answer |
|----------|--------|
| Entry trigger | At or below $0.48 |
| Second leg trigger | At or below $0.48 |
| Position sizing | $2.00 first leg, equal shares second leg |
| Exit timing | 3:30 remaining (configurable) |
| Multiple positions | One per market |
| Trend filter | Other side must be ≤ $0.52 |
| Markets | BTC, ETH, SOL 15-min only |
| Gabagool interaction | Independent operation |

---

## Implementation Status

### Phase 1: Foundation ✅ COMPLETE
1. ✅ **VolHappensConfig** - Added to `src/config.py` with all parameters
2. ✅ **VolHappensStrategy** - Created `src/strategies/vol_happens.py`
3. ✅ **Database schema** - Added `strategy_id` column via migration
4. ✅ **Main.py wiring** - Strategy starts alongside Gabagool
5. ✅ **.env.template** - Documented all configuration options
6. ✅ **Regression tests** - Created `tests/test_vol_happens.py`

### Next Steps
1. **Paper trade** - Enable with `VOL_HAPPENS_ENABLED=true` and `VOL_HAPPENS_DRY_RUN=true`
2. **Monitor logs** - Verify entry/exit logic works as expected
3. **Go live** - Set `VOL_HAPPENS_DRY_RUN=false` with small positions first

---

## Related Documents

- [polymarket-multi-strategy-architecture.md](./polymarket-multi-strategy-architecture.md) - Overall multi-strategy design
- [polymarket-bot-strategy-improvements.md](./polymarket-bot-strategy-improvements.md) - Gabagool improvements
- [STRATEGY_ARCHITECTURE.md](../../apps/polymarket-bot/docs/STRATEGY_ARCHITECTURE.md) - Current architecture
