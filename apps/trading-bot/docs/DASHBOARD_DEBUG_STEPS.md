# Dashboard Debugging Steps

**Issue**: Dashboard shows stale static data, no real data loading

## Immediate Actions Required

### 1. Restart Docker Container
The dashboard HTML file has been updated but the container may be serving a cached version.

```bash
cd /Users/joshuajenquist/repos/personal/home-server/apps/trading-bot
docker-compose restart bot
```

### 2. Clear Browser Cache
- Hard refresh: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows/Linux)
- Or open DevTools (F12) → Network tab → Check "Disable cache"
- Or clear browser cache completely

### 3. Check Browser Console
Open browser DevTools (F12) and check Console tab for:
- JavaScript errors
- `[Dashboard]` log messages (I added debug logging)
- API call errors
- Network request failures

### 4. Verify API Endpoints Work
Test the endpoints directly:

```bash
# Portfolio Summary
curl http://localhost:8021/api/trading/portfolio/summary?account_id=1

# Trade History  
curl http://localhost:8021/api/trading/trades?limit=5&account_id=1

# Performance Metrics
curl http://localhost:8021/api/trading/performance?account_id=1

# IBKR Status
curl http://localhost:8021/api/trading/ibkr/status
```

### 5. Check Network Tab
In browser DevTools → Network tab:
- Filter by "Fetch/XHR"
- Reload page
- Check if API calls are being made
- Check response status codes
- Check response data

## What Should Happen

When the page loads, you should see:

1. **Loading States**: Portfolio cards show "Loading..." with spinner
2. **API Calls**: Network tab shows calls to:
   - `/api/trading/portfolio/summary?account_id=1`
   - `/api/trading/trades?limit=10&account_id=1`
   - `/api/trading/performance?account_id=1`
   - `/api/market-data/quote/AAPL`
3. **Data Updates**: After API calls complete, cards should show:
   - Real portfolio value (not $100,000)
   - Real P&L (not "--")
   - Real win rate (not 68.5%)
   - Real active trades count
4. **Console Logs**: Should see `[Dashboard]` debug messages

## If Still Not Working

### Check JavaScript Execution
In browser console, type:
```javascript
dashboard
```
Should return the TradingDashboard object.

### Check API Call Function
In browser console, type:
```javascript
apiCall('/api/trading/portfolio/summary?account_id=1')
```
Should return a Promise that resolves with data.

### Force Data Refresh
In browser console:
```javascript
dashboard.loadPortfolioSummary()
dashboard.loadRecentTrades()
```

## Common Issues

1. **Container not restarted**: Changes won't show until container restarts
2. **Browser cache**: Old HTML/JS being served from cache
3. **API errors**: Endpoints returning 404 or 500 errors
4. **CORS issues**: API calls blocked by browser
5. **JavaScript errors**: Script failing before API calls execute

## Expected Console Output

You should see logs like:
```
[Dashboard] Initializing dashboard...
[Dashboard] Loading portfolio summary...
[Dashboard] Portfolio summary API response: {ok: true, data: {...}}
[Dashboard] Portfolio data: {portfolio_value: ..., daily_pnl: ..., ...}
[Dashboard] Portfolio summary updated successfully
[Dashboard] Dashboard initialization complete
```

If you don't see these, JavaScript isn't running or there's an error preventing execution.

