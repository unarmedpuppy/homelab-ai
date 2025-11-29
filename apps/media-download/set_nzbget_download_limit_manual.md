# Setting NZBGet Download Limit to 3

## Issue
NZBGet version 25.4 doesn't support the `MaxActiveDownloads` config option directly in the config file.

## Solution: Use Web UI

The limit must be set via the NZBGet web interface:

1. **Open NZBGet Web UI:**
   - Navigate to: http://192.168.86.47:6789
   - Login with:
     - Username: `nzbget`
     - Password: `nzbget`

2. **Navigate to Settings:**
   - Click the "Settings" tab at the top
   - In the left sidebar, click "Queue" under "Download Queue"

3. **Set Max Active Downloads:**
   - Find the "Max Active Downloads" option
   - Change the value to `3`
   - Scroll to the bottom and click "Save all changes"

4. **Verify:**
   - The setting should now be saved
   - NZBGet will limit parallel downloads to 3
   - Sonarr and Radarr can queue unlimited items, but only 3 will download at once

## Alternative: Limit via Server Connections

If the web UI option doesn't work, you can limit by reducing server connections:

- Edit `/config/nzbget.conf` in the NZBGet container
- Reduce `Server1.Connections`, `Server2.Connections`, etc. to lower values
- Total connections across all servers will effectively limit parallel downloads

However, the web UI method is preferred as it's the official way to set this limit.

