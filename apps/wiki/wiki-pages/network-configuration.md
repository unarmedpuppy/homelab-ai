# Network Configuration

### Firewall (UFW)

**1. Install UFW**:
```bash
sudo apt install ufw
```

**2. Allow SSH**:
```bash
sudo ufw allow 4242/tcp
```

**3. Enable UFW**:
```bash
sudo ufw enable
```

**4. Set Default Policies**:
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
```

**5. Allow Specific Services**:
```bash
sudo ufw allow 32400/tcp    # Plex
sudo ufw allow 19132/udp    # Minecraft
sudo ufw allow 28015/udp    # Rust
sudo ufw allow 28015/tcp    # Rust
sudo ufw allow 28016/tcp    # Rust (RCON)
sudo ufw allow 8080/tcp     # Rust (Web RCON)
sudo ufw allow 53/tcp       # AdGuard DNS
sudo ufw allow 53/udp       # AdGuard DNS
sudo ufw allow 51820/udp    # WireGuard VPN
```

**6. Check Status**:
```bash
sudo ufw status verbose
```

**Important**: For external traffic (game servers), don't forget to set up port forwarding on your router.

### Cloudflare Tunnel

Install and configure Cloudflare tunnel:
```bash
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb && \
sudo dpkg -i cloudflared.deb && \
sudo cloudflared service install eyJhIjoiYjk2OWY3ZmQ5MzlkYTZmOTQ0NDUyNzc0Nzg2YzViZjUiLCJ0IjoiMDQ4YmZiMjAtZjA2NC00NzU2LWJmZWEtYjM1NTg3MjQ5MzZkIiwicyI6Ik5HWTFNbU0zWWpndE9XSm1aQzAwTVRreExXSTRPREF0WkRZeVpqZ3lNalpoWldFeCJ9
```

### Reverse Proxy (Traefik)

Traefik is used as the reverse proxy with automatic HTTPS via Let's Encrypt.

**1. Create Configuration Directory**:
```bash
mkdir -p ~/server/apps/traefik/{config,logs}
```

**2. Create Traefik Configuration** (`~/server/apps/traefik/config/traefik.yml`):
```yaml
api:
  dashboard: true
  entryPoints:
    web:
      address: ":80"
    websecure:
      address: ":443"

  providers:
    docker:
      endpoint: "unix:///var/run/docker.sock"
      exposedByDefault: false
      network: my-network

certificatesResolvers:
  myresolver:
    acme:
      email: traefik@jenquist.com
      storage: acme.json
      httpChallenge:
        # Using httpChallenge means we're going to solve a challenge using port 80
        entryPoint: web
      # dnsChallenge:
        # provider: cloudflare
        # Delay before checking DNS propagation
        # delayBeforeCheck: 0

accessLog:
  filePath: "~/server/apps/traefik/logs/access.log"
  format: json

metrics:
  prometheus: {}

tracing:
  jaeger:
    samplingType: const
    samplingParam: 1.0
```

**3. Create acme.json for Certificates**:
```bash
touch ~/server/apps/traefik/config/acme.json && chmod 600 ~/server/apps/traefik/config/acme.json
```

**4. Docker Compose Example**:
See `apps/traefik/docker-compose.yml` for full configuration.

**5. Generate Basic Auth Credentials**:
```bash
sudo apt-get install apache2-utils
htpasswd -nb admin example
```

**6. Enable Traefik on Containers**:

Example labels for containers:
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.service.rule=Host(`service.server.unarmedpuppy.com`)"
  - "traefik.http.routers.service.entrypoints=websecure"
  - "traefik.http.routers.service.tls.certresolver=myresolver"
```

**7. Bypass Basic Auth for LAN**:

Example configuration to bypass auth for local IPs:
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.homepage.rule=Host(`server.unarmedpuppy.com`) && ClientIP(`192.168.1.0/24`, `76.156.139.101/24`)"
  - "traefik.http.routers.homepage.priority=99"
  - "traefik.http.routers.homepage.entrypoints=websecure"
  - "traefik.http.routers.homepage.middlewares=bypass"
  - "traefik.http.routers.homepage.tls.certresolver=myresolver"
  - "traefik.http.routers.homepage2.rule=Host(`server.unarmedpuppy.com`)"
  - "traefik.http.routers.homepage2.priority=100"
  - "traefik.http.routers.homepage2.entrypoints=websecure"
  - "traefik.http.routers.homepage2.middlewares=do-auth"
  - "traefik.http.middlewares.do-auth.chain.middlewares=homepage-auth"
  - "traefik.http.middlewares.bypass.chain.middlewares="
  - "traefik.http.middlewares.homepage-auth.basicauth.users=unarmedpuppy:$$apr1$$yE.A6vVX$$p7.fpGKw5Unp0UW6H/2c.0"
```

---