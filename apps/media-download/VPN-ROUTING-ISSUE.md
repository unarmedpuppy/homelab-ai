# VPN Routing Issue - Analysis & Options

## Current State

### What's Working ✅
1. WireGuard container starts successfully
2. WireGuard interface (wg0) is created
3. Handshake with ProtonVPN server succeeds
4. DNS servers are configured (1.1.1.1, 9.9.9.9)
5. Routing rules are added (ip route add 0.0.0.0/0 dev wg0 table 51820)
6. All services (Sonarr, Radarr, NZBHydra2) are running

### What's NOT Working ❌
1. **No internet connectivity through VPN** - `ping 8.8.8.8` fails from wireguard container
2. **DNS resolution fails** - cannot resolve `bonus.frugalusenet.com`
3. **Downloads fail** - NZBGet cannot connect to Frugal servers
4. **VPN is "connected" but traffic doesn't route** - handshake works, but no actual data flows

### Evidence from Logs
```
Peer Connection Initiated ✅
latest handshake: 1 minute, 21 seconds ago ✅
transfer: 13.91 KiB received, 270.98 KiB sent ✅

BUT:
PING 8.8.8.8 - 0 packets received ❌
could not establish connection to bonus.frugalusenet.com ❌
```

## Root Cause Analysis

The linuxserver/wireguard container is designed primarily for **SERVER mode** (you run a VPN server, others connect to YOU). In client mode (connecting TO a VPN), it:
- Creates the WireGuard interface ✅
- Establishes handshake ✅  
- Sets up routing rules ✅
- **BUT: The routing doesn't actually work in Docker's network namespace** ❌

The issue is that when using `network_mode: service:wireguard`, the WireGuard container's routing table doesn't properly route traffic through the VPN interface in Docker's network context.

---

## Options to Fix This (Without Abandoning WireGuard)

### Option 1: Fix Docker Networking for WireGuard Client
**Approach:** Configure WireGuard to route traffic properly in Docker context

**Changes needed:**
- Add `network_mode: host` to wireguard service (try again, properly configured)
- OR: Use a different approach to route traffic

**Pros:** Keeps your existing config
**Cons:** May not work with Docker's network isolation
**Difficulty:** Medium

---

### Option 2: Use Gluetun with ProtonVPN Auto-Discovery
**Approach:** Let Gluetun automatically connect to ProtonVPN without manual config

**Changes needed:**
```yaml
VPN_SERVICE_PROVIDER=protonvpn
VPN_TYPE=openvpn
OPENVPN_USER=your_email
OPENVPN_PASSWORD=your_password
SERVER_COUNTRIES=Switzerland
```

**Pros:** Works automatically, no manual config needed
**Cons:** Uses OpenVPN instead of WireGuard (less efficient, but functional)
**Difficulty:** Easy

---

### Option 3: Use WireGuard Directly on Host System
**Approach:** Install WireGuard on the host server, run it outside Docker

**Changes needed:**
- Install WireGuard on host: `apt install wireguard`
- Create `/etc/wireguard/wg0.conf` with your ProtonVPN config
- Start with: `wg-quick up wg0`
- Update docker-compose to NOT use network_mode service
- Run download containers with host network or bridge + NAT rules

**Pros:** Most direct approach, uses your exact config
**Cons:** Requires host-level installation, more complex
**Difficulty:** High

---

### Option 4: Test Downloads WITHOUT VPN First
**Approach:** Temporarily test that downloads work without VPN, then add VPN

**Changes needed:**
- Remove `network_mode: service:wireguard` from nzbget/qbittorrent
- Add them back to regular Docker network
- Test downloads
- Once working, figure out VPN

**Pros:** Validates that rest of system works
**Cons:** No VPN protection while testing
**Difficulty:** Easy

---

## Recommendation: Try Option 2 (Gluetun + ProtonVPN Credentials)

**Why:**
1. Gluetun is DESIGNED for this exact use case
2. Your credentials will make it connect automatically
3. No manual routing/config needed
4. Battle-tested solution

**Implementation:**
```yaml
gluetun:
  image: qmcgaw/gluetun:latest
  environment:
    - VPN_SERVICE_PROVIDER=protonvpn
    - VPN_TYPE=openvpn  # Uses OpenVPN, not WireGuard
    - OPENVPN_USER=dangerbahn@gmail.com
    - OPENVPN_PASSWORD=Eb5nOJKEnAqF@MIF
    - SERVER_COUNTRIES=Switzerland
```

---

## Next Steps

**Choose an option and we'll implement it.**

**Option 1: Keep trying WireGuard manually** - Requires Docker networking expertise  
**Option 2: Use Gluetun with ProtonVPN** - Simplest, proven solution  
**Option 3: Install WireGuard on host** - Most technical, but most direct  
**Option 4: Test without VPN first** - Validate other components work

**Recommendation: Option 2** - It's the most reliable and you already have the credentials ready to use.

