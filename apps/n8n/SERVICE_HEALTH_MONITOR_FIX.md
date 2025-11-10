# Service Health Monitor - Final Fix

## Issues Fixed

1. ✅ **Invalid URL error** - Changed from container names to host IP
2. ✅ **Wrong port for trading-bot** - Updated from 8000 to 8021
3. ✅ **Homepage removed** - Homepage doesn't have a `/health` endpoint (returns 404)

## Current Service List

The workflow now monitors:
- `trading-bot:8021` → `http://192.168.86.47:8021/health` ✅
- `grafana:3010` → `http://192.168.86.47:3010/api/health` (if available)
- `plex:32400` → `http://192.168.86.47:32400/` (root endpoint)
- `immich-server:2283` → `http://192.168.86.47:2283/api/server-info/ping` (if available)

## How to Update in n8n

1. Open the workflow: `https://n8n.server.unarmedpuppy.com/workflow/YwkC1oh0bGCcgPAU`

2. **Update Service List node**:
   - Click "Service List" node
   - Remove `homepage:3000` from the list
   - Update `trading-bot:8000` to `trading-bot:8021`
   - Save

3. **Update Check Health Endpoint node**:
   - URL: `http://192.168.86.47:{{ $json['service'].split(':')[1] }}/health`
   - Save

4. **Update Check Root Endpoint node**:
   - URL: `http://192.168.86.47:{{ $json['service'].split(':')[1] }}/`
   - Enable "Follow Redirect" option
   - Save

5. **Test the workflow** by clicking "Execute Workflow"

## Note on Health Endpoints

Not all services have `/health` endpoints:
- ✅ **trading-bot**: Has `/health` endpoint
- ❌ **homepage**: No health endpoint (removed from monitoring)
- ❓ **grafana**: May have `/api/health` (check if needed)
- ❓ **plex**: No standard health endpoint (check root)
- ❓ **immich**: Has `/api/server-info/ping` (different endpoint)

The workflow will check both health and root endpoints, so it should catch failures even if a service doesn't have a health endpoint.

