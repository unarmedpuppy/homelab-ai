# Trading Bot

A fully automated trading system with Interactive Brokers integration, multi-source sentiment analysis, and confluence-based signal generation.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           TRADING BOT SYSTEM                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────────────────┐  │
│   │ Market Data │────▶│  Strategy   │────▶│   Signal Generation     │  │
│   │  Providers  │     │  Evaluator  │     │  (Confluence Scoring)   │  │
│   └─────────────┘     └─────────────┘     └───────────┬─────────────┘  │
│          │                   │                        │                 │
│          │            ┌──────┴──────┐                 ▼                 │
│          │            │  Sentiment  │         ┌─────────────┐          │
│          │            │ Aggregator  │         │    Risk     │          │
│          │            │ (13 sources)│         │   Manager   │          │
│          │            └─────────────┘         └──────┬──────┘          │
│          │                                           │                  │
│          │                                           ▼                  │
│   ┌──────┴──────┐                           ┌─────────────┐            │
│   │   Trading   │◀──────────────────────────│    IBKR     │            │
│   │  Scheduler  │                           │   Client    │            │
│   └─────────────┘                           └─────────────┘            │
│          │                                           │                  │
│          ▼                                           ▼                  │
│   ┌─────────────┐                           ┌─────────────┐            │
│   │  Position   │                           │  IB Gateway │            │
│   │    Sync     │                           │  (Docker)   │            │
│   └─────────────┘                           └─────────────┘            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Start Services

```bash
cd apps/trading-bot

# Copy environment template and configure
cp .env.example .env
# Edit .env with your IBKR credentials

# Start all services
docker compose up -d
```

### 2. Complete IB Gateway Login

1. Connect to VNC: `vnc://your-server:5900`
2. Complete 2FA authentication in IB Gateway
3. Verify connection is green

### 3. Connect to IBKR via API

```bash
# Test connection
curl http://localhost:8000/api/trading/ibkr/test

# Connect
curl -X POST http://localhost:8000/api/trading/ibkr/connect
```

### 4. Add a Strategy

```bash
curl -X POST http://localhost:8000/api/strategies/add \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_type": "range_bound",
    "config": {
      "symbol": "SPY",
      "timeframe": "5m"
    },
    "enabled": true
  }'
```

### 5. Start Automated Trading

```bash
# Enable scheduler in .env: SCHEDULER_ENABLED=true
# Then restart, or start manually:
curl -X POST http://localhost:8000/api/scheduler/start
```

---

## System Components

### Core Flow: Signal → Trade

```
1. MARKET DATA          2. STRATEGY              3. SIGNAL
   └─ Price/OHLCV          └─ Technical             └─ BUY/SELL/HOLD
   └─ Volume                  Indicators            └─ Confidence score
   └─ Historical data      └─ Entry/Exit rules      └─ Price targets

        ↓                        ↓                        ↓

4. SENTIMENT            5. CONFLUENCE            6. RISK CHECK
   └─ Twitter              └─ Technical 50%         └─ PDT compliance
   └─ Reddit               └─ Sentiment 30%         └─ Position sizing
   └─ News                 └─ Options 20%           └─ Account limits
   └─ Options flow         └─ Score 0.0-1.0         └─ Settlement

        ↓                        ↓                        ↓

7. EXECUTION            8. POSITION SYNC         9. EXIT MONITORING
   └─ IBKR order           └─ DB update             └─ Profit taking
   └─ Market/Limit         └─ P&L tracking          └─ Stop loss
   └─ Fill tracking        └─ WebSocket             └─ Time-based
```

### Trading Scheduler

The scheduler runs background loops that:
1. **Evaluate strategies** every 60s (configurable)
2. **Check exit conditions** every 30s
3. **Sync positions** with IBKR every 5min

```
TradingScheduler
├─ _evaluation_loop()      # Generate signals, execute trades
├─ _exit_check_loop()      # Monitor profit/stop levels
└─ _position_sync_loop()   # Keep DB in sync with broker
```

### Strategies

| Strategy | Description | Entry Logic |
|----------|-------------|-------------|
| `range_bound` | Trade between Previous Day High/Low | Price near PDH/PDL |
| `momentum` | Momentum-based signals | RSI, MACD, Volume |
| `level_based` | Support/Resistance levels | Price at key levels |

### Risk Management

Pre-trade validation includes:
- **PDT Rules**: Pattern day trader compliance (<25k accounts)
- **Position Sizing**: Confidence-based (1-4% of account)
- **Trade Limits**: Daily/weekly limits
- **Settlement**: T+2 cash settlement tracking

### Sentiment Sources (13 providers)

| Provider | Data |
|----------|------|
| Twitter/X | Tweet sentiment |
| Reddit | r/wallstreetbets, r/stocks |
| StockTwits | Message sentiment |
| News | RSS feeds, NewsAPI |
| Google Trends | Search interest |
| Analyst Ratings | Price targets, ratings |
| Insider Trading | Insider transactions |
| SEC Filings | 10-K, 10-Q analysis |
| Options Flow | Unusual activity |

---

## API Reference

### Trading Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/trading/ibkr/status` | IBKR connection status |
| POST | `/api/trading/ibkr/connect` | Connect to IBKR |
| POST | `/api/trading/ibkr/disconnect` | Disconnect |
| POST | `/api/trading/ibkr/test` | Test connection |
| GET | `/api/trading/ibkr/account` | Account summary |
| GET | `/api/trading/ibkr/positions` | Current positions |
| POST | `/api/trading/execute` | Execute a trade |
| POST | `/api/trading/signal` | Generate signal for symbol |

### Strategy Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/strategies` | List strategy types |
| POST | `/api/strategies/add` | Add strategy to evaluator |
| GET | `/api/strategies/active` | List active strategies |
| POST | `/api/strategies/{id}/enable` | Enable strategy |
| POST | `/api/strategies/{id}/disable` | Disable strategy |
| DELETE | `/api/strategies/{id}` | Remove strategy |

### Scheduler Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/scheduler/status` | Scheduler status & stats |
| POST | `/api/scheduler/start` | Start auto-trading |
| POST | `/api/scheduler/stop` | Stop auto-trading |
| POST | `/api/scheduler/pause` | Pause (keep state) |
| POST | `/api/scheduler/resume` | Resume from pause |

### Other Endpoints

| Prefix | Description |
|--------|-------------|
| `/api/sentiment/*` | Sentiment data by source |
| `/api/confluence/*` | Confluence scoring |
| `/api/market-data/*` | Quotes, history |
| `/api/options-flow/*` | Options flow data |
| `/api/monitoring/*` | Health, metrics |

### WebSocket Streams

| Endpoint | Description |
|----------|-------------|
| `/ws/health` | System health |
| `/ws/prices` | Real-time prices |
| `/ws/signals` | Signal broadcasts |
| `/ws/portfolio` | Position updates |

---

## Configuration

### Environment Variables

```bash
# === IBKR Connection ===
IBKR_HOST=ib-gateway              # Hostname (use service name in Docker)
IBKR_PORT=4003                    # Port: 4003=live, 4004=paper
IBKR_CLIENT_ID=9                  # Unique client ID
IBKR_USERNAME=your_username
IBKR_PASSWORD=your_password
IBKR_TRADING_MODE=live            # live or paper

# === Scheduler (Auto-Trading) ===
SCHEDULER_ENABLED=true            # Enable automated trading
SCHEDULER_EVALUATION_INTERVAL=60  # Seconds between evaluations
SCHEDULER_EXIT_CHECK_INTERVAL=30  # Seconds between exit checks
SCHEDULER_MIN_CONFIDENCE=0.5      # Minimum confidence (0.0-1.0)
SCHEDULER_MAX_CONCURRENT_TRADES=5 # Max open positions
SCHEDULER_MARKET_HOURS_ONLY=true  # Only trade 9:30-4:00 ET

# === Risk Management ===
RISK_CASH_ACCOUNT_THRESHOLD=25000 # PDT threshold
RISK_PDT_ENFORCEMENT_MODE=strict  # strict or warning
RISK_DAILY_TRADE_LIMIT=5
RISK_WEEKLY_TRADE_LIMIT=20

# === Position Sync ===
POSITION_SYNC_ENABLED=true
POSITION_SYNC_INTERVAL=300        # Sync every 5 minutes

# === API ===
API_HOST=0.0.0.0
API_PORT=8000
DATABASE_URL=sqlite:///./data/trading.db
```

### Docker Compose Services

```yaml
services:
  ib-gateway:      # Interactive Brokers Gateway
    ports:
      - "4001:4003"  # Live trading API
      - "4002:4004"  # Paper trading API
      - "5900:5900"  # VNC for authentication

  trading-bot:     # FastAPI application
    ports:
      - "8000:8000"  # API & WebSocket
```

---

## Workflow Examples

### Manual Trading via API

```bash
# 1. Generate a signal
curl "http://localhost:8000/api/trading/signal" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL"}'

# 2. Execute based on signal
curl -X POST "http://localhost:8000/api/trading/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "symbol": "AAPL",
    "side": "BUY",
    "quantity": 10,
    "price_per_share": 175.50,
    "confidence_score": 0.75
  }'
```

### Automated Trading Setup

```bash
# 1. Configure .env
SCHEDULER_ENABLED=true
SCHEDULER_MIN_CONFIDENCE=0.6

# 2. Add strategies
curl -X POST http://localhost:8000/api/strategies/add \
  -d '{"strategy_type": "range_bound", "config": {"symbol": "SPY"}, "enabled": true}'

curl -X POST http://localhost:8000/api/strategies/add \
  -d '{"strategy_type": "momentum", "config": {"symbol": "QQQ"}, "enabled": true}'

# 3. Start scheduler
curl -X POST http://localhost:8000/api/scheduler/start

# 4. Monitor
curl http://localhost:8000/api/scheduler/status
```

### Check Positions & Performance

```bash
# Current positions from IBKR
curl http://localhost:8000/api/trading/ibkr/positions

# Portfolio summary
curl http://localhost:8000/api/trading/portfolio/summary

# Performance metrics
curl http://localhost:8000/api/trading/performance
```

---

## Project Structure

```
apps/trading-bot/
├── main.py                    # Entry point
├── docker-compose.yml         # Services (bot + IB Gateway)
├── .env.example               # Configuration template
│
├── src/
│   ├── api/
│   │   ├── main.py            # FastAPI app setup
│   │   ├── routes/            # API endpoints
│   │   │   ├── trading.py     # Trading & IBKR routes
│   │   │   ├── strategies.py  # Strategy management
│   │   │   ├── scheduler.py   # Scheduler control
│   │   │   ├── sentiment.py   # Sentiment endpoints
│   │   │   └── ...
│   │   └── websocket/         # Real-time streams
│   │
│   ├── core/
│   │   ├── strategy/          # Trading strategies
│   │   │   ├── base.py        # TradingSignal, Position
│   │   │   ├── range_bound.py # PDH/PDL strategy
│   │   │   ├── momentum.py    # RSI/MACD strategy
│   │   │   └── registry.py    # Strategy registration
│   │   │
│   │   ├── evaluation/        # Signal generation
│   │   │   └── evaluator.py   # StrategyEvaluator
│   │   │
│   │   ├── scheduler/         # Auto-trading
│   │   │   └── trading_scheduler.py
│   │   │
│   │   ├── risk/              # Risk management
│   │   │   ├── manager.py     # RiskManager
│   │   │   ├── compliance.py  # PDT, GFV rules
│   │   │   ├── position_sizing.py
│   │   │   └── profit_taking.py
│   │   │
│   │   ├── confluence/        # Multi-source scoring
│   │   │   └── calculator.py
│   │   │
│   │   └── sync/              # Position sync
│   │       └── position_sync.py
│   │
│   ├── data/
│   │   ├── brokers/
│   │   │   └── ibkr_client.py # IBKR integration
│   │   │
│   │   ├── providers/
│   │   │   ├── market_data.py # Price data
│   │   │   └── sentiment/     # 13 sentiment sources
│   │   │
│   │   └── database/
│   │       └── models.py      # SQLAlchemy models
│   │
│   ├── config/
│   │   └── settings.py        # Pydantic settings
│   │
│   └── utils/
│       └── metrics/           # Prometheus metrics
│
└── tests/
```

---

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

### Scheduler Stats

```bash
curl http://localhost:8000/api/scheduler/status
```

Returns:
```json
{
  "state": "running",
  "stats": {
    "evaluations_run": 150,
    "signals_generated": 12,
    "trades_executed": 8,
    "trades_rejected": 4,
    "errors": 0,
    "uptime_seconds": 9000
  },
  "can_run": true,
  "is_market_hours": true,
  "ibkr_connected": true
}
```

### Prometheus Metrics

Available at `/metrics`:
- `trading_signals_total` - Signals generated
- `trading_trades_executed_total` - Trades executed
- `trading_position_pnl` - Position P&L
- `ibkr_connection_status` - Broker connection

---

## Safety Notes

- **Paper trade first** - Test thoroughly before live trading
- **Start with low confidence threshold** - Fewer trades while learning
- **Monitor positions** - Check regularly, especially initially
- **Set trade limits** - Use daily/weekly limits
- **This is not investment advice** - Use at your own risk

---

## Troubleshooting

### IBKR Connection Issues

1. **Check IB Gateway is running**: VNC to port 5900
2. **Verify 2FA completed**: Gateway should show green "connected"
3. **Check port mapping**: Live=4001→4003, Paper=4002→4004
4. **Test connection**: `curl http://localhost:8000/api/trading/ibkr/test`

### Scheduler Not Trading

1. **Check enabled**: `SCHEDULER_ENABLED=true`
2. **Check market hours**: Set `SCHEDULER_MARKET_HOURS_ONLY=false` for testing
3. **Check IBKR connected**: `SCHEDULER_REQUIRE_IBKR_CONNECTION=true`
4. **Check strategies added**: `curl /api/strategies/active`
5. **Check confidence**: Lower `SCHEDULER_MIN_CONFIDENCE` if needed

### No Signals Generated

1. **Add strategies first**: Scheduler needs active strategies
2. **Check data providers**: Market data must be available
3. **Check confidence threshold**: Signals below threshold are filtered
4. **Check logs**: `docker logs trading-bot`
