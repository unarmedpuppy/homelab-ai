# SoulSync

Automated Music Discovery and Collection Manager

SoulSync is an automated music discovery and collection manager that integrates with Spotify, Tidal, Soulseek (via slskd), and media servers like Plex, Jellyfin, or Navidrome.

## Features

- **Automated Music Discovery**: Discover new music based on your watchlist
- **Soulseek Integration**: Search and download music via slskd API
- **Media Server Integration**: Works with Plex, Jellyfin, or Navidrome
- **Automatic Organization**: Organizes downloaded music with metadata enhancement
- **Lyrics Support**: Automatic LRC file generation for synchronized lyrics
- **Beatport Integration**: Discover dance music charts and DJ sets
- **Discover Page**: Personalized playlists based on your watchlist

## Prerequisites

### Required Services

1. **slskd** (Soulseek daemon) - Running in Docker behind VPN
   
   slskd is configured in the `media-download` stack and runs behind Gluetun VPN (just like qBittorrent and NZBGet) for security and privacy.

   **Setup:**
   - slskd is already configured in `apps/media-download/docker-compose.yml`
   - All P2P traffic routes through Gluetun VPN with kill switch enabled
   - DNS leak protection is enabled (all DNS queries go through VPN)
   - Web UI accessible at: `http://192.168.86.47:5030` (routed through VPN)
   - **Important**: Must share files in slskd to avoid bans
   - Configure shares at: `http://192.168.86.47:5030/shares`

   **Initial Configuration:**
   1. Verify slskd Docker image exists or build from source if needed:
      - Check: `docker pull slskd/slskd:latest`
      - If image doesn't exist, you may need to build from source or use an alternative image
      - Source: https://github.com/slskd/slskd
   2. Start the media-download stack: `cd apps/media-download && docker compose up -d`
   3. Wait for slskd to start (it depends on Gluetun being healthy)
   4. Access slskd web UI at `http://192.168.86.47:5030`
   5. Set up your Soulseek username/password
   6. Configure download and share directories
   7. Generate an API key in slskd settings (needed for SoulSync)
   8. **CRITICAL**: Configure file sharing - go to Shares section and add your music library

### Optional Services

- **Plex Media Server** (port 32400) - For media library integration
- **Jellyfin** (port 8096) - Alternative media server
- **Navidrome** (port 4533) - Alternative media server

## Setup

### 1. Initial Configuration

1. Copy the environment template:
   ```bash
   cp env.template .env
   ```

2. Edit `.env` and configure paths:
   - `DOWNLOAD_PATH`: Temporary download location
   - `TRANSFER_PATH`: Final music library location (should match your media server's music path)

3. Create data directory:
   ```bash
   mkdir -p data
   ```

### 2. Start SoulSync

```bash
docker compose up -d
```

Access the web UI at: `http://192.168.86.47:8008` or `https://soulsync.server.unarmedpuppy.com`

### 3. Configure API Credentials

After first startup, configure API credentials through the SoulSync web UI:

#### Spotify API Setup

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Click **"Create App"**
3. Fill out the form:
   - **App Name**: `SoulSync` (or whatever you want)
   - **App Description**: `Music library sync`
   - **Website**: `http://localhost` (or leave blank)
   - **Redirect URI**: `http://127.0.0.1:8888/callback`
4. Click **"Save"**
5. Click **"Settings"** on your new app
6. Copy the **Client ID** and **Client Secret**
7. Enter these in SoulSync Settings → Spotify

#### Tidal API Setup (Optional)

1. Go to [Tidal Developer Dashboard](https://developer.tidal.com/)
2. Click **"Create New App"**
3. Fill out the form:
   - **App Name**: `SoulSync`
   - **Description**: `Music library sync`
   - **Redirect URI**: `http://127.0.0.1:8889/callback`
   - **Scopes**: Select `user.read` and `playlists.read`
4. Click **"Save"**
5. Copy the **Client ID** and **Client Secret**
6. Enter these in SoulSync Settings → Tidal

#### Plex Token Setup

**Easy Method:**

1. Open Plex in your browser and sign in
2. Go to any movie/show page
3. Click **"Get Info"** or three dots menu → **"View XML"**
4. In the URL bar, copy everything after `X-Plex-Token=`
   - Example: `http://192.168.1.100:32400/library/metadata/123?X-Plex-Token=YOUR_TOKEN_HERE`
5. Your Plex server URL is typically `http://192.168.86.47:32400`

**Alternative Method:**

1. Go to plex.tv/claim while logged in
2. Your 4-minute claim token appears - this isn't what you need
3. Instead, right-click → Inspect → Network tab → Reload page
4. Look for requests with `X-Plex-Token` header and copy that value

#### Navidrome Setup

1. Open your Navidrome web interface and sign in
2. Go to **Settings** → **Users**
3. Click on your user account
4. Under **Token**, click **"Generate API Token"**
5. Copy the generated token
6. Your Navidrome server URL is typically `http://192.168.86.47:4533`

#### Jellyfin Setup

1. Open your Jellyfin web interface and sign in
2. Go to **Settings** → **API Keys**
3. Click **"+"** to create a new API key
4. Give it a name like "SoulSync"
5. Copy the generated API key
6. Your Jellyfin server URL is typically `http://192.168.86.47:8096`

### 4. Configure slskd Connection

In SoulSync Settings → Soulseek:
- **slskd URL**: `http://192.168.86.47:5030` (slskd is exposed through Gluetun VPN)
  - Alternative: `http://media-download-slskd:5030` (using container name, requires both on same network)
- **API Key**: Your slskd API key (generate in slskd web UI → Settings → API)
- **Download Path**: Should match slskd's download path in media-download stack
- **Transfer Path**: Should match your `TRANSFER_PATH` from `.env`

**Important**: 
- Make sure slskd is configured to share files, otherwise you'll get banned
- All slskd P2P traffic goes through Gluetun VPN with kill switch and DNS leak protection
- slskd must be started before SoulSync (it's in the media-download stack)

## Docker OAuth Fix (Remote Access)

If accessing SoulSync from a different machine than where it's running:

1. Set your Spotify callback URL to `http://127.0.0.1:8888/callback`
2. Open SoulSync settings and click authenticate
3. Complete Spotify authorization - you'll be redirected to `http://127.0.0.1:8888/callback?code=SOME_CODE_HERE`
4. If the page fails to load, edit the URL to use your actual SoulSync IP:
   - Change: `http://127.0.0.1:8888/callback?code=SOME_CODE_HERE`
   - To: `http://192.168.86.47:8008/callback?code=SOME_CODE_HERE`
5. Press Enter and authentication should complete

**Note**: Spotify only allows `127.0.0.1` as a local redirect URI, hence this workaround.

## File Flow

1. **Search**: Query Soulseek via slskd API
2. **Download**: Files saved to configured download folder
3. **Process**: Auto-organize to transfer folder with metadata enhancement
4. **Lyrics**: Automatic LRC file generation using LRClib.net API
5. **Server Scan**: Triggers library scan on your media server (60s delay)
6. **Database Sync**: Updates SoulSync database with new tracks
7. **Structure**: `Transfer/Artist/Artist - Album/01 - Track.flac` + `01 - Track.lrc`
8. **Import**: Media server picks up organized files with lyrics

## Usage

### Adding Artists to Watchlist

1. Go to the **Watchlist** page
2. Search for artists you want to follow
3. Add them to your watchlist
4. SoulSync will automatically monitor for new releases

### Using Discover Page

1. Go to the **Discover** page
2. View personalized playlists:
   - **Release Radar**: New releases from watchlist and similar artists
   - **Discovery Weekly**: Broader selection of recent releases
   - **Featured Artists**: Recommended similar artists

### Beatport Integration

1. Go to the **Beatport** section
2. Browse featured charts, DJ curated sets, and trending tracks
3. Download entire charts or individual tracks

## Troubleshooting

### Database Issues

The database is stored in `./data` and persists between container restarts. If you need to reset:
```bash
docker compose down
rm -rf data/*
docker compose up -d
```

### OAuth Authentication Issues

See "Docker OAuth Fix" section above for remote access issues.

### slskd Connection Issues

- Verify slskd is running: `docker ps | grep slskd` or `curl http://192.168.86.47:5030/health`
- Check API key is correct (generate in slskd web UI → Settings → API)
- Ensure slskd is sharing files (required to avoid bans) - check Shares section
- Verify Gluetun is healthy: `docker ps | grep gluetun`
- All slskd traffic routes through VPN - check Gluetun logs if connection fails
- If Docker image doesn't exist, you may need to build slskd from source or use alternative image
- slskd must be on media-download-network and behind Gluetun VPN

### Media Server Not Scanning

- Verify media server URL and token/credentials are correct
- Check that transfer path matches your media server's music library path
- Media server scan is triggered 60 seconds after file transfer

## Ports

- **8008**: Web UI (HTTP/HTTPS via Traefik)

## Volumes

- `./data`: SQLite database and configuration
- `./downloads` (or `DOWNLOAD_PATH`): Temporary download location
- `/jenquist-cloud/archive/entertainment-media/Music` (or `TRANSFER_PATH`): Final music library location

## Links

- **GitHub**: https://github.com/Nezreka/SoulSync
- **Docker Hub**: https://hub.docker.com/r/boulderbadgedad/soulsync
- **Web UI**: https://soulsync.server.unarmedpuppy.com

## Notes

- **Must share files in slskd** - downloaders without shares get banned
- **Docker uses separate database** from GUI/WebUI versions
- **Transfer path** should point to your media server music library
- **FLAC preferred** but supports all common formats
- **OAuth from different devices:** See "Docker OAuth Fix" section if you get "Insecure redirect URI" errors

