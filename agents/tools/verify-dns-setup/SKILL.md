---
name: verify-dns-setup
description: Verify AdGuard Home DNS configuration and accessibility
when_to_use: After DNS configuration changes, troubleshooting DNS issues, verifying AdGuard Home setup
script: scripts/verify-dns-setup.sh
---

# Verify DNS Setup

Verifies AdGuard Home DNS configuration and accessibility.

## When to Use

- After DNS configuration changes
- Troubleshooting DNS issues
- Verifying AdGuard Home setup
- Network connectivity problems
- After router configuration changes

## Usage

```bash
# From local machine or server
bash scripts/verify-dns-setup.sh
```

## What It Checks

1. **AdGuard Home container status** - Is the container running?
2. **DNS port (53) accessibility** - Can DNS requests reach the server?
3. **DNS resolution functionality** - Does DNS actually work?
4. **Current device DNS configuration** - What DNS is your device using?
5. **AdGuard Home web interface** - Is the web UI accessible?
6. **Firewall rules** - Are ports properly configured? (if on server)

## Output

- ✓ **Green checkmarks** - Checks passing
- ! **Yellow warnings** - Issues to review
- ✗ **Red errors** - Critical problems requiring action

## Common Issues

### DNS Not Resolving

**Problem**: DNS queries not reaching AdGuard Home

**Solutions**:
1. Check router DNS settings point to `192.168.86.47`
2. Verify firewall allows port 53
3. Check AdGuard Home container is running
4. See `agents/reference/setup/GOOGLE_HOME_DNS_SETUP.md` for router setup

### Container Not Running

**Problem**: AdGuard Home container is stopped

**Solution**:
```bash
bash scripts/connect-server.sh "cd ~/server/apps/adguard-home && docker compose up -d"
```

### Port 53 Blocked

**Problem**: Firewall blocking DNS port

**Solution**:
```bash
bash scripts/connect-server.sh "sudo ufw allow 53/udp"
```

## Related Documentation

- `agents/reference/setup/GOOGLE_HOME_DNS_SETUP.md` - Complete DNS setup guide
- `apps/adguard-home/README.md` - AdGuard Home documentation

## Related Tools

- `connect-server` - Execute commands on server
- `check-service-health` - Check all services

