# Agent Task 7: Connect Charts to Real Data

## Status: ✅ **COMPLETE**

**Priority**: 🟡 HIGH  
**Estimated Time**: 3-4 hours  
**Dependencies**: Agent 2 (Performance Metrics API), Agent 1 (Trade History API)

---

## Objective

Update the Chart.js charts in the main dashboard (`src/ui/templates/dashboard.html`) to display real data instead of hardcoded arrays. This includes the portfolio performance chart and trade distribution chart.

## Task Details

### Files to Modify

**Primary File**: `src/ui/templates/dashboard.html`  
**Charts**: 
1. Portfolio Performance Chart (line chart)
2. Trade Distribution Chart (pie/doughnut chart)

### Charts to Update

1. **Portfolio Performance Chart**:
   - Currently uses hardcoded data array
   - Needs historical portfolio value data
   - Options: Query trade history and calculate equity curve, or create new API endpoint

2. **Trade Distribution Chart**:
   - Currently shows hardcoded win/loss distribution
   - Use data from Performance Metrics API (`/api/trading/performance`)
   - Show: winning trades vs losing trades

### Implementation Steps

1. **Update Trade Distribution Chart**:

   ```javascript
   async function loadTradeDistributionData() {
       try {
           const response = await fetch('/api/trading/performance');
           if (!response.ok) {
               throw new Error(`HTTP error! status: ${response.status}`);
           }
           const data = await response.json();
           
           // Update chart
           tradeDistChart.data.datasets[0].data = [
               data.winning_trades || 0,
               data.losing_trades || 0
           ];
           tradeDistChart.update();
           
           return data;
       } catch (error) {
           console.error('Error loading trade distribution:', error);
           return null;
       }
   }
   ```

2. **Update Portfolio Performance Chart**:

   **Option A: Use Trade History** (Recommended for MVP):
   - Query `/api/trading/trades` for all trades
   - Calculate portfolio value over time from trades
   - Build equity curve: Starting balance + cumulative P&L
   - Create time-series data for chart

   **Option B: Create Portfolio History API** (Better long-term):
   - Create new endpoint: `GET /api/trading/portfolio/history?days=30`
   - Store daily portfolio snapshots in database
   - Query and return time-series data
   - **Note**: This requires database schema changes and daily snapshot job

   **For this task, implement Option A** (calculate from trades):

   ```javascript
   async function loadPortfolioChartData(days = 30) {
       try {
           // Get all trades (or last N days)
           const response = await fetch(`/api/trading/trades?limit=1000`);
           if (!response.ok) {
               throw new Error(`HTTP error! status: ${response.status}`);
           }
           const tradesData = await response.json();
           
           // Calculate equity curve
           const equityCurve = calculateEquityCurve(tradesData.trades);
           
           // Update chart
           portfolioChart.data.labels = equityCurve.dates;
           portfolioChart.data.datasets[0].data = equityCurve.values;
           portfolioChart.update();
           
           return equityCurve;
       } catch (error) {
           console.error('Error loading portfolio chart data:', error);
           return null;
       }
   }
   
   function calculateEquityCurve(trades) {
       // Sort trades by timestamp
       const sortedTrades = trades.sort((a, b) => 
           new Date(a.executed_at) - new Date(b.executed_at)
       );
       
       // Starting balance (get from portfolio summary or use default)
       let balance = 100000; // Default, should fetch from API
       
       const dates = [];
       const values = [];
       
       // For each trade, calculate portfolio value
       // This is simplified - in reality, need to track positions
       sortedTrades.forEach(trade => {
           // Calculate impact on portfolio
           // Simplified: just track cash changes for now
           // TODO: More accurate calculation needed
           
           dates.push(new Date(trade.executed_at).toLocaleDateString());
           values.push(balance); // Update this with actual calculation
       });
       
       return { dates, values };
   }
   ```

3. **Call Chart Loading Functions**:
   - Call `loadTradeDistributionData()` on page load
   - Call `loadPortfolioChartData()` on page load
   - Optionally refresh charts periodically (every 5 minutes)

4. **Handle Edge Cases**:
   - No trades: Show empty/zero chart
   - Insufficient data: Show message or placeholder
   - API errors: Show error state or use cached data

### UI Elements to Update

Find Chart.js initialization in `dashboard.html`:

```javascript
// Portfolio Performance Chart
const portfolioCtx = document.getElementById('portfolioChart');
const portfolioChart = new Chart(portfolioCtx, {
    type: 'line',
    data: {
        labels: [...], // Replace with real data
        datasets: [{
            data: [...] // Replace with real data
        }]
    }
});

// Trade Distribution Chart
const tradeDistCtx = document.getElementById('tradeDistChart');
const tradeDistChart = new Chart(tradeDistCtx, {
    type: 'doughnut',
    data: {
        datasets: [{
            data: [...] // Replace with real data
        }]
    }
});
```

### Reference Documentation

- **Implementation Guide**: `docs/DASHBOARD_REAL_DATA_INTEGRATION.md` (Step 4: Update Charts section)
- **Static Data Analysis**: `docs/DASHBOARD_STATIC_DATA_ANALYSIS.md` (Chart Data section)
- **API Endpoints**: 
  - `/api/trading/performance` (Agent 2)
  - `/api/trading/trades` (Agent 1)
- **Chart.js Docs**: https://www.chartjs.org/docs/latest/
- **Project TODO**: `docs/PROJECT_TODO.md` (UI Section, Tasks ui-8 and ui-9)

### Success Criteria

✅ Trade Distribution Chart shows real win/loss data  
✅ Portfolio Performance Chart shows real equity curve  
✅ Charts update on page load  
✅ Charts handle empty data gracefully  
✅ Charts handle API errors gracefully  
✅ Data is formatted correctly for Chart.js  
✅ Chart labels and tooltips are informative  
✅ No console errors  
✅ Code follows existing patterns

---

## Related Tasks

- **Agent 1**: Trade History API (needed for portfolio chart)
- **Agent 2**: Performance Metrics API (needed for trade distribution chart)
- **Agent 3-6**: Other UI integrations (parallel, no overlap)

## Notes

- **Equity Curve Calculation**: This is simplified. For accurate equity curve, need to:
  - Track positions over time
  - Calculate portfolio value at each point (cash + position value)
  - Consider open positions' unrealized P&L
- **Performance**: Limit trades query (e.g., last 1000 trades) to avoid slow queries
- **Future Enhancement**: Consider creating dedicated portfolio history table and API
- **Chart Refresh**: Don't refresh too frequently (charts are expensive to render)
- **Data Format**: Ensure dates are in correct format for Chart.js labels

---

**Ready to start?** Wait for Agents 1 and 2 to complete their API endpoints, or coordinate to implement in parallel (you can use the API specs to mock responses). Review the Chart.js initialization in `dashboard.html` and implement the data loading functions to populate the charts with real data.

