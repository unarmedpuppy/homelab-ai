# Polymarket Strategy Improvements Plan

## Context: $35 Loss Analysis (Dec 17, 2025)

### Root Cause
Partial fills creating **unhedged directional exposure**:
1. Bot attempts arbitrage (buy YES + NO where sum < $1.00)
2. One leg fills (MATCHED), other goes LIVE and doesn't fill
3. We end up with single-sided position (e.g., only YES shares)
4. Market resolves → 50/50 gamble → losses when our side loses

### Key Insight from @gemchange_ltd Analysis
A trader achieved **99.5% win rate** on 15-minute crypto markets using **momentum lag**, not arbitrage:
- Exploits fact that when crypto moves hard, Polymarket prices **lag by 30-90 seconds**
- Order books thin out, prices stick while underlying asset keeps moving
- Looks for **3-5% gaps** between where market should be vs current price
- Signal: "volatility compression into directional breaks"

### Market Reality (from research)
- Only **16.8% of Polymarket traders** are profitable
- Order book rule: If spread > 5¢, wait for more participants
- Volume filter: Trade markets with >$50k 24h volume (usually sub-2¢ spreads)
- Hybrid order book: off-chain matching, on-chain settlement

---

## Phase 1: Fix Arbitrage Execution (IMMEDIATE)

### Problem
When partial fill occurs:
- YES fills at $0.37, NO goes LIVE at $0.50
- We wait 2 seconds, NO still LIVE
- We cancel NO order
- We're left holding only YES shares
- Market resolves → we lose if DOWN wins

### Solution: Immediate Exit on Partial Fill

**Current behavior:**
```
1. Place YES order → MATCHED
2. Place NO order → LIVE
3. Wait 2 seconds
4. Cancel LIVE order
5. Log "partial fill" and continue
6. Hold single-sided position until resolution (GAMBLE)
```

**New behavior:**
```
1. Place YES order → MATCHED
2. Place NO order → LIVE
3. Wait 2 seconds
4. If still LIVE:
   a. Cancel LIVE order
   b. IMMEDIATELY sell filled shares at market
   c. Accept small loss (spread cost) vs 50% loss risk
5. Log "partial fill exited" with P&L
```

### Implementation Details

1. **Detect partial fill** (already done)
   - YES: MATCHED, NO: LIVE (or vice versa)

2. **Exit filled position immediately**
   - Get current best bid for filled side
   - Place market sell order (or limit at best bid - 1¢)
   - Accept slippage as cost of exiting bad trade

3. **Calculate and log exit P&L**
   - Entry cost: what we paid for filled shares
   - Exit proceeds: what we got selling
   - Loss = entry - exit (typically 1-3¢ per share)

4. **Config options**
   ```python
   partial_fill_exit_enabled: bool = True  # Exit partial fills immediately
   partial_fill_max_slippage_cents: float = 2.0  # Max slippage to accept on exit
   ```

### Expected Outcome
- Trade same partial fill scenario
- Instead of -$5 to -$10 loss (50% of position), lose -$0.20 to -$0.50 (spread cost)
- Much smaller, predictable losses

---

## Phase 2: Hybrid Momentum Filter (FUTURE)

### Concept
Keep arbitrage as base strategy, but add **momentum stability filter**:
- Only execute arbitrage when market is "stable" (no strong directional move)
- Avoid entering during volatility spikes when partial fills are more likely
- Momentum traders are taking liquidity → order books thin → our arb fails

### Momentum Stability Signals

1. **Price velocity check**
   - Track BTC/ETH/SOL spot price over last 60 seconds
   - If |price change| > 0.5% in 60s → market is "hot" → skip
   - If |price change| < 0.2% in 60s → market is "stable" → trade

2. **Order book depth check**
   - Before trading, verify depth on both sides
   - Require minimum $500 depth at our price level on BOTH sides
   - If one side is thin → momentum traders already hit it → skip

3. **Spread stability check**
   - Track spread over last 30 seconds via WebSocket
   - If spread was 3¢ but now 1.5¢ → someone just bought → market moving
   - Only trade if spread has been stable (within 0.5¢) for 30+ seconds

### Implementation Approach

1. **Add spot price feed**
   - Connect to Binance/Coinbase WebSocket for BTC/ETH/SOL
   - Calculate rolling 60-second price change
   - Expose `get_price_velocity(asset)` method

2. **Add stability score**
   ```python
   def calculate_stability_score(asset: str) -> float:
       """0.0 = volatile, 1.0 = stable"""
       price_velocity = get_price_velocity(asset)  # % change in 60s
       spread_stability = get_spread_stability(asset)  # std dev of spread
       depth_score = get_depth_score(asset)  # min depth / target depth

       # Weighted combination
       return (
           0.4 * (1 - min(price_velocity / 1.0, 1.0)) +  # Lower velocity = better
           0.3 * (1 - min(spread_stability / 0.01, 1.0)) +  # Lower std dev = better
           0.3 * depth_score
       )
   ```

3. **Gate arbitrage on stability**
   ```python
   if stability_score < 0.6:
       log.info("Skipping arb - market unstable", score=stability_score)
       return
   ```

### Config Options
```python
# Phase 2: Momentum stability filter
stability_filter_enabled: bool = False  # Enable momentum stability check
min_stability_score: float = 0.6  # Minimum stability to trade (0-1)
price_velocity_window_seconds: float = 60.0  # Window for price change calc
max_price_velocity_pct: float = 0.5  # Max % change in window to be "stable"
min_depth_per_side_usd: float = 500.0  # Minimum order book depth required
spread_stability_window_seconds: float = 30.0  # Window for spread stability
```

---

## Implementation Priority

### Immediate (Phase 1)
1. Add `partial_fill_exit_enabled` config option
2. Modify `execute_dual_leg_order_parallel()` to exit on partial fill
3. Add market sell logic for exiting filled position
4. Test with small trades

### Future (Phase 2)
1. Research and add spot price feed (Binance WebSocket)
2. Implement stability score calculation
3. Add stability gate to arbitrage entry
4. Backtest stability filter effectiveness

---

## References

- [@gemchange_ltd Twitter](https://x.com/gemchange_ltd) - Momentum lag strategy analysis
- [Top 10 Polymarket Trading Strategies](https://www.datawallet.com/crypto/top-polymarket-trading-strategies) - 16.8% trader profitability stat
- [Polymarket Order Book Docs](https://docs.polymarket.com/polymarket-learn/trading/using-the-orderbook) - Spread and depth guidance
- Polymarket uses hybrid CLOB: off-chain matching, on-chain settlement
