# Traefik Authentication Patterns

Reference guide for configuring Traefik authentication across homelab services.

## Overview

This document covers three authentication patterns used in the homelab:

1. **Basic Auth Pattern** - For services without built-in authentication
2. **External Pattern** - For services with their own authentication (Plex OAuth, user accounts, etc.)
3. **No Traefik Pattern** - For services that don't need web routing (game servers, internal services)

## Pattern 1: Basic Auth (Services Without Built-in Auth)

Use this pattern for services that have **no built-in authentication** and need Traefik to protect them.

### When to Use
- Indexers: NZBHydra2, Jackett, Prowlarr
- Download clients with weak/no auth: qBittorrent web UI
- Simple utilities: MeTube, Excalidraw, Bedrock-Viz
- Monitoring dashboards without auth: Prometheus, some Grafana instances

### Configuration Template

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.docker.network=my-network"

  # HTTPS redirect
  - "traefik.http.middlewares.SERVICE-redirect.redirectscheme.scheme=https"
  - "traefik.http.routers.SERVICE-redirect.middlewares=SERVICE-redirect"
  - "traefik.http.routers.SERVICE-redirect.rule=Host(`SERVICE.server.unarmedpuppy.com`)"
  - "traefik.http.routers.SERVICE-redirect.entrypoints=web"

  # Local network access (no auth) - highest priority
  - "traefik.http.routers.SERVICE-local.rule=Host(`SERVICE.server.unarmedpuppy.com`) && ClientIP(`192.168.86.0/24`)"
  - "traefik.http.routers.SERVICE-local.priority=100"
  - "traefik.http.routers.SERVICE-local.entrypoints=websecure"
  - "traefik.http.routers.SERVICE-local.tls.certresolver=myresolver"

  # External access (requires auth) - lowest priority
  - "traefik.http.routers.SERVICE.rule=Host(`SERVICE.server.unarmedpuppy.com`)"
  - "traefik.http.routers.SERVICE.priority=1"
  - "traefik.http.routers.SERVICE.entrypoints=websecure"
  - "traefik.http.routers.SERVICE.tls.certresolver=myresolver"
  - "traefik.http.routers.SERVICE.tls=true"
  - "traefik.http.routers.SERVICE.middlewares=SERVICE-auth"

  # Service and auth middleware
  - "traefik.http.services.SERVICE.loadbalancer.server.port=PORT"
  - "traefik.http.middlewares.SERVICE-auth.basicauth.users=unarmedpuppy:$$apr1$$yE.A6vVX$$p7.fpGKw5Unp0UW6H/2c.0"
  - "traefik.http.middlewares.SERVICE-auth.basicauth.realm=SERVICE_NAME"
```

### How It Works
1. **Local requests** (192.168.86.0/24): Match the `-local` router (priority 100), no auth required
2. **External requests**: Fall through to the main router (priority 1), basic auth required

### Cloudflare Tunnel Consideration
Traffic via Cloudflare Tunnel comes from Cloudflare's IP, not your local network. These services will require basic auth when accessed via Cloudflare Tunnel.

---

## Pattern 2: External Pattern (Services With Built-in Auth)

Use this pattern for services that have **their own authentication** (OAuth, user accounts, API keys, etc.). No Traefik basic auth needed.

### When to Use
- OAuth-based services: Plex, Overseerr (Plex OAuth)
- Services with user account systems: Gitea, N8N, Wiki.js, Jellyfin, Immich, Home Assistant, Vaultwarden, Mattermost, Mealie, Firefly III, Paperless-NGX, FreshRSS, Calibre-Web
- Services you want accessible via Cloudflare Tunnel without double-auth

### Configuration Template

```yaml
x-external: true  # Optional marker in compose file for documentation

labels:
  - "traefik.enable=true"
  - "traefik.docker.network=my-network"

  # HTTPS redirect
  - "traefik.http.middlewares.SERVICE-redirect.redirectscheme.scheme=https"
  - "traefik.http.routers.SERVICE-redirect.middlewares=SERVICE-redirect"
  - "traefik.http.routers.SERVICE-redirect.rule=Host(`SERVICE.server.unarmedpuppy.com`)"
  - "traefik.http.routers.SERVICE-redirect.entrypoints=web"

  # Single router - no ClientIP filtering, no auth middleware
  - "traefik.http.routers.SERVICE.rule=Host(`SERVICE.server.unarmedpuppy.com`)"
  - "traefik.http.routers.SERVICE.entrypoints=websecure"
  - "traefik.http.routers.SERVICE.tls.certresolver=myresolver"
  - "traefik.http.services.SERVICE.loadbalancer.server.port=PORT"
```

### Key Differences from Basic Auth Pattern
- **No `-local` router** with ClientIP rule
- **No priority settings** (only one router)
- **No auth middleware** - service handles its own auth
- **No basicauth.users** label

### Example: Plex (Reference Implementation)

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.plex.rule=Host(`plex.server.unarmedpuppy.com`)"
  - "traefik.http.routers.plex.entrypoints=websecure"
  - "traefik.http.routers.plex.tls.certresolver=myresolver"
  - "traefik.http.routers.plex.service=plex"
  - "traefik.http.services.plex.loadbalancer.server.port=32400"
  - "traefik.http.middlewares.plex-https-redirect.redirectscheme.scheme=https"
  - "traefik.http.routers.plex.middlewares=plex-https-redirect"
```

### Cloudflare Tunnel Benefit
Services using this pattern work seamlessly via Cloudflare Tunnel because there's no basic auth layer to interfere with the service's native authentication flow.

---

## Pattern 3: No Traefik (Internal/Special Services)

Use this for services that don't need Traefik web routing.

### When to Use
- Game servers: Valheim, 7 Days to Die, Rust, Minecraft (use UDP/TCP ports directly)
- VPN services: Tailscale, WireGuard
- Internal-only services: Background jobs, batch processors
- Services with their own port exposure needs

### Configuration
Simply don't add `traefik.enable=true` or any Traefik labels. Expose ports directly if needed:

```yaml
services:
  game-server:
    ports:
      - "27015:27015/udp"
      - "27016:27016/tcp"
    # No traefik labels
```

---

## Migration Guide: Basic Auth to External Pattern

To convert a service from Basic Auth pattern to External pattern (for services with built-in auth):

### Labels to REMOVE

```yaml
# Remove local router (all 4 lines)
- "traefik.http.routers.SERVICE-local.rule=Host(`...`) && ClientIP(`192.168.86.0/24`)"
- "traefik.http.routers.SERVICE-local.priority=100"
- "traefik.http.routers.SERVICE-local.entrypoints=websecure"
- "traefik.http.routers.SERVICE-local.tls.certresolver=myresolver"

# Remove priority from main router
- "traefik.http.routers.SERVICE.priority=1"

# Remove auth middleware reference
- "traefik.http.routers.SERVICE.middlewares=SERVICE-auth"

# Remove auth middleware definition (both lines)
- "traefik.http.middlewares.SERVICE-auth.basicauth.users=..."
- "traefik.http.middlewares.SERVICE-auth.basicauth.realm=..."
```

### Labels to KEEP

```yaml
- "traefik.enable=true"
- "traefik.docker.network=my-network"

# HTTPS redirect (keep all 4 lines)
- "traefik.http.middlewares.SERVICE-redirect.redirectscheme.scheme=https"
- "traefik.http.routers.SERVICE-redirect.middlewares=SERVICE-redirect"
- "traefik.http.routers.SERVICE-redirect.rule=Host(`SERVICE.server.unarmedpuppy.com`)"
- "traefik.http.routers.SERVICE-redirect.entrypoints=web"

# Main router (keep these, remove priority and middlewares)
- "traefik.http.routers.SERVICE.rule=Host(`SERVICE.server.unarmedpuppy.com`)"
- "traefik.http.routers.SERVICE.entrypoints=websecure"
- "traefik.http.routers.SERVICE.tls.certresolver=myresolver"
- "traefik.http.routers.SERVICE.tls=true"

# Service definition
- "traefik.http.services.SERVICE.loadbalancer.server.port=PORT"

# Homepage labels (keep all)
- "homepage.group=..."
- "homepage.name=..."
- "homepage.icon=..."
- "homepage.href=..."
- "homepage.description=..."
```

---

## Current Service Audit

### Services Correctly Using Basic Auth Pattern
(No built-in auth, need Traefik protection)

| Service | Notes |
|---------|-------|
| NZBHydra2 | Indexer, no user auth |
| Jackett | Indexer, API key only |
| Prowlarr | Indexer, API key only |
| Sonarr, Radarr, Lidarr, Bazarr | API keys but no user login |
| LazyLibrarian | No auth |
| Calibre (desktop) | No web auth |
| MeTube | No auth |
| Excalidraw | No auth |
| Bedrock-Viz | No auth |
| Grafana (trading) | May have auth, verify |

### Services That Could Use External Pattern
(Have built-in auth, could remove basic auth for better Cloudflare Tunnel support)

| Service | Auth Type | Current State | Recommendation |
|---------|-----------|---------------|----------------|
| Overseerr | Plex OAuth | Basic auth | **Remove basic auth** |
| Jellyfin | User accounts | Basic auth | Consider removing |
| Gitea | User accounts | Basic auth | Consider removing |
| N8N | User accounts | Basic auth | Consider removing |
| Wiki.js | User accounts | Basic auth | Consider removing |
| Immich | User accounts | Basic auth | Consider removing |
| Home Assistant | User accounts | Basic auth | Consider removing |
| Firefly III | User accounts | Basic auth | Consider removing |
| Paperless-NGX | User accounts | Basic auth | Consider removing |
| FreshRSS | User accounts | Basic auth | Consider removing |
| Calibre-Web | User accounts | Basic auth | Consider removing |

### Services Correctly Using External Pattern

| Service | Auth Type |
|---------|-----------|
| Plex | Plex OAuth |
| Vaultwarden | Master password |
| Mattermost | User accounts |
| Mealie | User accounts |
| Harbor | User accounts |

---

## Troubleshooting

### Service not accessible via Cloudflare Tunnel
1. Check if basic auth is configured (look for `-auth` middleware)
2. If service has built-in auth, consider switching to External pattern
3. Verify DNS is configured in Cloudflare DDNS

### Basic auth prompt appearing on local network
1. Verify ClientIP rule matches your local subnet (192.168.86.0/24)
2. Check priority is set correctly (local=100, external=1)
3. Ensure both routers are defined

### 404 errors after changing patterns
1. Restart the container: `docker compose restart SERVICE`
2. Check Traefik logs: `docker logs traefik --tail 50`
3. Verify service port matches loadbalancer.server.port

---

## References

- `agents/skills/configure-traefik-labels/SKILL.md` - Detailed label configuration guide
- `apps/plex/docker-compose.yml` - Reference implementation for External pattern
- `apps/media-download/docker-compose.yml` - Reference for Basic Auth pattern
