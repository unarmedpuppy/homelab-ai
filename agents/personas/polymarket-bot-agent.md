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
- `src/client/polymarket.py` - CLOB HTTP API client for order execution
- `src/client/websocket.py` - WebSocket client for real-time price streaming
- `src/client/gamma.py` - Gamma API client for market discovery

### Monitoring & Dashboard
- `src/monitoring/order_book.py` - Order book tracking and arbitrage detection
- `src/monitoring/market_finder.py` - 15-minute market discovery
- `src/dashboard.py` - Retro terminal web dashboard with SSE
- `src/persistence.py` - SQLite database for trade history
- `src/metrics.py` - Prometheus metrics

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

## Testing Commands

```bash
# Check if dashboard is responding
scripts/connect-server.sh "curl -s -o /dev/null -w '%{http_code}' http://localhost:8501/dashboard"

# Check container status
scripts/connect-server.sh "docker ps --filter name=polymarket"

# View real-time logs
scripts/connect-server.sh "docker logs -f polymarket-bot"
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
| Deploy changes | `scripts/connect-server.sh "cd /home/unarmedpuppy/server/apps/polymarket-bot && git pull && docker compose up -d --build"` |
| View logs | `scripts/connect-server.sh "docker logs polymarket-bot --tail 100"` |
| Check status | `scripts/connect-server.sh "docker ps --filter name=polymarket"` |
| Toggle dry run | Edit `.env` on server, then `docker compose down && up -d` |

See [apps/polymarket-bot/docs/strategy-rules.md](../../apps/polymarket-bot/docs/strategy-rules.md) for complete strategy documentation.
