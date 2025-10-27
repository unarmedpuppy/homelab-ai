# DNS Leak Prevention Guide

This guide explains how to configure DNS leak prevention in your WireGuard setup.

## Why DNS Leaks Matter

When using a VPN, if your DNS requests go to your ISP's DNS servers instead of the VPN's servers, websites you visit can be logged and tracked. This defeats the purpose of using a VPN for privacy.

## How to Configure

### 1. Edit WireGuard Configuration

Edit `wireguard/config/wg0.conf` and add DNS servers to the `[Interface]` section:

```ini
[Interface]
PrivateKey = YOUR_PRIVATE_KEY
Address = 10.8.0.2/24
# Add these DNS servers for leak prevention:
DNS = 1.1.1.1, 1.0.0.1, 9.9.9.9, 149.112.112.112

[Peer]
PublicKey = VPN_SERVER_KEY
Endpoint = your-vpn-server.com:51820
AllowedIPs = 0.0.0.0/0
```

### 2. Recommended DNS Servers

**Cloudflare (Privacy-focused):**
- Primary: `1.1.1.1`
- Secondary: `1.0.0.1`

**Quad9 (Security-focused):**
- Primary: `9.9.9.9`
- Secondary: `149.112.112.112`

**ControlD (Feature-rich):**
- Primary: `76.76.2.0`
- Secondary: `76.76.10.0`

**Google Public DNS (Fast, but not private):**
- Primary: `8.8.8.8`
- Secondary: `8.8.4.4`

**Recommendation:** Use Cloudflare (1.1.1.1) or Quad9 (9.9.9.9) for best balance of privacy and performance.

### 3. Verify DNS Configuration

After setting up your VPN, verify DNS is working:

```bash
# Check DNS servers in container
docker exec media-download-wireguard cat /etc/resolv.conf

# Test DNS resolution through VPN
docker exec media-download-wireguard dig @1.1.1.1 google.com

# Should show your VPN DNS servers, not your ISP's DNS
```

### 4. Test for DNS Leaks

Use online DNS leak test tools:

```bash
# Test public IP (should show VPN IP)
docker exec media-download-wireguard curl ifconfig.me

# Test DNS servers (should show VPN DNS)
docker exec media-download-wireguard dig TXT o-o.myaddr.l.google.com @8.8.8.8 +short
```

Visit these websites to check for DNS leaks:
- https://www.dnsleaktest.com
- https://ipleak.net
- https://dnsleak.com

### 5. Additional DNS Settings in WireGuard

You can also set DNS to specific providers that support DoH (DNS over HTTPS):

```ini
[Interface]
# ... other settings ...
DNS = 1.1.1.1, 1.0.0.1
# Prevent DNS leaks to ISP
```

### 6. Advanced: Using Unbound with DoH

For maximum privacy, you can run Unbound DNS resolver inside the WireGuard container:

1. Enable Unbound in the container
2. Configure it to use DoH upstream servers
3. Point WireGuard to use Unbound as DNS server

This requires additional configuration and is optional.

## Troubleshooting

### DNS still leaking to ISP

1. **Check WireGuard config:** Ensure DNS is set in both config file
2. **Restart WireGuard:** `docker-compose restart wireguard`
3. **Check DNS resolution:** `docker exec media-download-wireguard nslookup google.com`
4. **Flush DNS cache:** Inside container, if applicable

### DNS not resolving

1. **Check VPN connection:** WireGuard must be connected
2. **Verify DNS servers:** Test if DNS servers are reachable
3. **Check firewall:** Ensure DNS traffic is allowed
4. **Try different DNS servers:** Switch to 8.8.8.8 temporarily

### DNS tests show ISP DNS

1. Ensure `DNS = 1.1.1.1, 9.9.9.9` is in WireGuard config
2. Restart WireGuard container
3. Check if VPN is actually routing traffic: `curl ifconfig.me`
4. If still leaking, your VPN provider may not be properly configured

## Best Practices

1. **Always set DNS servers** in WireGuard config
2. **Use privacy-focused DNS** (Cloudflare or Quad9)
3. **Test regularly** for DNS leaks
4. **Monitor logs** for DNS issues
5. **Use VPN kill switch** (already configured via network_mode)
6. **Avoid ISP DNS** at all costs
7. **Use DoH if possible** for additional encryption

## Security Notes

- DNS leaks can reveal your browsing even when using VPN
- Some VPNs leak DNS by default
- Always test for DNS leaks after setup
- Consider using Tor for maximum anonymity if needed

## Quick Reference

```bash
# Set DNS in WireGuard config
echo "DNS = 1.1.1.1, 9.9.9.9" >> wireguard/config/wg0.conf

# Restart to apply
docker-compose restart wireguard

# Test for leaks
docker exec media-download-wireguard dig @1.1.1.1 example.com

# Check if DNS is leaking
docker exec media-download-wireguard cat /etc/resolv.conf
```

