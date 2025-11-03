# Dashboard Real Data Integration Guide

**Status**: ⏳ **TODO** - Dashboard currently uses static/hardcoded data  
**Priority**: 🔴 HIGH - Critical for functional dashboard

## Problem

The dashboard (`src/ui/templates/dashboard.html`) currently displays **hardcoded static data** instead of pulling real data from the database and APIs.

### Current Static Data Locations

1. **Portfolio Value**: Line 64 - `$100,000` (hardcoded)
2. **Today's P&L**: Line 76 - `+$1,250` (hardcoded)
3. **Win Rate**: Line 88 - `68.5%` (hardcoded)
4. **Active Trades**: Line 100 - `3` (hardcoded)
5. **Current Price**: Line 145 - `$150.25` (hardcoded)
6. **Recent Trades**: Lines 205-224 - Hardcoded HTML elements
7. **Portfolio Chart**: Lines 477-480 - Hardcoded data array
8. **Trade Distribution**: Lines 508-509 - Hardcoded win/loss percentages

## Available API Endpoints

### ✅ Already Implemented

1. **Account Summary**:
   - `GET /api/trading/ibkr/account` - Returns account data including NetLiquidation value
   - Response includes: `TotalCashValue`, `NetLiquidation`, `BuyingPower`, etc.

2. **Positions**:
   - `GET /api/trading/ibkr/positions` - Returns current open positions
   - Response includes: `symbol`, `quantity`, `average_price`, `market_price`, `unrealized_pnl`

3. **Market Data**:
   - `GET /api/market-data/quote/{symbol}` - Real-time quote for a symbol
   - Returns: `symbol`, `price`, `change`, `change_percent`, `volume`, `timestamp`

4. **Trade History**:
   - Need to check if `/api/trading/trades` endpoint exists
   - Database model exists: `Trade` model in `src/data/database/models.py`

### ❌ Missing Endpoints (Need to Create)

1. **Portfolio Summary Endpoint**:
   - Calculate total portfolio value
   - Calculate daily/weekly/monthly P&L
   - Calculate win rate from historical trades
   - Calculate total number of active trades

2. **Trade History Endpoint**:
   - `GET /api/trading/trades` - List recent trades with pagination
   - Should return: trades with symbol, side, quantity, price, P&L, timestamp

3. **Performance Metrics Endpoint**:
   - Calculate win rate from closed trades
   - Calculate total profit/loss
   - Calculate trade statistics

## Implementation Steps

### Step 1: Create Portfolio Summary API Endpoint

**File**: `src/api/routes/trading.py`

**Endpoint**: `GET /api/trading/portfolio/summary`

**Functionality**:
1. Get account summary from IBKR (`/api/trading/ibkr/account`)
2. Get current positions (`/api/trading/ibkr/positions`)
3. Query database for today's trades to calculate daily P&L
4. Query database for closed trades to calculate win rate
5. Return aggregated portfolio summary

**Response Structure**:
```json
{
  "portfolio_value": 100000.00,
  "cash_balance": 50000.00,
  "positions_value": 50000.00,
  "daily_pnl": 1250.00,
  "daily_pnl_percent": 1.25,
  "total_pnl": 5000.00,
  "win_rate": 0.685,
  "total_trades": 50,
  "winning_trades": 34,
  "losing_trades": 16,
  "active_positions": 3,
  "last_updated": "2024-12-19T14:30:00Z"
}
```

### Step 2: Create Trade History API Endpoint

**File**: `src/api/routes/trading.py`

**Endpoint**: `GET /api/trading/trades`

**Parameters**:
- `limit` (query, optional): Number of trades to return (default: 20)
- `offset` (query, optional): Pagination offset (default: 0)
- `symbol` (query, optional): Filter by symbol
- `side` (query, optional): Filter by side (BUY/SELL)

**Functionality**:
1. Query `Trade` table from database
2. Join with account and position data
3. Calculate realized P&L for closed trades
4. Return formatted trade list

**Response Structure**:
```json
{
  "trades": [
    {
      "id": 1,
      "symbol": "AAPL",
      "side": "BUY",
      "quantity": 10,
      "price": 150.25,
      "filled_price": 150.30,
      "status": "FILLED",
      "realized_pnl": 125.00,
      "timestamp": "2024-12-19T14:25:00Z",
      "strategy_id": "momentum_1"
    }
  ],
  "total": 50,
  "limit": 20,
  "offset": 0
}
```

### Step 3: Create Performance Metrics Endpoint

**File**: `src/api/routes/trading.py`

**Endpoint**: `GET /api/trading/performance`

**Functionality**:
1. Query all closed trades from database
2. Calculate win rate (winning trades / total closed trades)
3. Calculate average win/loss
4. Calculate profit factor
5. Calculate sharpe ratio (if enough data)

**Response Structure**:
```json
{
  "win_rate": 0.685,
  "total_trades": 50,
  "winning_trades": 34,
  "losing_trades": 16,
  "average_win": 250.00,
  "average_loss": -150.00,
  "profit_factor": 1.67,
  "largest_win": 500.00,
  "largest_loss": -300.00,
  "total_profit": 5000.00,
  "period": {
    "start": "2024-01-01",
    "end": "2024-12-19"
  }
}
```

### Step 4: Update Dashboard JavaScript

**File**: `src/ui/templates/dashboard.html`

**Changes Needed**:

1. **Add `loadPortfolioSummary()` function**:
   ```javascript
   async loadPortfolioSummary() {
       try {
           const response = await fetch('/api/trading/portfolio/summary');
           const data = await response.json();
           
           // Update portfolio value
           document.getElementById('portfolio-value').textContent = 
               `$${data.portfolio_value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
           
           // Update daily P&L
           const pnlEl = document.getElementById('daily-pnl');
           const pnlSign = data.daily_pnl >= 0 ? '+' : '';
           const pnlColor = data.daily_pnl >= 0 ? 'text-green-600' : 'text-red-600';
           pnlEl.textContent = `${pnlSign}$${Math.abs(data.daily_pnl).toLocaleString()}`;
           pnlEl.className = `text-2xl font-semibold ${pnlColor}`;
           
           // Update win rate
           document.getElementById('win-rate').textContent = 
               `${(data.win_rate * 100).toFixed(1)}%`;
           
           // Update active trades
           document.getElementById('active-trades').textContent = data.active_positions;
       } catch (error) {
           console.error('Error loading portfolio summary:', error);
       }
   }
   ```

2. **Add `loadRecentTrades()` function**:
   ```javascript
   async loadRecentTrades() {
       try {
           const response = await fetch('/api/trading/trades?limit=5');
           const data = await response.json();
           
           const recentTrades = document.getElementById('recent-trades');
           recentTrades.innerHTML = ''; // Clear existing
           
           data.trades.forEach(trade => {
               const tradeEl = document.createElement('div');
               tradeEl.className = 'flex justify-between items-center p-3 bg-gray-50 rounded-md';
               
               const pnl = trade.realized_pnl || 0;
               const pnlColor = pnl >= 0 ? 'text-green-600' : 'text-red-600';
               const pnlSign = pnl >= 0 ? '+' : '';
               const timeAgo = this.formatTimeAgo(new Date(trade.timestamp));
               
               tradeEl.innerHTML = `
                   <div>
                       <p class="font-medium">${trade.symbol}</p>
                       <p class="text-sm text-gray-500">${trade.side} ${trade.quantity} shares</p>
                   </div>
                   <div class="text-right">
                       <p class="font-semibold ${pnlColor}">${pnlSign}$${Math.abs(pnl).toFixed(2)}</p>
                       <p class="text-sm text-gray-500">${timeAgo}</p>
                   </div>
               `;
               
               recentTrades.appendChild(tradeEl);
           });
       } catch (error) {
           console.error('Error loading recent trades:', error);
       }
   }
   ```

3. **Update `init()` method**:
   ```javascript
   init() {
       this.connectWebSocket();
       this.setupEventListeners();
       this.initializeCharts();
       this.startPriceUpdates();
       
       // Load real data on initialization
       this.loadPortfolioSummary();
       this.loadRecentTrades();
       this.loadPortfolioChartData();
       
       // Refresh data every 30 seconds
       setInterval(() => {
           this.loadPortfolioSummary();
           this.loadRecentTrades();
       }, 30000);
   }
   ```

4. **Update price display to use real market data**:
   ```javascript
   async refreshPrice() {
       const symbol = document.getElementById('symbol-select').value;
       
       try {
           const response = await fetch(`/api/market-data/quote/${symbol}`);
           const data = await response.json();
           
           document.getElementById('current-price').textContent = `$${data.price.toFixed(2)}`;
           
           const change = data.change || 0;
           const changePct = data.change_percent || 0;
           const changeColor = change >= 0 ? 'text-green-600' : 'text-red-600';
           const changeSign = change >= 0 ? '+' : '';
           
           document.getElementById('price-change').textContent = 
               `${changeSign}$${Math.abs(change).toFixed(2)}`;
           document.getElementById('price-change-pct').textContent = 
               `${changeSign}${Math.abs(changePct).toFixed(2)}%`;
           
           document.getElementById('price-change').className = `text-lg font-semibold ${changeColor}`;
           document.getElementById('price-change-pct').className = `text-sm ${changeColor}`;
       } catch (error) {
           console.error('Error refreshing price:', error);
       }
   }
   ```

### Step 5: Update Chart Data

**Update `initializeCharts()` method**:

1. **Portfolio Performance Chart**:
   ```javascript
   async loadPortfolioChartData() {
       try {
           // Query database for historical portfolio values
           // This requires a new endpoint or querying trade history
           const response = await fetch('/api/trading/portfolio/history?days=30');
           const data = await response.json();
           
           // Update chart with real data
           portfolioChart.data.labels = data.dates;
           portfolioChart.data.datasets[0].data = data.values;
           portfolioChart.update();
       } catch (error) {
           console.error('Error loading portfolio chart data:', error);
       }
   }
   ```

2. **Trade Distribution Chart**:
   ```javascript
   async loadTradeDistributionData() {
       try {
           const response = await fetch('/api/trading/performance');
           const data = await response.json();
           
           tradeDistChart.data.datasets[0].data = [
               data.winning_trades,
               data.losing_trades
           ];
           tradeDistChart.update();
       } catch (error) {
           console.error('Error loading trade distribution:', error);
       }
   }
   ```

## Database Queries Needed

### Portfolio Value Calculation

```python
# From account summary
account_summary = await ibkr_client.get_account_summary()
portfolio_value = float(account_summary.get('NetLiquidation', {}).get('value', 0))
```

### Daily P&L Calculation

```python
from datetime import datetime, date
from sqlalchemy import func
from ...data.database.models import Trade

today = date.today()
daily_trades = db.query(Trade).filter(
    func.date(Trade.timestamp) == today,
    Trade.status == 'FILLED'
).all()

daily_pnl = sum(
    trade.realized_pnl for trade in daily_trades 
    if trade.realized_pnl is not None
)
```

### Win Rate Calculation

```python
closed_trades = db.query(Trade).filter(
    Trade.status == 'FILLED',
    Trade.realized_pnl.isnot(None)
).all()

winning_trades = [t for t in closed_trades if t.realized_pnl > 0]
win_rate = len(winning_trades) / len(closed_trades) if closed_trades else 0
```

### Active Positions Count

```python
positions = await ibkr_client.get_positions()
active_positions = len([p for p in positions if p.quantity != 0])
```

## Implementation Checklist

- [ ] **Step 1**: Create `GET /api/trading/portfolio/summary` endpoint
- [ ] **Step 2**: Create `GET /api/trading/trades` endpoint with pagination
- [ ] **Step 3**: Create `GET /api/trading/performance` endpoint
- [ ] **Step 4**: Update dashboard JavaScript:
  - [ ] Add `loadPortfolioSummary()` function
  - [ ] Add `loadRecentTrades()` function
  - [ ] Update `refreshPrice()` to use real API
  - [ ] Add auto-refresh interval
  - [ ] Add error handling
- [ ] **Step 5**: Update charts to use real data:
  - [ ] Portfolio performance chart
  - [ ] Trade distribution chart
- [ ] **Step 6**: Test with real IBKR connection
- [ ] **Step 7**: Test with real database data
- [ ] **Step 8**: Add loading states/indicators
- [ ] **Step 9**: Add error messages for failed API calls

## Testing

1. **Start with IBKR disconnected**: Should show errors gracefully
2. **Connect IBKR**: Should populate real account data
3. **With no trades**: Should show zeros/defaults appropriately
4. **With trades**: Should calculate accurate metrics
5. **WebSocket updates**: Should update in real-time

## Notes

- All API calls should handle errors gracefully
- Show loading indicators while fetching data
- Cache data briefly to avoid too many API calls
- Consider using WebSocket for real-time portfolio updates
- Portfolio chart may need historical data storage (separate table or daily snapshots)

