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
   - Add a new Plex server
   - Server URL: `http://plex:32400` (using Docker network hostname)
   - Or use: `http://192.168.86.47:32400` (using host IP)
   - Enter your Plex token (found in Plex settings)

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

## Notes

- Tunarr needs access to your Plex server to read media libraries
- Since both are on the `my-network` Docker network, Tunarr can access Plex using the container name `plex` or the host IP
- The Plex token can be found in Plex Settings > Network > Show Advanced > Manual Port Configuration (or use a tool to extract it)
- If Plex can't discover the tuner automatically, manually enter the device address using the container hostname format

