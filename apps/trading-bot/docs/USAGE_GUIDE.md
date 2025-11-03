# Trading Bot Usage Guide

**Last Updated**: December 19, 2024

## 🚀 Quick Start

### 1. Start the Services

```bash
cd /Users/joshuajenquist/repos/personal/home-server/apps/trading-bot
docker-compose up -d bot
```

### 2. Access the API

- **API Base**: `http://localhost:8021`
- **API Docs**: `http://localhost:8021/docs` (FastAPI Swagger UI)
- **Health Check**: `http://localhost:8021/health`

### 3. Monitor with Grafana

- **Grafana**: `http://localhost:3002`
- **Login**: `admin` / `admin` (change in production!)
- **Dashboards**: Navigate to "Dashboards" → "Trading Bot" folder

---

## 📡 IBKR Connection

### Current Status: **Manual Connection Required**

**Important**: The bot does NOT automatically connect to IBKR. You must manually connect via API.

### Step 1: Start TWS/IB Gateway

1. **Install TWS or IB Gateway** from Interactive Brokers
2. **Enable API**:
   - TWS: `Edit → Global Configuration → API → Settings`
   - Enable: ✅ "Enable ActiveX and Socket Clients"
   - Port: `7497` (Paper) or `7496` (Live)
   - Read-Only: ❌ Unchecked (needed for trading)
3. **Start TWS/Gateway** and keep it running

### Step 2: Connect via API

```bash
# Check connection status
curl http://localhost:8021/api/trading/ibkr/status

# Connect to IBKR
curl -X POST http://localhost:8021/api/trading/ibkr/connect \
  -H "Content-Type: application/json" \
  -d '{
    "host": "host.docker.internal",
    "port": 7497,
    "client_id": 9
  }'
```

**Note**: Since the bot runs in Docker, use `host.docker.internal` instead of `127.0.0.1` to reach TWS/Gateway on your host machine.

### Step 3: Verify Connection

```bash
curl http://localhost:8021/api/trading/ibkr/status
```

Should return: `{"connected": true, ...}`

---

## 🔄 Automatic Trading & Polling

### Current Status: **NOT IMPLEMENTED YET**

**The bot does NOT automatically:**
- ❌ Poll for trading signals
- ❌ Execute trades automatically
- ❌ Run strategies continuously

### How It Currently Works

The bot is **API-driven** - you must manually:

1. **Connect to IBKR** (see above)
2. **Create/Enable Strategies** via API
3. **Evaluate Strategies** via API to generate signals
4. **Execute Trades** manually via API

### Example Workflow

```bash
# 1. Connect to IBKR
curl -X POST http://localhost:8021/api/trading/ibkr/connect

# 2. List available strategies
curl http://localhost:8021/api/strategies

# 3. Add a strategy for a symbol
curl -X POST http://localhost:8021/api/strategies/add \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_type": "momentum",
    "config": {
      "symbol": "AAPL",
      "timeframe": "5m"
    },
    "enabled": true
  }'

# 4. Evaluate strategies (generates signals)
curl -X POST http://localhost:8021/api/strategies/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL"],
    "fetch_data": true
  }'

# 5. Manually execute trades based on signals
# (Check signals via WebSocket or API, then place orders)
```

### Future: Automatic Polling

This feature is **planned but not implemented**. It would require:
- Background scheduler/cron job
- Automatic strategy evaluation on intervals
- Signal → Trade execution pipeline
- See `docs/PROJECT_TODO.md` for more details

---

## 🖥️ User Interface

### Current Status: **Basic UI Exists, Comprehensive Dashboard NOT Built**

### What Exists

1. **Basic Dashboard** (`src/ui/templates/dashboard.html`)
   - Very basic template
   - Served at `http://localhost:8021/`
   - Not fully functional

2. **API Documentation** (`http://localhost:8021/docs`)
   - Full Swagger UI
   - Interactive API testing
   - All endpoints documented

3. **Grafana Dashboards**
   - Metrics visualization
   - Real-time monitoring
   - 7 pre-built dashboards

### What's Missing (From PROJECT_TODO.md)

The UI buildout is **planned but not started**:
- ❌ Comprehensive real-time dashboard
- ❌ Live portfolio balance display
- ❌ Trading history page
- ❌ Sentiment feed visualization
- ❌ Strategy management UI
- ❌ Trade execution UI

**Status**: `⏳ PLANNED` - See `docs/PROJECT_TODO.md` Section 11

---

## 📊 Available API Endpoints

### Trading & IBKR
- `GET /api/trading/ibkr/status` - Check IBKR connection
- `POST /api/trading/ibkr/connect` - Connect to IBKR
- `POST /api/trading/ibkr/disconnect` - Disconnect from IBKR
- `GET /api/trading/positions` - Get current positions
- `GET /api/trading/account` - Get account summary
- `POST /api/trading/orders/market` - Place market order
- `POST /api/trading/orders/limit` - Place limit order

### Strategies
- `GET /api/strategies` - List available strategies
- `POST /api/strategies/add` - Add/enable a strategy
- `POST /api/strategies/evaluate` - Evaluate strategies (generates signals)
- `GET /api/strategies/{strategy_id}` - Get strategy info
- `POST /api/strategies/{strategy_id}/enable` - Enable strategy
- `POST /api/strategies/{strategy_id}/disable` - Disable strategy

### Sentiment
- `GET /api/sentiment/twitter/{symbol}` - Get Twitter sentiment
- `GET /api/sentiment/reddit/{symbol}` - Get Reddit sentiment
- `GET /api/sentiment/aggregated/{symbol}` - Get aggregated sentiment

### Market Data
- `GET /api/market-data/{symbol}` - Get market data
- `GET /api/market-data/historical/{symbol}` - Get historical data

### Monitoring
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /api/monitoring/system` - System status

### WebSocket
- `WS /ws` - WebSocket endpoint for real-time updates

---

## 🔌 WebSocket Real-Time Updates

The bot supports WebSocket connections for real-time data:

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8021/ws');

// Subscribe to price updates
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'price',
  symbol: 'AAPL'
}));

// Receive updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
```

**Available Channels**:
- `price` - Real-time price updates
- `portfolio` - Portfolio updates
- `signals` - Trading signals
- `trades` - Trade executions

---

## 🎯 Typical Usage Workflow

### For Manual Trading

1. **Start Services**
   ```bash
   docker-compose up -d
   ```

2. **Connect to IBKR**
   - Start TWS/Gateway on your machine
   - Enable API access (port 7497)
   - Call `/api/trading/ibkr/connect` endpoint

3. **Monitor System**
   - Open Grafana: `http://localhost:3002`
   - View metrics and dashboards
   - Check API docs: `http://localhost:8021/docs`

4. **Evaluate Strategies**
   - List strategies: `GET /api/strategies`
   - Add strategy for a symbol
   - Evaluate: `POST /api/strategies/evaluate`

5. **Execute Trades**
   - Check signals via API or WebSocket
   - Place orders: `POST /api/trading/orders/market`
   - Monitor positions: `GET /api/trading/positions`

### For Automated Trading (Future)

This requires implementing:
- Background scheduler
- Automatic strategy evaluation loop
- Signal → Trade execution pipeline

**See**: `docs/PROJECT_TODO.md` for planned features

---

## 📚 Additional Resources

- **IBKR Connection Guide**: `docs/IBKR_CONNECTION.md`
- **API Documentation**: `http://localhost:8021/docs`
- **WebSocket Usage**: `docs/WEBSOCKET_USAGE.md`
- **Grafana Dashboards**: `docs/GRAFANA_DASHBOARDS.md`
- **Project TODO**: `docs/PROJECT_TODO.md`

---

## ⚠️ Important Notes

1. **No Automatic Trading**: The bot does NOT automatically poll or execute trades
2. **Manual IBKR Connection**: Must connect via API after starting TWS/Gateway
3. **Basic UI**: Dashboard is very basic, use API docs or Grafana for now
4. **Paper Trading First**: Always test with paper trading account first!

---

## 🐛 Troubleshooting

### IBKR Connection Issues

- **"Connection refused"**: TWS/Gateway not running or API not enabled
- **"Timeout"**: Check firewall, port (7497), and host (use `host.docker.internal` in Docker)
- **"Client ID in use"**: Another application using the same client ID

### Services Not Starting

- Check logs: `docker-compose logs bot`
- Verify ports aren't in use: `lsof -i :8021`
- Check health: `curl http://localhost:8021/health`

### Missing Data

- Check API keys are set in environment
- Verify providers are enabled in settings
- Check logs for API errors

