# Setup Reference - Your Credentials

## Frugal Usenet Credentials

**Username:** unarmedpuppy  
**Password:** nemesazi  

### Servers to Configure in NZBGet:

#### Primary Server (US East):
- Host: `news.frugalusenet.com`
- Port: `563` (SSL)
- Connections: 60
- Priority: 0

#### Backup Server (EU):
- Host: `eunews.frugalusenet.com`
- Port: `563` (SSL)
- Connections: 30
- Priority: 1

#### Bonus Server (EU-NL):
- Host: `bonus.frugalusenet.com`
- Port: `563` (SSL)
- Connections: 50
- Priority: 2

---

## NZBGeek Indexer

**API Key:** 7yQsz0trEPLqtTGtyi91DMJ8NYnzCMmn  
**URL:** https://api.nzbgeek.info/

---

## Next Steps

1. **Get ProtonVPN WireGuard config**
   - Download from ProtonVPN dashboard
   - Save as `wireguard/config/wg0.conf`
   - Add DNS: `DNS = 1.1.1.1, 9.9.9.9`

2. **Start services**
   ```powershell
   docker-compose up -d
   ```

3. **Configure NZBHydra2**
   - Go to http://localhost:5076
   - Add NZBGeek with the API key above

4. **Configure NZBGet**
   - Go to http://localhost:6789
   - Settings → News-servers
   - Add the 3 Frugal servers listed above

5. **Test download**
   - Search for something in NZBHydra2
   - Download an NZB
   - Verify it goes through WireGuard/VPN

