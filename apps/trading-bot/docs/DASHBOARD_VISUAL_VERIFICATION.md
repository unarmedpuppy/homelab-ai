# Dashboard Visual Verification Guide

**Issue**: Dashboard appears to show stale static data instead of real data

## What You Should See NOW

After restarting the container and refreshing the browser:

### 1. **Debug Banner** (Blue banner at top)
- Should appear briefly when page loads
- Indicates JavaScript is working
- Will auto-hide after 5 seconds

### 2. **Portfolio Stats Cards** (Top 4 cards)
- Should show "Loading..." with spinning icon initially
- Should update to real values after 1-2 seconds:
  - Portfolio Value: Real number from IBKR (not "$100,000")
  - Daily P&L: Real P&L with green/red color (not "--")
  - Win Rate: Real percentage from closed trades (not "68.5%")
  - Active Trades: Real count from IBKR positions (not "3")

### 3. **Recent Trades**
- Should show "Loading trades..." initially
- Should update to real trade list or "No trades yet" message

### 4. **Price Display**
- Current price should load for selected symbol
- Should not show hardcoded values

## How to Verify Changes Are Active

### Step 1: Restart Container
```bash
cd /Users/joshuajenquist/repos/personal/home-server/apps/trading-bot
docker-compose restart bot
```

Wait 10 seconds for container to fully restart.

### Step 2: Hard Refresh Browser
- **Mac**: `Cmd + Shift + R`
- **Windows/Linux**: `Ctrl + Shift + R`
- Or: Open DevTools (F12) → Right-click refresh button → "Empty Cache and Hard Reload"

### Step 3: Check Browser Console
1. Open DevTools (F12)
2. Go to Console tab
3. Look for these messages:
   ```
   [Dashboard] Initializing dashboard...
   [Dashboard] Loading portfolio summary...
   [Dashboard] Portfolio summary API response: {ok: true, data: {...}}
   ```

### Step 4: Check Network Tab
1. Open DevTools (F12)
2. Go to Network tab
3. Filter by "Fetch/XHR"
4. Reload page
5. Should see API calls:
   - `GET /api/trading/portfolio/summary?account_id=1`
   - `GET /api/trading/trades?limit=10&account_id=1`
   - `GET /api/trading/performance?account_id=1`

### Step 5: Verify API Endpoints Work
Test endpoints directly:
```bash
curl http://localhost:8021/api/trading/portfolio/summary?account_id=1
curl http://localhost:8021/api/trading/trades?limit=5&account_id=1
```

## Expected Behavior

### If Everything Works:
- Cards show "Loading..." for 1-2 seconds
- Cards update with real data
- No errors in console
- Network tab shows successful API calls (200 status)

### If API Calls Fail:
- Cards show "Loading..." forever
- Console shows error messages
- Network tab shows failed requests (404, 500, etc.)
- Error messages appear in UI

## Troubleshooting

### Still See Old Data?
1. **Container not restarted**: Code changes require container restart
2. **Browser cache**: Hard refresh required (Cmd+Shift+R)
3. **Service not running**: Check `docker-compose ps`
4. **API errors**: Check container logs `docker-compose logs bot`

### No "Loading..." Messages?
- JavaScript not executing
- Check console for JavaScript errors
- Verify `dashboard-utils.js` loads (Network tab)

### "Loading..." Forever?
- API calls are failing
- Check Network tab for failed requests
- Check console for error messages
- Check container logs for API errors

## Quick Test

In browser console, run:
```javascript
// Should return TradingDashboard object
dashboard

// Should trigger API call and update UI
dashboard.loadPortfolioSummary()

// Should show API response
fetch('/api/trading/portfolio/summary?account_id=1').then(r => r.json()).then(console.log)
```

---

**If after all this you still see stale data, please share:**
1. Browser console errors (if any)
2. Network tab showing API calls (screenshot or list)
3. What the cards actually display
4. Container logs: `docker-compose logs bot --tail 50`

