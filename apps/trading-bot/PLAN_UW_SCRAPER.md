# Unusual Whales Web Scraper Implementation Plan

## Overview
Build a hyper-rate-limited web scraper for Unusual Whales to extract market tide and ticker flow data without requiring the $350/month API subscription.

## Goals
1. Extract **Market Tide** data (net call/put premium, net volume)
2. Extract **Ticker Flow** data per symbol (net premium by ticker)
3. Keep module **isolated** from main codebase
4. Implement **aggressive rate limiting** (30-minute intervals)
5. **Cache data** to minimize requests

## Architecture

```
src/data/providers/unusual_whales_scraper/
├── __init__.py           # Public API exports
├── config.py             # Settings and configuration
├── models.py             # Data models (MarketTideData, TickerFlowData)
├── browser.py            # Playwright browser session management
├── scrapers/
│   ├── __init__.py
│   ├── market_tide.py    # Market tide page scraper
│   └── ticker_flow.py    # Ticker flow page scraper
├── cache.py              # File-based cache for persistence
├── scheduler.py          # Background task scheduler
└── provider.py           # Main provider class (integrates with sentiment system)
```

## Tasks

### Task 1: Create Data Models (`models.py`)
**Status:** Not Started
**Estimate:** Simple

Create dataclasses for:
- `MarketTideDataPoint` - Single timestamp entry with net_call_premium, net_put_premium, net_volume
- `MarketTideSnapshot` - Collection of data points + metadata (fetch time, interval)
- `TickerFlowData` - Per-ticker flow data (symbol, net_premium, call_volume, put_volume, timestamp)
- `ScraperStatus` - Track last fetch time, success/failure, error messages

### Task 2: Create Configuration (`config.py`)
**Status:** Not Started
**Estimate:** Simple

Settings class with:
- `UW_SCRAPER_ENABLED` - Enable/disable scraper
- `UW_SCRAPER_MARKET_TIDE_INTERVAL` - Minutes between market tide fetches (default: 30)
- `UW_SCRAPER_TICKER_FLOW_INTERVAL` - Minutes between ticker flow fetches (default: 60)
- `UW_SCRAPER_TICKER_FLOW_SYMBOLS` - List of symbols to track (default: ['SPY', 'QQQ', 'AAPL', 'NVDA', 'TSLA'])
- `UW_SCRAPER_CACHE_DIR` - Directory for cache files
- `UW_SCRAPER_SESSION_COOKIE` - Optional: logged-in session cookie for authenticated access
- `UW_SCRAPER_USER_AGENT` - Browser user agent string
- `UW_SCRAPER_HEADLESS` - Run browser headless (default: true)

### Task 3: Create Browser Session Manager (`browser.py`)
**Status:** Not Started
**Estimate:** Medium

Implement Playwright-based browser automation:
- `UWBrowserSession` class
  - Initialize Playwright with Chromium
  - Support headless and headed modes
  - Handle cookie injection for authenticated sessions
  - Implement page navigation with retry logic
  - Wait for JavaScript rendering
  - Screenshot capability for debugging
  - Graceful cleanup/shutdown

### Task 4: Create Market Tide Scraper (`scrapers/market_tide.py`)
**Status:** Not Started
**Estimate:** Medium

Target URL: `https://unusualwhales.com/flow/overview`

Extract from page:
1. Navigate to page, wait for JS render
2. Find market tide visualization/data elements
3. Extract:
   - Net call premium (cumulative or per interval)
   - Net put premium (cumulative or per interval)
   - Net volume differential
   - Timestamps (if available, else use fetch time)
4. Parse into `MarketTideDataPoint` objects
5. Return `MarketTideSnapshot`

DOM Inspection needed - will need to identify correct selectors during implementation.

### Task 5: Create Ticker Flow Scraper (`scrapers/ticker_flow.py`)
**Status:** Not Started
**Estimate:** Medium

Target URL: `https://unusualwhales.com/option-charts/ticker-flow?ticker_symbol={SYMBOL}`

Extract from page:
1. Navigate to ticker-specific flow page
2. Wait for chart/data to render
3. Extract:
   - Net premium (calls vs puts)
   - Call volume
   - Put volume
   - Premium distribution
   - Sentiment indicators if visible
4. Parse into `TickerFlowData` object

### Task 6: Create File-Based Cache (`cache.py`)
**Status:** Not Started
**Estimate:** Simple

Persistent caching to survive container restarts:
- `UWScraperCache` class
  - Store data as JSON files in configured directory
  - `save_market_tide(data: MarketTideSnapshot)`
  - `load_market_tide() -> Optional[MarketTideSnapshot]`
  - `save_ticker_flow(symbol: str, data: TickerFlowData)`
  - `load_ticker_flow(symbol: str) -> Optional[TickerFlowData]`
  - `is_stale(last_fetch: datetime, max_age_minutes: int) -> bool`
  - Automatic cleanup of old cache files

### Task 7: Create Background Scheduler (`scheduler.py`)
**Status:** Not Started
**Estimate:** Medium

Background task management:
- `UWScraperScheduler` class
  - Start/stop background scraping tasks
  - Schedule market tide fetches every N minutes
  - Schedule ticker flow fetches for each symbol
  - Stagger requests to avoid bursts
  - Track last successful fetch times
  - Emit events/callbacks on new data
  - Error handling with exponential backoff

### Task 8: Create Main Provider (`provider.py`)
**Status:** Not Started
**Estimate:** Medium

Integration point:
- `UnusualWhalesScraperProvider` class
  - Implements similar interface to existing sentiment providers
  - `get_market_tide() -> MarketTideSnapshot`
  - `get_ticker_flow(symbol: str) -> TickerFlowData`
  - `get_market_sentiment_score() -> float` (-1 to 1 based on market tide)
  - Start/stop scheduler
  - Health check methods
  - Metrics (last fetch, success rate, etc.)

### Task 9: Add Playwright Dependency
**Status:** Not Started
**Estimate:** Simple

Update `requirements/base.txt`:
- Add `playwright>=1.40.0`
- Update Dockerfile to run `playwright install chromium`

### Task 10: Integration with Sentiment Aggregator
**Status:** Not Started
**Estimate:** Simple

Optional integration:
- Add `unusual_whales_scraper` as a sentiment source
- Map market tide to sentiment score
- Add to aggregator if enabled

### Task 11: API Endpoints (Optional)
**Status:** Not Started
**Estimate:** Simple

FastAPI routes:
- `GET /api/options/market-tide` - Return cached market tide data
- `GET /api/options/ticker-flow/{symbol}` - Return cached ticker flow
- `GET /api/options/scraper/status` - Scraper health/status

### Task 12: Testing & Debugging
**Status:** Not Started
**Estimate:** Medium

- Manual testing of scrapers
- Screenshot dumps for debugging
- Verify data extraction accuracy
- Test rate limiting behavior
- Test cache persistence across restarts

## Dependencies
- `playwright` - Browser automation
- `aiofiles` - Async file operations for cache

## Rate Limiting Strategy
1. **Market Tide**: Fetch every 30 minutes during market hours
2. **Ticker Flow**: Fetch each symbol every 60 minutes, staggered
3. **Request spacing**: Minimum 60 seconds between any requests
4. **Market hours only**: 9:30 AM - 4:00 PM ET (optional)
5. **Exponential backoff**: On failure, wait 2x longer before retry

## Session/Auth Strategy
Two modes:
1. **Anonymous**: Basic scraping, may have limited data
2. **Authenticated**: Inject session cookie from logged-in browser
   - User logs in manually in browser
   - Export cookie and add to `.env`
   - Scraper uses cookie for authenticated access

## Risk Mitigation
- User-agent rotation (low priority)
- Request jitter (random delays)
- Respect robots.txt (check first)
- Graceful degradation if blocked
- Logging all requests for audit

## Implementation Order
1. Task 1 (Models) - Foundation
2. Task 2 (Config) - Settings
3. Task 6 (Cache) - Persistence
4. Task 3 (Browser) - Core infrastructure
5. Task 4 (Market Tide Scraper) - Primary feature
6. Task 9 (Dependencies) - Required for testing
7. Task 5 (Ticker Flow Scraper) - Secondary feature
8. Task 7 (Scheduler) - Automation
9. Task 8 (Provider) - Integration point
10. Task 10-12 - Polish and integration

## Notes
- Unusual Whales is a React/Next.js app - all data loads via JavaScript
- Will need to inspect actual DOM structure during implementation
- May need to adjust selectors if UI changes
- Consider adding screenshot-based OCR as fallback if DOM parsing fails
