# Deployment Checklist

This is your deployment readiness checklist for the media-download system.

## ✅ Completed Setup

- [x] Directory structure created
- [x] .env file configured with default paths
- [x] Docker Compose file validated
- [x] All required directories exist

## ⚠️ Required Before Starting Containers

### 1. WireGuard VPN Configuration (CRITICAL)

Before starting any containers, you MUST configure WireGuard with your VPN provider.

**Options:**

**Option A: Auto-generate and configure**
```bash
# Start WireGuard to generate server config
docker-compose up -d wireguard

# Get the generated config
docker exec media-download-wireguard cat /config/peer1/peer1.conf

# Add this config to your VPN provider (scan QR code or copy config)
# Then add your VPN provider's config to wireguard/config/wg0.conf
```

**Option B: Manual configuration**
1. Create `wireguard/config/wg0.conf`
2. Add your VPN provider's WireGuard configuration
3. CRITICAL: Add DNS servers to prevent leaks:
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

### 2. Verify VPN is Working

```bash
# Check if WireGuard is connected
docker exec media-download-wireguard wg show

# Test VPN connection
docker exec media-download-wireguard ping -c 3 1.1.1.1

# Verify public IP (should show VPN IP)
docker exec media-download-wireguard curl ifconfig.me
```

### 3. Test Kill Switch

```bash
# Try to access internet from download clients (should work through VPN)
docker exec media-download-nzbget ping -c 3 8.8.8.8

# If WireGuard stops, downloads should fail
docker-compose stop wireguard
docker exec media-download-nzbget ping -c 3 8.8.8.8
# Should fail or timeout - this confirms kill switch works
```

## 🚀 Deployment Steps

### Step 1: Start Services

```bash
cd /Users/joshuajenquist/repos/personal/home-server/apps/media-download

# Start everything
docker-compose up -d

# Or start in stages
docker-compose up -d wireguard
docker-compose up -d nzbhydra2 jackett
docker-compose up -d sonarr radarr lidarr bazarr
docker-compose up -d nzbget qbittorrent
```

### Step 2: Verify All Containers are Running

```bash
docker-compose ps
```

Expected output: All services should show "Up" status.

### Step 3: Access Web UIs

- **NZBHydra2**: http://localhost:5076 (Usenet search)
- **Jackett**: http://localhost:9117 (Torrent search)
- **Sonarr**: http://localhost:8989 (TV shows)
- **Radarr**: http://localhost:7878 (Movies)
- **Lidarr**: http://localhost:8686 (Music)
- **Bazarr**: http://localhost:6767 (Subtitles)
- **qBittorrent**: http://localhost:8080 (Torrent downloader - behind VPN)
- **NZBGet**: http://localhost:6789 (Usenet downloader - behind VPN)

### Step 4: Initial Configuration

See CONFIGURATION-STEPS.md for detailed setup instructions.

## 🔒 Security Checklist

- [ ] WireGuard configured with DNS leak prevention
- [ ] Kill switch verified and working
- [ ] All services use strong passwords
- [ ] Ports only exposed to LAN (not internet)
- [ ] DNS leak tested and working
- [ ] VPN connectivity verified

## 📝 Quick Configuration Guide

### Configure NZBGet (Usenet Downloader)

1. Access via http://localhost:6789
2. Settings → News-servers → Add Provider
3. Configure your Usenet provider details

### Configure NZBHydra2 (Usenet Search)

1. Access via http://localhost:5076
2. Settings → Indexers → Add Indexer
3. Enter your indexer credentials
4. Copy API key for Sonarr/Radarr

### Configure Jackett (Torrent Search)

1. Access via http://localhost:9117
2. Add Torrent trackers (only legal ones)
3. Test each tracker
4. Copy API key

### Configure Sonarr (TV Shows)

1. Access via http://localhost:8989
2. Settings → Indexers → Add NZBHydra2
3. Settings → Download Clients → Add NZBGet & qBittorrent
4. Settings → Media Management → Add TV root folder

### Configure Radarr (Movies)

1. Access via http://localhost:7878
2. Repeat same steps as Sonarr
3. Add movie root folder

### Configure Lidarr (Music)

1. Access via http://localhost:8686
2. Repeat same steps
3. Add music root folder

## 🧪 Testing

### Test Download Flow

1. Add a TV show to Sonarr
2. Wait for automatic search
3. Verify download starts
4. Check that traffic goes through VPN
5. Verify completed download appears

### Verify VPN Routing

```bash
# Check downloader IP (should be VPN IP)
docker exec media-download-nzbget curl ifconfig.me

# Test DNS (should use VPN DNS)
docker exec media-download-wireguard dig @1.1.1.1 google.com
```

## 📊 Monitoring

### Check Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f sonarr

# VPN only
docker-compose logs -f wireguard
```

### Check Health

```bash
# Container status
docker-compose ps

# Health checks
docker ps --format "table {{.Names}}\t{{.Status}}"
```

## 🛠️ Troubleshooting

### VPN Not Connecting

```bash
docker-compose logs wireguard
docker exec media-download-wireguard wg show
```

### Downloads Not Starting

```bash
# Check kill switch
docker exec media-download-nzbget ping 8.8.8.8

# Check NZBGet logs
docker-compose logs nzbget

# Verify VPN is working
docker exec media-download-wireguard wg show
```

### Can't Access Web UIs

```bash
# Check if containers are running
docker-compose ps

# Check port bindings
netstat -an | grep LISTEN | grep -E "(5076|8989|7878)"
```

## 📚 Next Steps After Deployment

1. Configure all services (see above)
2. Add your first TV show or movie
3. Monitor logs for first download
4. Set up automatic backups
5. Configure notifications (optional)
6. Fine-tune quality profiles

## 🔄 Regular Maintenance

```bash
# Update all services
docker-compose pull
docker-compose up -d

# Backup configurations
./backup-configs.sh

# Check for updates
docker-compose pull
```

## ⚠️ Important Reminders

1. **VPN must be configured before starting containers**
2. **Kill switch must be tested**
3. **DNS leak prevention must be configured**
4. **Never expose ports to internet**
5. **Use strong passwords for all services**
6. **Only use legal, reputable indexers**

