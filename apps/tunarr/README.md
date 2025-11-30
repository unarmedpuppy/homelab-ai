# Tunarr

Tunarr is a live TV streaming server that creates virtual channels from your Plex media library.

## References

- https://tunarr.com/
- https://github.com/chrisbenincasa/tunarr
- https://hub.docker.com/r/chrisbenincasa/tunarr

## Setup

1. Start the container:
   ```bash
   docker-compose up -d
   ```

2. Access the web UI at:
   - Local: http://192.168.86.47:8001
   - Remote: https://tunarr.server.unarmedpuppy.com

3. Configure Plex connection:
   - Go to Settings > Media Sources
   - Add a new Plex server or edit existing one
   - **IMPORTANT**: Use `http://plex:32400` (using Docker network hostname) - NOT the Plex remote access URL
   - Do NOT use `https://192-168-160-7.plex.direct:32400` or similar remote access URLs
   - Enter your Plex token (found in Plex settings)
   - If you see "ECONNREFUSED" errors, check that the Server URL uses `http://plex:32400`

## Configuration

- Port: 8001 (mapped from container port 8000)
- Data directory: `./data` (persists configuration and database)
- Timezone: America/Chicago (matches Plex configuration)
- Network: Connected to `my-network` for communication with Plex
- **GPU Transcoding**: Configured for NVIDIA GPU (GeForce GT 1030)
  - **IMPORTANT**: The GeForce GT 1030 (GP108) does NOT support NVENC hardware encoding. This is a hardware limitation, not a software issue.
  - The GT 1030 only supports NVDEC (hardware decoding), not NVENC (hardware encoding)
  - **You must use "Software" transcoding** in Tunarr: Settings > FFmpeg > Hardware Acceleration > Select "Software"
  - To enable hardware transcoding, you would need to upgrade to a GPU that supports NVENC:
    - Minimum: GeForce GTX 960 or GTX 1050
    - Recommended: GTX 1060 or higher, or any RTX series GPU

## Plex Live TV Tuner Setup

To add Tunarr as a Live TV tuner in Plex:

1. Go to Plex Settings > Live TV & DVR > Set Up
2. When prompted for the HDHomeRun device address, use:
   - **Container hostname (recommended)**: `http://tunarr:8000`
   - **OR host IP**: `http://192.168.86.47:8001`
3. For the XMLTV guide URL, use:
   - **Container hostname**: `http://tunarr:8000/api/xmltv.xml`
   - **OR host IP**: `http://192.168.86.47:8001/api/xmltv.xml`

**Note**: Since both Plex and Tunarr are on the same Docker network (`my-network`), using the container hostname `tunarr:8000` is recommended for better reliability.

### Refreshing Channel Schedules and Names

If channel schedules or names are not showing in Plex:

1. **Manual Guide Refresh**:
   - Go to Plex Settings > Live TV & DVR
   - Click "Refresh Guide" or "Refresh EPG" button
   - Wait a few minutes for the guide to update

2. **Verify XMLTV URL**:
   - In Plex Settings > Live TV & DVR > DVR
   - Check that the XMLTV/EPG URL is set to: `http://tunarr:8000/api/xmltv.xml`
   - If using host IP, use: `http://192.168.86.47:8001/api/xmltv.xml`

3. **Rescan Channels** (if needed):
   - In Plex Settings > Live TV & DVR > DVR
   - Click "Scan for Channels" to detect all Tunarr channels

4. **Check Scheduled Tasks**:
   - Go to Plex Settings > Scheduled Tasks
   - Ensure "Refresh Guide Data" is enabled and has a sufficient time window
   - The guide typically refreshes automatically, but you can trigger it manually

## Troubleshooting

### "ECONNREFUSED" or Connection Errors
- **Problem**: Tunarr can't connect to Plex
- **Solution**: 
  1. Go to Tunarr Settings > Media Sources
  2. Edit your Plex server configuration
  3. Change Server URL to: `http://plex:32400` (must use container hostname, not remote access URL)
  4. Save and test the connection

### Software Transcoding Not Working
- Ensure Hardware Acceleration is set to "Software" in Settings > FFmpeg
- Check that FFmpeg path is correct (should be `/usr/local/bin/ffmpeg` in Docker)
- Verify Plex connection is working first (see above)

## Notes

- Tunarr needs access to your Plex server to read media libraries
- Since both are on the `my-network` Docker network, Tunarr must use `http://plex:32400` (container hostname)
- Do NOT use Plex remote access URLs (`plex.direct`) - these won't work from within Docker network
- The Plex token can be found in Plex Settings > Network > Show Advanced > Manual Port Configuration (or use a tool to extract it)
- If Plex can't discover the tuner automatically, manually enter the device address using the container hostname format

