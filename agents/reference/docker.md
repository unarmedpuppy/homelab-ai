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

## Homepage Labels

For services to appear in the homepage dashboard:

```yaml
labels:
  - "homepage.group=Category"
  - "homepage.name=Service Name"
  - "homepage.icon=icon.png"
  - "homepage.href=http://192.168.86.47:PORT"
```

## Traefik Labels (HTTPS)

For services exposed via Traefik reverse proxy:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.SERVICE.rule=Host(`subdomain.server.unarmedpuppy.com`)"
  - "traefik.http.routers.SERVICE.entrypoints=websecure"
  - "traefik.http.routers.SERVICE.tls.certresolver=myresolver"
  - "traefik.http.services.SERVICE.loadbalancer.server.port=PORT"
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

