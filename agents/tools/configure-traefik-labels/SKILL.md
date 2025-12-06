---
name: configure-traefik-labels
description: Configure Traefik reverse proxy labels for Docker services
when_to_use: Setting up new apps, adding Traefik routing to existing services, standardizing Traefik configuration across services
---

# Configure Traefik Labels for Apps

Standard pattern for configuring Traefik reverse proxy labels in Docker Compose services. This ensures consistent routing, authentication, and HTTPS across all services.

## Standard Configuration Pattern

All services should follow this pattern unless they have `x-external: true` (which means no auth required).

### Required Components

1. **Enable Traefik**
2. **HTTPS Redirect** (HTTP → HTTPS)
3. **Local Network Access** (no auth, priority 100)
4. **External Access** (with auth, priority 1)
5. **Service Definition** (port mapping)
6. **Auth Middleware** (basic auth for external access)
7. **Homepage Labels** (for dashboard integration)
8. **Network Configuration** (connect to `my-network`)

## Complete Label Template

```yaml
services:
  your-service:
    image: your-image:latest
    restart: unless-stopped
    networks:
      - my-network
    ports:
      - "LOCAL_PORT:CONTAINER_PORT"  # Keep for direct access if needed
    labels:
      - "traefik.enable=true"
      
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
      - "traefik.http.services.SERVICE.loadbalancer.server.port=CONTAINER_PORT"
      - "traefik.http.middlewares.SERVICE-auth.basicauth.users=unarmedpuppy:$$apr1$$yE.A6vVX$$p7.fpGKw5Unp0UW6H/2c.0"
      - "traefik.http.middlewares.SERVICE-auth.basicauth.realm=SERVICE_NAME"
      
      # Homepage labels
      - "homepage.group=Category Name"
      - "homepage.name=Service Name"
      - "homepage.icon=si-iconname"
      - "homepage.href=https://SERVICE.server.unarmedpuppy.com"
      - "homepage.description=Service description"

networks:
  my-network:
    external: true
```

## Variable Substitutions

Replace these placeholders:
- `SERVICE` - Service name (lowercase, e.g., `planka`, `wiki`, `n8n`)
- `SERVICE_NAME` - Display name (e.g., `Planka`, `Wiki`, `n8n`)
- `CONTAINER_PORT` - Port the service listens on inside the container
- `LOCAL_PORT` - Optional: port for direct access (can be removed if not needed)
- `Category Name` - Homepage category (e.g., `Productivity & Organization`, `Infrastructure`)

## Example: Planka

```yaml
services:
  planka:
    image: ghcr.io/plankanban/planka:latest
    restart: unless-stopped
    networks:
      - my-network
    ports:
      - "3006:1337"
    environment:
      - BASE_URL=https://planka.server.unarmedpuppy.com
    labels:
      - "traefik.enable=true"
      # HTTPS redirect
      - "traefik.http.middlewares.planka-redirect.redirectscheme.scheme=https"
      - "traefik.http.routers.planka-redirect.middlewares=planka-redirect"
      - "traefik.http.routers.planka-redirect.rule=Host(`planka.server.unarmedpuppy.com`)"
      - "traefik.http.routers.planka-redirect.entrypoints=web"
      # Local network access (no auth) - highest priority
      - "traefik.http.routers.planka-local.rule=Host(`planka.server.unarmedpuppy.com`) && ClientIP(`192.168.86.0/24`)"
      - "traefik.http.routers.planka-local.priority=100"
      - "traefik.http.routers.planka-local.entrypoints=websecure"
      - "traefik.http.routers.planka-local.tls.certresolver=myresolver"
      # External access (requires auth) - lowest priority
      - "traefik.http.routers.planka.rule=Host(`planka.server.unarmedpuppy.com`)"
      - "traefik.http.routers.planka.priority=1"
      - "traefik.http.routers.planka.entrypoints=websecure"
      - "traefik.http.routers.planka.tls.certresolver=myresolver"
      - "traefik.http.routers.planka.tls=true"
      - "traefik.http.routers.planka.middlewares=planka-auth"
      # Service and auth middleware
      - "traefik.http.services.planka.loadbalancer.server.port=1337"
      - "traefik.http.middlewares.planka-auth.basicauth.users=unarmedpuppy:$$apr1$$yE.A6vVX$$p7.fpGKw5Unp0UW6H/2c.0"
      - "traefik.http.middlewares.planka-auth.basicauth.realm=Planka"
      # Homepage labels
      - "homepage.group=Productivity & Organization"
      - "homepage.name=Planka"
      - "homepage.icon=si-todoist"
      - "homepage.href=https://planka.server.unarmedpuppy.com"
      - "homepage.description=Projects, To-Do lists & Kanban"

networks:
  my-network:
    external: true
```

## Special Cases

### Services with `x-external: true`

Services marked with `x-external: true` do NOT require authentication for local or public access. Examples: `plex`, `maptapdat`, `minecraft`.

**Do NOT add:**
- Auth middleware
- Priority-based routing with ClientIP rules

**Still add:**
- HTTPS redirect
- Basic routing
- Service definition
- Homepage labels

Example (Plex):
```yaml
x-external: true

services:
  pms-docker:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.plex.rule=Host(`plex.server.unarmedpuppy.com`)"
      - "traefik.http.routers.plex.entrypoints=websecure"
      - "traefik.http.routers.plex.tls.certresolver=myresolver"
      - "traefik.http.services.plex.loadbalancer.server.port=32400"
```

### Services Without Traefik

Some services don't use Traefik (e.g., `adguard-home`, `libreddit` when Traefik is disabled).

**Use direct IP:port in homepage.href:**
```yaml
- "homepage.href=http://192.168.86.47:8083"
```

## Network Configuration

**Always add:**
```yaml
services:
  your-service:
    networks:
      - my-network

networks:
  my-network:
    external: true
```

**For multi-container services** (e.g., planka with postgres):
- Add `networks: - my-network` to ALL services that need to communicate
- Both the main service AND its dependencies (db, redis, etc.) need network access

## Cloudflare DDNS Configuration

After adding Traefik labels, add the subdomain to Cloudflare DDNS:

**File:** `apps/cloudflare-ddns/docker-compose.yml`

**Add to DOMAINS list:**
```yaml
- DOMAINS=..., existing.domains..., SERVICE.server.unarmedpuppy.com,
```

**Example:**
```yaml
- DOMAINS=..., planka.server.unarmedpuppy.com, # Add at end of list
```

## Environment Variables

Update service environment variables to use the HTTPS subdomain:

**Before:**
```yaml
- BASE_URL=http://192.168.86.47:3006
```

**After:**
```yaml
- BASE_URL=https://SERVICE.server.unarmedpuppy.com
```

Common variable names:
- `BASE_URL`
- `PUBLIC_URL`
- `URL`
- `DOMAIN`
- `HOST`

## Deployment Checklist

1. ✅ Add all Traefik labels to docker-compose.yml
2. ✅ Add service to `my-network`
3. ✅ Update environment variables (BASE_URL, etc.)
4. ✅ Update homepage.href to use subdomain
5. ✅ Add subdomain to Cloudflare DDNS config
6. ✅ Deploy and restart service
7. ✅ Verify Traefik discovers the service (check dashboard)
8. ✅ Test local access (no auth)
9. ✅ Test external access (with auth)

## Common Ports Reference

- **80** - Standard HTTP
- **3000** - Common web apps (homepage, wiki, etc.)
- **8080** - Alternative HTTP
- **1337** - Planka
- **2368** - Ghost
- **32400** - Plex
- **8200** - Paperless-ngx
- **9000** - Mealie

## Troubleshooting

### Service Not Appearing in Traefik Dashboard

1. Check `traefik.enable=true` is set
2. Verify service is on `my-network`
3. Check container is running: `docker ps | grep SERVICE`
4. Restart Traefik: `docker compose restart` in traefik directory
5. Check labels: `docker inspect CONTAINER_NAME | grep traefik`

### 404 Errors

1. Verify service port matches `loadbalancer.server.port`
2. Check service name matches container name (or use container name)
3. Verify router service references match service definition
4. Check Traefik logs: `docker logs traefik --tail 50`

### Certificate Issues

1. Verify domain is in Cloudflare DDNS
2. Check DNS propagation: `dig SERVICE.server.unarmedpuppy.com`
3. Wait for Let's Encrypt rate limits to expire (if hit)
4. Check Traefik logs for ACME errors

## Reference Services

See these working examples:
- `apps/planka/docker-compose.yml` - Complete standard setup
- `apps/n8n/docker-compose.yml` - Standard with auth
- `apps/plex/docker-compose.yml` - x-external: true (no auth)
- `apps/homepage/docker-compose.yml` - Special case with external IP bypass

