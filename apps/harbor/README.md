# Harbor Container Registry

Enterprise-class container registry with proxy cache support for offline rebuilds.

## Features

- **Proxy Cache**: Mirror Docker Hub, ghcr.io, lscr.io for offline access
- **Vulnerability Scanning**: Trivy integration for security scanning
- **Web UI**: Full management interface at https://harbor.server.unarmedpuppy.com
- **Custom Images**: Host your own Docker images

## Quick Start

1. **Create environment file**:
   ```bash
   cp .env.example .env
   # Edit .env with secure passwords
   ```

2. **Generate keys** (if not present):
   ```bash
   # Note: -traditional flag required for RSA format Harbor expects
   openssl genrsa -traditional -out config/core/private_key.pem 4096
   openssl req -new -x509 -key config/core/private_key.pem \
     -out config/registry/root.crt -days 3650 \
     -subj "/CN=harbor-token-issuer"
   chmod 644 config/core/private_key.pem config/registry/root.crt
   ```

3. **Start Harbor**:
   ```bash
   docker compose up -d
   ```

4. **Access UI**: https://harbor.server.unarmedpuppy.com
   - Default login: `admin` / `Harbor12345`
   - **Change the password immediately!**

## Setting Up Proxy Caches

After Harbor is running, configure proxy caches in the UI:

### 1. Create Registry Endpoints

Go to **Administration → Registries → New Endpoint**:

| Name | Provider | Endpoint URL |
|------|----------|--------------|
| docker-hub | Docker Hub | https://registry-1.docker.io |
| ghcr | GitHub GHCR | https://ghcr.io |
| lscr | Docker Registry | https://lscr.io |

### 2. Create Proxy Cache Projects

Go to **Projects → New Project**:

| Project Name | Access Level | Proxy Cache | Registry |
|--------------|--------------|-------------|----------|
| docker-hub | Public | ✓ | docker-hub |
| ghcr | Public | ✓ | ghcr |
| lscr | Public | ✓ | lscr |
| library | Private | ✗ | - |

### 3. Pull Images Through Cache

```bash
# Instead of: docker pull postgres:17-alpine
docker pull harbor.server.unarmedpuppy.com/docker-hub/library/postgres:17-alpine

# Instead of: docker pull ghcr.io/gethomepage/homepage:latest
docker pull harbor.server.unarmedpuppy.com/ghcr/gethomepage/homepage:latest

# Instead of: docker pull lscr.io/linuxserver/sonarr:latest
docker pull harbor.server.unarmedpuppy.com/lscr/linuxserver/sonarr:latest
```

## Migrating Custom Images

Push your existing custom images to the `library` project:

```bash
# Tag and push
docker tag registry.server.unarmedpuppy.com/pokedex:latest \
  harbor.server.unarmedpuppy.com/library/pokedex:latest
docker push harbor.server.unarmedpuppy.com/library/pokedex:latest
```

## Docker Compose Image Updates

Update your docker-compose files to use Harbor:

```yaml
# Before
image: postgres:17-alpine

# After (using proxy cache)
image: harbor.server.unarmedpuppy.com/docker-hub/library/postgres:17-alpine
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Traefik                              │
│                   (harbor.server.unarmedpuppy.com)           │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                     harbor-proxy                             │
│                       (nginx)                                │
└──────┬──────────┬──────────┬──────────┬────────────────────┘
       │          │          │          │
┌──────▼──┐ ┌─────▼────┐ ┌───▼────┐ ┌───▼───────┐
│  portal │ │   core   │ │registry│ │jobservice │
│  (UI)   │ │  (API)   │ │(images)│ │  (async)  │
└─────────┘ └────┬─────┘ └───┬────┘ └───────────┘
                 │           │
           ┌─────▼─────┬─────▼─────┐
           │  harbor-db│harbor-redis│
           │ (postgres)│           │
           └───────────┴───────────┘
```
