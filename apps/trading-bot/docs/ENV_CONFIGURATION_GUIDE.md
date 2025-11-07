# Environment Configuration Guide

## Overview

The trading bot uses environment variables for configuration. You have two template files:
- `env.template` - Comprehensive template with all possible settings
- `env.production` - Minimal production template

## Which File to Use?

**For your server deployment, you should create a `.env` file** (not `env.template` or `env.production`).

### Recommended Approach:
1. **Copy `env.template` to `.env`** (it has all settings with defaults)
2. **Fill in only the API keys you want to use**
3. **Leave others empty** - the app will work without them

## Required vs Optional Settings

### ✅ **REQUIRED** (App won't work without these)
- **None!** The app can run with all API keys empty.

### ⚠️ **HIGHLY RECOMMENDED** (Core functionality)
- `DATABASE_URL` - Database connection (defaults to SQLite if not set)
- `IBKR_HOST`, `IBKR_PORT`, `IBKR_CLIENT_ID` - For Interactive Brokers connection (already set in docker-compose.yml)

### 🔑 **OPTIONAL** (Enable specific features)

#### Market Data Providers (at least one recommended)
- `ALPHA_VANTAGE_API_KEY` - Free tier available
- `POLYGON_API_KEY` - Free tier available
- `IEX_CLOUD_API_KEY` - Free tier available
- `TWELVE_DATA_API_KEY` - Free tier available

**Note:** If IBKR is connected, market data will use IBKR. These are fallbacks.

#### Sentiment Data Sources (all optional, enable what you want)
- **Twitter/X**: `TWITTER_API_KEY`, `TWITTER_API_SECRET`, `TWITTER_BEARER_TOKEN`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_TOKEN_SECRET`
- **Reddit**: `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` (username/password optional)
- **StockTwits**: `STOCKTWITS_API_TOKEN` (optional, works without it)
- **News**: `NEWS_NEWSAPI_KEY` (optional, uses RSS feeds by default)
- **Google Trends**: No API key needed (free, rate-limited)
- **Analyst Ratings**: No API key needed (uses yfinance, free)
- **Insider Trading**: No API key needed (uses yfinance, free)
- **SEC Filings**: No API key needed (public data)

#### Options Flow (paid service)
- `UW_API_KEY` - Unusual Whales API (paid service)

#### Dark Pool Data (paid service)
- `DARK_POOL_API_KEY` - Dark pool data provider (paid service)

## Current Status

### What's Missing from `env.production`:
The `env.production` file is missing many settings that are in `env.template`:
- Most sentiment provider settings
- WebSocket configuration
- Sentiment aggregator weights
- Confluence calculator settings
- Data retention settings
- Risk management settings
- Scheduler settings
- Redis configuration (if using Redis)

### What's in `docker-compose.yml`:
The docker-compose.yml has hardcoded defaults for:
- Database: `sqlite:////data/trading_bot.db`
- IBKR: `host.docker.internal:7497`
- API: `0.0.0.0:8000`
- Logging: `INFO` level

## Recommended Setup Steps

1. **Create `.env` file**:
   ```bash
   cd /path/to/trading-bot
   cp env.template .env
   ```

2. **Edit `.env` and add only the API keys you want**:
   - At minimum, you can leave everything empty and the app will run
   - For market data: Add at least one market data provider API key (or use IBKR)
   - For sentiment: Add Twitter/Reddit keys if you want those features
   - For options flow: Add `UW_API_KEY` if you have Unusual Whales subscription

3. **Important settings to review**:
   - `DATABASE_URL` - Should match docker-compose.yml (`sqlite:////data/trading_bot.db`)
   - `IBKR_HOST` - Should be `host.docker.internal` for Docker (already in docker-compose.yml)
   - `ENVIRONMENT` - Set to `production` for server
   - `SECRET_KEY` and `JWT_SECRET` - Change from defaults for production

4. **Deploy**:
   ```bash
   docker-compose up -d
   ```

## How It Works

1. **docker-compose.yml** reads environment variables using `${VAR:-default}` syntax
2. If `.env` file exists in the same directory, docker-compose automatically loads it
3. **settings.py** also reads from `.env` file (line 635: `env_file = ".env"`)
4. If a variable is not set, it uses the default from `settings.py` or docker-compose defaults

## Verification

After creating `.env`, verify it's being loaded:
```bash
# Check if docker-compose sees the variables
docker-compose config | grep -A 5 "ALPHA_VANTAGE_API_KEY"

# Check container environment
docker exec trading-bot env | grep TWITTER
```

## Summary

- ✅ **Create `.env` from `env.template`** (most comprehensive)
- ✅ **All API keys are optional** - app works without them
- ✅ **Fill in only what you need** - leave others empty
- ✅ **docker-compose.yml already has good defaults** for core settings
- ⚠️ **Change `SECRET_KEY` and `JWT_SECRET`** for production security

