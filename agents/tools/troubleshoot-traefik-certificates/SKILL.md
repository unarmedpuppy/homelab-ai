---
name: troubleshoot-traefik-certificates
description: Troubleshoot Traefik SSL certificate issues - DNS and Let's Encrypt problems
when_to_use: When Traefik services show "connection is not private" errors or certificate errors
---

# Troubleshoot Traefik SSL Certificates

## Problem

Traefik services showing "connection is not private" errors or certificate errors. Common causes:

1. **Missing DNS records**: Subdomains not in Cloudflare DDNS
2. **DNS propagation delay**: DNS records not yet propagated
3. **Let's Encrypt rate limits**: Too many failed certificate requests
4. **Wildcard certificate not working**: Individual certificates being requested instead

## Diagnosis

### Check Traefik logs for certificate errors:
```bash
docker logs traefik --tail 200 | grep -i -E 'acme|certificate|error|NXDOMAIN|rateLimited'
```

### Check which subdomains are missing DNS records:
```bash
docker logs traefik --tail 100 | grep -i 'NXDOMAIN' | grep -oE '[a-z-]+\.server\.unarmedpuppy\.com' | sort -u
```

### Verify Cloudflare DDNS configuration:
```bash
# Check which domains are configured
grep DOMAINS apps/cloudflare-ddns/docker-compose.yml

# Check Cloudflare DDNS logs
docker logs cloudflare-ddns --tail 50
```

## Solution

### Step 1: Add Missing Subdomains to Cloudflare DDNS

1. Edit `apps/cloudflare-ddns/docker-compose.yml`
2. Add missing subdomains to the `DOMAINS` environment variable
3. Format: `subdomain.server.unarmedpuppy.com,` (comma-separated, no spaces)

### Step 2: Restart Cloudflare DDNS

```bash
cd apps/cloudflare-ddns
docker compose down
docker compose up -d
```

### Step 3: Wait for DNS Propagation

DNS records typically propagate within 5-10 minutes. Wait before restarting Traefik.

### Step 4: Restart Traefik

```bash
cd apps/traefik
docker compose restart
```

### Step 5: Monitor Certificate Requests

```bash
# Watch Traefik logs for certificate errors
docker logs traefik -f | grep -i -E 'acme|certificate|error'
```

## Rate Limit Issues

If you see rate limit errors:
- **Error**: `too many failed authorizations (5) for "domain" in the last 1h0m0s`
- **Solution**: Wait for the rate limit to expire (usually 1 hour) before retrying
- **Prevention**: Ensure all subdomains are in Cloudflare DDNS before requesting certificates

## Wildcard Certificate Configuration

Traefik is configured with a wildcard certificate (`*.unarmedpuppy.com`) at the entrypoint level. However, individual routers may still request certificates. The wildcard should cover all subdomains, but DNS records must exist for Let's Encrypt validation.

## Verification

After DNS propagation (5-10 minutes), verify certificates are working:

```bash
# Check if certificates are being issued
docker logs traefik --tail 50 | grep -i 'certificate.*obtained\|certificate.*renewed'

# Test a specific subdomain
curl -I https://subdomain.server.unarmedpuppy.com
```

## Related Tools

- `configure-traefik-labels/` - Configure Traefik labels for new services
- `verify-dns-setup/` - Verify DNS configuration

