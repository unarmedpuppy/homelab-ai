# Dashboard Actual Status

**Current Issue**: Dashboard shows stale static data. API endpoints are not being registered in container.

## Root Cause Identified

The `/api/trading/portfolio/summary` endpoint exists in the source code but is NOT registered in the running container. When I checked the router in the container, these routes exist:

- `/ibkr/status` ✅
- `/ibkr/connect` ✅
- `/ibkr/disconnect` ✅
- `/execute` ✅
- `/status` ✅
- `/portfolio/summary` ❌ **MISSING**

## What Was Actually Done

### ✅ Code Changes Made:
1. **Signal Generation Endpoint** (`POST /api/trading/signal`) - ✅ Created
2. **Dashboard UI Updates** - ✅ Enhanced displaySignal() function
3. **Loading States** - ✅ Added to HTML
4. **API Integration** - ✅ JavaScript calls API endpoints
5. **Debug Logging** - ✅ Added console logging

### ❌ What's NOT Working:
1. **Container Has Old Code** - Routes added to source not in container
2. **API Endpoints Missing** - `/portfolio/summary`, `/trades`, `/performance` not registered
3. **Browser Cache** - May be serving old HTML/JS

## Immediate Fix Required

### Step 1: Rebuild Container (Not Just Restart)
```bash
cd /Users/joshuajenquist/repos/personal/home-server/apps/trading-bot
docker-compose build --no-cache bot
docker-compose up -d bot
```

### Step 2: Verify Routes Are Registered
```bash
docker-compose exec bot python -c "from src.api.routes import trading; print([r.path for r in trading.router.routes if hasattr(r, 'path')])"
```

Should include:
- `/portfolio/summary`
- `/trades`
- `/performance`

### Step 3: Clear Browser Cache
- Hard refresh: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R`
- Or: DevTools → Network → Check "Disable cache"

### Step 4: Test API Endpoints
```bash
curl http://localhost:8021/api/trading/portfolio/summary?account_id=1
curl http://localhost:8021/api/trading/trades?limit=5&account_id=1
```

## Why This Happened

The container was **restarted** but not **rebuilt**. Restart just restarts the process, it doesn't pick up code changes. Code changes require:
1. Rebuilding the Docker image
2. Starting new container with new image

## Expected Behavior After Fix

1. **API endpoints work** - No more 404 errors
2. **Dashboard shows "Loading..."** - Then updates with real data
3. **Browser console shows** - `[Dashboard]` debug messages
4. **Network tab shows** - Successful API calls (200 status)

## Verification

After rebuilding, verify:
```bash
# Should return portfolio data, not 404
curl http://localhost:8021/api/trading/portfolio/summary?account_id=1

# Should return trades, not 404
curl http://localhost:8021/api/trading/trades?limit=5&account_id=1
```

If still 404, check:
1. Build completed successfully
2. Container restarted with new image
3. Routes actually registered (check route list)

---

**TL;DR**: Container needs to be **rebuilt**, not just restarted. Code changes exist but aren't in the running container.

