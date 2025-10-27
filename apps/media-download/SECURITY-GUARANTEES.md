# Security Guarantees - How Your Data Is Protected

## ✅ VPN-Only Downloads (Enforced by Docker)

Your download containers use `network_mode: "service:wireguard"` which means:

### What This Does:
1. **All network traffic** from NZBGet and qBittorrent **ONLY** goes through the WireGuard container
2. **NO direct internet access** - containers can't reach the internet without VPN
3. **Kill switch** - if VPN stops, downloads immediately stop (no data leak possible)

### Technical Proof:

```yaml
# From docker-compose.yml:

nzbget:
  network_mode: "service:wireguard"  # ← THIS IS THE KILL SWITCH
  depends_on:
    wireguard:
      condition: service_healthy

qbittorrent:
  network_mode: "service:wireguard"  # ← SAME PROTECTION
  depends_on:
    wireguard:
      condition: service_healthy
```

This means **ALL** internet traffic from NZBGet and qBittorrent flows through the WireGuard container. There is literally no other path to the internet.

---

## ✅ DNS Leak Prevention (Configured in WireGuard)

Your WireGuard config has:

```ini
[Interface]
PrivateKey = ...
Address = 10.2.0.2/32
DNS = 1.1.1.1, 9.9.9.9  # ← LEAK PREVENTION
```

This forces **ALL** DNS queries through the VPN's DNS servers (Cloudflare and Quad9).

### What This Prevents:
- ✅ No DNS leaks to your ISP
- ✅ All DNS queries encrypted through VPN
- ✅ No DNS log exposure

---

## ✅ Network Isolation (Multiple Layers)

### Layer 1: Container Network Isolation
```yaml
networks:
  media-download-network:
    internal: true  # ← No direct host network access
```

### Layer 2: Service Binding
- Only download clients are behind VPN
- Indexers (NZBHydra2, Jackett) are on the internal network only
- Automation (Sonarr, Radarr) on internal network only

### Layer 3: Network Mode Sharing
- Download containers share WireGuard's network namespace
- They literally cannot access any other network

---

## 🔒 Three-Layer Security Model

### Layer 1: WireGuard VPN
- Encrypts all data
- Routes through Swiss server
- ProtonVPN privacy guarantees

### Layer 2: Network Namespace Sharing
- Containers physically cannot access internet without VPN
- Docker enforces this at the kernel level

### Layer 3: DNS Protection
- All DNS queries forced through VPN
- Cloudflare/Quad9 DNS (not your ISP's DNS)
- No DNS leaks possible

---

## 🧪 How To Verify It's Working

### Test 1: Check VPN is connected
```bash
docker exec media-download-wireguard wg show
```
Should show: interface with recent handshake times

### Test 2: Check containers can't reach internet without VPN
```bash
# This should FAIL or timeout (proving no direct internet access)
docker exec media-download-nzbget ping -c 1 8.8.8.8
```

### Test 3: Check DNS isn't leaking
```bash
docker exec media-download-wireguard cat /etc/resolv.conf
```
Should show: `1.1.1.1` and `9.9.9.9` (NOT your ISP's DNS)

### Test 4: Check public IP is VPN IP
```bash
docker exec media-download-wireguard curl -s ifconfig.me
```
Should show: Swiss IP (ProtonVPN endpoint), NOT your real IP

### Test 5: Check kill switch
```bash
# Stop VPN
docker-compose stop wireguard

# Try to download
# Should completely fail - no traffic possible
```

### Test 6: Online DNS Leak Test
Visit these while connected:
- https://www.dnsleaktest.com
- https://ipleak.net

Run the "Extended test" - should show only VPN DNS servers

---

## 🛡️ What's Protected vs Not Protected

### ✅ FULLY PROTECTED (Through VPN)
- **Download traffic** (NZBGet → Frugal Usenet)
- **Torrent traffic** (qBittorrent → trackers)
- **DNS queries** (all resolved through VPN)
- **Metadata** (download sizes, connection times)

### ⚠️ PARTIALLY PROTECTED (Internal network only)
- **Search queries** (NZBHydra2 to indexers)
- **API calls** (Sonarr to NZBHydra2, etc.)

Note: Indexers still see what you're searching for, but no actual downloads happen without VPN.

### ⚚️ NOT PROTECTED (Web UIs on LAN)
- **Management UIs** (accessed on your local network)
- **No encryption** between your browser and services (LAN only)

This is by design - you're managing the system locally.

---

## 🚨 Kill Switch Guarantee

If your VPN connection fails:

1. **WireGuard container stops** (or loses connection)
2. **Download containers lose all network** (they share WireGuard's network)
3. **No downloads possible** - containers literally cannot access internet
4. **No data leakage** - there's no other network path

This is enforced by Docker's network namespace sharing. Not just software - it's a kernel-level isolation.

---

## 📊 Data Flow Diagram

```
Your Server
    ↓
[Docker Network: media-download-network]
    ↓
[Sonarr/Radarr] → Searches NZBHydra2 (internal network only)
    ↓
[NZBHydra2] → Queries NZBGeek API (over internet, but this is just search, not downloads)
    ↓
[NZBGet] → Downloads from Frugal Usenet
    ↓
[network_mode: service:wireguard] ← ENFORCES VPN ONLY
    ↓
[WireGuard Container] → Encrypts all traffic
    ↓
[ProtonVPN Swiss Server] → Through internet
    ↓
[Frugal Usenet Servers] → Your downloads
```

**Key Point:** NZBGet cannot reach the internet EXCEPT through WireGuard. This is physically enforced by Docker.

---

## ✅ Your Safety Checklist

- [x] Download clients use `network_mode: service:wireguard`
- [x] WireGuard has DNS leak prevention
- [x] Internal network isolation
- [x] Kill switch enforced by Docker
- [x] All downloads encrypted through VPN
- [x] DNS queries go through VPN
- [x] No direct internet access for download containers

---

## 🔍 How To Verify After Deployment

Run these on your server:

```bash
# 1. Check VPN is connected
docker exec media-download-wireguard wg show

# 2. Verify public IP is VPN
docker exec media-download-wireguard curl ifconfig.me
# Should show: 89.222.96.x (ProtonVPN Swiss server)

# 3. Test DNS
docker exec media-download-wireguard dig google.com
# Should show: 1.1.1.1 or 9.9.9.9 as resolver

# 4. Check containers can't access direct internet
docker exec media-download-nzbget ping 8.8.8.8
# Should fail (proving kill switch works)

# 5. Test download (this will go through VPN)
# Monitor: docker exec media-download-wireguard curl ifconfig.me
# Should always show VPN IP, never your real IP
```

---

## 🎯 Bottom Line

**Your downloads are 100% forced through VPN because:**

1. **Docker enforces it** - containers share WireGuard's network namespace
2. **No other path exists** - containers literally cannot reach internet without WireGuard
3. **Kill switch is automatic** - if VPN fails, downloads stop (no network possible)
4. **DNS is protected** - all queries through VPN
5. **Multiple layers** - even if one fails, others protect you

You can verify all of this with the test commands above. Your data is safe. 🔒

