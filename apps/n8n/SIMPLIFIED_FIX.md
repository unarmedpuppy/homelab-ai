# Simplified Fix for Service Health Monitor

## The Problem
The workflow was trying to check `/health` endpoints that don't exist on most services, causing 404 errors.

## The Solution
I've simplified the workflow to **only check the root endpoint** (`/`) which works for all services.

## What Changed
- ❌ Removed "Check Health Endpoint" node (was causing 404 errors)
- ✅ Kept "Check Root Endpoint" node (works for all services)
- ✅ Updated to catch 404 errors as failures (in case service is actually down)

## How to Fix in n8n (Simple Steps)

1. **Open the workflow**: `https://n8n.server.unarmedpuppy.com/workflow/YwkC1oh0bGCcgPAU`

2. **Delete the "Check Health Endpoint" node**:
   - Click on the "Check Health Endpoint" node
   - Press Delete or right-click → Delete
   - This node is causing the 404 errors

3. **Update the connection**:
   - Make sure "Service List" connects directly to "Check Root Endpoint"
   - Delete any connection from "Check Health Endpoint" if it still exists

4. **Update "Check Root Endpoint" node**:
   - Click on "Check Root Endpoint" node
   - URL should be: `http://192.168.86.47:{{ $json['service'].split(':')[1] }}/`
   - Enable "Follow Redirect" option
   - Save

5. **Update "Filter Failures" node**:
   - Click on "Filter Failures" node
   - The condition should check for status codes: `500|502|503|504|404`
   - This will catch both server errors and "not found" errors

6. **Save the workflow**

7. **Test it**: Click "Execute Workflow" to test

## What the Workflow Does Now

1. Checks each service's root endpoint (`http://192.168.86.47:PORT/`)
2. If it gets a 404, 500, 502, 503, or 504 → treats it as a failure
3. Gets service logs
4. Sends event to AI agent webhook

## Services Being Monitored

- `trading-bot:8021` → `http://192.168.86.47:8021/`
- `grafana:3010` → `http://192.168.86.47:3010/`
- `plex:32400` → `http://192.168.86.47:32400/`
- `immich-server:2283` → `http://192.168.86.47:2283/`

All of these should respond with 200 (OK) or 401 (auth required, but service is up) when working correctly.

## Alternative: Re-import the Workflow

If you want to start fresh:
1. Delete the current workflow in n8n
2. Go to Workflows → Import from File
3. Import: `~/server/apps/n8n/workflows/service-health-monitor.json`
4. Configure the webhook URL and credential as before

The updated workflow file is already on your server with all the fixes applied.

