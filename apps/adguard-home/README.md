# AdGuard Home - Local DNS & Ad Blocking

AdGuard Home provides network-wide ad blocking and DNS filtering.

## Quick Access

- **Web Interface**: http://192.168.86.47:8083
- **DNS Server**: 192.168.86.47:53
- **Initial Setup**: http://192.168.86.47:3003 (first time only)

## Configuration

### DNS Setup

**For Google Home Mesh Routers**: See [Google Home DNS Setup Guide](../../agents/reference/setup/GOOGLE_HOME_DNS_SETUP.md)

The guide covers:
- Configuring DNS with Google Home routers (limited options)
- Device-level DNS configuration (recommended)
- Troubleshooting and verification

### Verify Setup

Run the verification script:
```bash
bash scripts/verify-dns-setup.sh
```

## Ports

- `53/tcp` - DNS (TCP)
- `53/udp` - DNS (UDP)
- `8083` - Web interface (after setup)
- `3003` - Initial setup (first time only)

## Status

Currently **disabled** (`x-enabled: false`). Enable by setting `x-enabled: true` in docker-compose.yml.

## References

- [AdGuard Home GitHub](https://github.com/AdguardTeam/AdGuardHome)
- [Google Home DNS Setup Guide](../../agents/reference/setup/GOOGLE_HOME_DNS_SETUP.md)
