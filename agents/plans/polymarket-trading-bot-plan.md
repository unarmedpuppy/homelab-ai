# Polymarket Trading Bot Implementation Plan

**Created**: 2025-12-07
**Updated**: 2025-12-08
**Status**: Phase 1 Complete (Gabagool Arbitrage)
**Goal**: Build Polymarket trading bots with multiple strategies

## Overview

This plan covers the Polymarket trading bot infrastructure. The bot supports multiple trading strategies:

1. **Gabagool Arbitrage** (✅ IMPLEMENTED) - Exploits mispricing in 15-minute binary markets
2. **Copy Trading** (📋 PLANNED) - Mirrors positions from successful traders

---

## Phase 1: Gabagool Arbitrage Bot (COMPLETE)

**Epic**: `home-server-5qm` (CLOSED)
**Status**: Deployed and running in dry-run mode

### What Was Built

The Gabagool strategy exploits temporary mispricing in binary markets where YES + NO should sum to $1.00. When sum < $1.00, buying both sides guarantees profit regardless of outcome.

### Architecture (Implemented)

```
apps/polymarket-bot/
├── docker-compose.yml          # Docker orchestration (VPN proxy via gluetun)
├── Dockerfile                  # Python 3.11 container
├── requirements.txt            # Dependencies
├── .env.template               # Configuration template
├── src/
│   ├── main.py                 # GabagoolBot orchestrator
│   ├── config.py               # Pydantic settings
│   ├── client/
│   │   ├── polymarket.py       # CLOB client wrapper
│   │   ├── gamma.py            # Gamma API for market discovery
│   │   └── websocket.py        # Real-time streaming
│   ├── strategies/
│   │   ├── base.py             # Base strategy class
│   │   └── gabagool.py         # Arbitrage strategy
│   ├── monitoring/
│   │   ├── market_finder.py    # 15-minute market discovery
│   │   └── order_book.py       # Order book tracking
│   ├── risk/
│   │   ├── position_sizing.py  # Inverse weighting sizing
│   │   └── circuit_breaker.py  # Risk limits
│   ├── metrics.py              # Prometheus metrics
│   ├── metrics_server.py       # Metrics endpoint
│   ├── dashboard.py            # Retro terminal web UI
│   └── persistence.py          # SQLite for trade history
├── tests/                      # Unit tests
└── scripts/
    ├── derive_credentials.py   # API key generation
    └── test_credentials.py     # Credential validation
```

### Features Implemented

| Feature | Status | Notes |
|---------|--------|-------|
| CLOB API client | ✅ | Full L0/L1/L2 support |
| WebSocket streaming | ✅ | Real-time order book updates |
| 15-min market finder | ✅ | BTC/ETH up/down markets |
| Arbitrage detection | ✅ | Spread monitoring |
| Position sizing | ✅ | Inverse weighting (buy more of cheaper side) |
| Circuit breaker | ✅ | Daily loss/exposure limits |
| Prometheus metrics | ✅ | Port 8500 |
| Web dashboard | ✅ | Retro terminal UI at /dashboard |
| SQLite persistence | ✅ | Trade history, daily stats |
| Docker deployment | ✅ | VPN proxy via media-download-gluetun |
| Traefik integration | ✅ | Local no-auth, external with auth |

### Deployment Status

- **Container**: `polymarket-bot` (healthy)
- **Dashboard**: https://polymarket.server.unarmedpuppy.com/dashboard
- **Metrics**: Port 8500
- **Mode**: DRY RUN (no real trades)

### Configuration

Key environment variables (see `.env.template`):

```bash
# Strategy
GABAGOOL_ENABLED=true
GABAGOOL_DRY_RUN=true           # Set to false for live trading
GABAGOOL_MARKETS=BTC,ETH
GABAGOOL_MIN_SPREAD=0.02        # 2 cents minimum

# Position sizing
GABAGOOL_MAX_TRADE_SIZE=5.0     # $5 per order
GABAGOOL_MAX_DAILY_EXPOSURE=90.0

# Risk limits
GABAGOOL_MAX_DAILY_LOSS=5.0
```

---

## Phase 2: Enable Live Trading (PLANNED)

**Task**: `home-server-TBD`
**Status**: Not started
**Prerequisite**: Fund wallet, verify strategy performance in dry-run

### Checklist

- [ ] Review dry-run performance (dashboard shows expected P&L)
- [ ] Fund Polymarket wallet with USDC ($100 starting capital)
- [ ] Verify API credentials work for trading
- [ ] Update server .env: `GABAGOOL_DRY_RUN=false`
- [ ] Restart container and monitor first trades
- [ ] Set up alerting for errors/losses

### Risk Considerations

- Start with minimal position sizes ($5 max per trade)
- Monitor first few trades closely
- Have emergency stop procedure ready (set `GABAGOOL_ENABLED=false`)

---

## Phase 3: Copy Trading Strategy (PLANNED)

**Epic**: `home-server-TBD`
**Status**: Not started

### Overview

Copy trading mirrors positions from successful Polymarket traders. Unlike arbitrage (guaranteed small profits), copy trading follows directional bets with higher risk/reward.

### Architecture (Planned)

```
src/strategies/
└── copy_trading.py             # New strategy file

src/monitoring/
└── wallet_tracker.py           # Track target wallet positions
```

### Implementation Tasks

1. **Wallet Tracker** - Monitor target wallet via Gamma API
2. **Position Detector** - Detect new/changed/closed positions
3. **Copy Strategy** - Replicate positions with configurable sizing
4. **Risk Management** - Max position size, max exposure per market

### Configuration (Planned)

```bash
# Copy trading (add to .env.template)
COPY_TRADING_ENABLED=false
TARGET_WALLET_ADDRESS=           # Wallet to copy
POLL_INTERVAL_SECONDS=4
COPY_SIZE_MULTIPLIER=1.0         # 1.0 = same size as target
COPY_MAX_POSITION_SIZE=100.0     # Max USD per position
```

### Target Wallet Selection

Research successful traders:
- @gabagool22 (original strategy inspiration)
- Top leaderboard traders
- Wallets with consistent profitability

---

## Technical Reference

### API Endpoints

- CLOB HTTP: `https://clob.polymarket.com/`
- CLOB WebSocket: `wss://ws-subscriptions-clob.polymarket.com/ws`
- Gamma API: `https://gamma-api.polymarket.com`

### Authentication Levels

| Level | Access | Requirements |
|-------|--------|--------------|
| L0 | Public data | None |
| L1 | Wallet methods | Private key |
| L2 | Trading | API key, secret, passphrase |

### Key Dependencies

```txt
py-clob-client>=0.12.0    # Official Polymarket client
web3>=6.0.0               # Polygon interaction
httpx>=0.25.0             # Async HTTP
websockets>=12.0          # Real-time data
structlog>=24.0.0         # Logging
prometheus-client         # Metrics
aiohttp                   # Dashboard server
aiosqlite                 # Persistence
```

---

## Resources

### Official
- [Polymarket Docs](https://docs.polymarket.com/)
- [py-clob-client](https://github.com/Polymarket/py-clob-client)
- [Polymarket Agents](https://github.com/Polymarket/agents)

### Community
- [polymarket-copy-trading-bot](https://github.com/Trust412/polymarket-copy-trading-bot-v1)
- [Gabagool strategy analysis](https://jeremywhittaker.com/)

---

## Changelog

- **2025-12-08**: Updated plan to reflect Gabagool implementation, added Phase 2/3 plans
- **2025-12-07**: Initial plan created (copy trading focus)
- **2025-12-07**: Pivoted to Gabagool arbitrage, epic completed
