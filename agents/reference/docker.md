# Docker Patterns and Best Practices

Docker Compose patterns and conventions for the home server.

## Required Network

All services must use the external `my-network`:

```yaml
networks:
  my-network:
    external: true
```

## Common Variables

Standard environment variables for all services:

```yaml
environment:
  - TZ=America/New_York
  - PUID=1000
  - PGID=1000
```

## Homepage Labels with Traefik

All services should use Traefik reverse proxy and proper `*.server.unarmedpuppy.com` domains:

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
  - "traefik.http.services.SERVICE.loadbalancer.server.port=CONTAINER_PORT"
  - "traefik.http.middlewares.SERVICE-auth.basicauth.users=unarmedpuppy:$$apr1$$yE.A6vVX$$p7.fpGKw5Unp0UW6H/2c.0"
  - "traefik.http.middlewares.SERVICE-auth.basicauth.realm=SERVICE"
  # Homepage labels
  - "homepage.group=Category"
  - "homepage.name=Service Name"
  - "homepage.icon=icon.png"
  - "homepage.href=https://SERVICE.server.unarmedpuppy.com"
  - "homepage.description=Service description"
```

**Note**: New subdomains need to be added to `apps/cloudflare-ddns/` config.

## Common Commands

```bash
# List containers
docker ps

# View logs
docker logs <container> --tail 100

# Restart service
docker compose -f apps/X/docker-compose.yml restart

# Check disk usage
docker system df

# Validate configuration
docker compose config
```

## Troubleshooting

See `agents/tools/troubleshoot-container-failure/` for detailed troubleshooting guide.

