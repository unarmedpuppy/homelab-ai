# Trading Bot - Production Ready Architecture

A modern, modular trading bot with SMA strategy, comprehensive backtesting, and real-time web interface.

## 🚀 Features

### Core Trading
- **SMA Strategy**: Simple Moving Average-based entry/exit signals
- **Risk Management**: Configurable stop-loss, take-profit, and position sizing
- **Paper Trading**: Safe testing environment
- **Live Trading**: Interactive Brokers integration
- **Real-time Signals**: WebSocket-based live updates

### Advanced Features
- **Backtesting Engine**: Historical strategy performance analysis
- **Stock Screener**: Multi-criteria stock filtering
- **Portfolio Management**: Position tracking and P&L monitoring
- **Risk Metrics**: Sharpe ratio, drawdown, VaR calculations
- **Real-time Dashboard**: Modern web interface with live data

### Technical Excellence
- **Modular Architecture**: Clean separation of concerns
- **Type Safety**: Full Pydantic validation and type hints
- **Comprehensive Testing**: Unit, integration, and end-to-end tests
- **Production Ready**: Docker, monitoring, logging, error handling
- **Scalable**: Microservices architecture with background workers

## 📁 Project Structure

```
trading-bot/
├── src/                          # Source code
│   ├── core/                     # Core business logic
│   │   ├── strategy.py           # Trading strategies
│   │   ├── indicators.py         # Technical indicators
│   │   └── risk_management.py    # Risk management
│   ├── data/                     # Data access layer
│   │   ├── brokers/              # Broker integrations
│   │   ├── providers/            # Data providers
│   │   └── database/             # Database models & access
│   ├── api/                      # FastAPI application
│   │   ├── routes/               # API endpoints
│   │   ├── schemas/              # Pydantic models
│   │   └── middleware/           # Custom middleware
│   ├── backtesting/              # Backtesting engine
│   ├── screening/                # Stock screening
│   ├── config/                   # Configuration management
│   └── utils/                    # Utilities
├── tests/                        # Test suite
├── docker/                       # Docker configurations
├── docs/                         # Documentation
└── requirements/                # Dependency management
```

## 🛠️ Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Interactive Brokers TWS/Gateway (for live trading)
  - See [IBKR Connection Guide](docs/IBKR_CONNECTION.md) for setup instructions
- PostgreSQL (or use SQLite for development)

### Installation

1. **Clone and setup**:
```bash
git clone <repository>
cd trading-bot
cp .env.example .env
# Edit .env with your configuration
```

2. **Docker deployment** (Recommended):
```bash
docker-compose -f docker/docker-compose.yml up -d
```

Or **Local development**:
```bash
pip install -r requirements/development.txt
uvicorn src.api.main:app --reload
```

3. **Set up IBKR connection** (for live trading):
```bash
# Test your IBKR connection
python scripts/test_ibkr_connection.py
```
See the [IBKR Connection Guide](docs/IBKR_CONNECTION.md) for detailed setup instructions.

### Configuration

Create a `.env` file with your settings:

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/tradingbot

# Interactive Brokers
IBKR_HOST=127.0.0.1
IBKR_PORT=7497
IBKR_CLIENT_ID=9

# Unusual Whales (optional)
UW_API_KEY=your_api_key

# Trading Parameters
TRADING_DEFAULT_QTY=10
TRADING_ENTRY_THRESHOLD=0.005
TRADING_TAKE_PROFIT=0.20
TRADING_STOP_LOSS=0.10

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/trading-bot.log
```

## 🎯 Usage

### Web Interface
Access the dashboard at `http://localhost:8000`

Features:
- **Real-time Price Updates**: Live market data via WebSocket
- **Signal Generation**: AI-powered trading signals
- **Trade Execution**: Paper and live trading
- **Portfolio Monitoring**: Real-time P&L tracking
- **Performance Analytics**: Charts and metrics

### API Endpoints

#### Trading

**IBKR Connection Management**:
```bash
# Check connection status
GET /api/trading/ibkr/status

# Connect to IBKR
POST /api/trading/ibkr/connect
{
  "host": "127.0.0.1",  // Optional
  "port": 7497,         // Optional
  "client_id": 9        // Optional
}

# Test connection with diagnostics
POST /api/trading/ibkr/test

# Get account summary
GET /api/trading/ibkr/account

# Get current positions
GET /api/trading/ibkr/positions

# Disconnect
POST /api/trading/ibkr/disconnect
```

**Trading Operations**:
```bash
# Generate trading signal
POST /api/trading/signal
{
  "symbol": "AAPL",
  "entry_threshold": 0.005,
  "take_profit": 0.20,
  "stop_loss": 0.10,
  "quantity": 10
}

# Execute trade
POST /api/trading/execute
{
  "symbol": "AAPL",
  "side": "BUY",
  "quantity": 10,
  "price": 150.25
}

# Get positions
GET /api/trading/positions

# Get recent trades
GET /api/trading/trades?symbol=AAPL&limit=50
```

See [IBKR Connection Guide](docs/IBKR_CONNECTION.md) for detailed connection setup.

#### Backtesting
```bash
# Run backtest
POST /api/backtesting/run
{
  "symbol": "AAPL",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "strategy": "sma",
  "initial_capital": 100000
}

# Get backtest results
GET /api/backtesting/results/{backtest_id}
```

#### Screening
```bash
# Run stock screener
POST /api/screening/run
{
  "universe": ["AAPL", "MSFT", "NVDA", "GOOGL"],
  "filters": {
    "pe_max": 25,
    "debt_to_equity_max": 0.35,
    "eps_growth_min": 0.15
  }
}
```

### CLI Usage

```bash
# Generate signal
python -m src.scripts.cli signal --symbol AAPL --entry-threshold 0.005

# Run backtest
python -m src.scripts.cli backtest --symbol AAPL --start-date 2024-01-01 --end-date 2024-12-31

# Run screener
python -m src.scripts.cli screen --universe "AAPL,MSFT,NVDA" --output results.csv

# Live trading
python -m src.scripts.cli live --symbol AAPL --strategy sma
```

## 📊 Strategy Details

### SMA Strategy
The Simple Moving Average strategy generates signals based on:

**Entry Conditions**:
- Price within 0.5% of SMA(20) or SMA(200)
- RSI between 45-55 (not overbought/oversold)
- OBV slope positive (volume confirmation)
- Optional: Unusual Whales bullish signals

**Exit Conditions**:
- Take profit: +20% from entry
- Stop loss: -10% from entry
- SMA extension: Price moves >3% away from SMA(20)

**Risk Management**:
- Position sizing based on account value
- Maximum daily trades limit
- Portfolio-level risk controls

### Custom Strategies
Implement custom strategies by extending `BaseStrategy`:

```python
class MyStrategy(BaseStrategy):
    def generate_signal(self, data: pd.DataFrame, position: Optional[Position] = None) -> TradingSignal:
        # Your strategy logic here
        pass
    
    def should_exit(self, position: Position, data: pd.DataFrame) -> Tuple[bool, ExitReason]:
        # Your exit logic here
        pass
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/e2e/          # End-to-end tests
```

## 📈 Monitoring

### Health Checks
- API health: `GET /health`
- Database connectivity
- Redis connectivity
- IBKR connection status: `GET /api/trading/ibkr/status`

### Metrics (Prometheus)
- Trade execution metrics
- Strategy performance
- System resource usage
- Error rates and latencies

### Logging
Structured JSON logging with:
- Request/response logging
- Trade execution logs
- Error tracking
- Performance metrics

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**:
```bash
export ENVIRONMENT=production
export DATABASE_URL=postgresql://user:pass@db:5432/tradingbot
export REDIS_URL=redis://redis:6379/0
```

2. **Docker Compose**:
```bash
docker-compose -f docker/docker-compose.yml up -d
```

3. **With Monitoring**:
```bash
docker-compose -f docker/docker-compose.yml --profile monitoring up -d
```

### Scaling
- **Horizontal Scaling**: Multiple API instances behind load balancer
- **Background Workers**: Celery workers for heavy processing
- **Database**: PostgreSQL with read replicas
- **Caching**: Redis for session and data caching

## 🔒 Security

- **Input Validation**: Pydantic schemas for all inputs
- **Rate Limiting**: API rate limiting per IP
- **Authentication**: JWT-based authentication (optional)
- **HTTPS**: SSL/TLS encryption
- **Secrets Management**: Environment variables for sensitive data

## 📚 Documentation

- **API Documentation**: Available at `/docs` (Swagger UI)
- **IBKR Connection Guide**: See [docs/IBKR_CONNECTION.md](docs/IBKR_CONNECTION.md) - Complete setup and troubleshooting guide
- **Strategy Architecture**: See [docs/STRATEGY_ARCHITECTURE.md](docs/STRATEGY_ARCHITECTURE.md) - Modular strategy system design
- **Strategy Implementation Plan**: See [docs/STRATEGY_IMPLEMENTATION_PLAN.md](docs/STRATEGY_IMPLEMENTATION_PLAN.md) - Step-by-step implementation guide
- **Sentiment Integration Checklist**: See [docs/SENTIMENT_INTEGRATION_CHECKLIST.md](docs/SENTIMENT_INTEGRATION_CHECKLIST.md) - **Master checklist for sentiment data source integration** ⭐
- **Agent Workflow Guide**: See [docs/AGENT_WORKFLOW_SENTIMENT.md](docs/AGENT_WORKFLOW_SENTIMENT.md) - **For agents working on sentiment integrations** 👥
- **Twitter Sentiment Strategy**: See [docs/TWITTER_SENTIMENT_STRATEGY.md](docs/TWITTER_SENTIMENT_STRATEGY.md) - Twitter/X integration strategy and plan
- **Architecture Guide**: See `ARCHITECTURE.md`
- **Development Guide**: See `docs/DEVELOPMENT.md`
- **Deployment Guide**: See `docs/DEPLOYMENT.md`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## ⚠️ Disclaimer

This software is for educational and research purposes only. Trading involves substantial risk of loss. Past performance does not guarantee future results. Always test thoroughly with paper trading before using real money.

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Documentation**: `/docs` endpoint
- **Email**: support@yourdomain.com

---

**Happy Trading! 📈**
