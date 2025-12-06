# NZBGet Connection Issue - Fixed ✅

## Problem

Radarr and Sonarr were showing "Unable to communicate with NZBGet. Connection refused (media-download-gluetun:6789)" errors repeatedly.

## Root Cause

The issue occurs because:

1. **NZBGet shares network namespace with gluetun**: NZBGet uses `network_mode: "service:gluetun"`, meaning it shares gluetun's network stack.

2. **When gluetun restarts** (which happens during VPN reconnections, server reboots, or gluetun updates), NZBGet's network namespace disappears, causing it to stop.

3. **Race condition on restart**: The original `depends_on: gluetun` only ensures gluetun starts **first**, but doesn't wait for gluetun to be **healthy**. If NZBGet starts before gluetun's VPN connection is fully established, it fails to connect and exits.

4. **Restart loop**: When NZBGet exits, Docker tries to restart it (`restart: unless-stopped`), but if gluetun is still initializing, NZBGet fails again, creating a restart loop until gluetun becomes healthy.

## Solution

Updated `docker-compose.yml` to use healthcheck conditions:

```yaml
depends_on:
  gluetun:
    condition: service_healthy  # Wait for gluetun to be healthy before starting
```

This ensures:
- ✅ NZBGet waits for gluetun to be **healthy** (VPN connected, ports ready) before starting
- ✅ Prevents race conditions during gluetun restarts
- ✅ Reduces connection refused errors

## Changes Made

1. **Updated NZBGet dependency**:
   - Changed from: `depends_on: - gluetun`
   - Changed to: `depends_on: gluetun: condition: service_healthy`

2. **Updated qBittorrent dependency** (same issue):
   - Changed from: `depends_on: - gluetun`
   - Changed to: `depends_on: gluetun: condition: service_healthy`

## Why This Keeps Happening

This issue recurs because:

1. **VPN reconnections**: Gluetun may restart when:
   - VPN server disconnects/reconnects
   - Network changes occur
   - Gluetun updates are applied
   - Server reboots

2. **Previous fix was incomplete**: The original `depends_on` only handled initial startup, not restart scenarios.

3. **No healthcheck wait**: Without waiting for gluetun to be healthy, dependent services start too early.

## Verification

To verify the fix is working:

```bash
# Check container status
cd ~/server/apps/media-download
docker-compose ps gluetun nzbget

# Check gluetun health
docker inspect media-download-gluetun --format '{{.State.Health.Status}}'
# Should show: healthy

# Test NZBGet connection from Sonarr/Radarr network
docker exec media-download-sonarr curl -s -u nzbget:nzbget \
  'http://media-download-gluetun:6789/jsonrpc?version=1.1&method=status&id=1'
```

## Prevention

The fix prevents future occurrences by:
- ✅ Ensuring gluetun is healthy before NZBGet starts
- ✅ Handling restart scenarios properly
- ✅ Reducing race conditions

## Manual Recovery

If you still see connection errors:

1. **Restart gluetun and NZBGet**:
   ```bash
   cd ~/server/apps/media-download
   docker-compose restart gluetun
   # Wait for gluetun to be healthy (check with docker inspect)
   docker-compose restart nzbget
   ```

2. **Or restart everything**:
   ```bash
   cd ~/server/apps/media-download
   docker-compose restart gluetun nzbget
   ```

3. **Check logs**:
   ```bash
   docker logs media-download-gluetun
   docker logs media-download-nzbget
   ```

## Related Files

- `docker-compose.yml` - Updated with healthcheck conditions
- `check_and_fix_gluetun_connection.py` - Diagnostic script
- `GLUETUN_SETUP_COMPLETE.md` - Original setup documentation

