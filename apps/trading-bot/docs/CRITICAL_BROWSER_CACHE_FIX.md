# CRITICAL: Browser Cache Issue - Dashboard Not Updating

## The Problem
You're seeing static data ($100,000, etc.) because **your browser is serving a cached version** of the HTML file. The code changes ARE in the container, but your browser is showing an old cached copy.

## The Solution - FORCE CLEAR BROWSER CACHE

### Method 1: Hard Refresh (Easiest)
- **Mac**: Press `Cmd + Shift + R`
- **Windows/Linux**: Press `Ctrl + Shift + R`
- This forces a reload without using cache

### Method 2: DevTools Cache Bypass
1. Open DevTools (F12)
2. Go to **Network** tab
3. Check the box: **"Disable cache"** (at the top)
4. Keep DevTools open
5. Reload page (F5 or click reload button)

### Method 3: Clear Browser Cache (Nuclear Option)
1. **Chrome/Edge**:
   - Settings → Privacy → Clear browsing data
   - Select "Cached images and files"
   - Clear data

2. **Firefox**:
   - Settings → Privacy → Clear Data
   - Select "Cached Web Content"
   - Clear

3. **Safari**:
   - Develop → Empty Caches
   - (Or Cmd+Option+E)

### Method 4: Incognito/Private Window
Open dashboard in an incognito/private window:
- **Chrome**: `Cmd+Shift+N` (Mac) or `Ctrl+Shift+N` (Windows)
- **Firefox**: `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows)
- Navigate to: `http://192.168.86.47:8021`

## How to Verify It's Working

After clearing cache, you should see:

1. **Blue Debug Banner** at top:
   - Says "Dashboard Debug Mode"
   - Status changes from "Loading..." to "✅ JavaScript is running!"

2. **Console Messages** (F12 → Console tab):
   ```
   === DASHBOARD SCRIPT LOADING ===
   ✅ dashboard-utils.js loaded successfully
   ✅ apiCall function exists
   [Dashboard] Initializing dashboard...
   === [Dashboard] loadPortfolioSummary() called ===
   ```

3. **Network Tab** (F12 → Network → Filter "Fetch/XHR"):
   - Should show API calls to:
     - `/api/trading/portfolio/summary?account_id=1`
     - `/api/trading/trades?limit=10&account_id=1`

4. **Portfolio Cards**:
   - Initially show "Loading..." with spinner
   - Then update to real data (or show $0 if no data)

## Why This Happens

Browsers cache HTML/CSS/JS files to speed up page loads. When we update the code in the container, the browser still has the old version cached. The container has the new code, but your browser doesn't know to fetch it.

## Verify Container Has New Code

```bash
# Check if container has latest code
docker-compose exec bot grep -c "Dashboard Debug Mode" /app/src/ui/templates/dashboard.html

# Should return: 1 (or more)
```

If it returns 0, rebuild:
```bash
docker-compose build bot && docker-compose up -d bot
```

## Still Not Working?

1. **Check Console for Errors** (F12)
   - Any red errors will stop JavaScript execution
   - Fix those first

2. **Verify Static File Loads**:
   - In Network tab, check `/static/js/dashboard-utils.js`
   - Should be 200 status, not 404

3. **Test API Directly**:
   ```bash
   curl http://localhost:8021/api/trading/portfolio/summary?account_id=1
   ```
   Should return JSON, not 404

4. **Check Container Logs**:
   ```bash
   docker-compose logs bot --tail 50
   ```

---

**TL;DR: Do a hard refresh (`Cmd+Shift+R` or `Ctrl+Shift+R`) to clear browser cache!**

