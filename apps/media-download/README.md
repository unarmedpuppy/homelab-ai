# Media Download System

A fully containerized, secure media automation system with VPN kill switch, DNS leak prevention, and support for both Usenet (NZB) and torrent downloads.

## 🎯 Features

- **VPN Kill Switch**: All downloads route through WireGuard; if VPN fails, downloads stop automatically
- **DNS Leak Prevention**: Built-in DNS leak protection using DoH/DoT
- **Dual Download Methods**: Both Usenet and torrent support
- **Automated Content Discovery**: TV shows, movies, music, and books
- **Privacy First**: Only the download clients are behind VPN, not the automation UI
- **Secure by Default**: Internal network isolation, health checks, minimal privilege escalation

## 📋 Components

### Download Clients (Behind VPN - Kill Switch Enabled)
- **NZBGet**: Usenet downloader with par2 repair support
- **qBittorrent**: Torrent client with built-in search
- **SABnzbd** (Alternative): Alternative Usenet downloader

### Automation Services
- **Sonarr**: TV show library management and automatic downloading
- **Radarr**: Movie library management and automatic downloading
- **Lidarr**: Music library management and automatic downloading
- **Bookshelf**: Book library management and automatic downloading (Readarr fork - optional)

### Indexers & Aggregators
- **NZBHydra2**: Usenet search aggregator
- **Jackett**: Torrent indexer API

### Media Management
- **Bazarr**: Automatic subtitle downloading

### VPN Gateway
- **WireGuard**: VPN client with kill switch and DNS leak prevention

## 🚀 Quick Start

### 1. Prerequisites

- Docker and Docker Compose installed
- A WireGuard VPN provider account (see recommended providers below)
- A Usenet provider account (see recommended providers below)

### 2. Setup

```bash
cd apps/media-download

# Copy environment template
cp .env.template .env
# Edit .env with your paths

# Create directories
mkdir -p wireguard/config nzbhydra2/{config,data} jackett/config
mkdir -p nzbget/config qbittorrent/config sabnzbd/config
mkdir -p sonarr/config radarr/config lidarr/config bazarr/config readarr/config
mkdir -p downloads/{nzb,torrents,completed}
mkdir -p media/{tv,movies,music,books}
```

### 3. Configure WireGuard

1. Get your WireGuard config from your VPN provider
2. Place the config file in `wireguard/config/peer1/peer1.conf` (or update docker-compose to match your provider's config location)
3. The container will auto-generate server configuration

Alternatively, for easier setup with many providers:
1. Start the container: `docker-compose up -d wireguard`
2. Access the generated config: `docker exec -it media-download-wireguard cat /config/peer1/peer1.conf`
3. Scan the QR code or copy the config to your phone/system to generate server config
4. Add your VPN provider's config to `/config/wg0.conf`

**Important**: Make sure to configure DNS servers in WireGuard to prevent DNS leaks!

### 4. Start Services

```bash
# Start all services
docker-compose up -d

# Or start specific services
docker-compose up -d wireguard nzbget sonarr radarr

# View logs
docker-compose logs -f
```

### 5. Configure Services

Access the web UIs:
- **NZBHydra2**: http://localhost:5076 (Usenet search aggregator)
- **Jackett**: http://localhost:9117 (Torrent search aggregator)
- **Sonarr**: http://localhost:8989 (TV shows automation)
- **Radarr**: http://localhost:7878 (Movies automation)
- **Lidarr**: http://localhost:8686 (Music automation)
- **Bazarr**: http://localhost:6767 (Subtitles automation)
- **Readarr**: http://localhost:8787 (Books automation - optional)
- **qBittorrent**: http://localhost:8080 (Torrent downloader - behind VPN)
- **NZBGet**: http://localhost:6789 (Usenet downloader - behind VPN)
- **SABnzbd**: http://localhost:8079 (Alternative Usenet downloader - behind VPN)

Note: Download clients (qBittorrent, NZBGet, SABnzbd) route all traffic through VPN for security.

## 🔒 Security Configuration

### WireGuard DNS Leak Prevention

Edit `wireguard/config/wg0.conf` and ensure DNS is set:

```ini
[Interface]
PrivateKey = YOUR_PRIVATE_KEY
Address = 10.13.13.X/24
DNS = 1.1.1.1, 9.9.9.9
# Or use DoH with unbound
DNS = 1.1.1.1, 1.0.0.1

[Peer]
PublicKey = VPN_SERVER_KEY
Endpoint = VPN_SERVER_ADDRESS:PORT
AllowedIPs = 0.0.0.0/0
```

### Enable Kill Switch Verification

The kill switch works automatically via `network_mode: service:wireguard`. To verify:

```bash
# Check that containers can't access host network
docker exec media-download-nzbget ping -c 1 8.8.8.8

# Check VPN is working
docker exec media-download-wireguard ping -c 1 1.1.1.1
```

### Firewall Rules (Recommended)

Add firewall rules to block direct internet access except through WireGuard:

```bash
# Example iptables rules (adjust for your system)
# Block all outbound traffic except WireGuard
iptables -A OUTPUT -j ACCEPT -m conntrack --ctstate ESTABLISHED,RELATED
iptables -A OUTPUT -j DROP -o eth0

# Allow only WireGuard interface
iptables -A OUTPUT -j ACCEPT -o wg0
```

### Container Security

- All containers run as non-root (PUID/PGID 1000)
- Network isolation via internal Docker network
- Health checks enabled
- Read-only mounts where possible
- Minimal port exposure (LAN only)

## 📝 Configuration Guides

### NZBGet Configuration

1. Access via config file or restart with web UI port exposed temporarily
2. Set Usenet server credentials:
   - Server: `news.yourprovider.com`
   - Port: `563` (SSL) or `119` (non-SSL)
   - Username: Your usenet username
   - Password: Your usenet password
   - Connections: `20` (recommended)
   - Secure: `Yes`
3. Set download path to `/downloads`
4. Enable par2 repair
5. Set minimum free space

### Sonarr/Radarr Configuration

1. Go to Settings → Indexers
2. Add NZBHydra2:
   - URL: `http://nzbhydra2:5076/nzbhydra2`
   - API Key: (found in NZBHydra2 settings)
3. Add Jackett (for torrents):
   - URL: `http://jackett:9117/api/v2.0/indexers/all/results/torrentapi`
   - API Key: (found in Jackett settings)
4. Add download clients:
   - NZBGet: `http://nzbget:6789/xmlrpc` (with username/password)
   - qBittorrent: `http://qbittorrent:8080` (with credentials)
5. Set root folders and download categories

### NZBHydra2 - Add Usenet Indexers

Go to Settings → Indexers:
- Add only reputable, paid Usenet indexers
- Avoid public indexers
- Recommended: **NZBPlanet**, **NzbGeek**, **DrunkenSlug** (paid services)
- Configure your indexer API keys

### Jackett - Add Torrent Indexers

1. Go to Configuration → Indexers
2. Add only legitimate torrent indexers
3. For legal content only
4. Test each indexer

### qBittorrent Configuration

1. Set download path to `/downloads/torrents`
2. Enable UPnP/NAT-PMP
3. Configure bandwidth limits
4. Enable encryption
5. Set random port (port forwarding not needed behind VPN)

## 🏆 Recommended Providers

### Usenet Providers

- **Frugal Usenet** ($5.99/month): Affordable, good speed, decent retention
- **Newshosting** ($9.99/month): Fast, reliable, excellent support
- **Eweka** ($7.99/month): Excellent retention, good EU performance
- **UsenetServer** ($10/month): Good all-around provider
- **NewsDemon** ($7.99/month): Multiple tiers with good features

**Note**: Many providers offer discounts for annual plans.

### Usenet Indexers (Required)

- **NZBGeek** (lifetime $15): Popular, reliable, good API
- **NZBPlanet** ($10/year): Solid indexer with good automation
- **DrunkenSlug** ($10/year): Excellent automation, good catalog
- **Slug** (limited free tier, paid $10/year): Good open source indexer

### VPN Providers (Compatible with this setup)

- **Mullvad** ($5/month): No logging, excellent privacy
- **IVPN** ($8/month): Strong security, good reviews
- **ProtonVPN** ($8/month): Swiss privacy, free tier available
- **Perfect Privacy** ($9.99/month): Advanced features

## 🔍 Verification & Testing

### Test VPN Kill Switch

```bash
# Stop WireGuard and verify downloads stop
docker-compose stop wireguard

# Try to download something - should fail
docker exec media-download-nzbget curl -I ifconfig.me
# Should fail or timeout

# Restart WireGuard
docker-compose start wireguard
# Downloads should resume
```

### Test DNS Leak

Visit DNS leak test sites:
- https://www.dnsleaktest.com
- https://ipleak.net

Run from the WireGuard container:
```bash
docker exec media-download-wireguard dig google.com
# Should show VPN DNS servers
```

### Verify Services

```bash
# Check all containers are running
docker-compose ps

# Check logs
docker-compose logs -f

# Check specific service
docker-compose logs sonarr
```

## 📊 Monitoring

### Health Checks

All VPN-dependent services have health checks. View status:

```bash
docker-compose ps
```

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f sonarr radarr

# VPN connectivity
docker-compose logs -f wireguard
```

### Backups

Backup configuration directories periodically:

```bash
# Backup configs
tar -czf media-download-backup-$(date +%Y%m%d).tar.gz */config

# Restore
tar -xzf media-download-backup-20241206.tar.gz
```

## 🛡️ Security Best Practices

1. **Never expose ports to the internet** - Use LAN-only bindings
2. **Use strong passwords** for all services
3. **Keep containers updated**: `docker-compose pull && docker-compose up -d`
4. **Regular backups** of configuration directories
5. **Monitor logs** for unusual activity
6. **Use firewall rules** on the host
7. **Only add legitimate indexers** - avoid public/shady providers
8. **Don't share accounts** or passwords
9. **Check VPN logs** periodically for disconnections
10. **Use separate WireGuard config** for automation vs personal use

## 🚨 Troubleshooting

### Downloads not starting

1. Check WireGuard is running: `docker-compose ps wireguard`
2. Verify VPN is connected: `docker exec media-download-wireguard wg show`
3. Check downloader logs: `docker-compose logs nzbget`
4. Test internet from VPN container: `docker exec media-download-wireguard ping 1.1.1.1`

### DNS leaks

1. Check WireGuard config has DNS servers set
2. Verify DNS servers in container: `docker exec media-download-wireguard cat /etc/resolv.conf`
3. Use DNS leak test sites from within container

### Can't access web UIs

1. Check ports aren't blocked by firewall
2. Verify services are running: `docker-compose ps`
3. Check logs for errors: `docker-compose logs <service>`
4. Try different port if conflict exists

### Slow downloads

1. Check VPN speed: `docker exec media-download-wireguard speedtest-cli`
2. Consider different VPN endpoint (server)
3. Increase Usenet connections (max 30)
4. Check disk I/O with `iostat`
5. Verify not bandwidth throttled by ISP

## 📚 Additional Resources

- [Sonarr Documentation](https://wiki.servarr.com/sonarr)
- [Radarr Documentation](https://wiki.servarr.com/radarr)
- [Lidarr Documentation](https://wiki.servarr.com/lidarr)
- [NZBGet Manual](https://nzbget.net/documentation)
- [qBittorrent Wiki](https://github.com/qbittorrent/qBittorrent/wiki)
- [WireGuard Manual](https://www.wireguard.com/manpages/)

## ⚖️ Legal Notice

This system is designed for downloading legal, freely distributable content such as:
- Public domain content
- Creative Commons licensed content
- Content you have the right to download
- Linux ISOs and software distributions
- Educational content

**Always respect copyright laws** and only use reputable, legal indexers and sources.

## 🤝 Contributing

Feel free to open issues or pull requests for improvements.

## 📄 License

MIT License - Use at your own risk

