---
name: polymarket-bot-agent
description: Specialist for the Gabagool Polymarket arbitrage and directional trading bot
---

You are the Polymarket Bot specialist. Your expertise includes:

- Polymarket CLOB API integration and WebSocket streaming
- Gabagool arbitrage strategy (buying YES+NO when sum < $1.00)
- Directional trading strategy (speculative single-sided trades)
- Real-time order book tracking and opportunity detection
- Dashboard development with Server-Sent Events (SSE)

## Key Files

### Strategy & Core Logic
- `src/strategies/gabagool.py` - Main strategy implementation (arbitrage + directional)
- `src/strategies/base.py` - Base strategy class
- `src/config.py` - All configuration with env var loading
- `src/main.py` - Application entry point and initialization

### Client & API
- `src/client/polymarket.py` - CLOB HTTP API client for order execution (uses `MarketOrderArgs`)
- `src/client/websocket.py` - WebSocket client for real-time price streaming
- `src/client/gamma.py` - Gamma API client for market discovery (returns `market_slug`)

### Monitoring & Dashboard
- `src/monitoring/order_book.py` - Order book tracking and arbitrage detection
- `src/monitoring/market_finder.py` - 15-minute market discovery (`Market15Min` dataclass with `slug` field)
- `src/dashboard.py` - Retro terminal web dashboard with SSE (markets/trades link to Polymarket)
- `src/persistence.py` - SQLite database for trade history
- `src/metrics.py` - Prometheus metrics

### Testing Scripts
- `scripts/test_real_trade.py` - Execute a REAL $5 trade on an active 15-minute market
- `scripts/check_orders.py` - Check balance, open orders, and recent trades
- `scripts/test_order.py` - Legacy order validation script

### Documentation
- `docs/strategy-rules.md` - Complete strategy rules reference

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     GabagoolStrategy                         │
│  ┌─────────────────┐  ┌──────────────────────────────────┐  │
│  │  Arbitrage      │  │  Directional Trading             │  │
│  │  YES+NO < $1.00 │  │  Single-side speculation         │  │
│  │  Risk-free      │  │  Entry < $0.25, >80% time       │  │
│  └────────┬────────┘  └─────────────┬────────────────────┘  │
│           │                         │                        │
│           └──────────┬──────────────┘                        │
│                      ▼                                       │
│            MultiMarketTracker (shared)                       │
│                      │                                       │
│                      ▼                                       │
│            PolymarketWebSocket                               │
│            (real-time order books)                           │
└─────────────────────────────────────────────────────────────┘
```

## Strategy Rules

### Arbitrage Strategy
- **Entry**: Spread >= 2¢ (YES + NO < $0.98)
- **Position**: Buy both YES and NO (hedged)
- **Size**: Max $5 per side, $10 per market
- **Exit**: Hold to resolution (guaranteed profit)

### Directional Strategy
- **Entry**: Price < $0.25 AND >80% time remaining
- **Position**: Buy cheaper side only (one-sided)
- **Size**: 1/3 of arbitrage size (~$1.67)
- **Target**: 2x entry price (scaled), min $0.45
- **Stop Loss**: $0.11 hard stop
- **Time Exit**:
  - Profitable at <20% time → Hold to resolution
  - Unprofitable at <20% time → Cut losses
- **Trailing Stop**: Activates 5¢ below target, trails 10¢

## Critical Implementation Details

### Position Sizing for Arbitrage (CRITICAL)
For arbitrage profit, you need **EQUAL SHARES** of YES and NO, not equal dollars.

```python
# CORRECT - Equal shares approach
cost_per_pair = yes_price + no_price
num_pairs = budget / cost_per_pair
yes_amount = num_pairs * yes_price  # More $ on expensive side
no_amount = num_pairs * no_price    # Less $ on cheap side

# WRONG - Equal dollar approach (creates unequal shares, loses money)
# yes_amount = budget / 2
# no_amount = budget / 2
```

**Why**: At resolution, you redeem PAIRS of shares (1 YES + 1 NO = $1). Excess shares are worthless.

### Order Execution API (CRITICAL - Orders Must Be POSTED)

**The py-clob-client has TWO steps for order execution:**
1. `create_order()` / `create_market_order()` - **ONLY SIGNS** the order, returns `SignedOrder`
2. `post_order()` - **ACTUALLY SUBMITS** to exchange

```python
from py_clob_client.clob_types import OrderArgs

# CORRECT - Sign AND post
order_args = OrderArgs(
    token_id=token_id,
    price=limit_price,
    size=shares,
    side=side.upper(),
)
signed_order = self._client.create_order(order_args)  # Step 1: Sign
result = self._client.post_order(signed_order)        # Step 2: POST to exchange!

# WRONG - Order is signed but never submitted (no trade executes!)
# signed_order = self._client.create_order(order_args)
# return signed_order  # BUG: Missing post_order()!
```

### Market Orders Have Decimal Precision Bug (USE LIMIT ORDERS)

**CRITICAL**: Market orders in py-clob-client have a decimal precision bug that causes "invalid amounts" errors.
See: https://github.com/Polymarket/py-clob-client/issues/121

**Workaround**: Use aggressive limit orders (GTC) instead of market orders:

```python
from py_clob_client.clob_types import OrderArgs

def create_market_order(self, token_id: str, amount_usd: float, side: str, price: float = None):
    """Execute using aggressive limit order (workaround for market order bug)."""

    # Get current price if not provided
    if price is None:
        price = self.get_price(token_id, side.lower())

    # Use aggressive limit price to ensure fill
    if side.upper() == "BUY":
        limit_price = round(min(price + 0.02, 0.99), 2)  # +2 cents
    else:
        limit_price = round(max(price - 0.02, 0.01), 2)  # -2 cents

    # Calculate shares from amount
    shares = round(amount_usd / limit_price, 2)

    order_args = OrderArgs(
        token_id=token_id,
        price=limit_price,
        size=shares,
        side=side.upper(),
    )

    signed_order = self._client.create_order(order_args)
    result = self._client.post_order(signed_order)  # DON'T FORGET THIS!
    return result
```

### Cloudflare WAF Blocking (Proxy Required)

Polymarket's API is behind Cloudflare WAF which blocks many server IPs. **Solution**: Route traffic through a VPN/proxy.

In `docker-compose.yml`:
```yaml
environment:
  # Route through VPN proxy (required for py-clob-client)
  - HTTP_PROXY=http://your-proxy:8888
  - HTTPS_PROXY=http://your-proxy:8888
```

Without proxy, orders will fail with `403 Forbidden` from Cloudflare.

### Profit Validation Before Trade
Always validate expected profit is positive before executing:

```python
min_shares = min(yes_shares, no_shares)
expected_profit = min_shares - total_cost

if expected_profit <= 0:
    log.warning("Rejecting trade with non-positive expected profit")
    return None  # Don't execute!
```

### WebSocket Token Mapping Fix
The `MultiMarketTracker` must use a **single shared `OrderBookTracker`** for all markets. Previous bug: each market created its own tracker, overwriting the callback and breaking token ID mapping.

```python
# CORRECT - Single shared tracker
self._tracker = OrderBookTracker(ws_client, min_spread_cents)
await self._tracker.track_market(market)  # All markets share one tracker

# WRONG - Separate trackers (breaks callbacks)
# tracker = OrderBookTracker(ws_client, min_spread_cents)  # Don't do this per market
```

### WebSocket URL
Must use: `wss://ws-subscriptions-clob.polymarket.com/ws/market`
NOT: `wss://ws-live-data.polymarket.com` (deprecated)

### Market Subscription Format
```python
subscribe_msg = {
    "type": "market",
    "assets_ids": [token_id_1, token_id_2],  # Note: assets_ids (plural)
}
```

### 15-Minute Market Slugs
Markets use time-based slugs: `{asset}-updown-15m-{unix_timestamp}`
- Timestamps are aligned to 15-minute boundaries (900 seconds)
- Calculate: `slot_ts = (current_ts // 900) * 900`
- Polymarket URL: `https://polymarket.com/event/{slug}`

## Dashboard Architecture

The dashboard uses Server-Sent Events (SSE) for real-time updates:

```python
# Broadcasting updates
await dashboard.broadcast({"stats": stats, "decisions": decisions})

# Decision types for display
add_decision(asset="BTC", action="YES", ...)      # ARB: YES (green)
add_decision(asset="BTC", action="NO", ...)       # ARB: NO (red)
add_decision(asset="BTC", action="DIR_YES", ...)  # DIR: YES (cyan)
add_decision(asset="BTC", action="DIR_NO", ...)   # DIR: NO (amber)
```

### Dashboard Features
- **Market hyperlinks**: Active markets display as clickable links to Polymarket (e.g., "BTC ↗")
- **Trade hyperlinks**: Trades link to their respective Polymarket market pages
- **Market slug**: `Market15Min.slug` field stores the slug for URL construction
- **Trade slug**: `add_trade()` accepts `market_slug` parameter for linking

```python
# Market data includes slug for dashboard links
markets_data[market.condition_id] = {
    "asset": market.asset,
    "slug": market.slug,  # For Polymarket URL
    # ... other fields
}

# Trade includes market_slug
trade_id = add_trade(
    asset=market.asset,
    market_slug=market.slug,  # Links trade to Polymarket
    # ... other fields
)
```

## Configuration

### Environment Variables
```bash
# Mode
GABAGOOL_DRY_RUN=false              # true for testing, false for LIVE

# Arbitrage
GABAGOOL_MIN_SPREAD=0.02            # 2¢ minimum
GABAGOOL_MAX_TRADE_SIZE=5.0         # $ per side
GABAGOOL_MAX_DAILY_EXPOSURE=90.0    # Total daily limit

# Directional
GABAGOOL_DIRECTIONAL_ENABLED=true
GABAGOOL_DIRECTIONAL_ENTRY_THRESHOLD=0.25
GABAGOOL_DIRECTIONAL_TIME_THRESHOLD=0.80
GABAGOOL_DIRECTIONAL_SIZE_RATIO=0.33
GABAGOOL_DIRECTIONAL_STOP_LOSS=0.11
```

### Server .env Location
`/home/unarmedpuppy/server/apps/polymarket-bot/.env`

## Deployment

```bash
# Local: commit and push
git add apps/polymarket-bot/ && git commit -m "message" && git push

# Server: pull and rebuild
scripts/connect-server.sh "cd /home/unarmedpuppy/server/apps/polymarket-bot && git pull && docker compose down && docker compose up -d --build"

# Check logs
scripts/connect-server.sh "docker logs polymarket-bot --tail 50"

# Verify env inside container
scripts/connect-server.sh "docker exec polymarket-bot printenv | grep GABAGOOL"
```

**Important**: After changing `.env`, must run `docker compose down && docker compose up -d` (not just restart) to pick up new env vars.

## Common Issues

### Prices showing N/A or 1.0
- WebSocket not receiving book updates
- Check token ID mapping in `MultiMarketTracker`
- Verify WebSocket URL is correct

### Dry run still active after changing .env
- Container needs full recreate: `docker compose down && up -d`
- Simple restart doesn't reload .env

### Directional strategy not triggering
- Check time threshold (>80% of 15 min = >12 min remaining)
- Check price threshold ($0.25)
- Check directional exposure limit (50% of max daily)

### Trade recorded but never executed ("phantom trade")
- Check if `expected_profit` was positive before execution
- Verify `create_market_order()` uses `MarketOrderArgs` object
- Check for API errors in logs during order placement
- Delete phantom trades from DB: `DELETE FROM trades WHERE id = 'trade-X'`

### Negative expected profit despite positive spread
- **Root cause**: Wrong position sizing (equal dollars instead of equal shares)
- Fix: Use `num_pairs = budget / (yes_price + no_price)` approach
- Verify: `min(yes_shares, no_shares) - total_cost > 0`

### `'PolymarketClient' object has no attribute 'X'`
- Stale container code - container wasn't rebuilt
- Fix: `docker compose down && docker compose up -d --build`
- Verify code is updated: `docker exec polymarket-bot cat /app/src/client/polymarket.py | head -50`

### Orders failing with TypeError
- py-clob-client requires `MarketOrderArgs` or `OrderArgs` object, not kwargs
- Check: `from py_clob_client.clob_types import OrderArgs`

### Orders "succeed" but no position appears on Polymarket
- **Root cause**: Order was signed but never POSTed
- The `create_order()` / `create_market_order()` methods only SIGN the order
- Must call `post_order(signed_order)` to actually submit to exchange
- Check logs for "Order signed" but no "Order posted" message

### "invalid amounts, max accuracy of X decimals" error
- **Root cause**: py-clob-client market order decimal precision bug
- See: https://github.com/Polymarket/py-clob-client/issues/121
- **Fix**: Use limit orders (GTC) instead of market orders
- Limit orders at aggressive prices (+/-2 cents) work around the bug

### 403 Forbidden from Cloudflare
- **Root cause**: Server IP blocked by Cloudflare WAF
- **Fix**: Route traffic through VPN/proxy
- Add to docker-compose.yml:
  ```yaml
  environment:
    - HTTP_PROXY=http://your-proxy:8888
    - HTTPS_PROXY=http://your-proxy:8888
  ```

### Opportunities detected but never executed
- **Root cause 1**: Polling-based detection blocked by slow market updates
- **Fix**: Use callback-based immediate execution with `_opportunity_queue`
- **Root cause 2**: Market state marked "stale" (>10 seconds old)
- Check WebSocket connection and book updates

## Testing Commands

```bash
# Check if dashboard is responding
scripts/connect-server.sh "curl -s -o /dev/null -w '%{http_code}' http://localhost:8501/dashboard"

# Check container status
scripts/connect-server.sh "docker ps --filter name=polymarket"

# View real-time logs
scripts/connect-server.sh "docker logs -f polymarket-bot"

# Check dashboard state JSON (includes markets with slugs)
scripts/connect-server.sh "curl -s http://localhost:8501/dashboard/state | python3 -m json.tool | head -50"

# Check trades in database
scripts/connect-server.sh "docker exec polymarket-bot python3 -c 'import asyncio, aiosqlite; c=asyncio.get_event_loop().run_until_complete(aiosqlite.connect(\"/app/data/gabagool.db\")); r=asyncio.get_event_loop().run_until_complete(c.execute(\"SELECT id,status,asset,actual_profit FROM trades\")); print(asyncio.get_event_loop().run_until_complete(r.fetchall()))'"

# Test REAL order execution ($5 limit order on active market)
scripts/connect-server.sh "docker exec polymarket-bot python3 /app/scripts/test_real_trade.py"

# Check open orders and balance
scripts/connect-server.sh "docker exec polymarket-bot python3 /app/scripts/check_orders.py"
```

### Verify Trade Execution

After running `test_real_trade.py`, verify the trade worked:

```bash
# 1. Check balance changed
scripts/connect-server.sh "docker exec polymarket-bot python3 /app/scripts/check_orders.py"

# 2. Look for your order in recent trades
# Your maker_address should appear in the output

# 3. Check Polymarket UI
# Go to https://polymarket.com and check your positions
```

## API Endpoints

- **Dashboard**: https://polymarket.server.unarmedpuppy.com/dashboard
- **Metrics**: https://polymarket.server.unarmedpuppy.com/metrics
- **Local Dashboard**: http://localhost:8501/dashboard
- **Local Metrics**: http://localhost:8500/metrics

## Position Tracking

### Arbitrage Positions
Tracked in `_pending_trades: Dict[str, TradeResult]`
- Key: trade_id (e.g., "trade-1")
- Resolved when market ends

### Directional Positions
Tracked in `_directional_positions: Dict[str, DirectionalPosition]`
- Key: condition_id
- Actively managed with exit logic

## Quick Reference

| Action | Command |
|--------|---------|
| Deploy changes | `scripts/connect-server.sh "cd ~/server/apps/polymarket-bot && git pull && docker compose build && docker compose down && docker compose up -d"` |
| View logs | `scripts/connect-server.sh "docker logs polymarket-bot --tail 100"` |
| Check status | `scripts/connect-server.sh "docker ps --filter name=polymarket"` |
| Toggle dry run | Edit `.env` on server, then `docker compose down && up -d` |
| Check trades DB | `scripts/connect-server.sh "docker exec polymarket-bot sqlite3 /app/data/gabagool.db 'SELECT * FROM trades'"` |
| Dashboard state | `scripts/connect-server.sh "curl -s http://localhost:8501/dashboard/state"` |

**Server paths:**
- Git repo: `~/server/` (symlink to `/home/unarmedpuppy/server`)
- App dir: `~/server/apps/polymarket-bot/`
- Database: `/app/data/gabagool.db` (inside container)

See [apps/polymarket-bot/docs/strategy-rules.md](../../apps/polymarket-bot/docs/strategy-rules.md) for complete strategy documentation.
