# Homepage Dashboard Labels Reference

This document defines the standard homepage labels used for Docker services to appear on the Homepage dashboard.

## How Homepage Discovery Works

Homepage automatically discovers services via Docker labels. The homepage container has access to the Docker socket (`/var/run/docker.sock`) and reads labels from all containers on the `my-network`.

**Required Setup**:
1. Container must be on `my-network`
2. Container must have `homepage.*` labels defined
3. No manual entry in `apps/homepage/config/services.yaml` needed

## Standard Homepage Labels

Every service appearing on the homepage dashboard should have these labels:

```yaml
labels:
  - "homepage.group=<Group Name>"
  - "homepage.name=<Display Name>"
  - "homepage.icon=si-<iconname>"
  - "homepage.href=https://<service>.server.unarmedpuppy.com"
  - "homepage.description=Brief description of the service"
```

## Group Labels

**Use only these established groups.** New services must fit into an existing category.

| Group | Purpose | Examples |
|-------|---------|----------|
| `Infrastructure` | Core system services, networking, monitoring | Traefik, Grafana, AdGuard, Home Assistant, Tailscale, Cloudflare DDNS, Prometheus |
| `Productivity` | Task management, notes, documents, personal organization | Planka, Paperless-ngx, Mealie, Excalidraw, Wiki.js, Monica, Firefly III |
| `Media & Entertainment` | Streaming, media management, downloads | Plex, Jellyfin, Sonarr, Radarr, Overseerr, Immich, MeTube |
| `Finance & Trading` | Financial tracking, trading tools | Trading Bot, Tradenote, Maybe, Trading Journal |
| `Social & News` | Communication, RSS, social platforms | Mattermost, Campfire, FreshRSS, NewsBlur, Ghost, Libreddit |
| `Gaming` | Game servers, game-related tools | Minecraft, Rust, Bedrock-Viz, MapTapDat |
| `AI & Machine Learning` | AI tools, LLMs, ML services | Ollama, Local AI, Open Health |

### Choosing the Right Group

**Decision tree:**

1. Is it a core system service (proxy, DNS, monitoring, auth)? → `Infrastructure`
2. Does it manage media files or streaming? → `Media & Entertainment`
3. Is it for personal finance or trading? → `Finance & Trading`
4. Is it for communication or news consumption? → `Social & News`
5. Is it game-related? → `Gaming`
6. Is it AI/ML focused? → `AI & Machine Learning`
7. Everything else (tasks, notes, documents, personal tools) → `Productivity`

### Adding a New Group

**Do NOT create new groups without explicit approval.** If a service doesn't fit any existing category:

1. First, reconsider if it fits an existing category with a broader interpretation
2. If truly necessary, discuss with the user before adding
3. Update this reference document with the new group
4. Update `apps/homepage/config/settings.yaml` layout if ordering matters

## Icon Labels

Icons use the `si-` prefix for [Simple Icons](https://simpleicons.org/).

### Finding Icons

1. Go to [https://simpleicons.org/](https://simpleicons.org/)
2. Search for the service name or a related term
3. Click on the icon to see the slug (lowercase, hyphenated name)
4. Use `si-<slug>` as the icon value

### Icon Naming Rules

- Always use lowercase: `si-grafana` not `si-Grafana`
- Use exact slug from Simple Icons: `si-traefikproxy` not `si-traefik`
- For services without their own icon, use a related service icon:
  - News readers → `si-feedly` or `si-freshrss`
  - Trading tools → `si-tradingview`
  - Task management → `si-trello` or `si-todoist`
  - Maps/location → `si-openstreetmap` or `si-googlemaps`

### Common Icon Mappings

| Service Type | Recommended Icon |
|--------------|------------------|
| Trading/Finance | `si-tradingview`, `si-cashapp` |
| RSS/News | `si-feedly`, `si-freshrss` |
| Task Management | `si-trello`, `si-todoist` |
| Chat/Communication | `si-mattermost`, `si-basecamp` |
| Monitoring | `si-grafana`, `si-prometheus` |
| AI/ML | `si-anthropic`, `si-ollama` |
| Media Download | `si-youtube`, `si-spotify` |
| Game Server | `si-modrinth`, `si-rust` |

### Fallback Icons

If no matching Simple Icon exists, Homepage also supports:
- Material Design Icons: `mdi-icon-name`
- Dashboard Icons: Check [https://github.com/walkxcode/dashboard-icons](https://github.com/walkxcode/dashboard-icons)

## Href Labels (URLs)

**Always use HTTPS subdomains, never direct IP:port.**

### Correct Format

```yaml
- "homepage.href=https://<service>.server.unarmedpuppy.com"
```

### Rules

1. **Always use HTTPS** - All services go through Traefik with TLS
2. **Always use subdomains** - Never use `http://192.168.86.47:PORT`
3. **Use consistent naming** - Subdomain should match service name
4. **Include path if needed** - For dashboards: `https://service.server.unarmedpuppy.com/dashboard`

### Examples

| Correct | Incorrect |
|---------|-----------|
| `https://grafana.server.unarmedpuppy.com` | `http://192.168.86.47:3001` |
| `https://plex.server.unarmedpuppy.com` | `http://192.168.86.47:32400` |
| `https://trading-bot.server.unarmedpuppy.com/dashboard` | `http://localhost:8080/dashboard` |

### Exception: Services Without Traefik

Some services may not have Traefik routes (e.g., local-only services). In this case:
1. Still prefer creating a Traefik route
2. If truly not possible, use the local IP but document why

## Complete Example

Standard service with authentication:

```yaml
services:
  myservice:
    image: myservice:latest
    container_name: myservice
    restart: unless-stopped
    networks:
      - my-network
    labels:
      # Homepage labels
      - "homepage.group=Productivity"
      - "homepage.name=My Service"
      - "homepage.icon=si-myservice"
      - "homepage.href=https://myservice.server.unarmedpuppy.com"
      - "homepage.description=A service that does something useful"
      # Traefik labels...
```

External service (no auth, add `x-external: true`):

```yaml
x-external: true

services:
  publicapp:
    image: publicapp:latest
    container_name: publicapp
    labels:
      - "homepage.group=Gaming"
      - "homepage.name=Public App"
      - "homepage.icon=si-gamepad"
      - "homepage.href=https://publicapp.server.unarmedpuppy.com"
      - "homepage.description=A public-facing application"
```

## Validation Checklist

Before deploying a new service, verify:

- [ ] `homepage.group` uses an existing group from the table above
- [ ] `homepage.icon` uses valid `si-` prefix with correct slug
- [ ] `homepage.href` uses `https://` and proper subdomain format
- [ ] `homepage.name` is human-readable display name
- [ ] `homepage.description` is brief and informative
- [ ] Service is on `my-network`

## Related Documentation

- [app-implementation-agent.md](../personas/app-implementation-agent.md) - New service implementation workflow
- [infrastructure-agent.md](../personas/infrastructure-agent.md) - Traefik and DNS configuration
- [configure-traefik-labels](../tools/configure-traefik-labels/) - Traefik label patterns
