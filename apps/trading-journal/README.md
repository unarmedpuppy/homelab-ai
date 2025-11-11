# Trading Journal Application

A self-hosted trading journal application inspired by Tradezella, designed for personal use. Track trades, visualize performance, and analyze your trading activity through a comprehensive web interface.

## 📋 Features

### Core Features
- ✅ **Trade Entry & Management**: Support for stocks, options, crypto, and prediction markets
- ✅ **Dashboard**: Comprehensive KPIs including net P&L, win rate, profit factor, max drawdown, Zella score
- ✅ **Calendar View**: Monthly calendar with daily P&L visualization
- ✅ **Daily Journal**: Detailed daily trade summaries with P&L progression
- ✅ **Price Charts**: Interactive charts with trade overlays, indicators (SMA, EMA, RSI, Volume)
- ✅ **Analytics**: Performance metrics, breakdowns by ticker, type, and playbook
- ✅ **Options Chain**: View options chain data and Greeks
- ✅ **AI Agent Helpers**: Parse natural language trade descriptions, batch create trades, get suggestions
- ✅ **Responsive Design**: Mobile-friendly interface with adaptive layouts

### Trade Types Supported
- **STOCK**: Regular stock trades
- **OPTION**: Options contracts (CALL/PUT) with Greeks
- **CRYPTO_SPOT**: Cryptocurrency spot trades
- **CRYPTO_PERP**: Cryptocurrency perpetual futures
- **PREDICTION_MARKET**: Prediction market trades

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python 3.11+), PostgreSQL 15+, SQLAlchemy 2.0 (async)
- **Frontend**: React 18+, TypeScript, Vite, Material-UI (MUI)
- **Charts**: TradingView Lightweight Charts, Recharts
- **Infrastructure**: Docker Compose
- **Database Migrations**: Alembic

## 📚 Documentation

Before starting work on this project, read these documents in order:

1. **`STARTUP_GUIDE.md`** - Essential formulas, API keys, setup details
2. **`IMPLEMENTATION_PLAN.md`** - Complete feature specification and architecture
3. **`TRADING_JOURNAL_AGENTS_PROMPT.md`** - Guidelines for agents implementing features
4. **`TRADING_JOURNAL_AGENT_REVIEWER_PROMPT.md`** - Standards for code reviewers
5. **`TRADE_AGENT_PROMPT.md`** - Guide for AI agents extracting trades from screenshots
6. **`TASKS.md`** - Task tracking and status

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Network `my-network` must exist (created by other apps in the home-server setup)
- API keys for external data providers (optional, see below)

### Installation

1. **Clone the repository** (if not already done):
   ```bash
   cd apps/trading-journal
   ```

2. **Set up environment variables**:
   ```bash
   cp env.template .env
   ```

3. **Generate secure keys**:
   ```bash
   # Generate API key for authentication
   openssl rand -hex 32
   
   # Generate database password
   openssl rand -hex 32
   ```

4. **Edit `.env` file**:
   - Set `API_KEY` to the generated API key
   - Set `POSTGRES_PASSWORD` to the generated password
   - Update `DATABASE_URL` with the password
   - Add external API keys (optional):
     - `ALPHA_VANTAGE_API_KEY` - Get free key from https://www.alphavantage.co/support/#api-key
     - `COINGECKO_API_KEY` - Optional, works without key
     - `POLYGON_API_KEY` - Optional, for options data

5. **Start the application**:
   ```bash
   docker compose up -d --build
   ```

6. **Verify services are running**:
   ```bash
   docker compose ps
   ```

7. **Check logs** (if needed):
   ```bash
   docker compose logs -f backend
   docker compose logs -f frontend
   ```

8. **Access the application**:
   - Frontend: http://localhost:8101 (or http://<server-ip>:8101)
   - Backend API: http://localhost:8102/api (or http://<server-ip>:8102/api)
   - API Documentation: http://localhost:8102/api/docs (Swagger UI)

### First Time Setup

1. **Run database migrations** (if needed):
   ```bash
   docker compose exec backend alembic upgrade head
   ```

2. **Test the API**:
   ```bash
   # Health check (no auth required)
   curl http://localhost:8102/api/health
   
   # Test authenticated endpoint (replace API_KEY with your key)
   curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8102/api/trades
   ```

3. **Access the frontend** and start adding trades!

## 🔑 API Authentication

All API endpoints (except `/api/health`) require authentication via API key.

### Using the API

Include the API key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     http://localhost:8102/api/trades
```

### Frontend Configuration

The frontend automatically includes the API key from the `VITE_API_KEY` environment variable. This is set in `docker-compose.yml` from the `API_KEY` in your `.env` file.

## 📡 API Endpoints

### Core Endpoints

#### Trades
- `GET /api/trades` - List trades (with filters and pagination)
- `GET /api/trades/{id}` - Get trade by ID
- `POST /api/trades` - Create new trade
- `PUT /api/trades/{id}` - Update trade
- `PATCH /api/trades/{id}` - Partial update trade
- `DELETE /api/trades/{id}` - Delete trade
- `POST /api/trades/bulk` - Bulk create trades
- `GET /api/trades/search` - Search trades

#### Dashboard
- `GET /api/dashboard/stats` - Get dashboard statistics
- `GET /api/dashboard/cumulative-pnl` - Get cumulative P&L chart data
- `GET /api/dashboard/daily-pnl` - Get daily P&L chart data
- `GET /api/dashboard/drawdown` - Get drawdown chart data
- `GET /api/dashboard/recent-trades` - Get recent trades

#### Calendar
- `GET /api/calendar/month` - Get calendar month data
- `GET /api/calendar/summary` - Get calendar summary

#### Daily Journal
- `GET /api/daily/{date}` - Get daily journal for a date
- `GET /api/daily/{date}/trades` - Get trades for a date
- `GET /api/daily/{date}/summary` - Get daily summary
- `GET /api/daily/{date}/pnl-progression` - Get P&L progression
- `POST /api/daily/{date}/notes` - Create/update daily note
- `GET /api/daily/{date}/notes` - Get daily note

#### Charts
- `GET /api/charts/prices/{ticker}` - Get price data for charting
- `GET /api/charts/trade/{trade_id}` - Get price data for a specific trade

#### Options
- `GET /api/options/chain/{ticker}` - Get options chain
- `GET /api/options/chain/{ticker}/{expiration}` - Get options chain for expiration
- `GET /api/options/greeks/{ticker}` - Get Greeks data

#### Analytics
- `GET /api/analytics/performance` - Get performance metrics
- `GET /api/analytics/by-ticker` - Get performance by ticker
- `GET /api/analytics/by-type` - Get performance by trade type
- `GET /api/analytics/by-playbook` - Get performance by playbook

#### AI Agent Helpers
- `POST /api/ai/parse-trade` - Parse natural language trade description
- `POST /api/ai/batch-create` - Batch create trades from descriptions
- `GET /api/ai/suggestions/{ticker}` - Get trade suggestions for a ticker

#### Health
- `GET /api/health` - Health check (no auth required)

### API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8102/api/docs
- **ReDoc**: http://localhost:8102/api/redoc
- **OpenAPI JSON**: http://localhost:8102/api/openapi.json

## 🗄️ Database

### Database Schema

The application uses PostgreSQL with the following main tables:

- **trades**: Core trade data
- **price_cache**: Cached price data for charts
- **daily_notes**: Daily journal notes

### Migrations

Database migrations are managed with Alembic:

```bash
# Create a new migration
docker compose exec backend alembic revision --autogenerate -m "Description"

# Apply migrations
docker compose exec backend alembic upgrade head

# Rollback one migration
docker compose exec backend alembic downgrade -1
```

### Backup & Restore

```bash
# Backup database
docker compose exec postgres pg_dump -U trading_journal trading_journal > backup.sql

# Restore database
docker compose exec -T postgres psql -U trading_journal trading_journal < backup.sql
```

## 🚢 Deployment

### Production Deployment

1. **Update environment variables**:
   - Set `ENVIRONMENT=production`
   - Set `DEBUG=false`
   - Ensure all API keys are configured
   - Update `CORS_ORIGINS` with your frontend URLs

2. **Build and start**:
   ```bash
   docker compose up -d --build
   ```

3. **Run migrations**:
   ```bash
   docker compose exec backend alembic upgrade head
   ```

4. **Verify deployment**:
   ```bash
   curl http://localhost:8102/api/health
   ```

### Updating the Application

1. **Pull latest changes**:
   ```bash
   git pull origin main
   ```

2. **Rebuild and restart**:
   ```bash
   docker compose up -d --build
   ```

3. **Run migrations** (if schema changed):
   ```bash
   docker compose exec backend alembic upgrade head
   ```

### Port Configuration

Default ports:
- **Frontend**: 8101
- **Backend**: 8102
- **PostgreSQL**: 5432 (internal only)

To change ports, update `docker-compose.yml` and the `VITE_API_URL` in your `.env` file.

## 🔧 Configuration

### Environment Variables

See `env.template` for all available environment variables. Key variables:

- `API_KEY`: Authentication key for API access
- `DATABASE_URL`: PostgreSQL connection string
- `ALPHA_VANTAGE_API_KEY`: For stock price data
- `COINGECKO_API_KEY`: For crypto price data (optional)
- `POLYGON_API_KEY`: For options data (optional)
- `CORS_ORIGINS`: Comma-separated list of allowed origins

### Frontend Configuration

Frontend environment variables (set in `docker-compose.yml`):
- `VITE_API_URL`: Backend API URL
- `VITE_API_KEY`: API key for frontend requests
- `VITE_APP_NAME`: Application name

## 🧪 Testing

### Manual Testing

1. **Test API endpoints**:
   ```bash
   # Health check
   curl http://localhost:8102/api/health
   
   # List trades (requires API key)
   curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8102/api/trades
   
   # Create a trade
   curl -X POST \
        -H "X-API-Key: YOUR_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{
          "ticker": "AAPL",
          "trade_type": "STOCK",
          "side": "LONG",
          "entry_price": "150.50",
          "entry_quantity": "10",
          "entry_time": "2025-01-15T10:30:00"
        }' \
        http://localhost:8102/api/trades
   ```

2. **Test frontend**:
   - Open http://localhost:8101
   - Try creating a trade
   - Check dashboard, calendar, and charts

### Troubleshooting

**Backend won't start**:
- Check logs: `docker compose logs backend`
- Verify database is running: `docker compose ps postgres`
- Check environment variables are set correctly

**Frontend can't connect to backend**:
- Verify `VITE_API_URL` is correct in `docker-compose.yml`
- Check backend is running: `docker compose ps backend`
- Check CORS settings in backend

**Database connection errors**:
- Verify `DATABASE_URL` in `.env` matches `POSTGRES_PASSWORD`
- Check PostgreSQL container is healthy: `docker compose ps postgres`
- Check network connectivity: `docker compose exec backend ping postgres`

**API authentication errors**:
- Verify `API_KEY` in `.env` matches the key used in requests
- Check `X-API-Key` header is included in requests
- Verify frontend `VITE_API_KEY` matches backend `API_KEY`

## 📊 Performance Metrics

The application calculates various performance metrics:

- **Net P&L**: Total profit/loss after commissions
- **Gross P&L**: Total profit/loss before commissions
- **Win Rate**: Percentage of winning trades
- **Profit Factor**: Total gross profit / Total gross loss
- **Max Drawdown**: Maximum peak-to-trough decline
- **Zella Score**: Weighted composite metric
- **Sharpe Ratio**: Risk-adjusted return metric
- **Sortino Ratio**: Downside risk-adjusted return metric

See `STARTUP_GUIDE.md` for detailed calculation formulas.

## 🔐 Security

- API key authentication for all endpoints
- Environment variables for sensitive data
- CORS protection for frontend
- SQL injection protection via SQLAlchemy ORM
- Input validation via Pydantic schemas

## 📝 Development

### Project Structure

```
apps/trading-journal/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/        # API route handlers
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   ├── utils/             # Utility functions
│   │   ├── config.py          # Configuration
│   │   ├── database.py        # Database setup
│   │   └── main.py            # FastAPI app
│   ├── alembic/               # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/               # API client
│   │   ├── components/        # React components
│   │   ├── hooks/             # React hooks
│   │   ├── pages/             # Page components
│   │   └── App.tsx            # Main app component
│   ├── Dockerfile
│   └── package.json
├── data/                      # Persistent data
│   └── postgres/              # PostgreSQL data
├── docker-compose.yml
├── env.template
└── README.md
```

### Adding New Features

1. **Backend**:
   - Add models in `backend/app/models/`
   - Add schemas in `backend/app/schemas/`
   - Add services in `backend/app/services/`
   - Add routes in `backend/app/api/routes/`
   - Create migrations: `alembic revision --autogenerate`

2. **Frontend**:
   - Add components in `frontend/src/components/`
   - Add pages in `frontend/src/pages/`
   - Add API hooks in `frontend/src/hooks/`
   - Update routing in `frontend/src/App.tsx`

## 🤝 Contributing

This is a personal project, but if you're working on it:

1. Read the documentation (see above)
2. Check `TASKS.md` for available tasks
3. Follow coding standards in `TRADING_JOURNAL_AGENTS_PROMPT.md`
4. Submit code for review using `TRADING_JOURNAL_AGENT_REVIEWER_PROMPT.md`

## 📄 License

Personal use only.

## 🙏 Acknowledgments

- Inspired by Tradezella
- Built with FastAPI, React, and Material-UI
- Charts powered by TradingView Lightweight Charts

---

**Status**: Production Ready
**Last Updated**: 2025-11-11
**Version**: 1.0.0
