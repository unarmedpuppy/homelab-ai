# Dashboard Static Data Analysis

## Current Static Data Locations

The dashboard (`src/ui/templates/dashboard.html`) has the following hardcoded static data:

### 1. Portfolio Stats (Lines 64, 76, 88, 100)
```html
<!-- Line 64 -->
<p id="portfolio-value">$100,000</p>  <!-- HARDCODED -->

<!-- Line 76 -->
<p id="daily-pnl">+$1,250</p>  <!-- HARDCODED -->

<!-- Line 88 -->
<p id="win-rate">68.5%</p>  <!-- HARDCODED -->

<!-- Line 100 -->
<p id="active-trades">3</p>  <!-- HARDCODED -->
```

### 2. Current Price Display (Line 145)
```html
<p id="current-price">$150.25</p>  <!-- HARDCODED -->
<p id="price-change">+$0.15</p>  <!-- HARDCODED -->
<p id="price-change-pct">+0.10%</p>  <!-- HARDCODED -->
```

### 3. Recent Trades List (Lines 205-224)
```html
<!-- Hardcoded HTML elements with fake trade data -->
<div class="flex justify-between items-center p-3 bg-gray-50 rounded-md">
    <div>
        <p class="font-medium">AAPL</p>  <!-- FAKE -->
        <p class="text-sm text-gray-500">BUY 10 shares</p>  <!-- FAKE -->
    </div>
    <div class="text-right">
        <p class="font-semibold text-green-600">+$125</p>  <!-- FAKE -->
        <p class="text-sm text-gray-500">2m ago</p>  <!-- FAKE -->
    </div>
</div>
```

### 4. Chart Data (Lines 477-480, 508-509)
```javascript
// Portfolio Performance Chart - FAKE DATA
data: {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],  // HARDCODED
    datasets: [{
        data: [95000, 98000, 102000, 105000, 108000, 110000],  // HARDCODED
    }]
}

// Trade Distribution Chart - FAKE DATA
data: {
    datasets: [{
        data: [68, 32],  // HARDCODED win/loss percentages
    }]
}
```

## What Needs to Happen

### Step 1: Create API Endpoints for Dashboard Data

**Missing Endpoints:**
1. `GET /api/trading/portfolio/summary` - Portfolio overview
2. `GET /api/trading/trades?limit=20` - Recent trades list
3. `GET /api/trading/performance` - Win rate and performance stats

### Step 2: Update Dashboard JavaScript

Replace static values with API calls that:
1. Fetch real data on page load
2. Auto-refresh every 30-60 seconds
3. Update charts with real historical data

### Step 3: Use Existing Endpoints

**Already Available:**
- `GET /api/trading/ibkr/account` - Account summary (has NetLiquidation value)
- `GET /api/trading/ibkr/positions` - Current positions
- `GET /api/market-data/quote/{symbol}` - Real-time price data

## Detailed Implementation Plan

See `docs/DASHBOARD_REAL_DATA_INTEGRATION.md` for complete step-by-step guide.

