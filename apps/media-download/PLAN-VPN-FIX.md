# Media Download VPN Fix - Plan & Checklist

## Goal
Protect downloads (hide IP/DNS) by routing traffic through ProtonVPN before downloading content.

---

## What We're Trying To Do

### The Problem
- NZBGet is failing to download because it can't resolve hostnames
- DNS resolution is timing out (e.g., `bonus.frugalusenet.com: Error -3`)
- This happens because the VPN isn't routing traffic properly
- We're trying to use the wrong VPN setup (server vs client)

### The Solution
Route **all download traffic** through ProtonVPN so:
- Your IP is hidden (shows ProtonVPN IP)
- DNS queries go through ProtonVPN
- Downloads work properly
- If VPN drops, downloads stop (kill switch)

---

## Step-by-Step Plan

### Step 1: Choose the Right VPN Container
**What:** Pick a container that actually supports connecting AS A CLIENT to ProtonVPN  
**Why:** linuxserver/wireguard is for running your OWN server, not connecting to ProtonVPN  
**Validate:** Container starts and connects to ProtonVPN

**Status:** ❌ Currently trying protonvpn-docker but configuration is wrong

### Step 2: Configure VPN Properly
**What:** Provide correct ProtonVPN credentials and server  
**Why:** Container needs to know WHERE to connect and HOW to authenticate  
**Validate:** VPN establishes connection (check logs show "connected")

**Status:** ❌ Server name format is wrong (`CH#699` vs IP vs hostname)

### Step 3: Test DNS Resolution Through VPN
**What:** Verify that the VPN container can resolve hostnames  
**Why:** If DNS doesn't work, downloads can't find servers  
**Validate:** Run `nslookup bonus.frugalusenet.com` from container → works

**Status:** ❌ Not working because VPN isn't routing properly

### Step 4: Test NZBGet Can Reach Usenet Servers
**What:** Verify NZBGet can download content  
**Why:** This is the actual download client that needs protection  
**Validate:** NZBGet successfully downloads a test file

**Status:** ❌ Failing with "could not resolve hostname"

### Step 5: Verify IP/DNS Protection
**What:** Confirm your real IP is hidden  
**Why:** This is the whole point of the VPN  
**Validate:** Run `curl ifconfig.me` from VPN container → shows ProtonVPN IP, not your real IP

**Status:** ❌ Not tested yet

---

## Current Status Summary

✅ **Working:**
- Sonarr, Radarr, Lidarr can search via NZBHydra2
- NZBGeek is returning search results
- Services can communicate with each other

❌ **Not Working:**
- VPN (ProtonWire container) won't start
- Downloads fail due to DNS resolution
- IP/DNS are NOT protected (or VPN isn't routing)

---

## What Needs To Happen Next

### Option A: Fix ProtonVPN Docker Setup
1. Get correct ProtonVPN server name format (not just IP)
2. Configure ProtonWire container with correct settings
3. Test VPN connection works
4. Test downloads work through VPN

### Option B: Use Different VPN Solution
1. Try Gluetun (universal VPN client)
2. Or go back to linuxserver/wireguard but fix routing
3. Or use ProtonVPN's official CLI tool

---

## Validation Checklist

Before considering it "done", verify:

- [ ] VPN container starts successfully
- [ ] VPN shows "connected" in logs
- [ ] DNS resolution works from VPN container
- [ ] NZBGet can resolve hostnames
- [ ] Test download completes successfully
- [ ] IP check shows ProtonVPN IP, not real IP
- [ ] Kill switch works (if VPN drops, downloads stop)

---

## Next Steps

1. **Research:** What's the correct format for PROTONVPN_SERVER in protonvpn-docker?
2. **OR:** Try a different VPN solution that's simpler
3. **OR:** Test if linuxserver/wireguard actually works if configured differently
4. **Decide:** Which approach to take and commit to it

**Recommendation:** Let's research the correct protonvpn-docker configuration OR switch to Gluetun which handles VPN configuration more automatically.

