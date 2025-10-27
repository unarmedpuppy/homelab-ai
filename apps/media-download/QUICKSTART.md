# Quick Start Guide

Get your media download system up and running in 10 minutes.

## Prerequisites

1. **Docker** installed and running
2. **VPN Provider** account (Mullvad, IVPN, ProtonVPN, or similar)
3. **Usenet Provider** account (Frugal Usenet, Newshosting, or similar)
4. **Usenet Indexer** account (NZBGeek, NZBPlanet, or similar)

## Step-by-Step Setup

### 1. Initial Setup (2 minutes)

```powershell
cd apps\media-download

# Copy environment template
Copy-Item .env.template .env
# Edit .env if you want to change paths

# Create directories
.\setup.ps1
```

### 2. Configure WireGuard VPN (3 minutes)

Get your WireGuard config from your VPN provider.

**Option A: Manual Config File**
1. Create `wireguard\config\wg0.conf`
2. Add your VPN provider's config
3. Add DNS leak prevention: `DNS = 1.1.1.1, 9.9.9.9`

Example config:
```ini
[Interface]
PrivateKey = YOUR_PRIVATE_KEY
Address = 10.8.0.2/24
DNS = 1.1.1.1, 9.9.9.9

[Peer]
PublicKey = VPN_SERVER_KEY
Endpoint = your-vpn-server.com:51820
AllowedIPs = 0.0.0.0/0
```

**Option B: Use Peer Config**
```powershell
.\setup-wireguard.ps1
# Follow the on-screen instructions
# Add your VPN provider details
```

### 3. Verify VPN is Working (1 minute)

```powershell
.\verify-vpn.ps1
```

Should show:
- ✅ VPN: Connected
- ✅ Internet: Accessible through VPN
- ✅ Kill Switch: Working

### 4. Start All Services (1 minute)

```powershell
docker-compose up -d
```

### 5. Configure Services (3 minutes)

#### a) Configure NZBGet (Usenet Downloader)

1. Edit `nzbget\config\nzbget.conf` or wait for first start
2. Add your Usenet provider:
   ```
   Server1.Host=news.yourprovider.com
   Server1.Port=563
   Server1.Username=your_username
   Server1.Password=your_password
   Server1.Encryption=yes
   Server1.Connections=20
   ```

#### b) Configure NZBHydra2 (Usenet Search)

1. Open http://localhost:5076
2. Add your indexers (NZBGeek, etc.)
3. Get API key for Sonarr/Radarr

#### c) Configure Jackett (Torrent Search)

1. Open http://localhost:9117
2. Add torrent trackers (only legal ones)
3. Get API key

#### d) Configure Sonarr (TV Shows)

1. Open http://localhost:8989
2. Settings → Indexers:
   - Add NZBHydra2: `http://nzbhydra2:5076/nzbhydra2`
   - Add Jackett: `http://jackett:9117/api/v2.0/indexers/all/results/torrentapi`
3. Settings → Download Clients:
   - Add NZBGet: `http://nzbget:6789/xmlrpc`
   - Add qBittorrent: `http://qbittorrent:8080`
4. Settings → Root Folders → Add `/tv`

#### e) Configure Radarr (Movies)

1. Open http://localhost:7878
2. Repeat same steps as Sonarr
3. Add root folder: `/movies`

#### f) Configure Lidarr (Music)

1. Open http://localhost:8686
2. Repeat same steps
3. Add root folder: `/music`

### 6. Test the System

1. Add a TV show in Sonarr
2. Watch it automatically search and download
3. Verify download goes through VPN: `docker exec media-download-wireguard curl ifconfig.me`
4. Check completion in Sonarr

## Access URLs

- **NZBHydra2**: http://localhost:5076
- **Jackett**: http://localhost:9117
- **Sonarr**: http://localhost:8989
- **Radarr**: http://localhost:7878
- **Lidarr**: http://localhost:8686
- **Bazarr**: http://localhost:6767
- **qBittorrent**: http://localhost:8080
- **NZBGet**: http://localhost:6789
- **SABnzbd** (alternative): http://localhost:8079

## Troubleshooting

### VPN Not Connecting

```powershell
# Check logs
docker-compose logs wireguard

# Check config
cat wireguard\config\wg0.conf

# Test manually
docker exec media-download-wireguard wg show
```

### Downloads Not Working

```powershell
# Verify kill switch
docker exec media-download-nzbget ping 8.8.8.8
# Should FAIL if working correctly

# Check logs
docker-compose logs nzbget
```

### DNS Leak

1. Verify DNS in WireGuard config: `DNS = 1.1.1.1, 9.9.9.9`
2. Test from container: `docker exec media-download-wireguard dig @1.1.1.1 google.com`
3. Visit https://ipleak.net to test

## Security Checklist

- [ ] VPN is connected and working
- [ ] Kill switch is active (downloads stop if VPN fails)
- [ ] DNS leak prevention enabled
- [ ] All services use strong passwords
- [ ] Ports not exposed to internet
- [ ] Firewall rules configured
- [ ] Regular backups scheduled

## Daily Operations

### Check Status
```powershell
docker-compose ps
```

### View Logs
```powershell
docker-compose logs -f sonarr
```

### Restart Services
```powershell
docker-compose restart
```

### Backup Configuration
```powershell
.\backup-configs.ps1
```

### Update All Services
```powershell
docker-compose pull
docker-compose up -d
```

## Next Steps

1. Add your favorite TV shows to Sonarr
2. Configure quality profiles in Sonarr/Radarr
3. Set up Bazarr for automatic subtitles
4. Configure notifications (email, Discord, etc.)
5. Set up regular backups
6. Monitor logs for issues

## Getting Help

- Check `README.md` for detailed documentation
- Review logs: `docker-compose logs`
- Verify VPN: `.\verify-vpn.ps1`
- Check service health: `docker-compose ps`

## Important Reminders

⚠️ **Security First**
- Never expose ports to the internet
- Use strong passwords everywhere
- Keep services updated
- Monitor for VPN disconnections
- Test kill switch regularly

📝 **Legal Use Only**
- Only download content you have rights to
- Use reputable, legal indexers
- Don't use public/shady providers
- Respect copyright laws

💾 **Backup Regularly**
- Run `.\backup-configs.ps1` weekly
- Store backups in secure location
- Test restore process

