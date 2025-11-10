# Trading Journal - Startup Guide

This guide provides essential information to get started with implementing the Trading Journal application.

## Quick Start Checklist

Before starting implementation:

- [ ] Review `IMPLEMENTATION_PLAN.md` - Understand the full scope
- [ ] Review `TRADING_JOURNAL_AGENTS_PROMPT.md` - Understand your role and standards
- [ ] Review `TRADING_JOURNAL_AGENT_REVIEWER_PROMPT.md` - Know what reviewers will check
- [ ] Check `TASKS.md` - See available tasks
- [ ] Read this `STARTUP_GUIDE.md` - Get all the details you need
- [ ] Claim your first task in `TASKS.md`

## Calculation Formulas

### Net P&L Calculation

**For Stocks:**
```
Net P&L = (Exit Price - Entry Price) × Quantity - Entry Commission - Exit Commission
```

**For Options:**
```
Net P&L = (Exit Price - Entry Price) × Quantity × 100 - Entry Commission - Exit Commission
```
*Note: Options contracts are typically for 100 shares*

**For Crypto:**
```
Net P&L = (Exit Price - Entry Price) × Quantity - Entry Commission - Exit Commission
```

**For Short Positions:**
```
Net P&L = (Entry Price - Exit Price) × Quantity - Entry Commission - Exit Commission
```

### ROI (Return on Investment) Calculation

```
ROI = (Net P&L / Total Cost) × 100

Where:
Total Cost = (Entry Price × Quantity) + Entry Commission
```

**For Options:**
```
Total Cost = (Entry Price × Quantity × 100) + Entry Commission
```

### R-Multiple Calculation

```
R-Multiple = Net P&L / Risk Amount

Where:
Risk Amount = Entry Price × Quantity (for LONG)
Risk Amount = (Entry Price - Stop Loss) × Quantity (if stop loss defined)
```

**Default**: If no stop loss is defined, use entry price × quantity as risk amount.

### Profit Factor

```
Profit Factor = Total Gross Profit / Total Gross Loss

Where:
Total Gross Profit = Sum of all winning trades' gross profit
Total Gross Loss = Absolute value of sum of all losing trades' gross loss
```

### Max Drawdown

```
Max Drawdown = Maximum peak-to-trough decline in cumulative P&L

Algorithm:
1. Calculate cumulative P&L over time
2. Track peak values
3. Calculate drawdown = (Peak - Current) / Peak × 100
4. Max Drawdown = Maximum drawdown value
```

### Zella Score (Composite Metric)

```
Zella Score = Weighted average of normalized metrics

Components (all normalized to 0-100 scale):
- Win Rate: 30% weight
- Consistency: 20% weight (based on standard deviation of daily P&L)
- Profit Factor: 25% weight
- Avg Win/Loss Ratio: 15% weight
- Max Drawdown (inverse): 10% weight

Formula:
Zella Score = (WinRate × 0.30) + (Consistency × 0.20) + (ProfitFactor × 0.25) + 
              (AvgWinLoss × 0.15) + ((100 - MaxDrawdown) × 0.10)
```

## UI/UX Design Preferences

### Theme
- **Dark Mode**: Primary theme (dark background, light text)
- **Color Scheme**:
  - Green: Profitable trades/days (#10b981 or similar)
  - Red: Losing trades/days (#ef4444 or similar)
  - Gray: Neutral/no trades (#6b7280 or similar)
  - Purple: Brand/primary accent (match Tradezella style if possible)

### Layout
- **Sidebar Navigation**: Left side, collapsible
- **Main Content**: Center area
- **Calendar**: Right sidebar (on desktop), full width (on mobile)
- **Responsive**: Mobile-first design, breakpoints at 640px, 768px, 1024px

### Typography
- **Font**: System fonts (sans-serif stack)
- **Headings**: Bold, clear hierarchy
- **Numbers**: Monospace font for financial data

## API Key Setup

### Required API Keys

#### Alpha Vantage (Primary - Free Tier Available)
- **Get API Key**: https://www.alphavantage.co/support/#api-key
- **Free Tier**: 5 API calls per minute, 500 calls per day
- **Usage**: Stock and crypto price data
- **Environment Variable**: `ALPHA_VANTAGE_API_KEY`

#### CoinGecko (For Crypto - Free Tier Available)
- **Get API Key**: https://www.coingecko.com/en/api
- **Free Tier**: 10-50 calls per minute (depends on plan)
- **Usage**: Crypto spot and perpetual futures data
- **Environment Variable**: `COINGECKO_API_KEY` (optional, can use free tier without key)

#### Polygon.io (Optional - For Better Options Data)
- **Get API Key**: https://polygon.io/
- **Free Tier**: Limited
- **Usage**: Options chain data, Greeks (future enhancement)
- **Environment Variable**: `POLYGON_API_KEY`

### API Key Generation Commands

```bash
# Generate API key for authentication (use this for API_KEY env var)
openssl rand -hex 32

# Generate database password
openssl rand -hex 32
```

## Environment Variables Template

Create `env.template` with:

```env
# Database Configuration
# Generate password with: openssl rand -hex 32
DATABASE_URL=postgresql://trading_journal:CHANGE_ME@postgres:5432/trading_journal
POSTGRES_USER=trading_journal
POSTGRES_PASSWORD=CHANGE_ME
POSTGRES_DB=trading_journal

# API Authentication
# Generate with: openssl rand -hex 32
API_KEY=CHANGE_ME

# API Server Configuration
API_HOST=0.0.0.0
API_PORT=8000

# External Data Provider API Keys
# Get free API keys from:
# - Alpha Vantage: https://www.alphavantage.co/support/#api-key
# - CoinGecko: https://www.coingecko.com/en/api (optional, works without key)
# - Polygon.io: https://polygon.io/ (optional, for options data)
ALPHA_VANTAGE_API_KEY=
COINGECKO_API_KEY=
POLYGON_API_KEY=

# CORS Configuration
# Add your frontend URLs (comma-separated)
CORS_ORIGINS=http://localhost:8101,http://192.168.86.47:8101

# Environment
ENVIRONMENT=production
DEBUG=false

# Frontend Configuration (for frontend/.env)
VITE_API_URL=http://localhost:8100/api
VITE_APP_NAME=Trading Journal
```

## Historical Data Provider Strategy

### Priority Order

1. **Alpha Vantage** (Primary)
   - Supports: Stocks, some crypto
   - Free tier: 5 calls/min, 500/day
   - Use for: Stock price data, basic crypto

2. **yfinance** (Fallback - No API Key Needed)
   - Python library, free
   - Supports: Stocks, crypto
   - Use for: Fallback when Alpha Vantage fails

3. **CoinGecko** (Crypto Specific)
   - Free tier available
   - Supports: Crypto spot, perpetuals
   - Use for: Crypto-specific data

4. **Polygon.io** (Future - Options)
   - Paid service (better options data)
   - Use for: Options chain, Greeks (future)

### Caching Strategy

- Cache all price data in `price_cache` table
- Cache duration: 24 hours for daily data, 1 hour for intraday
- Check cache before making API calls
- Update cache on miss

## Database Setup Details

### PostgreSQL Configuration

- **Version**: PostgreSQL 15+
- **Database Name**: `trading_journal`
- **User**: `trading_journal`
- **Password**: Generate with `openssl rand -hex 32`
- **Port**: Internal only (5432 in container)
- **Volume**: `./data/postgres` (persistent)

### Initial Migration

The first migration should create:
1. `trades` table (with all fields from schema)
2. `daily_summaries` table
3. `price_cache` table
4. `daily_notes` table
5. All indexes as specified

## Docker Compose Structure

### Services

1. **postgres** (PostgreSQL database)
   - Image: `postgres:15-alpine`
   - No exposed ports (internal only)
   - Volume: `./data/postgres:/var/lib/postgresql/data`
   - Health check: Required

2. **backend** (FastAPI application)
   - Build: `./backend`
   - Port: `8100:8000`
   - Depends on: `postgres` (with health check)
   - Environment: From `.env` file
   - Volume: `./backend:/app` (for development)

3. **frontend** (React application)
   - Build: `./frontend`
   - Port: `8101:80` (Nginx serves built files)
   - Depends on: `backend` (for API calls)
   - Environment: From `.env` file

### Network
- All services on `my-network` (external network)
- Services communicate via service names: `postgres`, `backend`, `frontend`

## First Task Recommendation

**Start with T1.1: Project Structure Setup**

This task involves:
1. Creating directory structure
2. Setting up `.gitignore`
3. Creating initial `README.md`
4. No code dependencies

**Why start here:**
- No dependencies on other tasks
- Establishes foundation
- Quick win to get started
- Sets up project structure for all future work

## Common Gotchas to Avoid

1. **Port Conflicts**: 
   - Backend: 8100 (not 8000, which trading-bot uses)
   - Frontend: 8101 (not 3000, which homepage uses)

2. **Network Configuration**:
   - Must use `my-network` external network
   - Don't create new networks

3. **Database Migrations**:
   - Use Alembic for all schema changes
   - Never modify database directly
   - Always create migrations for changes

4. **API Endpoints**:
   - Every UI action needs an API endpoint
   - Don't forget pagination for list endpoints
   - Always include API key authentication

5. **Type Safety**:
   - No `any` types in TypeScript
   - All Python functions need type hints
   - Use Pydantic for validation

6. **Calculations**:
   - Test with known values
   - Handle edge cases (zero, negative, very large)
   - Different formulas for different trade types

## Testing Your Setup

After completing T1.1 and T1.2 (Docker Compose), test:

```bash
# Build and start services
cd apps/trading-journal
docker compose up -d --build

# Check services are running
docker compose ps

# Check backend logs
docker compose logs backend

# Check frontend logs
docker compose logs frontend

# Test backend health
curl http://localhost:8100/api/health

# Test frontend (should serve static files)
curl http://localhost:8101
```

## Getting Help

- **Implementation Details**: See `IMPLEMENTATION_PLAN.md`
- **Agent Guidelines**: See `TRADING_JOURNAL_AGENTS_PROMPT.md`
- **Review Standards**: See `TRADING_JOURNAL_AGENT_REVIEWER_PROMPT.md`
- **Server Setup**: See `apps/docs/SERVER_AGENT_PROMPT.md`
- **Task Tracking**: See `TASKS.md`

## Next Steps

1. **Claim T1.1** in `TASKS.md`
2. **Read the task details** in `TRADING_JOURNAL_AGENTS_PROMPT.md`
3. **Start implementing** following the guidelines
4. **Complete Pre-Submission Checklist** before marking as `[REVIEW]`
5. **Wait for review** and address any feedback

---

**Ready to start?** Claim T1.1 in `TASKS.md` and begin!

