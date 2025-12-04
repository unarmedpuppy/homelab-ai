# Gluetun & NZBGet Connection - Setup Complete ✅

## What Was Done

1. **Started Containers**
   - `media-download-gluetun` - VPN gateway (running)
   - `media-download-nzbget` - Usenet download client (running)

2. **Verified Configuration**
   - Sonarr and Radarr are configured to connect via `media-download-gluetun:6789`
   - NZBGet is accessible through gluetun's port mapping

## Container Status

Both containers are now running:
- **gluetun**: Up and healthy
- **nzbget**: Up and running

## Connection Details

- **Sonarr → NZBGet**: `http://media-download-gluetun:6789`
- **Radarr → NZBGet**: `http://media-download-gluetun:6789`
- **NZBGet Credentials**: `nzbget:nzbget`

## Auto-Start Configuration

Containers have `restart: unless-stopped` in docker-compose.yml, so they will:
- ✅ Auto-start when Docker starts
- ✅ Restart if they crash
- ⚠️ Will NOT auto-start after server reboot unless Docker is enabled

### To Ensure Auto-Start on Boot

If containers don't start after server reboot, ensure Docker is enabled:

```bash
sudo systemctl enable docker
sudo systemctl start docker
```

Then containers will auto-start via `restart: unless-stopped`.

## Verification

To verify everything is working:

1. **Check Sonarr**: http://192.168.86.47:8989
   - Go to Settings → Download Clients
   - NZBGet should show "Connected" status

2. **Check Radarr**: http://192.168.86.47:7878
   - Go to Settings → Download Clients
   - NZBGet should show "Connected" status

3. **Test NZBGet directly**:
   ```bash
   curl -u nzbget:nzbget "http://192.168.86.47:6789/jsonrpc?version=1.1&method=status&id=1"
   ```

## Troubleshooting

If connection issues persist:

1. **Check container logs**:
   ```bash
   docker logs media-download-gluetun
   docker logs media-download-nzbget
   ```

2. **Restart containers**:
   ```bash
   cd ~/server/apps/media-download
   docker-compose restart gluetun nzbget
   ```

3. **Run diagnostic script** (from local machine):
   ```bash
   cd apps/media-download
   python3 check_and_fix_gluetun_connection.py
   ```

## Quick Commands

**Start containers**:
```bash
cd ~/server/apps/media-download
docker-compose up -d gluetun nzbget
```

**Check status**:
```bash
docker-compose ps gluetun nzbget
```

**View logs**:
```bash
docker logs -f media-download-gluetun
docker logs -f media-download-nzbget
```

