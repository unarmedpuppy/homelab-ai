# Fix for Service Health Monitor Workflow

## Issue
The "Check Root Endpoint" node was showing "Invalid URL" error.

## Root Cause
The workflow was trying to construct URLs using Docker container names (e.g., `http://trading-bot:8000/`), but n8n needs to use the host IP address since services are exposed on host ports.

## Fix Applied
Updated both HTTP Request nodes to use the host IP (`192.168.86.47`) instead of container names:

**Before:**
- `http://{{ $json['service'].split(':')[0] }}:{{ $json['service'].split(':')[1] }}/`
- This would create: `http://trading-bot:8000/` ❌

**After:**
- `http://192.168.86.47:{{ $json['service'].split(':')[1] }}/`
- This creates: `http://192.168.86.47:8000/` ✅

## How to Update in n8n

1. Open the workflow: `https://n8n.server.unarmedpuppy.com/workflow/YwkC1oh0bGCcgPAU`
2. Click on the **"Check Root Endpoint"** node
3. Update the **URL** field to: `http://192.168.86.47:{{ $json['service'].split(':')[1] }}/`
4. Also update **"Check Health Endpoint"** node URL to: `http://192.168.86.47:{{ $json['service'].split(':')[1] }}/health`
5. Save the workflow

## Alternative: Re-import Workflow

The workflow file has been updated in the repository. You can:
1. Delete the current workflow in n8n
2. Re-import from: `~/server/apps/n8n/workflows/service-health-monitor.json`

Or manually update the URLs as described above.

## Service List

The workflow monitors these services:
- `trading-bot:8000` → `http://192.168.86.47:8000`
- `homepage:3000` → `http://192.168.86.47:3000`
- `grafana:3010` → `http://192.168.86.47:3010`
- `plex:32400` → `http://192.168.86.47:32400`
- `immich-server:2283` → `http://192.168.86.47:2283`

Note: Make sure these ports are actually exposed on the host. If any service uses a different port, update the service list accordingly.

