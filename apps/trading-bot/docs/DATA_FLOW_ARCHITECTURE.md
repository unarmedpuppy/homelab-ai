# Data Flow Architecture & Persistence Strategy

## Overview

This document describes how trading data flows through the system, what is persisted to the database, and recommendations for improvements.

## Current Data Flow

### 1. Trade Execution Flow

```
User/API Request
    ↓
/api/trading/execute
    ↓
Risk Management Validation
    ↓
IBKR Order Placement
    ↓
✅ Trade Record Saved to DB (trades table)
    ↓
Settlement Tracking Saved (settlement_tracking table)
    ↓
Day Trade Detection & Recording (day_trades table)
    ↓
Trade Frequency Tracking (trade_frequency_tracking table)
```

**What Gets Persisted:**
- ✅ **Trade record** (`Trade` model) - All trade details (symbol, side, quantity, price, status, timestamps)
- ✅ **Settlement tracking** (`SettlementTracking` model) - T+2 settlement dates and amounts
- ✅ **Day trade records** (`DayTrade` model) - For PDT compliance
- ✅ **Trade frequency** (`TradeFrequencyTracking` model) - Daily/weekly trade counts

**Status:** ✅ **FULLY PERSISTED** - All trade data is saved to database

### 2. Position Data Flow

```
IBKR Position Update (real-time)
    ↓
IBKR Client Callbacks
    ↓
WebSocket Broadcast (real-time)
    ↓
❌ NOT Synced to Database
```

**What Gets Persisted:**
- ❌ **Positions are NOT automatically synced to database**
- ❌ The `Position` table exists but is rarely populated
- ❌ Positions are only queried from IBKR in real-time

**Current Behavior:**
- Positions are fetched from IBKR API on-demand (`/api/trading/ibkr/positions`)
- Dashboard reads positions directly from IBKR (not from database)
- No background sync job to keep `Position` table updated

**Status:** ⚠️ **NOT PERSISTED** - Positions exist only in IBKR and memory

### 3. Portfolio Summary Flow

```
Dashboard Request
    ↓
/api/trading/portfolio/summary
    ↓
Query IBKR API (real-time)
    ↓
Query Database (trades, positions)
    ↓
Aggregate & Return
```

**Data Sources:**
- **Portfolio Value**: From IBKR API (`NetLiquidation`)
- **Cash Balance**: From IBKR API (`TotalCashValue`)
- **Active Positions**: From IBKR API (real-time positions)
- **Daily P&L**: Calculated from IBKR positions (unrealized P&L)
- **Win Rate**: From database (`Position` table - closed positions)
- **Total Trades**: From database (`Trade` table)

**Status:** ⚠️ **HYBRID** - Mix of real-time IBKR data and database queries

### 4. Dashboard Data Flow

```
Dashboard Load
    ↓
JavaScript API Calls
    ↓
/api/trading/portfolio/summary (IBKR + DB)
    ↓
/api/trading/trades (Database)
    ↓
/api/market-data/quote/{symbol} (Market Data Provider)
    ↓
Render UI
```

**Data Sources:**
- **Portfolio Stats**: Hybrid (IBKR API + Database)
- **Trade History**: Database (`Trade` table)
- **Market Prices**: Market data providers (Alpha Vantage, Polygon, etc.)
- **Performance Charts**: Calculated from database trades

**Status:** ✅ **MOSTLY PERSISTED** - Trade history is persisted, but positions are not

### 5. Scheduler Data Flow

```
Scheduler Evaluation Cycle
    ↓
Get Positions from IBKR (real-time)
    ↓
Evaluate Strategies
    ↓
Generate Signals
    ↓
Execute Trades via /api/trading/execute
    ↓
✅ Trades Saved to Database
    ↓
❌ Positions NOT Synced to Database
```

**Status:** ⚠️ **PARTIAL** - Trades are persisted, but position state is not tracked in DB

## Database Models

### ✅ Fully Utilized Models

1. **`Trade`** - All executed trades are saved
2. **`SettlementTracking`** - T+2 settlement tracking
3. **`DayTrade`** - Day trade records for PDT compliance
4. **`TradeFrequencyTracking`** - Trade frequency limits
5. **`CashAccountState`** - Cash account balance tracking
6. **`Tweet`**, **`TweetSentiment`** - Twitter sentiment data
7. **`RedditPost`**, **`RedditSentiment`** - Reddit sentiment data
8. **`SymbolSentiment`**, **`AggregatedSentiment`** - Aggregated sentiment
9. **`ConfluenceScore`** - Confluence calculations
10. **`OptionsFlow`**, **`OptionsPattern`** - Options flow data

### ⚠️ Underutilized Models

1. **`Position`** - Model exists but positions are NOT synced from IBKR
   - Only populated manually or through closed positions
   - Dashboard reads positions from IBKR API, not database
   - No historical position tracking

2. **`PerformanceMetrics`** - Model exists but not actively populated
   - Could be used for daily portfolio snapshots
   - Currently, performance is calculated on-demand

3. **`MarketData`** - Model exists but not actively used
   - Could store historical OHLCV data
   - Currently, market data is fetched on-demand and cached in Redis

## Current Gaps & Issues

### 🔴 Critical Gaps

1. **No Position Sync to Database**
   - Positions are only in IBKR (real-time)
   - If IBKR is disconnected, position history is lost
   - Cannot analyze historical position changes
   - Dashboard cannot show positions when IBKR is offline

2. **No Historical Portfolio Snapshots**
   - Portfolio value is only available when IBKR is connected
   - Cannot track portfolio value over time
   - Performance charts rely on trade data only, not actual portfolio value

3. **Incomplete P&L Tracking**
   - Daily P&L is calculated from unrealized P&L (positions)
   - Realized P&L is not properly tracked when positions close
   - Win rate calculation relies on closed positions, but positions aren't synced

### 🟡 Medium Priority Gaps

4. **No Market Data Persistence**
   - Market data is cached in Redis (temporary)
   - No historical OHLCV data stored
   - Cannot backtest or analyze historical price movements

5. **No Performance Metrics Snapshots**
   - `PerformanceMetrics` table exists but is not populated
   - Could store daily portfolio snapshots for trend analysis

6. **Position Lifecycle Not Tracked**
   - When positions open/close, this is not recorded in database
   - Cannot track position duration, entry/exit prices accurately

## Recommendations

### 🔴 High Priority: Position Sync Service

**Problem:** Positions are not persisted, making historical analysis impossible.

**Solution:** Create a background service that syncs IBKR positions to the database.

**Implementation:**
```python
# src/core/sync/position_sync.py
class PositionSyncService:
    """
    Syncs IBKR positions to database Position table
    Runs periodically (every 5 minutes) or on position change callbacks
    """
    
    async def sync_positions(self, account_id: int):
        """Sync current IBKR positions to database"""
        # 1. Get positions from IBKR
        # 2. Get existing positions from database
        # 3. Compare and update/create/close positions
        # 4. Track position lifecycle (open -> close)
        pass
```

**Benefits:**
- Historical position tracking
- Dashboard works offline (shows last known positions)
- Accurate P&L calculation
- Position duration analysis

### 🔴 High Priority: Portfolio Snapshot Service

**Problem:** Portfolio value is only available when IBKR is connected.

**Solution:** Store daily/hourly portfolio snapshots.

**Implementation:**
```python
# Use existing PerformanceMetrics model
# Create background job that runs every hour
async def snapshot_portfolio(account_id: int):
    """Store current portfolio state"""
    # 1. Get portfolio value from IBKR
    # 2. Get positions
    # 3. Store snapshot in PerformanceMetrics table
    pass
```

**Benefits:**
- Historical portfolio value tracking
- Performance charts with actual portfolio value
- Trend analysis over time

### 🟡 Medium Priority: Market Data Persistence

**Problem:** Market data is only cached temporarily in Redis.

**Solution:** Store historical OHLCV data in `MarketData` table.

**Implementation:**
- When fetching market data, also store in database
- Use for backtesting and historical analysis
- Implement data retention policies

### 🟡 Medium Priority: Realized P&L Tracking

**Problem:** Realized P&L is not properly calculated when positions close.

**Solution:** Calculate and store realized P&L when positions are closed.

**Implementation:**
- When position closes, calculate realized P&L from entry/exit prices
- Store in `Trade` model or create `ClosedPosition` model
- Update win rate calculation to use realized P&L

### 🟢 Low Priority: Position Lifecycle Events

**Problem:** Position open/close events are not tracked.

**Solution:** Create `PositionEvent` model to track position lifecycle.

**Implementation:**
- Track when positions open (first buy)
- Track when positions close (final sell)
- Track partial closes
- Calculate position duration

## Proposed Data Flow (After Improvements)

### Position Sync Flow

```
IBKR Position Update
    ↓
Position Sync Service (background job)
    ↓
Compare with Database Positions
    ↓
✅ Update/Create/Close Position Records
    ↓
✅ Store Position Snapshot
    ↓
✅ Calculate Realized P&L (if closed)
    ↓
✅ Update Performance Metrics
```

### Portfolio Snapshot Flow

```
Hourly/Daily Snapshot Job
    ↓
Get Portfolio Value from IBKR
    ↓
Get All Positions
    ↓
✅ Store Snapshot in PerformanceMetrics
    ↓
✅ Update Portfolio Charts
```

### Complete Trade Lifecycle

```
Trade Executed
    ↓
✅ Trade Record Saved
    ↓
Position Sync Service Detects Change
    ↓
✅ Position Updated/Created in DB
    ↓
Position Closed (via sync service)
    ↓
✅ Realized P&L Calculated
    ↓
✅ Position Status = CLOSED
    ↓
✅ Win Rate Updated
```

## Implementation Priority

1. **Phase 1 (Critical):**
   - [ ] Position sync service
   - [ ] Portfolio snapshot service
   - [ ] Realized P&L calculation

2. **Phase 2 (Important):**
   - [ ] Market data persistence
   - [ ] Position lifecycle tracking
   - [ ] Performance metrics snapshots

3. **Phase 3 (Nice to Have):**
   - [ ] Historical data analysis tools
   - [ ] Advanced performance metrics
   - [ ] Data retention policies

## Summary

### Current State
- ✅ **Trades**: Fully persisted
- ⚠️ **Positions**: Not persisted (only in IBKR)
- ⚠️ **Portfolio Value**: Not persisted (only real-time)
- ⚠️ **Market Data**: Cached only (not persisted)
- ✅ **Sentiment Data**: Fully persisted

### Recommended State
- ✅ **Trades**: Fully persisted (keep as-is)
- ✅ **Positions**: Synced to database (add sync service)
- ✅ **Portfolio Value**: Snapshot service (add hourly/daily snapshots)
- ✅ **Market Data**: Persisted for historical analysis (optional)
- ✅ **Sentiment Data**: Fully persisted (keep as-is)

### Key Takeaway
**The main gap is position persistence.** Currently, if IBKR is disconnected, the dashboard cannot show positions, and there's no historical position data for analysis. Implementing a position sync service would solve this critical gap.

