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

## Notes

- Tunarr needs access to your Plex server to read media libraries
- Since both are on the `my-network` Docker network, Tunarr can access Plex using the container name `plex` or the host IP
- The Plex token can be found in Plex Settings > Network > Show Advanced > Manual Port Configuration (or use a tool to extract it)

