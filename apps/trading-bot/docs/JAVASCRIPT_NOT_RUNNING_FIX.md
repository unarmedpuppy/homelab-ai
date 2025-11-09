# JavaScript Not Running - Fix Guide

## Issue
Dashboard shows static data ($100,000, etc.) instead of "Loading..." states, and Network tab shows NO API calls.

## Root Cause
JavaScript is either:
1. Not loading at all
2. Failing silently before API calls
3. Browser is serving cached version

## Debugging Steps

### 1. Open Browser Console (F12)
Look for:
- `=== DASHBOARD SCRIPT LOADING ===` - Should appear immediately
- `✅ apiCall function exists` - Should confirm utilities loaded
- `[Dashboard] Initializing dashboard...` - Should appear after DOM loads
- Any red error messages

### 2. Check Network Tab
Filter by "Fetch/XHR" and reload page. Should see:
- `GET /api/trading/portfolio/summary?account_id=1`
- `GET /api/trading/trades?limit=10&account_id=1`
- `GET /api/trading/performance?account_id=1`

### 3. Force Hard Refresh
- **Mac**: `Cmd + Shift + R`
- **Windows/Linux**: `Ctrl + Shift + R`
- Or: DevTools → Network tab → Check "Disable cache" → Reload

### 4. Check if Debug Banner Appears
If you see the blue "Dashboard Debug Mode" banner, JavaScript IS loading.
- If banner says "JavaScript is running!" ✅ - JS is working
- If banner says "Loading..." ❌ - JS not executing

### 5. Manual Test in Console
Open browser console (F12) and run:
```javascript
// Check if dashboard object exists
dashboard

// Check if apiCall exists
typeof apiCall

// Manually trigger API call
apiCall('/api/trading/portfolio/summary?account_id=1').then(console.log)

// Manually trigger dashboard load
dashboard.loadPortfolioSummary()
```

## Expected Console Output
If everything works, you should see:
```
=== DASHBOARD SCRIPT LOADING ===
Document ready state: loading
✅ apiCall function exists
[Dashboard] DOM loaded, initializing...
[Dashboard] Initializing dashboard...
✅ JavaScript is running!
=== [Dashboard] loadPortfolioSummary() called ===
[Dashboard] Calling API: /api/trading/portfolio/summary?account_id=1
=== [Dashboard] API Response Received ===
```

## If Still Not Working

### Check Static Files Loading
In Network tab, verify these load with 200 status:
- `/static/js/dashboard-utils.js`
- Chart.js (from CDN)
- Tailwind CSS (from CDN)

### Check for JavaScript Errors
Any red errors in console will stop execution. Fix those first.

### Verify Container Has Latest Code
```bash
docker-compose restart bot
# Or rebuild if code changed:
docker-compose build bot && docker-compose up -d bot
```

### Test API Endpoints Directly
```bash
curl http://localhost:8021/api/trading/portfolio/summary?account_id=1
```
Should return JSON, not 404.

---

**Most Common Fix**: Hard refresh browser cache (`Cmd+Shift+R` or `Ctrl+Shift+R`)

