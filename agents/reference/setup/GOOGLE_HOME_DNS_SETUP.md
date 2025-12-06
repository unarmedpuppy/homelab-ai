# Google Home Mesh Router - AdGuard Home DNS Setup

Complete guide for configuring AdGuard Home as your local DNS server with Google Home/Nest mesh routers.

## Prerequisites

- ✅ AdGuard Home running on server (192.168.86.47:53)
- ✅ Server has static IP (192.168.86.47)
- ✅ Google Home app installed on your phone
- ✅ Admin access to your Google Home network

---

## Method 1: Google Home App (Recommended)

### Step 1: Open Google Home App

1. Open the **Google Home** app on your phone
2. Tap on your **Wi-Fi** network (or "Wi-Fi settings")
3. Tap on **Network settings** or **Advanced networking**

### Step 2: Configure DNS Settings

**Note**: Google Home routers have limited DNS configuration options. You may need to use Method 2 if DNS settings aren't available in the app.

1. Look for **DNS** or **Advanced DNS** settings
2. If available, set:
   - **Primary DNS**: `192.168.86.47`
   - **Secondary DNS**: `8.8.8.8` (Google DNS as backup)
3. Save settings

---

## Method 2: Google Home Web Interface

### Step 1: Access Router Admin

1. Open a web browser
2. Navigate to: `http://192.168.86.1` (or check your router's IP)
   - You can find your router IP by running: `ip route | grep default`
3. You may be redirected to Google Home app - follow the prompts

### Step 2: Configure DNS

**Note**: Google Home routers may not expose DNS settings in the web interface. If unavailable, use Method 3.

---

## Method 3: DHCP Configuration (Most Reliable)

Since Google Home routers have limited DNS configuration options, the most reliable method is to configure devices individually or use AdGuard Home's DHCP server.

### Option A: Configure Devices Manually

Configure DNS on each device:

**Windows:**
1. Settings → Network & Internet → Change adapter options
2. Right-click your network → Properties
3. Internet Protocol Version 4 (TCP/IPv4) → Properties
4. Use the following DNS server addresses:
   - Preferred: `192.168.86.47`
   - Alternate: `8.8.8.8`

**macOS:**
1. System Preferences → Network
2. Select your network → Advanced → DNS
3. Click `+` and add: `192.168.86.47`
4. Add backup: `8.8.8.8`

**iOS:**
1. Settings → Wi-Fi
2. Tap `(i)` next to your network
3. Configure DNS → Manual
4. Add server: `192.168.86.47`
5. Add server: `8.8.8.8`

**Android:**
1. Settings → Network & Internet → Wi-Fi
2. Long-press your network → Modify network
3. Advanced options → IP settings: Static
4. DNS 1: `192.168.86.47`
5. DNS 2: `8.8.8.8`

### Option B: Enable AdGuard Home DHCP (Advanced)

If you want AdGuard Home to handle DHCP (not recommended if Google Home is managing it):

1. **Enable DHCP in AdGuard Home:**
   - Access AdGuard Home: `http://192.168.86.47:8083`
   - Settings → DHCP settings
   - Enable DHCP server
   - Configure IP range (e.g., 192.168.86.100-192.168.86.200)
   - Set gateway: `192.168.86.1` (your Google Home router)
   - Set DNS: `192.168.86.47`

2. **Disable DHCP on Google Home:**
   - This may not be possible with Google Home routers
   - **Warning**: Having two DHCP servers can cause conflicts

**Recommendation**: Keep Google Home as DHCP server, configure DNS per device or use Method 4.

---

## Method 4: Router-Level DNS (If Supported)

Some Google Home/Nest routers support custom DNS via the Google Home app's advanced settings:

1. Open **Google Home** app
2. Go to **Wi-Fi** → **Network settings**
3. Look for **DNS** or **Custom DNS** option
4. Enter: `192.168.86.47`
5. Save

**Note**: This feature may not be available on all Google Home router models.

---

## Verification

### Step 1: Check DNS Resolution

Run these commands to verify DNS is working:

```bash
# Test DNS resolution
nslookup google.com 192.168.86.47

# Check if device is using AdGuard Home
dig @192.168.86.47 google.com

# On server, check AdGuard Home logs
docker logs adguard --tail 50
```

### Step 2: Check AdGuard Home Dashboard

1. Open: `http://192.168.86.47:8083`
2. Go to **Dashboard**
3. You should see DNS queries appearing
4. Check **Statistics** for blocked ads/queries

### Step 3: Test Ad Blocking

Visit a site with ads (like a news website). If AdGuard Home is working, ads should be blocked.

---

## Troubleshooting

### Issue: Devices Not Using AdGuard Home DNS

**Symptoms**: AdGuard Home dashboard shows no queries

**Solutions**:
1. Verify device DNS settings point to `192.168.86.47`
2. Check firewall rules (UFW should allow port 53)
3. Verify AdGuard Home is running: `docker ps | grep adguard`
4. Test DNS directly: `nslookup google.com 192.168.86.47`

### Issue: Google Home Router Doesn't Support Custom DNS

**Solution**: Configure DNS on individual devices (Method 3, Option A)

### Issue: DNS Queries Not Appearing in AdGuard Home

**Check**:
1. AdGuard Home is listening on all interfaces
2. Port 53 is not blocked by firewall
3. Device is actually using `192.168.86.47` as DNS

**Verify**:
```bash
# On server
sudo netstat -tulpn | grep :53
# Should show AdGuard Home listening on 0.0.0.0:53

# Check firewall
sudo ufw status | grep 53
# Should show: 53/tcp and 53/udp allowed
```

### Issue: Slow DNS Resolution

**Possible causes**:
1. AdGuard Home upstream DNS servers are slow
2. Network latency
3. Too many filter lists enabled

**Fix**:
1. In AdGuard Home: Settings → DNS settings
2. Change upstream DNS to faster servers:
   - `1.1.1.1` (Cloudflare - fast)
   - `8.8.8.8` (Google - reliable)
   - `9.9.9.9` (Quad9 - privacy-focused)

---

## Google Home Router Limitations

**Known Limitations**:
- Google Home/Nest routers have **limited DNS configuration options**
- May not support router-level custom DNS
- DHCP DNS settings may not be configurable
- Some models require Google Home app (no web interface)

**Workarounds**:
1. Configure DNS on individual devices (most reliable)
2. Use AdGuard Home's DHCP server (if you can disable Google Home DHCP)
3. Use a network-level solution (Pi-hole on a Raspberry Pi as gateway)

---

## Alternative: Network-Level Solution

If Google Home router limitations are too restrictive, consider:

1. **Use a secondary router** as gateway with AdGuard Home
2. **Raspberry Pi** running AdGuard Home as network gateway
3. **Keep Google Home for Wi-Fi**, use another device for routing/DNS

---

## Quick Setup Script

Use the verification script to check your setup:

```bash
bash scripts/verify-dns-setup.sh
```

This will:
- Check if AdGuard Home is running
- Verify port 53 is accessible
- Test DNS resolution
- Show current DNS configuration

---

## Next Steps

After DNS is working:

1. **Configure AdGuard Home filters**:
   - Settings → Filters → DNS blocklists
   - Enable recommended filter lists
   - Add custom blocklists if needed

2. **Set up custom DNS records** (for local services):
   - Settings → DNS rewrites
   - Add: `server.unarmedpuppy.com` → `192.168.86.47`
   - Add other local services

3. **Enable query logging** (optional):
   - Settings → General settings
   - Enable query log

4. **Set up parental controls** (if needed):
   - Settings → Parental control
   - Configure time limits, blocked services

---

## References

- [AdGuard Home Documentation](https://github.com/AdguardTeam/AdGuardHome)
- [Google Home Router Support](https://support.google.com/googlenest)
- [DNS Configuration Guide](https://kb.adguard.com/en/general/dns-providers)

---

**Last Updated**: 2024-12-19  
**Server IP**: 192.168.86.47  
**AdGuard Home**: http://192.168.86.47:8083

